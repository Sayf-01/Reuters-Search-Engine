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

    naive = []
    spimi = []
    for run in range(repeats):
        builders = (
            ("naive", naive, lambda: build_index(sort_and_dedupe(pairs))),
            ("spimi", spimi, lambda: build_spimi_index_from_pairs(pairs)),
        )
        builders = tuple(reversed(builders)) if run % 2 else builders

        idx = {}
        for name, samples, builder in builders:
            started = time.perf_counter()
            idx[name] = builder()
            samples.append(time.perf_counter() - started)

        if idx["naive"] != idx["spimi"]:
            raise AssertionError("Naive and SPIMI indexes differ")

    return {
        "pair_count": len(pairs),
        "unique_pair_count": len(sort_and_dedupe(pairs)),
        "repeats": repeats,
        "statistic": "median",
        "naive_seconds": statistics.median(naive),
        "spimi_seconds": statistics.median(spimi),
        "naive_samples": naive,
        "spimi_samples": spimi,
    }


if __name__ == "__main__":
    data_dir = Path(__file__).resolve().parent / "DATA"
    res = benchmark_indexers(data_dir)
    print(
        f"Built {res['pair_count']} identical term-document pairs "
        f"({res['unique_pair_count']} unique) over {res['repeats']} runs."
    )
    print(f"Median naive index-build time: {res['naive_seconds']:.6f} s")
    print(f"Median SPIMI index-build time: {res['spimi_seconds']:.6f} s")
    print(
        "SPIMI/naive median ratio: "
        f"{res['spimi_seconds'] / res['naive_seconds']:.3f}x"
    )
