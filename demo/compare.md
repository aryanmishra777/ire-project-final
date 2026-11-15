# compare.py

## What it does
A live command-line demo. Give it any research question, or a LitSearch question id, and it shows
the top papers retrieved from LitSearch's 64k-paper corpus in four lists:
- the raw question under BM25;
- the LLM rewrite under BM25;
- the raw question under dense retrieval;
- the LLM rewrite under dense retrieval.

For a LitSearch question, the gold papers are marked ★.

## Responsibility
Owns the interactive single-question view of the experiment. It does no evaluation, and it
reuses the harness's retrievers, prompts, rewrite cache and request rules, so what the demo shows
is exactly what the experiment measured.

## How
1. Loads the corpus and the cached BM25 index and E5 embeddings.
2. Gets the rewrite: from the cache if this exact question was already rewritten (every LitSearch
   question was), otherwise with one call to the configured LLM (local Ollama by default).
3. `search()` builds each request with the same rules as `rewrite_eval/run.py`: rephrase
   replaces the question, expand appends terms, HyDE mixes in the abstract (vector average for
   dense), and multi-query fuses with RRF.
4. Prints the four ranked lists, marking gold papers when `--qid` is used.

Examples:
```bash
.venv/Scripts/python -m demo.compare --qid q042 --variant rephrase
.venv/Scripts/python -m demo.compare "papers that compress BERT with knowledge distillation" --variant hyde
```

## Why
- **The command line instead of a web app.** It needs no extra dependencies, starts in seconds
  once the indexes are cached, and is easy to run live during a viva.
- **A `--qid` mode with gold marks.** It turns the aggregate numbers into a concrete example: you
  can watch a rewrite push a gold paper up, or knock it out of the top 5.
- **Shared request rules.** If the demo built requests differently from the experiment, it could
  show behaviour the results don't describe.
