# run.py

## What it does
Executes every retriever × variant cell for the chosen queries, saves the rankings, and scores
each query.

## Responsibility
Owns the definition of how each rewriting variant becomes a retrieval request. That's the
experiment's main design decision, so it lives in one function, `_requests()`. It also records
retrieval time per cell for the cost analysis.

## How
- `build_indexes()` loads the corpus and builds, or loads from cache, the BM25 index and the
  E5 embeddings.
- `_requests()` maps a variant to a request:
  - **raw**: the question itself;
  - **rephrase**: the rewrite replaces the question;
  - **expand**: question + terms;
  - **hyde**: question + abstract for BM25, and the question vector averaged with the abstract's
    passage vector for dense;
  - **multi**: the question plus 3 generated queries, each searched separately, then fused with
    RRF.
- `run_cells()` loops over the variants, times each retriever, and writes
  `results/runs_<tag>.parquet`, `retrieval_timing_<tag>.csv` and `per_query_<tag>.csv`.
- `score()` attaches all metrics plus LitSearch's metadata (specificity, quality, query set) for
  the subgroup analysis.

## Why
- **Expansion and HyDE keep the original question.** That's how the source methods work (Query2doc
  and Jagerman et al. concatenate; HyDE mixes in the query). It also means those variants test
  adding LLM text, while rephrase tests replacing the user's words. That contrast is where the
  expected failure mode shows up.
- **Multi-query includes the original in the fusion.** The usual RAG-Fusion setup does, and
  generated queries alone would confound "more queries" with "lost the original".
- **The same variant definition for both retrievers wherever possible.** The only exception is
  HyDE, because a dense model can mix vectors and BM25 can't. Otherwise a retriever × variant
  interaction could be an artefact of different request formats.
- **Saved rankings, not just scores.** The analysis can be rerun, and new metrics added, without
  rerunning retrieval.
