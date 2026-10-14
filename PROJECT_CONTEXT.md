# Project Context and Build Notes

## Purpose

Create a small, understandable information-retrieval system for the COMP 479
Project 1 assignment. Use the original Reuters-21578 SGML corpus and each
article's `NEWID` as its document ID. Required work: naive and SPIMI inverted
indexers, single-term and AND queries, a lossy dictionary-compression
experiment, a timing comparison, challenge-query output, a report, and a demo.

## Rules for future changes (including AI-assisted work)

- Read this file and the assignment requirements before editing.
- Keep the existing simple, top-level Python module layout unless a concrete
  requirement justifies restructuring it.
- Reuse one corpus reader and one tokenizer for both indexers and query
  normalization. Do not create parallel implementations that can drift.
- Preserve original numeric Reuters `NEWID` values; do not substitute NLTK's
  Reuters corpus IDs or renumber documents.
- Make behavior measurable with small tests before running expensive full-data
  experiments. Keep test fixtures independent of the full corpus.
- Record each completed project change below: files changed, purpose, key
  design decisions, why they were chosen, and validation result.
- Never infer compression settings from memory: use the assignment's specified
  first two columns of textbook Table 5.1 when implementing Subproject III.
- Keep explanations tied to actual code and measured results. Clearly label
  planned behavior, assumptions, and known limitations so this guide can be
  trusted as implementation context and presentation preparation.

## Current design

| Concern | Current decision |
| --- | --- |
| Corpus | Original `.sgm` files in `DATA/`; articles are identified by numeric `NEWID`. |
| Document text | Concatenate unescaped title and body; missing title/body becomes an empty string. |
| File order | Sort `.sgm` filenames before reading so corpus iteration is deterministic. |
| Text encoding | Latin-1, matching the corpus and avoiding UTF-8 decode failures. |
| Tokenization | Extract ASCII letters/digits with `[A-Za-z0-9]+`; preserve case and omit punctuation. |
| Preprocessing | Optional number removal, case folding, corpus-derived stop words, and Porter stemming are configured through the shared tokenizer. |
| Naive index | Produce `(term, docid)` pairs, sort and deduplicate them, then group by term. |
| Project layout | Existing top-level scripts/modules; do not reorganize without need. |

## Why these technologies and design choices

### Python and the standard library

Python is the implementation language because it makes the transformations
from text to tokens, pairs, and postings visible and easy to explain. The
assignment is about comparing information-retrieval algorithms, not building
an application framework, so plain scripts and small modules keep attention
on those algorithms.

The corpus reader uses Python's `os`, `re`, and `html` standard-library
modules. They are enough for this fixed, known Reuters SGML format: `os`
enumerates files, regular expressions locate the article and field tags, and
`html.unescape` converts encoded entities to readable text. This avoids adding
a parser dependency for a constrained input format. Regex parsing is a
deliberate simplicity tradeoff, not a general-purpose SGML parser; if inputs
or markup become less predictable, a real SGML/XML parser should be evaluated.

`pathlib.Path` in the runner anchors the `DATA` location to the script. That
prevents the command from depending on the directory from which the user
launches it, making the demo and marker's execution more reliable.

### NLTK and the tokenizer

The baseline tokenizer intentionally does not use NLTK's `word_tokenize`.
That function requires tokenizer data downloads and has tokenization behavior
that is unnecessary for this assignment's requirement to omit punctuation.
Instead, the compiled `[A-Za-z0-9]+` regular expression is explicit: each
maximal run of ASCII letters and digits becomes one token; punctuation and
whitespace are separators; case is preserved. Compiling the expression once
avoids recompiling it for every text.

NLTK supplies `PorterStemmer` for the textbook's stemming row. Porter
stemming needs the library but no downloaded tokenizer corpus; base
tokenization remains a regular expression. Stemming is a distinct
normalization transformation and is applied consistently to corpus terms and
query terms. `requirements.txt` declares NLTK so another environment can
reproduce the experiment.

The shared `tokenize` function accepts options for removing digit-only
tokens, case folding, removing a supplied stop-word set, and stemming. This
lets naive indexing, SPIMI, and query processing use precisely the same
normalization instead of maintaining separate implementations.

