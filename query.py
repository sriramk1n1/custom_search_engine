import json
from nltk.stem import PorterStemmer
import os
from urllib.parse import unquote
import requests
from bs4 import BeautifulSoup as bs
from urllib.parse import quote
import google.generativeai as genai
from requests import request

stemmer = PorterStemmer()

def page_rank(query):
    dfreq = dict()
    with open("doc_freq", "r") as f:
        dfreq = json.load(f)
    no_of_doc = len(os.listdir("index"))

    query = list(map(str.upper, query.split()))
    pdict = {}
    for filename in os.listdir("index"):
        rating = 0
        tdict = {}
        with open(os.path.join("index", filename), "r", encoding="utf-8") as f:
            tdict = json.load(f)
        for j in query:
            j = stemmer.stem(j).lower()
            rating += tdict.get(j, 0) * ((no_of_doc) / (dfreq.get(j, no_of_doc)))
        pdict[filename] = rating

    psorted = sorted(pdict.items(), key=lambda x: x[1], reverse=True)[:10]
    results = [{"url": unquote(item[0]), "score": item[1]} for item in psorted]
    urls = [result['url'] for result in results]

    return {"urls": urls, "no_of_docs": no_of_doc}


GOOGLE_API_KEY=""
genai.configure(api_key=GOOGLE_API_KEY)


def generate_context(url,local=True):
    if url.endswith("pdf"):
        return ""
    if local==True:
        context = ""
        with open("data/"+quote(url,safe='')[:201],"r") as f:
            context = f.read()
        print(len(context))
        return context
    else:
        user_agent = 'Mozilla/5.0'
        headers = {'User-Agent': user_agent }
        html_page=requests.get(url,headers)
        soup = bs(html_page.content,'html.parser')
        text = soup.get_text()
        print(len(text))
        return text
    
def generate_summary(query, url):
    context = generate_context(url,local=False)
    prompt = "You are a assistant who will be given with context and query. You need to answer question based on facts mentioned in context and nothing else. The context and query is as follows:"

    user_query=f" Context: {context}\n Query: {query}"
    model = genai.GenerativeModel('gemini-1.5-flash')
    res = ""
    for chunk in model.generate_content(prompt+user_query,stream=True):
        res+=chunk.text
    return res
