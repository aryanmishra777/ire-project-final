# config.py

## What it does
Holds every path, model name and experiment constant in one place, and loads `.env`.

## Responsibility
Owns *settings only*: where data and results live, which dense model and LLM to use, which variants
and retrievers make up the grid, and the statistics constants. It contains no logic, so changing
the experiment means editing this one file.

## How
- Resolves the project root from its own location, then creates `data/`, `results/` and
  `results/figures/` if they are missing.
- Calls `load_dotenv` on the project's `.env`, so `GROQ_API_KEY` and the overrides
  (`LLM_PROVIDER`, `GROQ_MODEL`, `OLLAMA_MODEL`, `DENSE_MODEL`) are in the environment before
  anything else imports them.
- Exposes constants: `DENSE_MODEL` and its `query: ` / `passage: ` prefixes, `TOP_K = 100`,
  `VARIANTS`, `RETRIEVERS`, `RRF_K = 60`, `N_BOOT`, `N_PERM`, `ALPHA` and the seeds.

## Why
- **E5-large-v2 as the dense model.** LitSearch reports it as a baseline (Table 3). That lets the
  harness check its dense numbers against a published figure, which a compact model like
  bge-small would not allow.
- **Local Qwen 3.6 MoE (35B total, about 3B active) through Ollama as the rewriter**, set with
  `LLM_PROVIDER=ollama` in `.env`. It needs no API key and runs fully offline, so every rewrite
  can be regenerated on the same laptop. It's also the kind of model a small academic group could
  self-host. Groq stays available as a hosted alternative (`--provider groq`).
- **`OLLAMA_NUM_CTX = 24576` (24K).** It's the same window the author's other local tools,
  including the literature-review tool, load the model with. Ollama reloads the ~18 GB model whenever the
  window changes, so one shared value avoids reloads when switching tools.
- **`TOP_K = 100`.** Recall@100 is the deepest metric, so nothing deeper is needed.
- **RRF constant 60.** This is the value Cormack et al. recommend, and it's what most RRF uses in
  the literature.
- **Settings via environment overrides.** Reviewers can swap models without touching the code.
