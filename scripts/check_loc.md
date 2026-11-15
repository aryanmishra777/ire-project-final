# check_loc.py

## What it does
Checks every Python source file against the project's file rules (README, "Conventions"), and exits
non-zero if any file breaks one.

## Responsibility
Owns enforcing three rules:
- at most 150 lines of code;
- at most 170 lines including docstrings;
- a companion `.md` next to every source file (except empty `__init__.py`).

## How
- Walks the project for `*.py`, skipping `.venv`, `data`, `results`, `__pycache__` and `build`.
- Parses each file with `ast` and collects the line ranges of module, class and function
  docstrings.
- Counts non-blank lines in total, and non-blank lines outside docstrings (code; comments count).
- Prints one status line per file and a pass/fail total.

## Why
- **`ast`, not a regex for triple quotes.** A regex can't tell a docstring from a multi-line
  string used as data. The parser knows exactly which strings are docstrings.
- **Blank lines not counted.** The rule is about how much logic a file holds, not about spacing,
  so blank lines between functions shouldn't push a file over.
- **A script, not a convention.** Rules that are only written down drift. A check that fails
  loudly keeps every file small and documented.
