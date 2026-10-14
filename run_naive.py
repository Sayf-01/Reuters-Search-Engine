import time
from pathlib import Path

from pairs import build_pairs
from naive_indexer import sort_and_dedupe, build_index

if __name__ == '__main__':
    start = time.perf_counter()

    data_dir = Path(__file__).resolve().parent / 'DATA'
    F = build_pairs(data_dir)
    sorted_F = sort_and_dedupe(F)
    index = build_index(sorted_F)

    elapsed = time.perf_counter() - start

    print(f"Processed corpus: {len(F)} raw pairs, {len(sorted_F)} unique pairs, {len(index)} unique terms")
    print(f"Elapsed time: {elapsed:.2f} seconds")