# failure.py

## What it does
Tests the failure mode the proposal predicted: a rewrite turns a specific technical question into
generic phrasing and drops the term that pointed to the right paper.

## Responsibility
Owns the term-level analysis of the rephrase variant, the only variant that replaces the user's
words. It writes the per-query table and the worked examples used in the slides.

## How
- Tokenizes like BM25: lower-case, split on hyphens and punctuation (so "health-related" is
  "health" + "related"), drop stopwords, Snowball-stem.
- Counts, for every stemmed word, how many of the 64k titles and abstracts contain it (document
  frequency).
- A query word is **rare** if fewer than 100 papers contain it. These are the discriminating
  terms: method names, dataset names, unusual task words.
- For each query, it finds the rare terms missing from the rewrite (after stemming), and joins
  each query's Δ nDCG@10 for BM25 and dense.
- The summary compares the mean Δ for queries that lost at least one rare term against queries
  that kept them all.
- `write_examples()` lists the six largest BM25 losses with the question, the rewrite and the
  terms it lost.

## Why
- **The same tokenization as BM25.** An earlier version kept hyphenated words whole. It then
  reported "health-rel" as lost when a rewrite kept both "health" and "related". A term only counts
  as lost if the retriever itself can no longer match it.
- **A document-frequency threshold, not a list of named entities.** It needs no extra model,
  works for any jargon, and matches what BM25 rewards (high-IDF terms).
- **Only rephrase.** Expansion, HyDE and multi-query all keep the original question, so they can't
  lose its terms by construction.
- **Worked examples next to the averages.** The averages show whether the effect exists, and the
  examples show what it looks like, which a viva audience understands faster.
