from reader import ReadData
from tokenizer import tokenize


def build_spimi_index_from_pairs(pairs):
    idx = {}
    prev_doc = 0

    for term, doc_id in pairs:
        if doc_id < prev_doc:
            raise ValueError("SPIMI requires pairs in increasing NEWID order")
        prev_doc = doc_id

        docs = idx.setdefault(term, [])
        if not docs or docs[-1] != doc_id:
            docs.append(doc_id)

    return idx


def build_spimi_index(folder, *, tokenizer_options=None):
    def document_pairs():
        for doc_id, text in ReadData(folder):
            for term in tokenize(text, **(tokenizer_options or {})):
                yield term, doc_id


    return build_spimi_index_from_pairs(document_pairs())