This tokenizer defines the experiment's vocabulary, so its choices affect
dictionary size, postings counts, and query results. It is currently
ASCII-only: accented characters are split or omitted. Preserve this known
limitation in the report unless the assignment calls for Unicode-aware terms
and the tokenizer is changed.

### Reuters IDs and document order

Use the raw Reuters corpus rather than NLTK's repackaged Reuters collection.
The raw corpus provides the original `NEWID` values required by the
assignment; substituting IDs from another distribution would make retrieval
results incomparable with the expected documents.

IDs are integers rather than strings so numeric ordering works as intended
(for example, 9 comes before 10). Sorting filenames and preserving the
corpus's article order makes ingestion deterministic. The reader explicitly
fails for a missing ID instead of quietly indexing an article under an
unknown or fabricated identifier.

Title and body are combined because both are article text likely to contain
useful search terms. Other SGML metadata and topic labels are excluded so the
index represents article content rather than the corpus's classification
annotations. Missing titles or bodies are treated as empty text because
Reuters records do not all have every field.

### Why use an inverted index

The desired result is fast document retrieval by term. An inverted index
stores the reverse of a document-to-words representation:

```text
term -> sorted list of document IDs containing that term
```

For example, if document 1 and document 2 both contain `market`, the index
contains `market -> [1, 2]`. A single-term query can then look up one key
instead of scanning every article. An AND query intersects the postings lists
for its terms, leaving only documents containing every term.

The Python dictionary is a hash table, so a term's postings can be accessed
directly by key on average. Python lists are simple to inspect and support
the sorted-list intersection algorithm. These structures are sufficient for
the assignment's in-memory corpus; a database or web framework would add
complexity without helping explain the required indexing algorithms.

### Why keep the naive indexer

The naive indexer intentionally materializes every token occurrence as
`(term, docid)` in `F`. A term repeated several times in one article therefore
produces duplicate pairs. Sorting and deduplicating `F` turns occurrences
into the set of unique term-document relationships required by a
non-positional index. Grouping adjacent equal terms then creates each
postings list. Because pairs sort first by term and then by numeric ID, each
posting list is ascending.

This method is intentionally not the fastest approach: it uses memory for all
occurrences and pays for sorting. Its value is that each operation in the
assignment is explicit and it provides a clear correctness reference for
SPIMI. The intended index answers whether a term appears in a document; it
does not store positions or term frequency.

### Why SPIMI should be faster

SPIMI (Single-Pass In-Memory Indexing) avoids the global occurrence list and
global sort. As each document is processed, it looks up the term in a
dictionary and appends that document ID directly to the term's postings list.
Since the corpus is read in ascending ID order, repeated occurrences of the
same term in the same document can be suppressed by comparing against the
last appended ID. The output is already deduplicated and ordered, provided
that this input-order invariant holds.

SPIMI is expected to reduce construction work by avoiding sorting all
term-document pairs; it still has to read and tokenize the corpus and store
the resulting index. The timing comparison tests this expectation, while
equality with the naive index remains the key correctness check.

The benchmark path materializes the first 10,000 term-document pairs before
starting either timer. Naive timing includes set-based deduplication,
sorting, and grouping into postings. SPIMI timing includes direct dictionary
updates and duplicate suppression from that exact same ordered pair sequence.
Both procedures produce the same index, but parsing and tokenization are
excluded so the comparison focuses on index construction as requested.

## System walkthrough and what each stage produces

1. `reader.py` scans the sorted SGML files, extracts each Reuters article,
   parses `NEWID`, unescapes its title/body, and yields `(docid, text)`. This
   gives downstream components a stable document identity and plain text
   independent of SGML markup.
2. `tokenizer.py` converts the text into tokens. For example,
   `Market's gain: 2.5%` becomes `Market`, `s`, `gain`, `2`, `5`. The
   baseline preserves case; optional transformations are explicit and
   selectable so their effects can be measured.
3. `pairs.py` composes reading and tokenizing, producing each
   `(term, docid)` occurrence. If `Market` occurs three times in document 7,
   the naive input contains three copies of `("Market", 7)`.
