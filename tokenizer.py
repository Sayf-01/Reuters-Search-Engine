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
    tokens = TOKEN_PATTERN.findall(text)

    if remove_numbers:
        tokens = [token for token in tokens if not token.isdigit()]
    if case_fold:
        tokens = [token.lower() for token in tokens]
    if stopwords is not None:
        tokens = [token for token in tokens if token not in stopwords]
    if stemming:
        tokens = [_stem_token(token) for token in tokens]

    return tokens
