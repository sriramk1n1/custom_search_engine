from flask import Flask, jsonify, render_template, request, redirect, url_for, session, send_file
from werkzeug.security import generate_password_hash
from crud import add_user, add_page, get_all_pages_for_user, is_valid_user, delete_page, add_url_to_hash, get_url_from_hash, set_crawling, is_user_premium
from threading import Thread
import hashlib
from Crawler_tf import MainCrawl
import shutil
from functools import wraps
import json
import os
from urllib.parse import unquote
from nltk.stem import PorterStemmer
from flask_socketio import SocketIO, emit
from others import generate_context, getgURL, genai
import re
import logging

# Initialize Flask and Flask-SocketIO
app = Flask(__name__)
socketio = SocketIO(app)
app.secret_key = 'custom_search'
stemmer = PorterStemmer()

# -------------------------
# Configure Logging
# -------------------------

# Configure Logging
log_file = "app.log"
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.StreamHandler()
                    ])

# Set up File Handler separately
file_handler = logging.FileHandler(log_file)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

logger = logging.getLogger(__name__)
logger.addHandler(file_handler)
logger.propagate = False  # Prevent Flask's default logger from handling it


# -------------------------
# Helper Functions
# -------------------------

def login_required(f):
    """Decorator to restrict access to logged-in users."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'email' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def gethash(input_str):
    """Generate a SHA-256 hash for a given input string."""
    return hashlib.sha256(input_str.encode()).hexdigest()

def get_base_url(url):
    """Extract the base URL from a full URL."""
    url += "/"
    match = re.findall(r"https?://([^/]+)/", url)
    return match[0] if match else ""

# -------------------------
# Route Handlers
# -------------------------

@app.route('/')
@login_required
def index():
    """Render the index page for logged-in users."""
    logger.info("User accessed the index page.")
    return render_template('index.html')

@app.route('/register', methods=['POST', 'GET'])
def register():
    """Handle user registration."""
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        hashed_password = generate_password_hash(password)
        add_user(email, hashed_password)
        logger.info(f"New user registered: {email}")
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['POST', 'GET'])
def login():
    """Handle user login."""
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if is_valid_user(email, password):
            session["email"] = email
            logger.info(f"User logged in: {email}")
            return redirect(url_for('index'))
        logger.warning(f"Failed login attempt for: {email}")
        return render_template('login.html')
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Log the user out and redirect to index."""
    email = session.get("email")
    session.pop('email', None)
    logger.info(f"User logged out: {email}")
    return redirect(url_for('index'))

@app.route('/crawl', methods=['POST'])
def crawl():
    """Initiate a web crawl based on the user's provided parameters."""
    data = request.get_json()
    url = data.get('url')
    threads = int(data.get("threads", 1))
    pattern = data.get("pattern", "")
    iterations = int(data.get("iterations", 1))
    links_to_crawl = int(data.get("linksToCrawl", 10))
    socket_id = data.get("socket_id")
    base_url = get_base_url(url)

    if not url:
        logger.error("Crawl initiation failed: No URL provided")
        return jsonify({'error': 'No URL provided'}), 400

    url_hash = gethash(base_url)
    set_crawling(url_hash)
    add_url_to_hash(url_hash, base_url)
    add_page(session["email"], url_hash, url, "Pending")

    logger.info(f"Starting crawl for {url} with hash {url_hash}")

    # Start the crawler in a new thread
    thread = Thread(target=MainCrawl, args=(socketio, socket_id,  url, url_hash, links_to_crawl, threads, pattern, iterations))
    thread.start()

    return jsonify({"id": url_hash, "url": url, "status": "Pending..."}), 200