4. `naive_indexer.py` sorts and deduplicates these pairs, then groups pairs
   with the same term into postings. In the example, the three occurrences
   become only one posting for document 7.
5. `run_naive.py` is the current executable entry point and resolves `DATA`
   relative to its own file, rather than the process's working directory.
6. `query.py` applies the shared tokenizer to query text, retrieves a
   single-term postings list, or intersects postings lists for an AND query.
   This means query syntax uses the same token boundaries and case behavior as
   indexing.

The intended index shape is `dict[str, list[int]]`: each key is a term and its
value is the ascending list of document IDs containing that term.

## Correctness and performance story for a presentation

Explain the project as a pipeline: raw SGML -> `(NEWID, article text)` ->
tokens -> term-document pairs -> inverted index -> query result document IDs.
Each boundary has a concrete invariant: IDs are present, unique, and numeric;
tokens omit punctuation; postings contain unique, ascending IDs.

The naive and SPIMI implementations are two ways to build the same logical
index. The naive version is the understandable reference; SPIMI updates the
dictionary in one pass. Verify the outcome by comparing the complete
dictionaries, not merely their term counts. Then compare timings on the same
first 10,000 term-document pairings, with parsing/tokenization outside the
timed section, so the measurement isolates the index-building difference
specified by the assignment. Report the repeat policy and statistic (for
example, median of repeated runs); do not claim a speedup before measuring.

An AND query uses sorted postings lists. A two-pointer intersection advances
the pointer holding the smaller document ID, and emits an ID only when both
lists match. It is correct because IDs are sorted, and it avoids constructing
an unneeded general set. For multiple terms, starting with the shortest
postings list can reduce intermediate work; implement this only if it fits
the required query interface.

The preprocessing experiment changes the dictionary and/or postings because
terms may be removed, merged by case folding, or conflated by stemming. The
stop lists are the top 30/150 terms by token frequency in this Reuters corpus
after number removal and case folding; ties are alphabetical for
reproducibility. The 30- and 150-word percentage deltas both use the case
folding row as their reference, per Table 5.1. Count distinct terms and
unique term-document pairs consistently. Compare percentage changes rather
than raw counts because the Reuters corpus sizes differ.

For a live explanation, demonstrate one article becoming tokens, show one
term's postings, run a single-term lookup, and intersect two lists for an AND
query. Then explain how SPIMI avoids the pair-list sort and show the
correctness/timing comparison. Keep report prose and measured tables aligned
with the code that is actually submitted.

## Progress and verified decisions

### Completed: corpus loading

- Updated `reader.py` to scan sorted `.sgm` filenames, decode as Latin-1,
  parse IDs from the opening Reuters tag, return IDs as integers, tolerate
  absent title/body tags, and fail explicitly if an article lacks `NEWID`.
- Updated `run_naive.py` to use the repository's uppercase `DATA` folder via
  a path relative to the script.
- Validation: full corpus yielded 21,578 articles, 21,578 unique IDs, in
  increasing order from 1 through 21,578.

### Completed: base tokenizer

- Updated `tokenizer.py` to use a compiled regular expression rather than
  NLTK's downloaded `word_tokenize` data. The public function remains
  `tokenize(text)`.
- The tokenizer preserves case for the unfiltered baseline and removes
  punctuation by matching only ASCII letters/digits.
- Validation: checks passed for case preservation, punctuation, digit
  sequences, and empty text.
- Known decision to revisit only if required: the ASCII expression splits or
  excludes accented letters.

### Completed: naive index baseline

- Added `test_tiny.py` tests using `testDATA/fake1.sgm` to check numeric
  document IDs, pair sorting/deduplication, exact postings, and sorted unique
  posting lists.
- Validation: `python -m unittest test_tiny.py` passes.
- Built the naive index over all Reuters files: 2,866,956 raw token-document
  pairs became 1,781,942 unique term-document pairs, grouped under 61,453
  terms. The 1,085,014 removed duplicates are repeated occurrences of terms
  within documents; a non-positional index records each term-document
  relationship once.
