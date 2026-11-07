import random
import unittest
from pathlib import Path

from bench import benchmark_indexers
from compress import build_compression_table, most_frequent_terms
from naive_indexer import build_index, sort_and_dedupe
from pairs import build_pairs
from query import and_query, intersect_postings, single_term_query
from spimi_indexer import build_spimi_index, build_spimi_index_from_pairs
from tokenizer import tokenize


PROJECT_ROOT = Path(__file__).resolve().parent
TINY_DATA = PROJECT_ROOT / "testDATA"


class NaiveIndexerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pairs = build_pairs(TINY_DATA)
        cls.index = build_index(sort_and_dedupe(pairs))

    def test_pairs_use_numeric_document_ids(self):
        pairs = build_pairs(TINY_DATA)
        self.assertTrue(pairs)
        docs = {doc_id for _, doc_id in pairs}
        self.assertEqual(docs, {1, 2})
        self.assertTrue(
            all(isinstance(doc_id, int) for doc_id in docs)
        )

    def test_sort_dedupe_and_build_index(self):
        pairs = build_pairs(TINY_DATA)
        sorted_pairs = sort_and_dedupe(pairs)
        idx = build_index(sorted_pairs)

        self.assertEqual(sorted_pairs, sorted(set(pairs)))
        self.assertEqual(
            idx,
            {
                "Cat": [1],
                "Dog": [2],
                "The": [1, 2],
                "cat": [1],
                "dog": [2],
                "mat": [1],
                "on": [1, 2],
                "rug": [2],
                "sat": [1, 2],
                "the": [1, 2],
            },
        )
        for postings in idx.values():
            self.assertEqual(postings, sorted(set(postings)))

    def test_spimi_matches_naive_index(self):
        pairs = build_pairs(TINY_DATA)
        naive = build_index(sort_and_dedupe(pairs))
        spimi = build_spimi_index(TINY_DATA)

        self.assertEqual(spimi, naive)

    def test_spimi_from_pairs_matches_naive_and_rejects_unsorted_input(self):
        pairs = build_pairs(TINY_DATA)
        self.assertEqual(
            build_spimi_index_from_pairs(pairs),
            build_index(sort_and_dedupe(pairs)),
        )
        with self.assertRaises(ValueError):
            build_spimi_index_from_pairs([("first", 2), ("second", 1)])

    def test_single_term_queries(self):
        self.assertEqual(single_term_query(self.index, "cat"), [1])
        self.assertEqual(single_term_query(self.index, "cat!"), [1])
        self.assertEqual(single_term_query(self.index, "missing"), [])

    def test_and_queries(self):
        self.assertEqual(and_query(self.index, "cat sat"), [1])
        self.assertEqual(and_query(self.index, "sat on"), [1, 2])
        self.assertEqual(and_query(self.index, "cat rug"), [])
        self.assertEqual(and_query(self.index, "missing sat"), [])

    def test_intersection_matches_set_reference(self):
        rng = random.Random(479)
        for _ in range(100):
            left = sorted(
                rng.sample(
                    range(100), rng.randrange(101)
                )
            )
            right = sorted(
                rng.sample(
                    range(100), rng.randrange(101)
                )
            )
            self.assertEqual(
                intersect_postings(left, right),
                sorted(set(left) & set(right)),
            )

    def test_invalid_query_shapes_raise(self):
        with self.assertRaises(ValueError):
            single_term_query(self.index, "cat sat")
        with self.assertRaises(ValueError):
            and_query(self.index, "!!!")

    def test_tokenizer_preprocessing_options(self):
        self.assertEqual(
            tokenize(
                "The 123 Markets are running",
                remove_numbers=True,
                case_fold=True,
                stopwords={"the", "are"},
                stemming=True,
            ),
            ["market", "run"],
        )

    def test_stopwords_use_case_folded_corpus_frequency(self):
        self.assertEqual(most_frequent_terms(TINY_DATA, 1), {"the"})
        with self.assertRaises(ValueError):
            most_frequent_terms(TINY_DATA, -1)

    def test_compression_table_counts_unique_postings(self):
        rows = build_compression_table(TINY_DATA)

        self.assertEqual(
            [row["variant"] for row in rows],
            [
                "unfiltered",
                "no numbers",
                "case folding",
                "30 stop words",
                "150 stop words",
                "stemming",
            ],
        )
        self.assertIsNone(rows[0]["term_delta_pct"])
        self.assertEqual(rows[0]["terms"], len(self.index))
        self.assertEqual(
            rows[0]["postings"],
            sum(len(postings) for postings in self.index.values()),
        )

    def test_benchmark_uses_requested_pair_count_and_checks_equality(self):
        res = benchmark_indexers(TINY_DATA, pair_limit=5, repeats=2)

        self.assertEqual(res["pair_count"], 5)
        self.assertEqual(
            res["unique_pair_count"],
            len(set(build_pairs(TINY_DATA)[:5])),
        )
        self.assertEqual(res["repeats"], 2)
        self.assertGreaterEqual(res["naive_seconds"], 0)
        self.assertGreaterEqual(res["spimi_seconds"], 0)

    def test_filtered_query_terms_do_not_weaken_and_query(self):
        opts = {"case_fold": True, "stopwords": {"the"}}
        idx = build_spimi_index(
            TINY_DATA,
            tokenizer_options=opts,
        )

        self.assertEqual(
            single_term_query(
                idx,
                "the",
                tokenizer_options=opts,
            ),
            [],
        )
        self.assertEqual(
            and_query(
                idx,
                "the cat",
                tokenizer_options=opts,
            ),
            [],
        )


if __name__ == "__main__":
    unittest.main()