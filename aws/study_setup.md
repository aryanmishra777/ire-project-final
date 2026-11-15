# study_setup.sh

## What it does
One-time setup of the AWS study-runner instance, so it can run the literature-review tool for
human-study participants. It installs:
- Ollama, with the same Qwen model the laptop uses;
- Python 3.14, the tool's version;
- the tool's full dependencies, including the private venue module's `curl_cffi`;
- the tool's Camoufox browser.

## Responsibility
Owns the environment only. It doesn't run any participant (that's `study_batch.sh`), and it
doesn't launch, stop or terminate the instance. Those cost-bearing steps are run from the laptop.

## How
1. **Ollama** with `OLLAMA_NUM_PARALLEL=3`, so three workers' LLM calls are served at once, and
   `OLLAMA_LOAD_TIMEOUT=15m`, so loading the 18 GB model from a cold disk after a restart doesn't
   time out.
2. **Model:** pulls `hf.co/unsloth/Qwen3.6-35B-A3B-GGUF:UD-IQ4_XS` and recreates the
   `qwen3.6-moe` alias with a 24K context and Qwen's stop tokens, the same file and settings as
   the laptop.
3. **Python:** uv creates `~/tool/venv` with Python 3.14 and installs
   `requirements-private.txt`, which includes the base requirements.
4. **Browser:** `camoufox fetch` downloads the browser, and `playwright install-deps firefox`
   adds the Linux libraries it needs. Both are allowed to fail without stopping setup, because
   the tool falls back to plain HTTP fetching when the browser is unavailable.
5. **Progress:** each finished stage is appended to `~/STAGE`, and the logs go to `~/logs/`.

## Why
- **Python 3.14 exactly.** It's the version the tool runs on locally. A different version could
  resolve different dependency versions and change the tool's behaviour between the laptop and
  the server.
- **Three Ollama slots.** Three workers run at once, so three LLM calls can arrive together. One
  18 GB model plus three 24K contexts still fits in the L4's 23 GB, where four could run out of
  memory.
- **One shared venv.** The heavy packages (torch, LangGraph, the browser) are installed once.
  Only the tool's small code and cache files are copied per worker.