- Full-index checks passed: every posting list is ascending and duplicate-free,
  all IDs are integers within the Reuters range 1–21,578, and the sum of
  posting-list lengths equals the unique-pair count.
- The existing run completed in 3.33 seconds on this environment. Treat this
  as an observation, not a formal benchmark: it includes reading and
  tokenization, and no repeated-run statistic was collected.

### Completed: SPIMI indexer

- Added `spimi_indexer.py` with `build_spimi_index(folder)`. It reads the same
  `(NEWID, text)` stream from `reader.py` and tokens from `tokenizer.py` as
  the naive route, but writes each document ID directly into the term's
  postings list rather than building the global pair list.
- For each token, SPIMI appends the current ID only when the term's last
  posting is not already that ID. This suppresses within-document repeats
  without a global sort because the input has increasing IDs.
- The builder raises `ValueError` if document IDs are not strictly
  increasing. This makes the ordering assumption explicit instead of silently
  generating invalid postings for out-of-order input.
- Added a tiny-corpus equality test comparing the complete SPIMI dictionary
  to the naive dictionary. All three tests in `test_tiny.py` pass.
- Full-corpus comparison passed: both indexes have 61,453 terms and 1,781,942
  unique term-document pairs, and the dictionaries are identical. SPIMI
  postings are also sorted and duplicate-free.
- No performance conclusion is recorded yet. The assignment's comparison
  must separately time the same 10,000 precomputed term-document pairs and
  exclude parsing/tokenization.

### Completed: single-term and AND queries

- Added `query.py` with `single_term_query`, `and_query`, and the reusable
  two-pointer `intersect_postings` function. Query strings are normalized by
  the same tokenizer used for indexing, so punctuation boundaries and
  case-sensitivity match the baseline index.
- Single-term queries require exactly one resulting alphanumeric token.
  Queries containing no tokens or multiple tokens raise `ValueError` rather
  than silently changing the request.
- AND queries require at least one token. A missing term yields no results.
  The implementation intersects the shortest postings list first, then
  intersects each intermediate result with the next list.
- The two-pointer algorithm relies on sorted postings. It advances whichever
  side has the smaller document ID, and emits a document only when both sides
  match. Thus every emitted document contains every AND term.
- Tests cover hits, misses, punctuation, invalid single-term shape, and
  100 deterministic generated list pairs compared with a set-intersection
  reference. All seven tests in `test_tiny.py` pass.

### Completed: preprocessing and compression experiment

- Extended `tokenizer.py` with optional digit-only number removal, case
  folding, stop-word removal, and cached NLTK Porter stemming. `pairs.py`,
  `spimi_indexer.py`, and `query.py` pass the same tokenizer options to build
  or query each variant consistently.
- Added `requirements.txt` with `nltk>=3.9,<4`. NLTK is used only for
  `PorterStemmer`; the base tokenizer still needs no downloaded tokenizer
  data.
- Added `compress.py`. Stop words are ranked by token frequency after number
  removal and case folding; equal-frequency terms are alphabetically
  tie-broken. The stop ranking is computed once per experiment and used for
  both list sizes. Variants follow the table sequence; stemming follows the
  150-stop-word row.
- Query normalization uses the chosen index variant. If preprocessing removes
  any term from an AND query, it returns no results rather than silently
  reducing the query to fewer terms.
- Full corpus results: unfiltered has 61,453 terms and 1,781,942 postings;
  no numbers 59,252 and 1,622,359; case folding 43,197 and 1,499,117;
  30 stop words 43,167 and 1,218,450; 150 stop words 43,047 and 930,958;
  stemming 32,318 and 886,223.
- Compared with unfiltered, cumulative reductions are 3.6% terms/9.0%
  postings for no numbers; 29.7%/15.9% for case folding; 29.8%/31.6% for
  30 stop words; 30.0%/47.8% for 150 stop words; and 47.4%/50.3% for
  stemming. Full percentage values and the comparison with Table 5.1 are in
  `Compression experiment.md`.
- Selected and measured three single-term plus three AND queries on all six
  variants. Results and reasoning are in `Compression experiment.md`.
