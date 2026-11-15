"""Numeric tables: reproduction check, rewrite-vs-raw tests, interaction, subgroups, cost."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .config import VARIANTS
from .data import load_queries
from .rewrite import RewriteCache
from .stats import benjamini_hochberg, compare

REWRITES = [v for v in VARIANTS if v != "raw"]
METRICS = ("ndcg@10", "recall@20", "recall@50", "mrr")

# LitSearch Table 3 (titles + abstracts): broad → R@20, specific → R@5, in percent.
PAPER = {
    "bm25": {"inline broad R@20": 37.4, "inline specific R@5": 38.5, "author broad R@20": 48.6,
             "author specific R@5": 62.6, "avg broad R@20": 39.9, "avg specific R@5": 50.0},
    "dense": {"inline broad R@20": 55.8, "inline specific R@5": 50.4, "author broad R@20": 54.3,
              "author specific R@5": 62.6, "avg broad R@20": 55.4, "avg specific R@5": 56.2},
}


def with_groups(df: pd.DataFrame) -> pd.DataFrame:
    """Add LitSearch's two splits: inline-citation vs author-written, broad vs specific."""
    df = df.copy()
    df["set"] = np.where(df["query_set"].str.startswith("inline"), "inline", "author")
    df["spec"] = np.where(df["specificity"].astype(int) == 1, "specific", "broad")
    return df


def reproduction(pq: pd.DataFrame) -> pd.DataFrame:
    raw = with_groups(pq[pq["variant"] == "raw"])
    rows = []
    for ret in ("bm25", "dense"):
        r = raw[raw["retriever"] == ret]
        ours = {}
        for s in ("inline", "author"):
            ours[f"{s} broad R@20"] = r[(r.set == s) & (r.spec == "broad")]["recall@20"].mean()
            ours[f"{s} specific R@5"] = r[(r.set == s) & (r.spec == "specific")]["recall@5"].mean()
        ours["avg broad R@20"] = r[r.spec == "broad"]["recall@20"].mean()
        ours["avg specific R@5"] = r[r.spec == "specific"]["recall@5"].mean()
        for k, v in ours.items():
            rows.append({"retriever": ret, "measure": k, "ours": round(100 * v, 1),
                         "paper": PAPER[ret][k], "diff": round(100 * v - PAPER[ret][k], 1)})
    return pd.DataFrame(rows)


def comparisons(pq: pd.DataFrame, metrics=METRICS) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Each rewrite vs raw per retriever; BH within each metric's family of 8 tests."""
    wide = pq.pivot_table(index="qid", columns=["retriever", "variant"], values=list(metrics))
    rows = []
    for m in metrics:
        fam = []
        for ret in ("bm25", "dense"):
            for v in REWRITES:
                s = compare(wide[(m, ret, "raw")].to_numpy(), wide[(m, ret, v)].to_numpy())
                fam.append({"metric": m, "retriever": ret, "variant": v, **s})
        for row, padj in zip(fam, benjamini_hochberg([r["p"] for r in fam])):
            row["p_bh"], row["significant"] = padj, padj < 0.05
        rows += fam
        s = compare(wide[(m, "bm25", "raw")].to_numpy(), wide[(m, "dense", "raw")].to_numpy())
        rows.append({"metric": m, "retriever": "dense − bm25", "variant": "raw", **s,
                     "p_bh": s["p"], "significant": s["p"] < 0.05})
    return pd.DataFrame(rows), wide


def interaction(wide: pd.DataFrame, metric: str = "ndcg@10") -> pd.DataFrame:
    """(gain under BM25) − (gain under dense) per query; positive → BM25 gains more."""
    rows = []
    for v in REWRITES:
        gain_b = wide[(metric, "bm25", v)] - wide[(metric, "bm25", "raw")]
        gain_d = wide[(metric, "dense", v)] - wide[(metric, "dense", "raw")]
        s = compare(gain_d.to_numpy(), gain_b.to_numpy())
        rows.append({"metric": metric, "variant": v, "gain_bm25": float(gain_b.mean()),
                     "gain_dense": float(gain_d.mean()), "interaction": s["delta"],
                     "ci_lo": s["ci_lo"], "ci_hi": s["ci_hi"], "p": s["p"]})
    for row, padj in zip(rows, benjamini_hochberg([r["p"] for r in rows])):
        row["p_bh"] = padj
    return pd.DataFrame(rows)


def subgroups(pq: pd.DataFrame, metric: str = "ndcg@10") -> pd.DataFrame:
    df = with_groups(pq)
    raw = df[df.variant == "raw"].set_index(["qid", "retriever"])[metric]
    rows = []
    for v in REWRITES:
        cur = df[df.variant == v].set_index(["qid", "retriever"])
        cur = cur.assign(delta=cur[metric] - raw.reindex(cur.index)).reset_index()
        for (ret, s, sp), g in cur.groupby(["retriever", "set", "spec"]):
            rows.append({"variant": v, "retriever": ret, "query_set": s, "specificity": sp,
                         "n": len(g), "delta": g["delta"].mean()})
    return pd.DataFrame(rows)


def cost(timing: pd.DataFrame, pq: pd.DataFrame, provider: str) -> pd.DataFrame:
    """Tokens and LLM latency per variant from the cache, joined to quality and retrieval time."""
    cache = pd.DataFrame(RewriteCache().rows.values())
    cache = cache[(cache["provider"] == provider) & (cache["sample"] == 0)
                  & cache["query"].isin(load_queries()["query"])]
    cache = cache.assign(tokens=cache["prompt_tokens"] + cache["completion_tokens"])
    llm = cache.groupby("variant").agg(
        tokens_per_query=("tokens", "mean"), completion_tokens=("completion_tokens", "mean"),
        llm_latency_mean_s=("latency_s", "mean"),
        llm_latency_p95_s=("latency_s", lambda s: s.quantile(0.95)),
        model=("model", "first")).reset_index()
    raw = pd.DataFrame([{"variant": "raw", "tokens_per_query": 0, "completion_tokens": 0,
                         "llm_latency_mean_s": 0, "llm_latency_p95_s": 0, "model": "none"}])
    llm = pd.concat([raw, llm], ignore_index=True)
    means = pq.groupby(["retriever", "variant"])[["recall@50", "ndcg@10"]].mean().reset_index()
    return means.merge(llm, on="variant").merge(timing, on=["retriever", "variant"], how="left")
