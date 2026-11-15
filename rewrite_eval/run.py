"""Run every (retriever × variant) cell and score it per query.

How each variant becomes a retrieval request (identical for both retrievers unless noted):
  raw       the question as written
  rephrase  the LLM rewrite replaces the question
  expand    question + LLM term list (appended)
  hyde      BM25: question + hypothetical abstract (query2doc-style concatenation)
            dense: mean of the question vector and the abstract's passage vector (HyDE)
  multi     the question + 3 LLM queries, each retrieved separately, fused by RRF
"""
from __future__ import annotations

import time

import numpy as np
import pandas as pd

from .config import LLM_PROVIDER, RESULTS_DIR, TOP_K, VARIANTS
from .data import doc_texts, load_corpus, load_queries
from .metrics import all_metrics
from .retrieval import BM25Retriever, DenseRetriever, rrf
from .rewrite import RewriteCache, lookup, multi_queries


def build_indexes():
    corpus = load_corpus()
    ids = corpus["corpusid"].to_numpy()
    texts = doc_texts(corpus)
    t0 = time.perf_counter()
    bm25 = BM25Retriever(ids, texts)
    print(f"BM25 ready in {time.perf_counter() - t0:.0f}s")
    t0 = time.perf_counter()
    dense = DenseRetriever(ids, texts)
    print(f"dense ready in {time.perf_counter() - t0:.0f}s")
    return bm25, dense


def _requests(q: str, variant: str, provider: str, cache: RewriteCache):
    if variant == "raw":
        return {"text": q}
    out = lookup(q, variant, provider, cache=cache)["output"]
    if variant == "rephrase":
        return {"text": out or q}
    if variant == "expand":
        return {"text": f"{q} {out}"}
    if variant == "hyde":
        return {"text": f"{q} {out}", "passage": out}
    if variant == "multi":
        return {"texts": [q] + multi_queries(out)}
    raise ValueError(variant)


def run_cells(provider: str = LLM_PROVIDER, variants: list[str] = VARIANTS,
              qids: list[str] | None = None, tag: str = "main") -> pd.DataFrame:
    queries = load_queries()
    if qids is not None:
        queries = queries[queries["qid"].isin(qids)]
    bm25, dense = build_indexes()
    cache = RewriteCache()
    rows, timing = [], []
    for v in variants:
        reqs = [_requests(q, v, provider, cache) for q in queries["query"]]
        # BM25
        t0 = time.perf_counter()
        if v == "multi":
            bm = [rrf(bm25.search(r["texts"])) for r in reqs]
        else:
            bm = bm25.search([r["text"] for r in reqs])
        timing.append({"retriever": "bm25", "variant": v,
                       "retrieval_ms_per_query": 1000 * (time.perf_counter() - t0) / len(reqs)})
        # dense
        t0 = time.perf_counter()
        if v == "multi":
            de = [rrf(dense.search(r["texts"])) for r in reqs]
        elif v == "hyde":
            qv = dense.encode_queries(list(queries["query"]))
            pv = dense.encode_docs([r["passage"] for r in reqs])
            mix = qv + pv
            mix /= np.linalg.norm(mix, axis=1, keepdims=True)
            de = dense.search_vectors(mix)
        else:
            de = dense.search([r["text"] for r in reqs])
        timing.append({"retriever": "dense", "variant": v,
                       "retrieval_ms_per_query": 1000 * (time.perf_counter() - t0) / len(reqs)})
        for qid, b, d in zip(queries["qid"], bm, de):
            rows.append({"qid": qid, "retriever": "bm25", "variant": v, "ranking": b[:TOP_K]})
            rows.append({"qid": qid, "retriever": "dense", "variant": v, "ranking": d[:TOP_K]})
        print(f"  {v}: done")
    runs = pd.DataFrame(rows)
    runs["provider"] = provider
    runs.to_parquet(RESULTS_DIR / f"runs_{tag}.parquet", index=False)
    pd.DataFrame(timing).to_csv(RESULTS_DIR / f"retrieval_timing_{tag}.csv", index=False)
    per_query = score(runs, queries)
    per_query.to_csv(RESULTS_DIR / f"per_query_{tag}.csv", index=False)
    return per_query


def score(runs: pd.DataFrame, queries: pd.DataFrame) -> pd.DataFrame:
    meta = queries.set_index("qid")
    out = []
    for r in runs.itertuples():
        gold = set(meta.at[r.qid, "corpusids"])
        out.append({"qid": r.qid, "retriever": r.retriever, "variant": r.variant,
                    **all_metrics(list(r.ranking), gold)})
    df = pd.DataFrame(out)
    cols = [c for c in ("specificity", "quality", "query_set") if c in meta.columns]
    return df.merge(meta[cols].reset_index(), on="qid", how="left")