@app.route('/query', methods=['POST'])
def process_query():
    """Process search queries and return relevant documents."""
    url_hash = request.form["hash"]
    query = request.form["query"]
    path = f"data/{url_hash}/"
    
    # Load document frequencies and initialize variables
    try:
        with open(path + "doc_freq", "r") as f:
            doc_freq = json.load(f)
        logger.info(f"Loaded document frequencies for query on {url_hash}")
    except FileNotFoundError:
        logger.error("Document frequency file not found.")
        return jsonify({"error": "Document frequency file not found."}), 500
    
    num_docs = len(os.listdir(path + "index"))

    # Process and rank documents based on query
    query_tokens = [stemmer.stem(token.lower()) for token in query.upper().split()]
    doc_scores = {}

    for filename in os.listdir(path + "index"):
        with open(os.path.join(path + "index", filename), "r", encoding="utf-8") as f:
            term_freq = json.load(f)
        
        score = sum(term_freq.get(token, 0) * (num_docs / doc_freq.get(token, num_docs)) for token in query_tokens)
        doc_scores[filename] = score

    # Return top 10 results
    sorted_docs = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)[:10]
    results = [{"url": unquote(item[0]), "score": item[1]} for item in sorted_docs]

    logger.info(f"Query processed for {url_hash} with query '{query}'")
    return jsonify({"urls": [result['url'] for result in results], "no_of_docs": num_docs})

@app.route('/crawlnext', methods=['POST'])
def crawlnext():
    """Continue crawling the next set of links from a URL."""
    data = request.get_json()
    url = data.get('url')
    threads = int(data.get("threads", 1))
    pattern = data.get("pattern", "")
    iterations = int(data.get("iterations", 1))
    links_to_crawl = int(data.get("linksToCrawl", 10))
    socket_id = data.get("socket_id")

    if not url:
        logger.error("Next crawl initiation failed: No URL provided")
        return jsonify({'error': 'No URL provided'}), 400

    url_hash = gethash(get_base_url(url))
    set_crawling(url_hash)

    # Start next crawl in a new thread
    thread = Thread(target=MainCrawl, args=(socketio,socket_id, url, url_hash, links_to_crawl, threads, pattern, iterations))
    thread.start()

    logger.info(f"Continuing crawl for {url} with hash {url_hash}")
    return jsonify({"url": url}), 200

@app.route('/pages', methods=['GET'])
def get_pages():
    """Retrieve all pages for the logged-in user."""
    pages = get_all_pages_for_user(session["email"])
    response_data = [{"id": page.pageid, "status": page.status, "url": page.url} for page in pages]
    logger.info(f"Pages retrieved for user: {session['email']}")
    return jsonify(response_data), 200

@app.route('/delete', methods=['POST'])
def delete():
    """Delete a page based on page ID."""
    page_id = request.form["pageid"]
    delete_page(page_id, session["email"])
    logger.info(f"Page deleted for user {session['email']}: Page ID {page_id}")
    return "Deleted"

@app.route('/search/<hash>')
def searchpage(hash):
    """Render the search page with a specific hash."""
    url = get_url_from_hash(hash)
    logger.info(f"Search page accessed for hash: {hash}")
    return render_template('search.html', url=url, hash=hash)

@socketio.on('summary')
def handle_summary(data):
    """Generate and emit a summary based on user query if authorized."""
    query = data.get('query')
    url = data.get('url')
    if is_user_premium(session["email"]):
        resolved_url = getgURL(query, url)
        if resolved_url is None:
            emit('summary', {'chunk': "Something went wrong, try again later."})
            return
        context = generate_context(resolved_url, local=False)
        prompt = "You are an assistant providing answers based solely on context."

        user_query = f" Context: {context}\n Query: {query}"
        model = genai.GenerativeModel('gemini-1.5-flash')
        for chunk in model.generate_content(prompt + user_query, stream=True):
            emit('summary', {'chunk': chunk.text})
        logger.info(f"Summary generated for query: {query}")
    else:
        emit('summary', {'chunk': "User is not authorized for summary."})
        logger.warning(f"Unauthorized summary request by user {session['email']}")

@app.route('/download/<hashval>', methods=['GET'])
def download_zip(hashval):
    """Package and send data files as a zip archive for download."""
    try:
        shutil.copytree(f"data/{hashval}", "output/")
        shutil.copy2("query.py", "output/query.py")
        shutil.make_archive("output", "zip", "output")
        logger.info(f"Download archive created for hash: {hashval}")
        return send_file('output.zip', as_attachment=True, download_name=f"{hashval}.zip")
    except Exception as e:
        logger.error(f"Error creating download archive for hash {hashval}: {e}")
        return str(e), 500
    finally:
        if os.path.exists('output.zip'):
            os.remove('output.zip')
        shutil.rmtree("output")

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=80)
