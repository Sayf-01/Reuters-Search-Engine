from reader import ReadData
from tokenizer import tokenize


def build_pairs(folder, limit=None, *, tokenizer_options=None):
    F = []
    for newid, fullTxt in ReadData(folder):
        for term in tokenize(fullTxt, **(tokenizer_options or {})):
            F.append((term, newid))
            if limit and len(F) >= limit:
                return F
    return F