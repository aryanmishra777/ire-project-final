# analyze.py

## What it does
Runs the whole analysis for one result set: calls the table builders, the failure analysis and
the figures, then writes `results/summary.md`.

## Responsibility
Owns the order of the analysis and the output file names, nothing more. All computation lives in
`tables.py`, `failure.py` and `figures.py`.

## How
1. Reads `per_query_<tag>.csv`, and the provider from `runs_<tag>.parquet`.
2. Writes the cell means, the comparisons and the interaction for every run.
3. For cross-check runs (`tag` other than `main`, e.g. the local Ollama subset), prints the
   nDCG@10 comparisons and stops.
4. For the main run, it also writes the reproduction, subgroup, cost and failure tables, draws all
   figures, and assembles `summary.md` from the tables as markdown.

## Why
- **A thin orchestrator.** It keeps every step independently testable, and each file stays under
  the project's 150-line limit.
- **Cross-check runs skip the extras.** The reproduction, cost and failure views describe the main
  configuration. Recomputing them for a 100-query subset would produce misleading duplicates.
- **`summary.md` built from the same DataFrames as the CSVs.** No number in the summary is ever
  typed by hand.
