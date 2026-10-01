from reader import ReadData
from tokenizer import tokenize

def build_pairs(folder, limit=None):
    F = []
    for newid, fullTxt in ReadData(folder):
        for term in tokenize(fullTxt):
            F.append((term, newid))
            if limit and len(F) >= limit:
                return F
    return F