from collections import Counter

from reader import ReadData
from spimi_indexer import build_spimi_index
from tokenizer import tokenize


def _ranked_terms(folder):
    freq = Counter()
    for _, text in ReadData(folder):
        freq.update(tokenize(text, remove_numbers=True, case_fold=True))

    return sorted(
        freq,
        key=lambda term: (-freq[term], term),
    )


def most_frequent_terms(folder, count):
    if count < 0:
        raise ValueError("Stop-word count must be non-negative")
    return set(_ranked_terms(folder)[:count])


def _percentage_change(value, reference):
    return (value / reference - 1) * 100 if reference else 0.0


def compression_variants(folder):
    ranked = _ranked_terms(folder)
    stop_30 = set(ranked[:30])
    stop_150 = set(ranked[:150])

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
    all_terms = all_posts = None
    folded_terms = folded_posts = None
    prev_terms = prev_posts = None

    for variant, options in variants:
        idx = build_spimi_index(folder, tokenizer_options=options)
        terms = len(idx)
        posts = sum(map(len, idx.values()))

        if variant == "unfiltered":
            all_terms, all_posts = terms, posts
        if variant == "case folding":
            folded_terms, folded_posts = terms, posts

        if variant in ("30 stop words", "150 stop words"):
            ref_terms, ref_posts = folded_terms, folded_posts
        else:
            ref_terms, ref_posts = prev_terms, prev_posts

        rows.append(
            {
                "variant": variant,
                "terms": terms,
                "term_delta_pct": (
                    None
                    if variant == "unfiltered" or ref_terms is None
                    else _percentage_change(terms, ref_terms)
                ),
                "term_total_pct": (
                    None
                    if variant == "unfiltered" or all_terms is None
                    else _percentage_change(terms, all_terms)
                ),
                "postings": posts,
                "posting_delta_pct": (
                    None
                    if variant == "unfiltered" or ref_posts is None
                    else _percentage_change(posts, ref_posts)
                ),
                "posting_total_pct": (
                    None
                    if variant == "unfiltered" or all_posts is None
                    else _percentage_change(posts, all_posts)
                ),
            }
        )

        prev_terms, prev_posts = terms, posts

    return rows
