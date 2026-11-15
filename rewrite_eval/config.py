"""Paths, model choices and experiment constants. One place to change the grid."""
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
RESULTS_DIR = ROOT / "results"
FIG_DIR = RESULTS_DIR / "figures"
for _d in (DATA_DIR, RESULTS_DIR, FIG_DIR):
    _d.mkdir(parents=True, exist_ok=True)

load_dotenv(ROOT / ".env")

# ── Benchmark ─────────────────────────────────────────────────────────────── #
DATASET = "princeton-nlp/LitSearch"

# ── Retrievers ────────────────────────────────────────────────────────────── #
# E5-large-v2 is one of the dense baselines LitSearch reports (Table 3), so the harness can
# check its numbers against the paper. E5 expects "query: " / "passage: " prefixes.
DENSE_MODEL = os.environ.get("DENSE_MODEL", "intfloat/e5-large-v2")
DENSE_QUERY_PREFIX = "query: "
DENSE_DOC_PREFIX = "passage: "
DENSE_BATCH = int(os.environ.get("DENSE_BATCH", "32"))
TOP_K = 100  # depth of every run; recall@100 is the deepest metric

# ── Rewriting LLM ─────────────────────────────────────────────────────────── #
# provider "groq" (hosted, default) or "ollama" (local cross-check).
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "groq")
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.1-8b-instant")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen3.6-moe")
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
# 24K matches the window the author's other local tools (including the literature-review tool)
# load the model with, so switching between them never forces Ollama to reload the ~18 GB model.
OLLAMA_NUM_CTX = int(os.environ.get("OLLAMA_NUM_CTX", "24576"))
LLM_TEMPERATURE = 0.0
LLM_SEED = 13

REWRITE_CACHE = DATA_DIR / "rewrite_cache.jsonl"

# ── Grid ──────────────────────────────────────────────────────────────────── #
VARIANTS = ["raw", "rephrase", "expand", "hyde", "multi"]
RETRIEVERS = ["bm25", "dense"]
RRF_K = 60  # reciprocal rank fusion constant (Cormack et al.)

# ── Statistics ────────────────────────────────────────────────────────────── #
N_BOOT = 10_000
N_PERM = 10_000
ALPHA = 0.05
STATS_SEED = 2026
