# build_deck.py

## What it does
Builds `slides/deck.pptx` from the current results and writes `slides/narration.md`, the speaker
notes of every slide as plain text.

## Responsibility
Owns slide order and the output files. Content lives in the three `content_*.py` modules, looks
in `theme.py`, and numbers in `facts.py`.

## How
1. `facts.load()` reads every results table once.
2. Calls each slide function from `content_intro`, then `content_results`, then
   `content_close`.
3. Saves the deck, then collects each slide's notes into `narration.md` (one section per slide).

Run it with `python -m slides.build_deck` from the project root, after
`python -m rewrite_eval analyze` and `python -m study.make_illustrative`.

## Why
- **The deck is a build artefact.** Rerunning the analysis and then this script always gives a
  deck consistent with the data. There's no manual copy-paste of numbers.
- **`narration.md` as well as notes.** The script can be reviewed and edited as text, and the
  video builder reads the same notes, so what's said always matches what's shown.
