# content_results.py

## What it does
Builds slides 7–12:
- the reproduction check against LitSearch Table 3;
- the effect of each rewrite on nDCG@10;
- the retriever × rewrite interaction (the hypothesis test);
- per-question wins and losses;
- the cost frontier;
- the rare-term failure analysis with a worked example.

## Responsibility
Owns how results are presented and narrated. Every number comes from the `facts` dictionary or
the figures in `results/figures/`. Titles that state a conclusion are chosen by rules, for
example "match / are close to / differ from" for the reproduction check, depending on the
largest gap.

## How
- **Reproduction:** a table of our raw-question recall next to the paper's, per measure and
  retriever.
- **Effects and interaction:** each slide has its figure plus a table, or the `headline()`
  sentences.
- **Wins/losses:** the narration names the cell with the most per-question losses.
- **Cost:** the Pareto figure plus a tokens and p95-latency table. The narration quotes HyDE's
  cost.
- **Failure:** a table of the mean Δ for queries that kept vs lost a rare term, and the single
  worst BM25 loss with its question, rewrite and lost terms.

## Why
- **Rule-chosen wording.** The same code works whether or not the hypothesis holds. The slides
  can't overstate a result the data doesn't support.
- **A worked example on the failure slide.** An average Δ is abstract. Seeing the exact term a
  rewrite dropped makes the mechanism obvious in a viva.
- **Latency labelled with its hardware.** Latency depends on the machine (one NVIDIA L4 here),
  so the slide says so instead of presenting it as a property of the method.
