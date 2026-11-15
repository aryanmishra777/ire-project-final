# __main__.py

## What it does
The command-line entry point: `python -m rewrite_eval <step>`. The steps are `prepare`,
`rewrite`, `retrieve`, `analyze` and `all`.

## Responsibility
Owns argument parsing and the order of steps. It delegates every step to its module, which is
imported only when needed, so `analyze` doesn't load torch.

## How
- Flags:
  - `--provider groq|ollama` chooses the rewriting LLM;
  - `--workers` sets the number of concurrent LLM calls;
  - `--limit N` restricts the run to the first N queries;
  - `--tag` names the result files.
- The default tag is `main` for the full Groq run. Anything else gets a tag like `ollama_100`,
  so cross-checks never overwrite the main results.
- `rewrite` fills the cache for all non-raw variants. `retrieve` runs the cells, and `analyze`
  builds the outputs.

## Why
- **Separate steps.** Each has a different cost profile (download, paid API calls, CPU-heavy
  embedding, quick analysis), so they can be rerun independently. The released cache means a
  reproducer can skip `rewrite` entirely.
- **Tags derived from provider and limit.** Running the local cross-check can't silently
  overwrite the main run's files.
