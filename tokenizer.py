from functools import lru_cache
import re

from nltk.stem import PorterStemmer

TOKEN_PATTERN = re.compile(r"[A-Za-z0-9]+")
_PORTER_STEMMER = PorterStemmer()


@lru_cache(maxsize=100_000)
def _stem_token(token):
    return _PORTER_STEMMER.stem(token)


def tokenize(
    text,
    *,
    remove_numbers=False,
    case_fold=False,
    stopwords=None,
    stemming=False,
):
    data = TOKEN_PATTERN.findall(text)

    if remove_numbers:
        data = [word for word in data if not word.isdigit()]

    if case_fold:
        data = [word.lower() for word in data]

    if stopwords is not None:
        data = [word for word in data if word not in stopwords]

    if stemming:
        data = [_stem_token(word) for word in data]

    return data
