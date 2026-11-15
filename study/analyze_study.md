# analyze_study.py

## What it does
Scores the human study. For each question it computes nDCG@10 and P@10 for the run with the
original question and the run with the LLM rewrite, using blind relevance labels. It then runs
the paired test. When participants' fidelity replies exist, it also relates fidelity to the gain.
It writes a table, a summary and a figure.

## Responsibility
Owns the human-study numbers. It reuses `rewrite_eval.metrics` and `rewrite_eval.stats`, so the
human data and the LitSearch benchmark go through identical metric and significance code. It also
owns two labels: who judged relevance, and the stamp on illustrative outputs.

## How
1. For every participant with a graded sheet (`ratings/<pid>.csv`), it rebuilds each condition's
   ranked list from `key.csv`. Ungraded participants are skipped, so it can run mid-study.
2. It computes nDCG@10 with graded gains (0/1/2), using the ideal ranking over all pooled papers.
   P@10 counts any grade ≥ 1 as relevant.
3. It joins `fidelity.csv` if present. Missing or blank replies stay empty, and the fidelity
   analysis runs only once at least 3 replies exist.
4. **The main analysis** leaves out the pids given in `--exclude`, e.g. the researcher's own
   dry-run question P01. An extra row reports nDCG@10 with everyone included, as a sensitivity
   check.
5. `compare()` gives the mean Δ, the 95% paired-bootstrap CI, the randomisation p-value, the wins
   and losses, and the minimum detectable effect (MDE). The fidelity line adds a Spearman
   correlation between fidelity and Δ.
6. **Outputs:** `results/study_per_question.csv` (every graded participant), `study_summary.md`,
   and `study_figure.png`. The figure has paired slopes per question, labelled by pid, plus a
   fidelity-vs-Δ panel when there are replies.
7. `--judge researcher|participants` sets the "who judged relevance" wording in the summary and
   on the figure's axis. `--fidelity-by researcher|participants` does the same for the fidelity
   line. In the real pilot both are `researcher`. `ILLUSTRATIVE.txt` in the folder stamps
   everything as simulated.

## Why
- **The ideal ranking comes from the pool.** Both conditions are measured against the same set of
  known-relevant papers, which keeps the paired comparison fair.
- **Fidelity is optional.** In the real pilot, relevance was judged first and the fidelity replies
  came later. Requiring them would block the analysis for no reason.
- **The researcher's own question is excluded from the main result.** The researcher knows the
  hypothesis. Reporting it only as a sensitivity row keeps the main result to the questions they
  didn't write.
- **Who judged is printed.** The real pilot's relevance labels come from the researcher, judging
  blind, not from participants. The summary and the figure say so, so the design change can't be
  missed.
- **The MDE is in every row.** With 7–8 questions the study can only detect large effects.
  Stating the MDE stops a null result being read as "no effect".
