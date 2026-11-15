# data.py

## What it does
Downloads LitSearch from the Hugging Face hub once, caches it as parquet, and hands out the
queries, the corpus, and the text indexed for each paper.

## Responsibility
Owns the benchmark's on-disk form. Other modules call `load_queries()`, `load_corpus()` and
`doc_texts()`, and never touch the hub or the raw schema.

## How
- `_download()` loads two configs: `query` (597 rows) and `corpus_clean` (64,183 rows, only
  `corpusid`, `title` and `abstract`).
- It adds a stable `qid` (`q000`–`q596`), casts gold `corpusids` to int, and fills missing
  titles or abstracts with empty strings.
- Both tables are written to `data/*.parquet`. Later calls read the parquet files.
- `doc_texts()` builds the indexed string `"<title>. <abstract>"`.

## Why
- **Titles and abstracts only.** LitSearch's main results (Table 3) use exactly this, so the
  reproduction check compares like with like. The paper also shows full text does not help
  consistently (Table 5).
- **Only three corpus columns.** `corpus_clean` also has a `full_paper` column of up to 635k
  characters. Reading it would cost gigabytes of RAM for nothing.
- **Parquet cache.** Later runs start in seconds and work offline. The dataset is also pinned to
  what was downloaded, even if the hub copy changes.
