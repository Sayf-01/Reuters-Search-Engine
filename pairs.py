from reader import ReadData
from tokenizer import tokenize


def build_pairs(folder, limit=None, *, tokenizer_options=None):
    pairs = []
    for doc_id, text in ReadData(folder):
        for term in tokenize(text, **(tokenizer_options or {})):
            pairs.append((term, doc_id))
            if limit and len(pairs) >= limit:
                return pairs
    return pairs