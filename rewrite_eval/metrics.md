# metrics.py

## What it does
Computes per-query retrieval metrics from a ranked list of paper ids and the gold set.

## Responsibility
Owns the metric definitions and nothing else. It gets plain lists and sets, never DataFrames or
file paths, so the LitSearch harness and the human study share the same code.

## How
- `recall_at(k)`: the fraction of gold papers that appear in the top k.
- `precision_at(k)`: the fraction of the top k with grade > 0 (used by the human study).
- `mrr()`: 1 / the rank of the first gold paper within the top 100, or 0 if none appears.
- `ndcg_at(k)`: DCG with gain = grade and a log2(rank + 1) discount, divided by the ideal DCG
  built from all judged grades. LitSearch's gold set gives binary grades (1). The human study's
  labels give graded 0/1/2.
- `all_metrics()` returns nDCG@10, recall@5/20/50/100 and MRR for one query.

## Why
- **Recall@5 and @20.** These are what LitSearch reports (R@5 for specific questions, R@20 for
  broad), so they're needed for the reproduction check.
- **nDCG@10.** It's the headline effect metric: it rewards putting the right paper near the top,
  where a researcher actually looks.
- **Recall@50.** It's the quality axis of the cost plot, as the proposal specified.
- **Hand-written formulas, not a library.** They're a few lines each, easy to check at the viva,
  and they can take graded labels without a format conversion.
