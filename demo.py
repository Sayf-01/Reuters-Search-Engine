import argparse
from pathlib import Path

from compress import build_compression_table
from naive_indexer import build_index, sort_and_dedupe
from pairs import build_pairs
from query import and_query, single_term_query
from spimi_indexer import build_spimi_index

PROJECT_ROOT = Path(__file__).resolve().parent


def show_tiny_demo():
    data = PROJECT_ROOT / "testDATA"
    pairs = build_pairs(data)
    naive = build_index(sort_and_dedupe(pairs))
    spimi = build_spimi_index(data)

    print(f"Input pairs: {pairs}")
    print(f"naive index: {naive}")
    print(f"Indexes equal: {naive == spimi}")
    print(f"query Cat: {single_term_query(spimi, 'Cat')}")
    print(f"Query Cat AND rat: {and_query(spimi, 'Cat rat')}")


def show_query_demo():
    idx = build_spimi_index(PROJECT_ROOT / "DATA")
    
    for label, query, search in (
        ("Single-term", "coffee", single_term_query),
        ("AND", "coffee crop", and_query),
    ):
        
        docs = search(idx, query)
        print(f"{label} {query!r}: {len(docs)} documents")
        print(f"First document IDs: {docs[:10]}")


def show_compression_demo():
    rows = build_compression_table(PROJECT_ROOT / "DATA")
    print(f"{'Variant':<16} {'Terms':>10} {'Postings':>12}")

    for row in rows:
        print(
            f"{row['variant']:<16} {row['terms']:>10,} "
            f"{row['postings']:>12,}"
        )


def main():
    parser = argparse.ArgumentParser(description="Run a Reuters index demo.")
    parser.add_argument(
        "section",
        choices=("tiny", "queries", "compression"),
        help="demo section to run",
    )
    section = parser.parse_args().section

    if section == "tiny":
        show_tiny_demo()
    elif section == "queries":
        show_query_demo()
    else:
        show_compression_demo()



if __name__ == "__main__":
    main()