- Validation: 11 unit tests pass, including preprocessing behavior,
  corpus-ranked stop words, compression row shape/counts on the fixture,
  query transformation, and no weakened AND queries. Full-corpus statistics
  and query counts were computed successfully.

### Completed: naive versus SPIMI timing

- Added `build_spimi_index_from_pairs` so SPIMI can consume a precomputed
  ordered pair sequence. It rejects decreasing document IDs and appends a
  document only once per term.
- Added `bench.py`. It materializes the first 10,000 unfiltered pairs once,
  alternates which indexer runs first, builds both indexes seven times, and
  asserts their dictionaries match on every repetition. Median index-build
  durations are reported; pair generation happens before timing.
- Measured 10,000 input pairs, containing 6,218 unique term-document pairs.
  Median naive time was 0.001989 seconds; median SPIMI time was 0.000712
  seconds. SPIMI took 0.358 times the naive time (about 64.2% less time, or
  2.79 times as fast) in this run.
- Interpret cautiously: these are very short in-memory operations and
  timings vary by machine and system load. They are the requested fixed-size
  comparison, not a prediction of full-corpus elapsed time. Parsing and
  tokenization were excluded from both indexer timings.
- Tests verify pair-based SPIMI equality, rejection of out-of-order pairs,
  and that the benchmark uses its requested pair count. All 13 tests pass.

## Remaining assignment work

1. Prepare challenge-query execution and demo as required by the rubric.
2. Confirm the contradictory challenge release dates with course materials:
   the brief says both October 8, 2025 and 24 hours before the October 19,
   2026 deadline.
3. Write the final academic report using `Project Report Outline.md` as a
   starting point and complete its course-specific references/disclosures.

## Change log

- Initial guide created; append a concise entry after each subsequent
  implementation milestone.
- Naive-index baseline tests added and passing; existing naive indexer logic
  required no changes.
- Expanded the guide to explain why the technologies and algorithms are used,
  their tradeoffs, system invariants, and a presentation-ready walkthrough.
- Built and validated the full naive index; recorded pair/term counts,
  duplicate suppression, and non-benchmark elapsed time above.
- Added the SPIMI indexer, tiny-corpus equality coverage, and verified exact
  full-corpus equality with the naive index.
- Added single-term and AND query processing with shared normalization,
  sorted-list intersection tests, and explicit invalid-query behavior.
- Implemented and measured the six preprocessing variants, selected query
  comparisons, and the separate compression experiment document.
- Added the controlled 10,000-pair timing harness, validated index equality,
  and recorded the seven-run medians.
- Added `Project Report Outline.md` with verified results and explicit
  placeholders for challenge output, course citations, and final disclosure.

## Self-study guide: learn the ideas behind this project

This section is intended for a reader who is new to information retrieval.
Read it in order, then inspect the matching source module and try the
checkpoint questions. The concepts explain the project; measured claims
about this particular implementation are called out separately.

### Learning route and prerequisites

You only need basic Python to start: strings, lists, dictionaries, loops,
functions, imports, and running a script. Helpful but not required:
regular expressions, sorting, sets, and the idea of algorithmic complexity.

Suggested order:

1. Learn what a document collection and a search query are.
2. Learn tokenization, terms, document IDs, and term-document pairs.
3. Learn inverted indexes, dictionaries, and postings lists.
4. Trace naive indexing on the worked example below.
5. Trace SPIMI and compare its input-order invariant with naive indexing.
6. Trace single-term lookup and postings intersection.
7. Study the preprocessing variants and interpret the measured table.
8. Review test evidence and the limits of the timing comparison.

After each stage, explain the idea in your own words before looking at the
next section. Then open the named source module and connect the explanation
to the implementation.

### Essential vocabulary

- **Document / corpus:** one article is a document; all 21,578 articles form
  the corpus (the collection being searched).
- **Document ID (`docid`):** a stable identifier for one document. This
  project uses Reuters' original numeric `NEWID`.
- **Token:** a piece of text emitted by the tokenizer. Here, a token is a
  maximal ASCII letter/digit sequence. For example, `Oil-price` becomes
  `Oil`, `price`.
