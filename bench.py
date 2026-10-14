import statistics
import time
from pathlib import Path

from naive_indexer import build_index, sort_and_dedupe
from pairs import build_pairs
from spimi_indexer import build_spimi_index_from_pairs


def benchmark_indexers(folder, *, pair_limit=10_000, repeats=7):
    if pair_limit <= 0:
        raise ValueError("Pair limit must be positive")
    if repeats <= 0:
        raise ValueError("Repeat count must be positive")

    pairs = build_pairs(folder, limit=pair_limit)
    if len(pairs) != pair_limit:
        raise ValueError(
            f"Expected {pair_limit} pairs, but corpus produced {len(pairs)}"
        )

    naive_times = []
    spimi_times = []
    for iteration in range(repeats):
        builders = (
            ("naive", naive_times, lambda: build_index(sort_and_dedupe(pairs))),
            ("spimi", spimi_times, lambda: build_spimi_index_from_pairs(pairs)),
        )
        if iteration % 2:
            builders = tuple(reversed(builders))

        indexes = {}
        for name, samples, builder in builders:
            start = time.perf_counter()
            indexes[name] = builder()
            samples.append(time.perf_counter() - start)

        if indexes["naive"] != indexes["spimi"]:
            raise AssertionError("Naive and SPIMI indexes differ")

    return {
        "pair_count": len(pairs),
        "unique_pair_count": len(sort_and_dedupe(pairs)),
        "repeats": repeats,
        "statistic": "median",
        "naive_seconds": statistics.median(naive_times),
        "spimi_seconds": statistics.median(spimi_times),
        "naive_samples": naive_times,
        "spimi_samples": spimi_times,
    }


if __name__ == "__main__":
    data_dir = Path(__file__).resolve().parent / "DATA"
    result = benchmark_indexers(data_dir)
    print(
        f"Built {result['pair_count']} identical term-document pairs "
        f"({result['unique_pair_count']} unique) over {result['repeats']} runs."
    )
    print(f"Median naive index-build time: {result['naive_seconds']:.6f} s")
    print(f"Median SPIMI index-build time: {result['spimi_seconds']:.6f} s")
    print("SPIMI/naive median ratio: "
          f"{result['spimi_seconds'] / result['naive_seconds']:.3f}x")
