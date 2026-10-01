import os
import re
import html
import nltk
import time
nltk.download('punkt_tab')
from nltk.tokenize import word_tokenize



''' we'll be iterationg through all the files in the DATA directory, and extracting the relevant information from each article 
     we'll be using regular expressions to extract the information we need, and then we'll be storing it in a dictionary for later use.'''      
def ReadData(DATA): 
    for filename in os.listdir(DATA):
        full_path = os.path.join(DATA, filename)

        with open(full_path, 'r', encoding='latin-1') as f:
            content = f.read()
        
        articles = re.findall(r'<REUTERS.*?</REUTERS>', content, re.DOTALL)
        for article in articles:
            newidMatch = re.search(r'NEWID="(\d+)"', article)
            if newidMatch:
                newid = newidMatch.group(1).strip()
            else: 
                newid = None

            titleMatch = re.search(r'<TITLE>(.*?)</TITLE>', article, re.DOTALL)
            if titleMatch:
                title = titleMatch.group(1).strip()
                title = html.unescape(title)
            else: 
                title = ''

            bodyMatch = re.search(r'<BODY>(.*?)</BODY>', article, re.DOTALL)
            if bodyMatch:
                body = bodyMatch.group(1).strip()
                body = html.unescape(body)
            else:
                body = ''
            yield (newid, title + ' ' + body)

