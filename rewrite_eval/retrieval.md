# retrieval.py

## What it does
Provides the two retrievers (BM25 and dense) over the LitSearch corpus, plus reciprocal rank
fusion (RRF) for the multi-query variant.

## Responsibility
Owns indexing and search. Given query strings (or query vectors) it returns the top-100 corpus
ids in rank order. It doesn't know about rewriting variants or metrics.

## How
- **`BM25Retriever`** uses `bm25s` (Lucene-style BM25, k1=1.5, b=0.75) with English stopwords and
  a Snowball stemmer. It builds the index once and saves it to `data/bm25_index/`.
  - `search()` tokenises each query on its own. A query whose words are all stopwords returns an
    empty list instead of failing the batch.
- **`DenseRetriever`** loads `intfloat/e5-large-v2` with sentence-transformers.
  - It encodes every paper as `"passage: <text>"`, L2-normalised, and caches the vectors as
    float16 `.npy`.
  - Queries are encoded as `"query: <text>"`.
  - `search_vectors()` does exact cosine search: a matrix product, then `argpartition` for the
    top-k and a sort of just those k.
  - `encode_docs()` is exposed so the HyDE variant can embed a hypothetical abstract as a
    passage.
- **`rrf()`** scores each document as the sum over lists of 1 / (60 + rank) and keeps the top 100.

## Why
- **Exact search, not approximate (ANN).** 64k × 1024 floats fits easily in RAM, and a matrix
  product takes milliseconds. Exact search also removes approximation error as a confound.
- **`bm25s`.** It's a fast, pure-Python BM25 that matches Lucene's scoring, with no Java or
  Pyserini setup. That matters for a reproduction kit people should run on a laptop.
- **float16 cache, float32 search.** It halves the file on disk without measurable effect on
  rankings.
- **One BM25 query at a time.** It's slower than batching but robust to empty queries, and BM25
  over 64k documents is fast anyway.
