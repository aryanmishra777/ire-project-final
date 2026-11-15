# content_intro.py

## What it does
Builds slides 1–6: the title, motivation, research question and hypothesis, related work, the
experiment setup, and the evaluation method. Each slide's speaker notes are the narration for
that slide.

## Responsibility
Owns the content of the framing slides, the parts of the talk that don't depend on results. The
one number used here, the query count, comes from `facts` rather than being typed.

## How
- Each `s_*` function takes the presentation and the facts dictionary and adds one slide, using
  the builders in `theme.py`.
- `SLIDES` lists the functions in talk order. `build_deck.py` calls them in sequence.
- The narration is written in first person, as Aryan presenting to the professor, at about
  60–90 words a slide.

## Why
- **Notes as narration.** The deck and the video then share one script, so they can't disagree.
  The notes are also there for a live presentation.
- **Related work as a table.** It shows each line of work next to what it leaves open, which
  makes the gap visible at a glance instead of in a paragraph.
- **Claims kept to what was checked.** Two statements were confirmed from the papers themselves:
  - "LitSearch tests GPT-4o reranking, not rewriting" (from the LitSearch paper, Table 3);
  - the closest prior work, Weller et al. (EACL 2024, arXiv 2309.08541): expansion "improves
    scores for weaker models, but generally harms stronger models", tested by re-ranking BM25's
    top 100 over 12 datasets with no literature-search benchmark, and reporting no cost.
- **The gap is stated against that closest work.** This project's contribution is the same
  question on scholarly literature search, with full first-stage retrieval per retriever and with
  cost measured.
