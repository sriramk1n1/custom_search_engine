import requests
from bs4 import BeautifulSoup as bs
from urllib.parse import quote
import google.generativeai as genai
from requests import request

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
    