- **Term:** a token treated as a searchable vocabulary item. Depending on
  preprocessing, `Oil`, `oil`, and a stemmed form may be separate or merged.
- **Vocabulary / dictionary:** the set of distinct terms; in code, these are
  the keys of the index dictionary.
- **Term-document pair:** `(term, docid)`, meaning the term occurs at least
  once in that document.
- **Occurrence:** one appearance of a token in text. A term can occur several
  times in one document, creating repeated term-document pairs before
  deduplication.
- **Posting:** one document ID in a term's postings list. This project has
  nonpositional postings: they say which document contains a term, but not
  where or how often it occurs.
- **Postings list:** the sorted list of document IDs associated with one
  term, e.g. `oil -> [2, 8, 15]`.
- **Document frequency (`df`):** number of documents containing a term;
  equivalently, the length of its postings list in this nonpositional index.
- **Term frequency (`tf`):** number of times a term occurs, usually counted
  within a document. This implementation does not preserve per-document `tf`.
- **Inverted index:** a lookup structure organized from term to documents,
  rather than from document to its terms.
- **AND query:** a request for documents that contain every query term.
- **Normalization / preprocessing:** transformations that make terms
  comparable or remove some terms before index construction.
- **Stemming:** reducing related word forms to a shared approximate root;
  it is a rule-based conflation, not a guarantee that the words have exactly
  the same meaning.
- **Lossy transformation:** a transformation that discards distinctions or
  terms. Stop-word removal loses the removed terms; case folding loses
  capitalization distinctions; stemming merges forms. Results may change.
- **Distinct-term count:** number of dictionary keys.
- **Nonpositional-posting count:** sum of all postings-list lengths, i.e.
  number of unique term-document pairs after deduplication.

### Worked example: from text to answers

Suppose a tiny collection has these two documents:

```text
D1: The cat sat on the mat.
D2: The cat ate fish.
```

Use the project's base tokenizer, which preserves case and removes
punctuation:

```text
D1 -> ["The", "cat", "sat", "on", "the", "mat"]
D2 -> ["The", "cat", "ate", "fish"]
```

Each token is paired with its document ID. `D1` produces
`("The", 1)` and `("the", 1)` as distinct pairs because case is preserved.
Repeated appearances of the exact same term in one document would make
duplicate pairs; for example, a second lowercase `cat` in D1 would repeat
`("cat", 1)`.

After sorting and removing duplicate pairs, group by term:

```text
The  -> [1, 2]
ate  -> [2]
cat  -> [1, 2]
fish -> [2]
mat  -> [1]
on   -> [1]
sat  -> [1]
the  -> [1]
```

A single-term query for `cat` returns `[1, 2]`: both documents contain it.
The AND query `cat sat` intersects `[1, 2]` with `[1]`, returning `[1]`.
Document 2 is excluded because it has `cat` but not `sat`.

With case folding enabled, `The` and `the` become the same term, and queries
do not need to guess which capitalization appeared in the article. This
increases matches for a lowercase query but loses the distinction between
capitalized and lowercase forms.

### Naive indexing, step by step

The naive route directly follows the assignment's stages:

1. Read each document and tokenize it.
2. Append every `(term, docid)` occurrence to `F`.
3. Convert `F` to `sorted(set(F))`: the set removes repeated occurrences of
   the same term in the same document; sorting groups equal terms and orders
   their numeric document IDs.
4. Scan the sorted pairs and append each ID to its term's postings list.

Why keep duplicate occurrences until step 3? It makes the assignment's
intermediate representation explicit and gives a baseline to compare with
SPIMI. The cost is memory for all raw pairs and the work of sorting them.
For `P` raw pairs, sorting generally scales on the order of
`P log P` comparisons; the exact runtime also depends on hashing, duplicate
rates, data distribution, and implementation details.

In this implementation, `sort_and_dedupe` performs step 3 and `build_index`
performs step 4 in `naive_indexer.py`. `pairs.py` produces the raw list from
the reader and tokenizer.

### SPIMI, step by step

