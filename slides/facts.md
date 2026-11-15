# facts.py

## What it does
Loads the experiment's result tables, plus the illustrative study's per-question table, and turns
them into the numbers and plain-language findings the slides and narration use.

## Responsibility
Owns the link between results and words. It's the only place where a result becomes a sentence
("2 of 4 rewrites help significantly…"), so no slide or narration can state a number or a verdict
that isn't in `results/`.

## How
- `load()` reads `comparisons.csv`, `interaction.csv`, `cost.csv`, `reproduction.csv`,
  `failure_terms.csv` and `per_query_main.csv`, and derives:
  - the best variant per retriever on nDCG@10;
  - how many rewrites help or hurt significantly (BH-adjusted p < 0.05);
  - the hypothesis verdict;
  - the raw dense − BM25 gap;
  - the largest reproduction difference;
  - the rare-term loss summary and the worst example.
- **The verdict rule:** "supported" if at least 3 of the 4 variants show a significant positive
  interaction (BM25 gains more than dense); "partly supported" if 1–2 do; otherwise "not
  supported".
- `study_facts()` reads the real pilot (`study/data/results/study_per_question.csv`). It leaves
  out the researcher's dry-run question (`DRY_RUN = "P01"`), recomputes the paired comparison
  with the same `compare()` used everywhere else, and also returns the all-in comparison and the
  questions the rewrite made worse. Fidelity numbers are included only once at least 3 replies
  exist.
- `headline()` returns the three findings sentences, and `fmt_ci()` formats a Δ with its CI.

## Why
- **Fixed rules instead of hand-written conclusions.** If a rerun changes a number, the wording
  changes with it, so the deck can't drift from the data. Fixing the rules before seeing results
  also guards against wording the conclusion to fit what the data happened to show.
- **The verdict needs 3 of 4 variants.** One significant variant out of four could be a fluke of
  that prompt. Most of the variants agreeing is a reasonable bar for "supported".
