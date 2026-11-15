# pool.py

## What it does
Merges each participant's two top-10 lists into one deduplicated, shuffled rating sheet. It also
writes the hidden key that records which condition ranked each paper, and where.

## Responsibility
Owns blinding. Participants only ever see `rating_sheets/<pid>.csv`, which carries no condition
information. The mapping back to conditions lives only in `key.csv`.

## How
1. Reads every `runs/<pid>.json`.
2. Treats the same paper found by both runs as one item. It matches on the lower-cased title
   with punctuation stripped, falling back to the DOI only when a record has no title. The first
   real run (P01) found the same paper twice under different DOIs (journal and arXiv), so DOI
   matching would show it to the participant twice.
3. Records `rank_on` and `rank_off` for each item (blank if that run didn't return it). If the
   same paper appears twice in one list, it keeps the better rank.
4. Shuffles the items with a random generator seeded from the participant id, and labels them
   `P01-01`, `P01-02`, ….
5. Writes `rating_sheets/<pid>.csv` (item, title, abstract, year, venue, blank grade), `key.csv`,
   and `fidelity_template.csv` (question + rewrite, for Part B of Form 2).

## Why
- **Pooling plus shuffling (standard TREC-style pooling).** The participant judges each paper once,
  without knowing its source, so a preference for one condition can't leak into the labels.
- **Deduplication.** A paper both runs found is rated once, and that single label counts for both
  conditions. That's fair, and it shortens the task.
- **Existing sheets are never overwritten.** Participants (or the researcher) may grade a sheet
  in place. Re-running pooling for new participants must not wipe those grades. The seeded
  shuffle means a sheet never needs regenerating anyway.
- **Seeded shuffle.** A lost sheet can be regenerated identically, and the order is still
  unpredictable to the participant.
- **Fidelity questions in a separate file.** Part B is shown after the ratings. Seeing the rewrite
  first could bias relevance judgments.
