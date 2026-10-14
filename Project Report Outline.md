# Project Report 1 — Working Outline

> Replace bracketed prompts with course-specific details and your own final
> prose. Verify every number against the submitted code and rerun commands
> before submission. Do not include screenshots or log files; the assignment
> deducts marks for screenshots and explicitly excludes logs.

## Title page

- **Title:** Reuters-21578 Inverted Indexing and Preprocessing Experiments
- **Course:** [course name and number]
- **Author:** [name and student ID, if required]
- **Instructor:** [name]
- **Submission date:** October 19, 2026

## Abstract

This project implements and evaluates two in-memory inverted-index
construction methods over Reuters-21578 Distribution 1.0: a naive
sort-and-group indexer and a SPIMI-inspired indexer that appends document IDs
directly to postings lists. Articles are identified by their original
`NEWID` values. The system also supports single-term and AND queries and
measures how the preprocessing variants in textbook Table 5.1 affect
distinct-term and nonpositional-posting counts. Both indexers produced
identical results on the full corpus. On the required benchmark of the first
10,000 term-document pairs, median times over seven runs were 0.001989
seconds for naive indexing and 0.000712 seconds for SPIMI. Preprocessing
reduced the distinct-term count from 61,453 to 32,318 and nonpositional
postings from 1,781,942 to 886,223 in the most processed variant. [Revise
this summary after final validation and add a sentence on the key takeaway.]

## 1. Introduction

### 1.1 Problem and goals

The project explores how an inverted index supports retrieval over a text
collection. Its goals are to implement a naive indexer, a SPIMI-inspired
indexer, single-term and AND query processing, and a preprocessing experiment
based on Table 5.1 of the course textbook.

### 1.2 Dataset

The corpus is Reuters-21578, Distribution 1.0: 21,578 Reuters articles
stored in 22 SGML files. The implementation reads the supplied files rather
than NLTK's separately packaged Reuters corpus. It retains each original
numeric `NEWID` as the document ID. The indexed text is the unescaped title
concatenated with the body; absent title or body fields are allowed.

### 1.3 Scope

The project is an in-memory, nonpositional retrieval system. It does not
store token positions or term frequencies within documents, provide ranked
retrieval, or implement a web interface. [State any other scope limits that
matter to your submission.]

## 2. System design and implementation

### 2.1 Processing pipeline

Describe the flow:

```text
Reuters SGML -> (NEWID, title + body) -> tokens
             -> (term, NEWID) pairs -> inverted index -> query result IDs
```

The central index representation is `term -> sorted list of document IDs`.
Each list contains one ID per document, even if the term occurs repeatedly
within that document.

### 2.2 Corpus parsing and tokenization

The reader scans `.sgm` files in sorted filename order and opens them as
Latin-1. It extracts Reuters article blocks, reads `NEWID` from the article's
opening tag, extracts title/body, and HTML-unescapes both fields.

The tokenizer uses the compiled regular expression `[A-Za-z0-9]+`.
Punctuation and whitespace delimit tokens; case is preserved in the
unfiltered baseline. Optional transforms remove digit-only tokens, lowercase
tokens, remove supplied stop words, and apply the NLTK Porter stemmer.
Describe the ASCII-only tokenization limitation and its possible effect on
accented text.

### 2.3 Naive indexer (Subproject I)

For each input token, the system emits `(term, docid)` into a list `F`. After
all input is read, it computes `sorted(set(F))`: the set removes duplicate
term-document pairs, and sorting places each term's postings together in
ascending numeric document-ID order. A final pass groups each term with its
posting list.

On the full corpus, 2,866,956 raw term-document pairs became 1,781,942
unique pairs over 61,453 terms. Thus 1,085,014 repeated within-document
occurrences did not need separate postings.

### 2.4 Query processing (Subproject II)

A single-term query uses the same tokenizer and normalization settings as
the selected index, then returns that term's postings list. An AND query
intersects the postings lists with a two-pointer algorithm. Because lists
are sorted, the pointer with the smaller ID advances; equal IDs are emitted
to the result. For multi-term queries, lists are processed shortest first.
If query preprocessing removes an AND term, the result is empty; the query is
not silently weakened.

The six sample queries and their counts across preprocessing variants are
reported in the compression experiment document. [Add a brief explanation of
how the sample queries were chosen.]

### 2.5 SPIMI indexer (Subproject IV)

The SPIMI-inspired indexer processes terms as documents arrive and updates a
hash-table entry for each term directly. It appends the current document ID
only when that ID is not already the final posting. Since articles are
processed in increasing `NEWID` order, this both suppresses repeated
occurrences within a document and keeps postings sorted without globally
sorting all pairs. The implementation checks this ordering assumption.

