"""The four LLM rewriting variants, the LLM client, and the rewrite cache.

Every call is cached in data/rewrite_cache.jsonl keyed by (variant, provider, model, sample,
query), with its output, token counts, latency and date. Re-running never pays for a call
twice, and anyone can reproduce the retrieval numbers from the released cache with no LLM.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from tqdm import tqdm

from .config import (GROQ_MODEL, LLM_PROVIDER, LLM_SEED, LLM_TEMPERATURE, OLLAMA_HOST,
                     OLLAMA_MODEL, OLLAMA_NUM_CTX, REWRITE_CACHE)

SYSTEM = "You rewrite literature-search questions for an academic paper search engine."

PROMPTS = {
    # (i) light normalisation to academic phrasing; replaces the question
    "rephrase": (
        "Rewrite this literature-search question as a short search query (under 25 words) in "
        "the standard terminology of the field. Keep every specific technical term, method, "
        "dataset or task name. Output only the query.\n\nQuestion: {q}"),
    # (ii) keyword/term expansion; appended to the question
    "expand": (
        "List 8 to 12 technical terms, synonyms and closely related concepts that a relevant "
        "paper's title or abstract would likely contain. Output only a comma-separated list."
        "\n\nQuestion: {q}"),
    # (iii) HyDE-style hypothetical abstract
    "hyde": (
        "Write the title and abstract (about 120 words) of a research paper that would answer "
        "this question. Output only the title and abstract.\n\nQuestion: {q}"),
    # (iv) multi-query generation, fused with the original by RRF
    "multi": (
        "Write 3 different search queries that together cover this question, each from a "
        "different angle. Output exactly 3 lines, one query per line, no numbering."
        "\n\nQuestion: {q}"),
}
MAX_TOKENS = {"rephrase": 60, "expand": 100, "hyde": 260, "multi": 120}


def _model_name(provider: str) -> str:
    return GROQ_MODEL if provider == "groq" else OLLAMA_MODEL


def cache_key(variant: str, provider: str, model: str, sample: int, query: str) -> str:
    raw = "\x1f".join([variant, provider, model, str(sample), query])
    return hashlib.sha1(raw.encode()).hexdigest()


def _clean(text: str) -> str:
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.S).strip()
    return text.strip().strip('"').strip()


class LLM:
    def __init__(self, provider: str = LLM_PROVIDER):
        self.provider = provider
        self.model = _model_name(provider)
        if provider == "groq":
            from groq import Groq
            self._client = Groq(max_retries=0)
        else:
            import ollama
            self._client = ollama.Client(host=OLLAMA_HOST)

    def chat(self, prompt: str, max_tokens: int, temperature: float = LLM_TEMPERATURE) -> dict:
        messages = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}]
        for attempt in range(8):
            t0 = time.perf_counter()
            try:
                if self.provider == "groq":
                    r = self._client.chat.completions.create(
                        model=self.model, messages=messages, temperature=temperature,
                        seed=LLM_SEED, max_tokens=max_tokens)
                    out, pt, ct = (r.choices[0].message.content or "",
                                   r.usage.prompt_tokens, r.usage.completion_tokens)
                else:
                    r = self._client.chat(
                        model=self.model, messages=messages, think=False,
                        options={"temperature": temperature, "seed": LLM_SEED,
                                 "num_predict": max_tokens, "num_ctx": OLLAMA_NUM_CTX})
                    out, pt, ct = r.message.content or "", r.prompt_eval_count, r.eval_count
                return {"output": _clean(out), "prompt_tokens": pt, "completion_tokens": ct,
                        "latency_s": round(time.perf_counter() - t0, 3)}
            except Exception as exc:  # rate limits and transient network errors
                wait = _retry_after(exc) or min(60, 4 * 2 ** attempt)
                time.sleep(wait)
        raise RuntimeError("LLM call failed after 8 attempts")


def _retry_after(exc: Exception) -> float | None:
    resp = getattr(exc, "response", None)
    headers = getattr(resp, "headers", None) or {}
    val = headers.get("retry-after")
    try:
        return float(val) + 0.5 if val else None
    except ValueError:
        return None


class RewriteCache:
    def __init__(self, path=REWRITE_CACHE):
        self.path = path
        self._lock = threading.Lock()
        self.rows: dict[str, dict] = {}
        if path.exists():
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    row = json.loads(line)
                    self.rows[row["key"]] = row

    def get(self, key: str) -> dict | None:
        return self.rows.get(key)

    def put(self, row: dict) -> None:
        with self._lock:
            self.rows[row["key"]] = row
            with self.path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")


def generate(queries: list[tuple[str, str]], variants: list[str], provider: str = LLM_PROVIDER,
             sample: int = 0, workers: int = 4, temperature: float = LLM_TEMPERATURE) -> None:
    """Fill the cache for every (qid, query) × variant. Already-cached calls are skipped."""
    llm, cache = LLM(provider), RewriteCache()
    todo = []
    for qid, q in queries:
        for v in variants:
            key = cache_key(v, provider, llm.model, sample, q)
            if cache.get(key) is None:
                todo.append((key, qid, q, v))

    def work(item):
        key, qid, q, v = item
        res = llm.chat(PROMPTS[v].format(q=q), MAX_TOKENS[v], temperature)
        cache.put({"key": key, "qid": qid, "variant": v, "provider": provider,
                   "model": llm.model, "sample": sample, "temperature": temperature,
                   "query": q, "date": dt.date.today().isoformat(), **res})

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futs = [pool.submit(work, t) for t in todo]
        for f in tqdm(as_completed(futs), total=len(futs), desc=f"rewrites ({provider})"):
            f.result()


def lookup(query: str, variant: str, provider: str = LLM_PROVIDER, sample: int = 0,
           cache: RewriteCache | None = None) -> dict:
    cache = cache or RewriteCache()
    row = cache.get(cache_key(variant, provider, _model_name(provider), sample, query))
    if row is None:
        raise KeyError(f"no cached {variant} rewrite for: {query[:60]}")
    return row


def multi_queries(output: str) -> list[str]:
    lines = [re.sub(r"^\s*(\d+[.)]|[-*•])\s*", "", ln).strip() for ln in output.splitlines()]
    return [ln for ln in lines if ln][:3]
