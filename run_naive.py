import time
from pathlib import Path

from naive_indexer import sort_and_dedupe, build_index
from pairs import build_pairs

if __name__ == "__main__":
    started = time.perf_counter()

    data_dir = Path(__file__).resolve().parent / "DATA"
    pairs = build_pairs(data_dir)
    unique = sort_and_dedupe(pairs)
    idx = build_index(unique)

    elapsed = time.perf_counter() - started

    print(
        f"Processed corpus: {len(pairs)} raw pairs, "
        f"{len(unique)} unique pairs, "
        f"{len(idx)} unique terms"
    )
    print(f"Elapsed time: {elapsed:.2f} seconds")