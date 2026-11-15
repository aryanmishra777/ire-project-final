# rewrite.py

## What it does
Defines the four LLM rewriting prompts, calls the LLM (Groq or local Ollama), and stores every
call in a cache file.

## Responsibility
Owns everything that touches an LLM: the prompts, the token and latency accounting, retries
and rate limits, and the cache. Retrieval code only reads finished rewrites through `lookup()`.

## How
- **`PROMPTS`** holds one template per variant, each with a token cap in `MAX_TOKENS`:
  - `rephrase`: a short query in field terminology, keeping specific terms;
  - `expand`: 8–12 related terms;
  - `hyde`: a hypothetical title and abstract of about 120 words;
  - `multi`: 3 queries from different angles.
- **`LLM.chat()`** sends one system message and one user message with temperature 0 and a fixed
  seed, and records prompt tokens, completion tokens and wall-clock latency.
  - On an error (rate limit or network) it waits for the server's `retry-after` header, or
    backs off exponentially, for up to 8 attempts.
  - For Ollama it passes `think=False`, so Qwen's reasoning traces don't count as rewrite tokens.
- **`RewriteCache`** is an append-only JSONL file with one row per call. The key is a SHA-1 of
  variant, provider, model, sample and query. Each row stores the output, tokens, latency and
  date.
- **`generate()`** fills the cache for every query × variant not already in it, using a thread
  pool.
- **`lookup()`** reads a single rewrite back, and `multi_queries()` parses the 3-line output.

## Why
- **Cache keyed on the full call identity.** No call is ever paid for twice. Releasing
  `rewrite_cache.jsonl` lets anyone reproduce every retrieval number without an API key, even
  after the hosted model is retired. This was the proposal's main reproducibility fix.
- **Temperature 0 with a seed.** It cuts LLM randomness as far as the provider allows. The
  `sample` field in the key leaves room to measure the remaining nondeterminism.
- **Short, generic prompts that don't name the corpus.** A deployed scholarly search tool
  wouldn't tell the LLM which papers it indexes, so the prompts don't either. Short prompts also
  keep the token cost honest and inside Groq's free-tier daily limit.
- **Append-only JSONL.** A crash mid-run loses at most one call, and it's thread-safe with a
  single lock.
