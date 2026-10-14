from tokenizer import tokenize


def _query_terms(query, tokenizer_options):
    original_terms = tokenize(query)
    if not original_terms:
        raise ValueError("Query must contain at least one alphanumeric term")
    terms = tokenize(query, **tokenizer_options)
    return original_terms, terms


def single_term_query(index, query, *, tokenizer_options=None):
    options = tokenizer_options or {}
    original_terms, terms = _query_terms(query, options)
    if len(original_terms) != 1:
        raise ValueError("Single-term query must contain exactly one term")
    if not terms:
        return []
    return index.get(terms[0], [])


def intersect_postings(left, right):
    intersection = []
    left_pos = 0
    right_pos = 0

    while left_pos < len(left) and right_pos < len(right):
        if left[left_pos] == right[right_pos]:
            intersection.append(left[left_pos])
            left_pos += 1
            right_pos += 1
        elif left[left_pos] < right[right_pos]:
            left_pos += 1
        else:
            right_pos += 1

    return intersection


def and_query(index, query, *, tokenizer_options=None):
    original_terms, terms = _query_terms(query, tokenizer_options or {})
    if len(terms) != len(original_terms):
        return []
    postings_lists = [index.get(term, []) for term in terms]
    postings_lists.sort(key=len)

    if not postings_lists[0]:
        return []

    result = postings_lists[0]
    for postings in postings_lists[1:]:
        result = intersect_postings(result, postings)
        if not result:
            break

    return result