SPIMI means Single-Pass In-Memory Indexing. It avoids keeping and globally
sorting the full occurrence list:

1. Visit documents in increasing numeric `NEWID` order.
2. For each token, find or create that term's postings list in a dictionary.
3. Append the current document ID unless it is already the last ID.

Why is comparing with the last ID enough? A document is processed as one
continuous block. If a term appears repeatedly in that document, its
postings list already ends with that document ID. When the next document is
processed, its ID is larger, so a later occurrence of that term can safely
be appended. The condition depends on increasing document order; the
implementation rejects decreasing IDs rather than pretending the result is
valid.

The result should be identical to the naive index. This project verifies
equality of the complete dictionaries, not just equality of term or posting
counts. The implementation is in `spimi_indexer.py`.

The classic SPIMI algorithm can write blocks to disk when memory fills; this
project uses a single in-memory dictionary because the assignment permits
hash tables and the corpus fits this experiment. Do not claim disk-based
indexing was implemented.

### Query algorithms

For a single term, the dictionary locates a postings list directly. A hash
table has expected near-constant key lookup as the dictionary grows (the
lookup still depends on hashing and collisions); returning the matches then
costs at least the length of the returned list.

For AND, the implementation intersects two sorted lists using two positions:

```text
i = 0, j = 0
while both positions are in range:
    if left[i] == right[j]: emit ID; advance both
    else if left[i] < right[j]: advance i
    else: advance j
```

No match can be skipped: if the left ID is smaller, it cannot appear at the
current or any later position in the right list, so advancing left is safe.
The same argument holds symmetrically. For lists of lengths `m` and `n`, the
algorithm takes `O(m + n)` time and `O(k)` output space, where `k` is the
number of matches. For multiple AND terms, starting with the shortest list
often reduces intermediate lists. This optimization does not change the
answer.

The query and index must use the same normalization. Otherwise, an index
could contain `Oil` while a lowercased query looks for `oil` and incorrectly
gets no results. If stop-word removal removes a query term, this project
returns no results; it does not silently treat `cat the` as just `cat`.
Functions and tests are in `query.py` and `test_tiny.py`.

### Why preprocessing changes index statistics

The experiment reproduces these Table 5.1 stages cumulatively:

1. **Unfiltered:** baseline tokens.
2. **No numbers:** remove tokens that are entirely digits. Alphanumeric
   tokens remain.
3. **Case folding:** lowercase tokens so case variants merge.
4. **30 stop words:** remove the most frequent 30 tokens.
5. **150 stop words:** remove the most frequent 150 tokens.
6. **Stemming:** apply Porter stemming after the 150-word stop list.

The stop lists here are derived from this Reuters corpus, counting token
occurrences after number removal and case folding. This is a reproducible
project choice; another list or a different tie-break can change the exact
results. The 30- and 150-word Δ% values use the case-folded row as their
reference because that is how the provided textbook Table 5.1 defines them.
Other rows compare with the previous row. `T%` always compares with
unfiltered.

These operations affect the index differently:

- Number removal removes numeric terms and all their postings.
- Case folding merges capitalization variants. It usually reduces
  vocabulary; postings may also merge when the variants occurred in the
  same document.
- Stop-word removal removes selected terms and all their postings. A small
  number of very frequent terms can account for many document relationships.
- Stemming maps forms such as `connect`, `connected`, and `connecting`
  toward common stems. This can merge vocabulary and can broaden or distort
  query matches.

The table measures term keys and unique term-document relationships. It does
not measure encoded bytes, compression ratio of a binary index, or positional
index size. The posting count can be interpreted as the size of an
uncompressed nonpositional posting representation only in a structural
counting sense.

Our observed values are specific to Reuters-21578, the fields indexed, the
tokenizer, and the generated stop lists. Table 5.1 uses Reuters-RCV1, so
compare percentage patterns rather than raw counts and explain differences
without claiming one corpus should reproduce the other's exact values.
See `Compression experiment.md` for the actual table and six-query results.

### How to understand the experiment and timing

