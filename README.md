# Does LLM Query Rewriting Actually Improve Scholarly Retrieval?

Final project for CS4.406 Information Retrieval and Extraction (Monsoon 2026), IIIT Hyderabad.
Aryan Mishra (Team Solo Retriever).

Many search pipelines ask an LLM to rewrite the user's question before searching. This project
measures whether that step helps scholarly literature search on its own, under which retriever,
and at what cost. It runs a controlled grid on LitSearch:
- **queries:** 597 real literature-search questions over 64,183 ACL and ICLR papers;
- **retrievers:** BM25 and dense retrieval (E5-large-v2);
- **query forms:** the raw question and four LLM rewrites (rephrasing, term expansion,
  a HyDE-style abstract, multi-query with RRF fusion).

The hypothesis: rewriting helps BM25 clearly and helps dense retrieval little. It's tested
directly as a retriever × rewrite interaction.

## Results
All numbers are in `results/summary.md`, the CSVs in `results/`, and the figures in
`results/figures/`. The deck (`slides/deck.pptx`) and video (`video/presentation.mp4`) are
generated from those files, so they always agree with them.

## Deliverables

| Deliverable | Path | Built by |
|---|---|---|
| Code | `rewrite_eval/`, `study/`, `demo/` | — |
| Results | `results/` | `python -m rewrite_eval analyze` |
| Slide deck | `slides/deck.pptx` (+ `slides/narration.md`) | `python -m slides.build_deck` |
| Report (PDF) | `../Final Report - Aryan Mishra.pdf` | `python -m report.build_report` |
| Narrated video | `video/presentation.mp4` (built locally, not stored in the repo) | `python -m video.build_video` (voice: `video/chatterbox_tts.py`) |
| Demo | `demo/compare.py` | `python -m demo.compare --qid q042` |

## What's in the code
- **`rewrite_eval/`**: the benchmark experiment.
  - Data and indexes: `data.py`, `retrieval.py`.
  - LLM rewrites and their cache: `rewrite.py`.
  - The grid: `run.py`.
  - Metrics and paired statistics: `metrics.py`, `stats.py` (bootstrap CIs, randomisation test,
    Benjamini–Hochberg, minimum detectable effect).
  - Tables, figures and failure analysis: `tables.py`, `figures.py`, `failure.py`, `analyze.py`.
- **`study/`**: the human-study kit.
  - Participant forms.
  - Running the literature-review tool with its rewriting step on and off.
  - Blind pooling and the analysis.
- **`demo/`**: the side-by-side retrieval demo.
- **`aws/`**: the GPU run on AWS. This covers the IAM policy that was granted, the remote script,
  and the teardown commands.

## Conventions
- **Small files.** No source file has more than 150 lines of code, or 170 including docstrings.
- **A companion doc for every source file.** Each `x.py` has an `x.md` next to it explaining what
  it does, what it's responsible for, how it works and why it's built that way.
- **Checked by a script.** `python scripts/check_loc.py` enforces both rules.
- **No hand-typed numbers.** Every number in the results, deck and narration is read from the
  output files.

## The human study (pilot)
**Data:** `study/data/`, with results in `study/data/results/study_summary.md`.
- **Participants:** 7 participants (P02–P08) each gave one literature-search question from their
  own work. P01 is the researcher's own question, run as a dry run and kept out of the main
  numbers.
- **Runs:** each question ran through the literature-review tool twice, rewriting on and
  bypassed, using Crossref + arXiv + LLM-suggested venues. The runs were done on an AWS L4.
- **Who judged what:** participants supplied their questions. They had no time for the rating
  task, so **relevance was judged by the researcher, blind to condition** (pooled, shuffled
  sheets). **Fidelity** (how much of each question the rewrite kept, 1–5, plus what it dropped)
  was **also assessed by the researcher**, after all relevance grading was finished
  (`study/data/fidelity_assessed.csv`).
- **How to read it:** this is a pilot. With 7 questions only large effects are detectable, and
  the summary reports the minimum detectable effect next to every result.

`study/illustrative/` is a separate, **simulated** demo of the same pipeline
(`study/make_illustrative.py`). It's labelled as such everywhere, and it isn't used in the deck
or in any result.

## Reproducing
See `REPRODUCE.md`. The released `data/rewrite_cache.jsonl` holds every LLM rewrite used in the
results, so the retrieval and analysis can be reproduced exactly without running any LLM.

## Prior-work note
The human study runs my own literature-review tool, which predates this course. The tool is
reused unchanged as the test system. The harness, the experiment, the study design and the
analysis here are new work for this course.

An automated check found no code copied from the tool: 1 identical line (a standard
`mkdir` idiom) and 0 shared blocks. See `prior-work-overlap.md`.
