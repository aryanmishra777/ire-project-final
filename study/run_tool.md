# run_tool.py

## What it does
Runs each participant's question through the literature-review tool in two conditions, and saves
both top-10 lists plus the tool's rewrite to `<study>/runs/<pid>.json`:
- **on**: the tool's LLM query understanding rewrites the question;
- **off**: the raw question goes straight to retrieval.

## Responsibility
Owns producing the two conditions with everything else held fixed: the same sources, ranker,
model and result depth. It doesn't pool, rate or score; that's `pool.py` and `analyze_study.py`.

## How
- Run it with the **tool's own venv interpreter**, because it imports the tool's modules (add the
  tool folder to `sys.path`). It never edits the tool.
- **on**: calls `pipeline.run_retrieval(question)`, so the tool's normal path runs, including
  query understanding.
- **off**: passes `structured=StructuredQuery(refined_query=question, keywords=[])`. The tool then
  skips its LLM step and searches with the participant's exact words. The same switch is how the
  tool's Plan Mode supplies a ready-made query, so this uses an existing path, not a hack.
- Sets the tool's full-text stage to `None` for the run, so no PDFs are downloaded, and turns off
  LLM tiering and Sci-Hub. Only the ranked list matters for the study.
- **Sources:** `--source` (default `crossref,arxiv`) uses the tool's own multi-source translator,
  which searches both concurrently and de-duplicates by DOI.
- **Venues:** `--venues auto` lets the tool suggest venues for each question and auto-pick the top
  3 (its non-interactive path). `--venues "ACL,EMNLP"` gives a fixed list. Either way it calls the
  tool's `venue_flow.select_venues`, so venue handling is the tool's own.
- **One pipeline per question:** a fresh pipeline is built for each question, venues are chosen
  once, and both conditions run on that same pipeline.
- Saves one JSON file per participant, recording the sources, the chosen venues and the tool's
  model alongside the two lists. Participants already done are skipped, so a crash costs at most
  one question.

## Why
- **The bypass goes through `run_retrieval`'s `structured` argument.** It needs no edit to the
  tool, keeps sources, ranking and enrichment identical between conditions, and isolates the one
  stage under test.
- **Top 10 per condition.** Two lists of 10 pool to at most 20 papers. That keeps the rating task
  near 15 minutes, which is what volunteers will tolerate.
- **Venues chosen once and shared by both conditions.** If each condition picked its own venues,
  the rewrite-on run could search different conferences than the rewrite-off run, and the
  difference would no longer be only the rewrite.
- **crossref + arXiv by default.** Much recent CS work exists only as a preprint, and most
  participants at IIIT-H are in CS-adjacent fields.
- **A separate interpreter.** The tool has heavy dependencies (LangGraph, browser automation)
  that don't belong in this project's venv.
