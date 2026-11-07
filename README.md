# Reuters Search Engine

A compact, educational information-retrieval project that builds inverted indexes over the Reuters-21578 news collection. It includes a straightforward in-memory index, a single-pass index builder, Boolean term and AND queries, tokenizer preprocessing options, and scripts for comparing index construction and vocabulary statistics.

> **Project scope:** This is a command-line search prototype for demonstrating indexing and retrieval techniques. It does not provide a web interface, ranked search results, or a persistent/on-disk index.

## Features

- Reads Reuters SGML files and extracts each article's `NEWID`, title, and body.
- Builds an inverted index mapping each term to its sorted document-ID postings list.
- Provides both a naive sort-and-deduplicate index builder and a single-pass SPIMI-style builder.
- Supports single-term lookup and Boolean AND queries using postings-list intersection.
- Offers optional number removal, case folding, stop-word filtering, and Porter stemming.
- Includes a small correctness demo, a corpus query demo, an indexer benchmark, and preprocessing statistics.

## Repository layout

| Path | Description |
| --- | --- |
| `DATA/` | Reuters SGML corpus used by the demos and benchmark |
| `testDATA/` | Small sample corpus used by tests and the tiny demo |
| `reader.py` | SGML article reader |
| `tokenizer.py` | Tokenization and optional preprocessing |
| `pairs.py` | Generates term/document-ID pairs |
| `naive_indexer.py` | Sorts and deduplicates pairs to build an index |
| `spimi_indexer.py` | Builds an index in a single pass over ordered documents |
| `query.py` | Single-term and Boolean AND retrieval |
| `compress.py` | Preprocessing variants and vocabulary/postings statistics |
| `bench.py` | Repeated timing comparison of the naive and SPIMI builders |
| `demo.py` | Selectable project demos |
| `run_naive.py` | Runs the naive index builder over `DATA/` |
| `test_tiny.py` | Unit tests |

## Requirements

- Python 3.9 or later
- `pip`
- The Reuters SGML files in `DATA/` (included in this repository)

The only third-party Python dependency is NLTK, used for Porter stemming. It is declared in [`requirements.txt`](requirements.txt).

## Setup

Create and activate a virtual environment from the project root:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

On Windows PowerShell, activate it with:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install the project dependency:

```bash
python -m pip install -r requirements.txt
```

## Run the demos

Run one of the three demo sections from the project root:

```bash
python demo.py tiny
python demo.py queries
python demo.py compression
```

- **`tiny`** compares the naive and SPIMI indexes on `testDATA/` and runs sample queries.
- **`queries`** runs example `coffee` and `coffee AND crop` searches on `DATA/`.
- **`compression`** reports term and postings counts for several preprocessing variants on `DATA/`.

Other useful commands:

```bash
# Build the naive index and report its size and elapsed time.
python run_naive.py

# Compare index builders on a sample of term/document pairs.
python bench.py

# Run the unit tests.
python -m unittest -v
```

The benchmark uses a fixed sample of 10,000 term/document pairs and reports median timings across repeated runs. It verifies that both builders produce equal indexes before returning results.

## Use the search API

Build an index and query it from Python:

```python
from pathlib import Path

from query import and_query, single_term_query
from spimi_indexer import build_spimi_index

data_dir = Path("DATA")
index = build_spimi_index(data_dir)

coffee_documents = single_term_query(index, "coffee")
coffee_and_crop_documents = and_query(index, "coffee crop")

print(coffee_documents)
print(coffee_and_crop_documents)
```

Each result is a list of Reuters numeric document IDs (`NEWID`), not article text or a relevance-ranked result set. `and_query` returns documents containing every query term. Query terms use the same tokenization settings used to build the index.

### Preprocessing

The tokenizer accepts optional settings. Apply matching settings both when building the index and when querying it:

```python
from pathlib import Path

from query import and_query
from spimi_indexer import build_spimi_index

options = {
    "remove_numbers": True,
    "case_fold": True,
    "stemming": True,
}

index = build_spimi_index(
    Path("DATA"),
    tokenizer_options=options,
)
results = and_query(
    index,
    "Coffee crops",
    tokenizer_options=options,
)
```

Available tokenizer options:

| Option | Default | Effect |
| --- | --- | --- |
| `remove_numbers` | `False` | Discards tokens consisting only of digits |
| `case_fold` | `False` | Converts tokens to lowercase |
| `stopwords` | `None` | Discards tokens found in the supplied collection |
| `stemming` | `False` | Applies the NLTK Porter stemmer |

By default, token matching is case-sensitive. If you build an index with preprocessing enabled, use the same options for searches so query terms are normalized consistently.

## How indexing works

The reader processes `.sgm` files in filename order, extracts `<REUTERS>` articles, and uses each article's numeric `NEWID` as its document ID. It combines the article title and body as the text to tokenize.

The naive path creates term/document pairs, sorts and deduplicates them, then builds postings lists. The SPIMI-style path consumes pairs in document order and appends each document ID to the corresponding term's postings list. The index is held in memory as a Python dictionary:

```text
{
    "market": [1, 4, 12],
    "trade": [2, 4]
}
```

The SPIMI builder expects documents to arrive in increasing `NEWID` order, which the bundled reader provides when reading the corpus.

## Preprocessing statistics

`python demo.py compression` compares these variants:

1. Unfiltered tokens
2. Number removal
3. Number removal and case folding
4. The above plus the 30 most frequent terms as stop words
5. The above plus the 150 most frequent terms as stop words
6. Stemming in addition to the 150-stop-word configuration

The report counts unique terms and term/document postings. These are useful index-size proxies for studying preprocessing; the script does **not** encode postings or measure a compressed index file's byte size.

## Dataset

The project uses the Reuters-21578, Distribution 1.0 text categorization collection. The dataset is available from the [UCI Machine Learning Repository](https://archive.ics.uci.edu/dataset/137/reuters+21578+text+categorization+collection) and was compiled by David D. Lewis and contributors. The repository includes SGML data under `DATA/` and a small sample under `testDATA/`.

Please consult the dataset source for its terms of use and attribution requirements.

## Project documents

- [Project report](Project%20Report%20-%20479.pdf)
- [Project demo slides](Project%20demo%20-%20479%20%281%29.pdf)
- [Compression experiment](Compression%20experiment%20%281%29.pdf)
