from flask import Flask, request, jsonify
from others import genai, generate_context, getgURL
import os
import json
from urllib.parse import unquote
from nltk.stem import PorterStemmer
import hashlib
import re
from flask_cors import CORS
from crud import is_page_crawled

stemmer = PorterStemmer()
app = Flask(__name__)
CORS(app, resource={
    r"/*":{
        "origins":"*"
    }
})



def get_base_url(url):
    """Extract the base URL from a given URL."""
    url += "/"  # Ensure there's a trailing slash
    match = re.findall(r"https?://([^/]+)/", url)
    return match[0] if match else ""

def gethash(str):
    return hashlib.sha256(str.encode()).hexdigest()


@app.route('/query', methods=['POST'])
def handle_query():
    data = request.get_json()
    query = data.get('query')
    url = data.get('url')
    url = get_base_url(url)
    if is_page_crawled(url):
        print(url,query)
        hash = gethash(url)
        if not query:
            return jsonify({"error": "No query provided"}), 400
        
        url = getgURL(query,url)
        context = generate_context(url,local=False)
        prompt = "You are a assistant who will be given with context and query. You need to answer question based on facts mentioned in context and nothing else. The context and query is as follows:"

        user_query=f" Context: {context}\n Query: {query}"
        model = genai.GenerativeModel('gemini-1.5-flash')
        results = ""
        for chunk in model.generate_content(prompt+user_query,stream=True):
            results+=chunk.text
        
        path = "data/"+hash+"/"
        dfreq = dict()
        with open(path+"doc_freq", "r") as f:
            dfreq = json.load(f)
        no_of_doc = len(os.listdir(path+"index"))

        query = list(map(str.upper, query.split()))
        pdict = {}
        for filename in os.listdir(path+"index"):
            rating = 0
            tdict = {}
            with open(os.path.join(path+"index", filename), "r", encoding="utf-8") as f:
                tdict = json.load(f)
            for j in query:
                j = stemmer.stem(j).lower()
                rating += tdict.get(j, 0) * ((no_of_doc) / (dfreq.get(j, no_of_doc)))
            pdict[filename] = rating
        

        psorted = sorted(pdict.items(), key=lambda x: x[1], reverse=True)[:10]
        result = [{"url": unquote(item[0]), "score": item[1]} for item in psorted]
        urls = [res['url'] for res in result]

        return jsonify({"results": results, "links": urls})
    else:
        return jsonify({"results": "This page is not crawled."})


if __name__ == '__main__':
    # Run the Flask app
    app.run(host='0.0.0.0', port=8008, debug=True)
