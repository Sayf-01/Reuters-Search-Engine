def sort_and_dedupe(F):
    return sorted(set(F))

def build_index(sorted_F):
    index = {}
    for term, docid in sorted_F:
        index.setdefault(term, []).append(docid)
    return index