# Code overlap: IRE project vs literature-review tool

- Project: 30 Python files, 1864 non-blank lines
- Tool: 105 Python files, 6544 non-blank lines (venv/output excluded)
- Identical non-trivial lines (≥25 chars, not imports/boilerplate): **1**
- Shared blocks of 4 consecutive lines: **0**

## Identical lines

- `out_dir.mkdir(parents=True, exist_ok=True)`
  - project: video/build_video.py:28
  - tool: cli_run.py:119

## Method

Every Python file in both code bases was compared, excluding virtual environments, caches and output folders. Whitespace was normalised. A line counted if it was at least 25 characters and not an import or boilerplate (`if __name__`, decorators, comments, closing brackets). A block is 4 consecutive normalised lines with at least 80 characters in total. This catches verbatim and lightly reformatted copying; it would not catch code that was rewritten with renamed variables.

The project uses the tool only through `study/run_tool.py`, which imports the tool's `LiteratureReviewPipeline` and `StructuredQuery` at run time and does not copy or modify the tool.