### 2.6 Correctness validation

On the full corpus, both indexers produced identical dictionaries:
61,453 terms and 1,781,942 unique term-document pairs. Posting lists were
verified to be sorted, duplicate-free, and to use valid Reuters IDs. The
automated test suite additionally checks a two-article fixture, query
examples, and 100 deterministic posting-list intersection comparisons
against a set-intersection reference. [Rerun tests before submission and
record the final command/result.]

## 3. Indexer timing experiment

### 3.1 Method

The benchmark generates the first 10,000 unfiltered term-document pairs
once, before timing. Naive indexing includes set-based deduplication,
sorting, and grouping. SPIMI indexing consumes the same ordered pairs and
updates the postings dictionary directly. Parsing and tokenization are
excluded. The benchmark alternates which indexer runs first, performs seven
runs, checks index equality each time, and reports the median.

### 3.2 Results

| Indexer | Median time (seconds) |
|---|---:|
| Naive | 0.001989 |
| SPIMI | 0.000712 |

There were 6,218 unique term-document pairs among the 10,000 input pairs.
In this run, SPIMI took about 0.358 times the naive median, or about 64.2%
less time. The observed result is machine- and load-dependent; these very
short measurements should not be treated as a universal speedup.

### 3.3 Discussion

Explain the expected cost difference: naive indexing sorts the materialized
pair collection, while SPIMI appends to term postings in input order. Discuss
that both methods still process all 10,000 pairs and that the timing excludes
parsing/tokenization by design. [Include machine/runtime details if required
by your instructor; do not invent them.]

## 4. Preprocessing experiment (Subproject III)

The full method, counts, query result table, and comparison with textbook
Table 5.1 are in the required separate document, [Compression experiment](./Compression%20experiment.md).
Summarize the main observation here without duplicating that document:

- From unfiltered to the final stemming variant, terms fell from 61,453 to
  32,318 (47.4% cumulative reduction).
- Nonpositional postings fell from 1,781,942 to 886,223 (50.3% cumulative
  reduction).
- Removing 150 stop words left term count nearly unchanged relative to case
  folding but reduced postings by 37.9%.
- Stemming reduced terms by 24.9% from the 150-stop-word row and postings by
  4.8%.

Discuss why results differ from Reuters-RCV1: corpus size and token
distribution differ, and measured values also depend on tokenization and the
specific corpus-derived stop lists. Distinguish these unique term-document
posting counts from encoded index bytes; no postings compression scheme was
measured here.

## 5. Challenge queries

The challenge query file and results are not available in this workspace yet.
When released, record:

- Release date/source: [verify with course materials; the supplied brief has
  conflicting dates.]
- Exact command and query-file name: [fill in]
- Naive results and timing: [fill in]
- SPIMI results and timing: [fill in]
- Confirmation that the two indexers returned matching results: [fill in]

Attach or submit the required run output separately. Do not paste raw logs
into this report if the course says not to include log files.

## 6. Limitations and future work

- Tokenization is ASCII-only and treats apostrophes and decimal punctuation
  as separators (for example, `2.5` becomes `2`, `5`).
- Indexing only title and body is a deliberate choice; the report should
  state it because other fields in the SGML are excluded.
- The index is in memory and nonpositional; postings store document presence,
  not term frequency or within-document locations.
- The SPIMI implementation is in-memory; it does not flush blocks to disk.
- Timing covers the assignment's 10,000-pair index-building segment and is
  sensitive to the runtime environment.
- [Add any limitations or unsuccessful approaches actually encountered.]

## 7. Conclusion

Summarize whether the project met each stated objective. Emphasize that the
naive and SPIMI methods produce the same index, while SPIMI avoids the
global sort for the measured input. State how preprocessing changed terms,
postings, and selected query results. Avoid claiming that one approach is
universally best based only on this dataset and benchmark.

## References

1. [Course textbook author(s)], *[Title]*, [edition], Table 5.1, section 5.1,
   and the Porter stemming reference. [Complete bibliographic details from
   the syllabus or textbook.]
2. Lewis, D. D. et al. *Reuters-21578, Distribution 1.0*, 1997. Cite the
   corpus documentation included in `reference/README.txt` and provide the
   dataset location required by the course.
3. [NLTK documentation or package reference, if required by course citation
   style.]

## Generative AI use disclosure

[Follow the course's required disclosure policy. State accurately which tools
were used and for what tasks, such as brainstorming, code assistance,
debugging, or language editing. Review and understand all submitted code and
claims yourself; do not copy this placeholder unchanged.]
