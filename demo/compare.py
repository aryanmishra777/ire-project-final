"""Live demo: type a research question, see what the raw question and an LLM rewrite retrieve
from LitSearch's 64k papers, under BM25 and under dense retrieval, side by side.

  python -m demo.compare "your question" [--variant expand] [--k 5]
  python -m demo.compare --qid q042            # a LitSearch question; gold papers are marked

Uses the cached BM25 index and E5 embeddings (python -m rewrite_eval prepare) and the local
Ollama rewriter. For a LitSearch question the cached rewrite is used, so no LLM call is needed.
"""
from __future__ import annotations

import argparse
import textwrap

import numpy as np

from rewrite_eval.config import LLM_PROVIDER
from rewrite_eval.data import load_corpus, load_queries
from rewrite_eval.retrieval import BM25Retriever, DenseRetriever, rrf
from rewrite_eval.rewrite import LLM, MAX_TOKENS, PROMPTS, RewriteCache, lookup, multi_queries


def rewrite(question: str, variant: str) -> str:
    try:
        return lookup(question, variant, LLM_PROVIDER, cache=RewriteCache())["output"]
    except KeyError:
        print(f"(asking {LLM_PROVIDER} for a {variant} rewrite…)")
        return LLM().chat(PROMPTS[variant].format(q=question), MAX_TOKENS[variant])["output"]


def search(question: str, variant: str, out: str, bm25, dense, k: int):
    """Same request construction as rewrite_eval.run, for one question."""
    if variant == "raw":
        return bm25.search([question], k)[0], dense.search([question], k)[0]
    if variant == "rephrase":
        return bm25.search([out], k)[0], dense.search([out], k)[0]
    if variant == "expand":
        q = f"{question} {out}"
        return bm25.search([q], k)[0], dense.search([q], k)[0]
    if variant == "hyde":
        mix = dense.encode_queries([question]) + dense.encode_docs([out])
        mix /= np.linalg.norm(mix, axis=1, keepdims=True)
        return bm25.search([f"{question} {out}"], k)[0], dense.search_vectors(mix, k)[0]
    qs = [question] + multi_queries(out)
    return rrf(bm25.search(qs, k), k), rrf(dense.search(qs, k), k)


def show(label: str, ids: list[int], titles: dict, gold: set) -> None:
    print(f"\n  {label}")
    for r, d in enumerate(ids, start=1):
        mark = "★" if d in gold else " "
        print(f"   {mark} {r}. {textwrap.shorten(titles.get(d, '?'), 92)}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("question", nargs="?")
    ap.add_argument("--qid", help="use a LitSearch question, e.g. q042")
    ap.add_argument("--variant", default="expand", choices=["rephrase", "expand", "hyde", "multi"])
    ap.add_argument("--k", type=int, default=5)
    a = ap.parse_args()
    gold: set = set()
    question = a.question
    if a.qid:
        row = load_queries().set_index("qid").loc[a.qid]
        question, gold = row["query"], set(int(x) for x in row["corpusids"])
    if not question:
        ap.error("give a question or --qid")
    corpus = load_corpus()
    ids = corpus["corpusid"].to_numpy()
    titles = dict(zip(corpus["corpusid"], corpus["title"]))
    bm25, dense = BM25Retriever(ids), DenseRetriever(ids)
    out = rewrite(question, a.variant)
    print(f"\nQuestion: {question}\n{a.variant} rewrite: {textwrap.shorten(out, 300)}")
    if gold:
        print("★ = a gold paper for this LitSearch question")
    raw_b, raw_d = search(question, "raw", out, bm25, dense, a.k)
    rw_b, rw_d = search(question, a.variant, out, bm25, dense, a.k)
    show("BM25 · raw question", raw_b, titles, gold)
    show(f"BM25 · {a.variant}", rw_b, titles, gold)
    show("Dense · raw question", raw_d, titles, gold)
    show(f"Dense · {a.variant}", rw_d, titles, gold)


if __name__ == "__main__":
    main()
