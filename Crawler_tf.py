import os
import re
import json
import requests
import string
import threading
import logging
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from urllib.parse import urljoin, quote
from bs4 import BeautifulSoup as bs
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
import nltk
from crud import update_status

# Download required NLTK resources
nltk.download('stopwords', quiet=True)
nltk.download('punkt', quiet=True)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Constants
PATTERN = ""
THREADS = 100
ITERATIONS = 1
stop_words = set(stopwords.words('english'))
punctuation = set(string.punctuation)
lock = threading.Lock()
stemmer = PorterStemmer()

def load_crawled_urls(prefix=""):
    """Load crawled URLs from file."""
    try:
        with open(os.path.join(prefix, "crawled.txt"), "r") as crawled_file:
            return set(line.strip() for line in crawled_file)
    except FileNotFoundError:
        logging.warning("Crawled file not found. Returning empty set.")
        return set()

def load_uncrawled_urls(num_urls=100, prefix=""):
    """Retrieve uncrawled URLs, returning a specified number of entries."""
    uncrawled_file_path = os.path.join(prefix, "uncrawled.txt")
    try:
        with open(uncrawled_file_path, "r") as uncrawled_file:
            urls = [line.strip() for line in uncrawled_file]

        selected_urls = set(urls[:num_urls])
        remaining_urls = urls[num_urls:]

        with open(uncrawled_file_path, "w") as uncrawled_file:
            for url in remaining_urls:
                uncrawled_file.write(url + '\n')

        return selected_urls
    except FileNotFoundError:
        logging.warning("Uncrawled file not found. Returning empty set.")
        return set()

def extract_base_url(url):
    """Extract the base URL from a given URL."""
    url += "/"  
    match = re.findall(r"(https?://[^/]+)/", url)
    return match[0] if match else ""

def save_word_frequency(word_freq, url, text, prefix=""):
    """Save word frequency and text content to storage files."""
    sorted_word_freq = dict(sorted(word_freq.items(), key=lambda item: item[1], reverse=True))

    with open(os.path.join(prefix, "index", quote(url, safe='')[:201]), "w") as f:
        json.dump(sorted_word_freq, f)
    with open(os.path.join(prefix, "data", quote(url, safe='')[:201]), "w") as f:
        f.write(text)

def update_document_frequency(word_freq, document_freq):
    """Update document frequency count, with thread safety."""
    with lock:
        for key, val in word_freq.items():
            document_freq[key] = document_freq.get(key, 0) + 1

def filter_word_frequency(word_freq):
    """Filter out stop words and punctuation from word frequency."""
    with lock:
        to_remove = {key for key in word_freq if key.lower() in stop_words or key in punctuation}
    for key in to_remove:
        del word_freq[key]

def remove_punctuation(text):
    """Remove punctuation from a text string."""
    return re.sub(r'[^\w\s]', '', text)

def calculate_term_frequency(text, url, prefix, document_freq):
    """Calculate and save term frequency, updating document frequency count."""
    cleaned_text = re.sub(r'\s+', ' ', text).strip()  
    words = [remove_punctuation(word).upper() for word in cleaned_text.split() if word.isalpha()]
    words = [stemmer.stem(word) for word in words]  
    word_freq = Counter(words)  

    filter_word_frequency(word_freq)
    save_word_frequency(word_freq, url, cleaned_text, prefix)
    update_document_frequency(word_freq, document_freq)

def process_html_content(url, soup, prefix, document_freq):
    """Process HTML content for term frequency calculation."""
    text = soup.get_text()  
    calculate_term_frequency(text, url, prefix, document_freq)

def update_crawled_file(url_set, file_path):
    """Update a file with a set of URLs."""
    with open(file_path, "w") as file:
        for url in url_set:
            file.write(url + '\n')

def update_uncrawled_file(obtained, file_path):
    with open(file_path, "r") as uncrawled_file:
        urls = set(line.strip() for line in uncrawled_file)

    urls.update(obtained)
    count = len(urls)
    with open(file_path, "w") as uncrawled_file:
        for url in urls:
            uncrawled_file.write(url + '\n')
    return count

def load_document_frequency(prefix=""):
    """Load document frequency from file, if available."""
    document_freq = {}
    doc_freq_path = os.path.join(prefix, "doc_freq")
    if os.path.exists(doc_freq_path):
        with open(doc_freq_path, "r") as f:
            document_freq = json.load(f)
    return document_freq

def is_valid_link(url):
    """Determine if a URL points to a valid HTML page."""
    return not any(url.lower().endswith(ext) for ext in ["jpg", "jpeg", "pdf", "png", "webp", "xls", "xlsx", "PDF"])

