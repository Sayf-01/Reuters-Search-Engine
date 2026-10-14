from reader import ReadData
from tokenizer import tokenize


def build_spimi_index_from_pairs(pairs):
    index = {}
    previous_docid = 0

    for term, docid in pairs:
        if docid < previous_docid:
            raise ValueError("SPIMI requires pairs in increasing NEWID order")
        previous_docid = docid

        postings = index.setdefault(term, [])
        if not postings or postings[-1] != docid:
            postings.append(docid)

    return index


def build_spimi_index(folder, *, tokenizer_options=None):
    def iter_pairs():
        for docid, text in ReadData(folder):
            for term in tokenize(text, **(tokenizer_options or {})):
                yield term, docid

    return build_spimi_index_from_pairs(iter_pairs())
