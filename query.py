from tokenizer import tokenize


def _query_terms(query_text, tokenizer_options):
    raw = tokenize(query_text)
    if not raw:
        raise ValueError("Query must contain at least one alphanumeric term")
    cooked = tokenize(query_text, **tokenizer_options)
    return raw, cooked


def single_term_query(index, query, *, tokenizer_options=None):
    opts = tokenizer_options or {}
    raw, cooked = _query_terms(query, opts)
    if len(raw) != 1:
        raise ValueError("Single-term query must contain exactly one term")
    return [] if not cooked else index.get(cooked[0], [])


def intersect_postings(left, right):
    res = []
    i = j = 0

    while i < len(left) and j < len(right):
        if left[i] == right[j]:
            res.append(left[i])
            i += 1
            j += 1
        elif left[i] < right[j]:
            i += 1
        else:
            j += 1

    return res


def and_query(index, query, *, tokenizer_options=None):
    raw, cooked = _query_terms(
        query, tokenizer_options or {}
    )
    if len(cooked) != len(raw):
        return []
    docs = [index.get(term, []) for term in cooked]
    docs.sort(key=len)

    if not docs[0]:
        return []

    res = docs[0]
    for postings in docs[1:]:
        res = intersect_postings(res, postings)
        if not res:
            break

    return res