The number of raw token occurrences is not the same as the number of
postings. A term repeated many times in one article contributes many raw
pairs but one nonpositional posting. On our measured baseline, 2,866,956 raw
pairs became 1,781,942 unique term-document pairs.

For the required timing comparison, the first 10,000 raw pairs are prepared
once outside the timer. Naive timing includes deduplication, sorting, and
grouping; SPIMI timing includes direct dictionary updates. Seven runs are
performed, execution order alternates to reduce consistent order bias, and
the median is reported. Full equality is checked each run.

The observed medians were 0.001989 s (naive) and 0.000712 s (SPIMI), so
SPIMI used about 0.358 times the naive time on this machine/run. This
supports the expected benefit for this benchmark; it is not proof that
SPIMI is always faster on every machine, corpus, or input size. The timing
excludes parsing/tokenization and is so short that machine load and timer
resolution matter.

### How to study the code and check your understanding

Use this loop for each idea:

1. Explain it without code.
2. Trace the two-document example by hand.
3. Read the corresponding function.
4. Run the focused test.
5. Explain what invariant makes the code correct and name an input that
   would violate that invariant.

Suggested file map:

| Topic | File to inspect | Questions to answer |
|---|---|---|
| SGML article extraction and IDs | `reader.py` | How is `NEWID` kept attached to the correct title/body? What happens if it is missing? |
| Token boundaries and transformations | `tokenizer.py` | What exact text becomes one token? Why must query transforms match index transforms? |
| Occurrence generation | `pairs.py` | Why can the output contain duplicates? |
| Sort-and-group baseline | `naive_indexer.py` | Why sort before grouping? Why use a set? |
| Direct postings construction | `spimi_indexer.py` | Why must IDs be increasing? Why is checking the final posting sufficient? |
| Single and AND query | `query.py` | Why does the two-pointer algorithm not miss matches? |
| Preprocessing measurements | `compress.py` | How are frequent terms selected? What do counts and percentages mean? |
| Fair timing | `bench.py` | Which work is timed and which work is deliberately excluded? |
| Correctness examples | `test_tiny.py` | What behavior does each test protect? |

Practice questions:

1. If term `market` appears five times in document 10, how many raw pairs
   and how many nonpositional postings does it contribute?
2. Why can the naive indexer sort `(term, docid)` pairs and then append IDs
   without a separate per-postings sort?
3. What breaks if SPIMI processes document 12 and later document 8?
4. Intersect `[1, 4, 8, 10]` with `[2, 4, 7, 10]` by hand. What is the result
   and which pointer moves at each comparison?
5. Why can removing 150 stop words have little effect on dictionary size but
   a large effect on posting count?
6. Why can stemming increase the number of results for an AND query?
7. What would be unfair about timing corpus parsing for one indexer but not
   the other?
8. Does a 50% reduction in posting count prove the compressed file uses 50%
   fewer bytes? Why not?

Check answers only after trying: (1) five raw pairs, one posting; (2) Python
tuple order groups terms first and numeric IDs second; (3) postings may no
longer be ascending and duplicates may not be adjacent; (4) `[4, 10]`;
advance left on 1<2, advance right on 4>2, match 4, then advance the smaller
side at each later comparison until 10 matches; (5) frequent terms have many
document IDs but each term is only one dictionary key; (6) several surface
forms can map to a shared stem; (7) it mixes algorithm cost with different
amounts of parsing work; (8) no, this experiment counts relationships rather
than encoding postings into bytes.

### Reusable AI tutor prompt

Give this prompt together with `PROJECT_CONTEXT.md` and the source files when
asking an AI to tutor you:

> I am learning information retrieval and this Reuters-21578 project from the
> beginning. Teach me rather than just summarize or edit code. Follow the
> self-study route in PROJECT_CONTEXT.md. Explain one concept at a time in
> plain language, define new terms, and use the two-document worked example.
> Ask me a short question after each concept and wait for my answer before
> continuing. If I am wrong, explain the reasoning and let me try again.
> Connect each concept to the actual source file/function and distinguish
> general theory from this project's implementation choices and measured
> facts. Do not invent results or textbook details. Start by asking what I
> already know about tokens, dictionaries, and lists.
