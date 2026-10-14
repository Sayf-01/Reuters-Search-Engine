# Compression Experiment

## Purpose

This experiment measures how the preprocessing rows in textbook Table 5.1
change the number of distinct terms and nonpositional postings in the
Reuters-21578 index. These are structural size indicators, not measurements
of bytes after a postings-list encoding algorithm.

The Reuters-21578 corpus has 21,578 articles. The reader indexes the
unescaped title and body and uses each original numeric `NEWID`. All
measurements use the same punctuation-omitting tokenizer and the same
nonpositional index definition: one posting for each unique term-document
pair, regardless of how many times the term occurs in that article.

## Method

The tokenizer extracts maximal ASCII-letter/digit sequences with
`[A-Za-z0-9]+`. The unfiltered row preserves token case. The preprocessing
rows are cumulative in this order:

1. **Unfiltered:** tokenize without number removal, case folding, stop words,
   or stemming.
2. **No numbers:** remove tokens for which `str.isdigit()` is true. Tokens
   containing both letters and digits are retained.
3. **Case folding:** lowercase the remaining tokens.
4. **30 stop words:** remove the 30 most frequent tokens from the
   number-filtered, case-folded Reuters corpus.
5. **150 stop words:** remove the 150 most frequent tokens from that same
   number-filtered, case-folded reference corpus.
6. **Stemming:** apply NLTK's Porter stemmer to the case-folded corpus after
   removing the 150 stop words.

The frequency ranking counts token occurrences, not documents. Ties are
ordered alphabetically so the stop lists are reproducible. The textbook
specifies the case-folding row as the reference for both stop-word rows, so
their Δ% values are measured against case folding, not against the preceding
stop-word row. Other Δ% values are relative to the preceding row. T% is
relative to unfiltered.

For every variant, SPIMI builds the index. Distinct terms are `len(index)`;
nonpositional postings are the sum of the lengths of all postings lists.
Stemming uses `nltk.stem.PorterStemmer`, which requires no downloaded corpus
or tokenizer data. NLTK is declared in `requirements.txt`.

## Results

Percentages are rounded to one decimal place. Negative values indicate a
reduction.

| Preprocessing | Distinct terms | Δ% | T% | Nonpositional postings | Δ% | T% |
|---|---:|---:|---:|---:|---:|---:|
| Unfiltered | 61,453 | — | — | 1,781,942 | — | — |
| No numbers | 59,252 | -3.6% | -3.6% | 1,622,359 | -9.0% | -9.0% |
| Case folding | 43,197 | -27.1% | -29.7% | 1,499,117 | -7.6% | -15.9% |
| 30 stop words | 43,167 | -0.1% | -29.8% | 1,218,450 | -18.7% | -31.6% |
| 150 stop words | 43,047 | -0.3% | -30.0% | 930,958 | -37.9% | -47.8% |
| Stemming | 32,318 | -24.9% | -47.4% | 886,223 | -4.8% | -50.3% |

## Comparison with textbook Table 5.1

The broad trends match the textbook: removing numbers changes the dictionary
less than stemming or case folding; stop-word removal barely changes the
distinct-term count but substantially reduces postings; and stemming merges
many surface forms into fewer terms.

The magnitude differs. In this corpus, case folding reduces distinct terms
by 27.1% from the preceding no-numbers row, compared with 17% in Table 5.1.
It reduces postings by 7.6%, compared with 3% there. The 30-word and
150-word lists reduce postings by 18.7% and 37.9% from the case-folding
reference, compared with approximately 14% and 30% in the textbook. Stemming
reduces distinct terms by 24.9% from the 150-stop-word row, compared with
17% in the textbook, while its 4.8% postings reduction is close to the
textbook's 4%.

These differences show why the assignment calls for measuring Reuters-21578
instead of copying Reuters-RCV1 counts. The datasets have different document
sets, vocabulary distributions, and token frequencies. Percentages enable a
more meaningful comparison than raw counts, but they are still corpus- and
tokenizer-dependent.

The strong postings reduction from stop words occurs because frequent terms
appear in many documents. Removing only 150 terms can therefore remove many
term-document relationships while eliminating few distinct term keys.
Stemming has the opposite emphasis: many inflected or related forms collapse
to shared roots, shrinking the vocabulary; postings shrink less because a
document containing any form still contributes a posting for the stem.

## Six sample queries across variants

Three single-term and three AND queries were selected. They include common
terms, terms affected by the 150-word stop list, and conjunctions with a
small result set. Query terms are processed with the same transformations as
the corresponding index. If preprocessing removes any term from an AND
query, the result is empty rather than silently weakening the conjunction.

| Query type | Query | Unfiltered | No numbers | Case folding | 30 stop words | 150 stop words | Stemming |
|---|---|---:|---:|---:|---:|---:|---:|
| Single | `coffee` | 166 | 166 | 196 | 196 | 196 | 196 |
| Single | `trade` | 1,605 | 1,605 | 1,957 | 1,957 | 0 | 0 |
| Single | `acquisition` | 685 | 685 | 829 | 829 | 829 | 1,001 |
| AND | `coffee crop` | 25 | 25 | 29 | 29 | 29 | 36 |
| AND | `gold mining` | 39 | 39 | 89 | 89 | 89 | 158 |
| AND | `bankruptcy acquisition` | 10 | 10 | 12 | 12 | 12 | 13 |

Case folding increases result counts for these lowercase queries because
case variants that were separate terms in the unfiltered index are combined.
The 150-word stop list removes `trade`, so that single-term query returns no
documents. Stemming increases some result counts because distinct forms map
to the same stem; this increases recall but can also introduce false
positives when words with related stems are not interchangeable in meaning.
Number removal does not affect these selected queries because none contains
a number.

## Implementation and reproduction

The shared tokenizer and preprocessing options are in `tokenizer.py`;
frequency ranking and the six variant definitions are in `compress.py`.
SPIMI builds each variant so the measurement uses the same unique,
document-sorted postings definition as the main indexer.

Run the project tests with:

```sh
python -m unittest test_tiny.py
```

Recompute the statistics and query table from the repository root using:

```sh
python -c "from pathlib import Path; from compress import build_compression_table; print(*build_compression_table(Path('DATA')), sep='\\n')"
```
