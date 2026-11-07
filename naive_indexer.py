def sort_and_dedupe(F):
    return sorted(set(F))


def build_index(sorted_F):
    idx = {}
    for term, document_id in sorted_F:
        idx.setdefault(term, []).append(document_id)
    return idx