def crawl_url(url, obtained_urls, url_index, prefix, document_freq, crawled_set, uncrawled_total, count, socketio, socket_id):
    """Crawl the given URL, extracting hyperlinks and calculating term frequency."""
    if not is_valid_link(url):
        logging.info(f"Skipping invalid URL: {url}")
        return

    base_url = extract_base_url(url)
    headers = {'User-Agent': 'Mozilla/5.0'}

    try:
        html_page = requests.get(url, headers=headers, timeout=5)  
        if html_page.status_code != 200:
            logging.warning(f"Failed to retrieve {url}: {html_page.status_code}")
            return

        soup = bs(html_page.content, 'html.parser')
        process_html_content(url, soup, prefix, document_freq)
        
        new_links = []
        for anchor in soup.find_all('a'):
            link = urljoin(base_url, anchor.get('href'))
            if link not in crawled_set and link not in obtained_urls and base_url in link and (PATTERN in link):
                new_links.append(link)

        with lock:
            count["value"]+=1
            socketio.emit('count', {"value":f"{count["value"]}/{uncrawled_total}","hash":prefix[5:]}, to=socket_id)
            obtained_urls.update(new_links)
            logging.info(f"({url_index}/{uncrawled_total}) Extracted {len(new_links)} URLs from {url}")

    except requests.RequestException as e:
        logging.error(f"Error crawling {url}: {e}")

def MainCrawl(socketio, socket_id, seed_url, prefix="", max_urls=100, num_threads=100, pattern="", iterations=1):
    """Orchestrate the main crawling process with configuration parameters."""
    global THREADS, ITERATIONS, PATTERN
    THREADS = num_threads
    ITERATIONS = iterations
    PATTERN = pattern
    prefix = f"data/{prefix}"
    
    os.makedirs("data", exist_ok=True)
    os.makedirs(os.path.join(prefix, "index"), exist_ok=True)
    os.makedirs(os.path.join(prefix, "data"), exist_ok=True)
    
    for file in ["uncrawled.txt", "crawled.txt"]:
        if not os.path.exists(os.path.join(prefix, file)):
            open(os.path.join(prefix, file), "w").close()

    try:
        for _ in range(ITERATIONS):
            uncrawled_urls = load_uncrawled_urls(num_urls=max_urls, prefix=prefix)
            if not uncrawled_urls and seed_url:
                logging.info(f"Adding seed URL to uncrawled set: {seed_url}")
                with open(os.path.join(prefix, "uncrawled.txt"), "a") as file:
                    file.write(seed_url + '\n')
                uncrawled_urls.add(seed_url)

            obtained_urls, crawled_set = set(), load_crawled_urls(prefix)
            document_freq = load_document_frequency(prefix)
            uncrawled_total = len(uncrawled_urls)
            futures = []

            count = dict()
            count["value"]=0
            with ThreadPoolExecutor(max_workers=THREADS) as executor:
                for idx, url in enumerate(uncrawled_urls, start=1):
                    future = executor.submit(crawl_url, url, obtained_urls, idx, prefix, document_freq, crawled_set, uncrawled_total, count, socketio, socket_id)
                    futures.append(future)

                for future in futures:
                    try:
                        future.result(timeout=10)
                    except TimeoutError:
                        logging.warning("A thread has timed out.")
                    except Exception as e:
                        logging.error(f"Thread encountered an error: {e}")

            crawled_set.update(uncrawled_urls)
            update_crawled_file(crawled_set, os.path.join(prefix, "crawled.txt"))
            uncrawled_count = update_uncrawled_file(obtained_urls, os.path.join(prefix,"uncrawled.txt"))

            logging.info(f"Iteration complete. Crawled: {len(crawled_set)}, Remaining: {len(obtained_urls)}")
            update_status(prefix[5:], f"{len(crawled_set)} crawled, {uncrawled_count} remaining, Stopped.")
            socketio.emit('update')

    except KeyboardInterrupt:
        logging.info("Crawling interrupted. Saving state...")
        update_crawled_file(crawled_set, os.path.join(prefix, "crawled.txt"))
        update_uncrawled_file(obtained_urls, os.path.join(prefix, "uncrawled.txt"))

    finally:
        with open(os.path.join(prefix, "doc_freq"), "w") as f:
            json.dump(document_freq, f)

if __name__ == "__main__":
    seed_url = "https://wikipedia.com/wiki/Kannada" 
    MainCrawl(None, seed_url, "test")
