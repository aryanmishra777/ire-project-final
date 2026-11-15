# figures.py

## What it does
Draws the four result figures used in the slides and the video: effect sizes with CIs, the
interaction slopes, the cost-quality plot, and per-query wins and losses.

## Responsibility
Owns presentation only. It gets finished tables from `tables.py` and writes PNGs to
`results/figures/`. It does no statistics.

## How
- `effects()` plots Δ vs raw with 95% bootstrap CIs, one point per variant and retriever, each
  labelled with its value.
- `interaction()` draws one small panel per variant with a raw → rewritten line per retriever. If
  the lines aren't parallel, there's an interaction.
- `pareto()` plots recall@50 against LLM tokens per query, and against p95 added latency, in two
  panels on one shared quality axis.
- `win_loss()` draws diverging bars: per cell, how many queries improved and how many got worse.

## Why
- **Blue for BM25, orange for dense.** The pair was checked with a colour-vision-deficiency
  validator. Orange is low-contrast on white, so every series is also labelled directly and
  colour is never the only cue.
- **Intervals, not bars, for effects.** The question is "is the gain different from zero, and by
  how much". A dot with a CI answers that, while a bar suggests a quantity starting at zero.
- **Small multiples for the interaction.** Four variants on one plot would overlap. Separate
  panels with a shared y-axis keep the slopes comparable.
- **Two panels, not two y-axes, for cost.** Tokens and seconds have different units, and a dual
  axis would invent a relation between them.
- **Win/loss counts as well as means.** A small mean gain can hide many queries that got worse.
  The counts show how risky the step is per query, which is what a system builder needs.
