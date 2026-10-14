from collections import Counter

from reader import ReadData
from spimi_indexer import build_spimi_index
from tokenizer import tokenize


def _ranked_terms(folder):
    frequencies = Counter()
    for _, text in ReadData(folder):
        frequencies.update(
            tokenize(text, remove_numbers=True, case_fold=True)
        )

    return sorted(
        frequencies,
        key=lambda term: (-frequencies[term], term),
    )


def most_frequent_terms(folder, count):
    if count < 0:
        raise ValueError("Stop-word count must be non-negative")
    return set(_ranked_terms(folder)[:count])


def _percentage_change(value, reference):
    if not reference:
        return 0.0
    return (value / reference - 1) * 100


def compression_variants(folder):
    ranked_terms = _ranked_terms(folder)
    stop_30 = set(ranked_terms[:30])
    stop_150 = set(ranked_terms[:150])

    return [
        ("unfiltered", {}),
        ("no numbers", {"remove_numbers": True}),
        (
            "case folding",
            {"remove_numbers": True, "case_fold": True},
        ),
        (
            "30 stop words",
            {
                "remove_numbers": True,
                "case_fold": True,
                "stopwords": stop_30,
            },
        ),
        (
            "150 stop words",
            {
                "remove_numbers": True,
                "case_fold": True,
                "stopwords": stop_150,
            },
        ),
        (
            "stemming",
            {
                "remove_numbers": True,
                "case_fold": True,
                "stopwords": stop_150,
                "stemming": True,
            },
        ),
    ]


def build_compression_table(folder):
    variants = compression_variants(folder)
    rows = []
    unfiltered_terms = None
    unfiltered_postings = None
    case_fold_terms = None
    case_fold_postings = None
    previous_terms = None
    previous_postings = None

    for name, tokenizer_options in variants:
        index = build_spimi_index(folder, tokenizer_options=tokenizer_options)
        term_count = len(index)
        posting_count = sum(len(postings) for postings in index.values())

        if name == "unfiltered":
            unfiltered_terms = term_count
            unfiltered_postings = posting_count
        if name == "case folding":
            case_fold_terms = term_count
            case_fold_postings = posting_count

        if name in ("30 stop words", "150 stop words"):
            reference_terms = case_fold_terms
            reference_postings = case_fold_postings
        else:
            reference_terms = previous_terms
            reference_postings = previous_postings

        rows.append(
            {
                "variant": name,
                "terms": term_count,
                "term_delta_pct": (
                    None
                    if name == "unfiltered" or reference_terms is None
                    else _percentage_change(term_count, reference_terms)
                ),
                "term_total_pct": (
                    None
                    if name == "unfiltered" or unfiltered_terms is None
                    else _percentage_change(term_count, unfiltered_terms)
                ),
                "postings": posting_count,
                "posting_delta_pct": (
                    None
                    if name == "unfiltered" or reference_postings is None
                    else _percentage_change(posting_count, reference_postings)
                ),
                "posting_total_pct": (
                    None
                    if name == "unfiltered" or unfiltered_postings is None
                    else _percentage_change(posting_count, unfiltered_postings)
                ),
            }
        )

        previous_terms = term_count
        previous_postings = posting_count

    return rows
