import nltk
from nltk.tokenize import word_tokenize

nltk.download('punkt_tab', quiet=True)

def tokenize(text):
    return [t for t in word_tokenize(text.lower()) if t.isalnum()]