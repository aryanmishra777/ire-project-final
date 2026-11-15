# tables.py

## What it does
Builds the numeric result tables from per-query scores: the reproduction check, the rewrite-vs-raw
tests, the retriever × rewrite interaction, the subgroup breakdowns, and cost.

## Responsibility
Owns the analysis that produces numbers. It doesn't draw (that's `figures.py`), and it doesn't
decide file names or order (that's `analyze.py`).

## How
- `with_groups()` adds LitSearch's two splits: inline-citation vs author-written, and broad vs
  specific.
- `reproduction()` computes the raw-question baselines the way LitSearch reports them (R@20 for
  broad questions, R@5 for specific ones, in percent) next to the paper's Table 3 values, with
  the difference.
- `comparisons()` pivots to one row per query and runs `stats.compare` for each rewrite against
  raw, per retriever and per metric. It applies BH within each metric's family of 8 comparisons
  and adds the raw dense − BM25 gap.
- `interaction()` computes, per query, (rewrite − raw under BM25) − (rewrite − raw under dense)
  and tests whether its mean is zero. Positive means BM25 gains more, which is the hypothesis.
- `subgroups()` gives the mean Δ nDCG@10 per variant × retriever × query set × specificity.
- `cost()` takes average tokens and mean / p95 LLM latency from the rewrite cache and joins them
  to recall@50, nDCG@10 and retrieval time.

## Why
- **The interaction tested per query.** The hypothesis is about a difference of gains.
  Eyeballing two separate CIs can't test that, so it gets its own paired test.
- **Reproduction in the paper's own format.** A reviewer can check the numbers against Table 3
  directly.
- **Cost from the cache, not re-measured.** The cache already holds every call's real tokens and
  latency. Re-measuring would cost money and add noise.
