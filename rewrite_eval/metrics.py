"""Per-query retrieval metrics with binary relevance (LitSearch's gold paper ids).

Graded variants (for the human study's 0/1/2 labels) take a {doc: grade} dict instead.
"""
from __future__ import annotations

import math


def recall_at(ranked: list, gold: set, k: int) -> float:
    return len(set(ranked[:k]) & gold) / len(gold) if gold else 0.0


def precision_at(ranked: list, rel: dict, k: int) -> float:
    return sum(1 for d in ranked[:k] if rel.get(d, 0) > 0) / k


def mrr(ranked: list, gold: set, k: int = 100) -> float:
    for r, d in enumerate(ranked[:k], start=1):
        if d in gold:
            return 1.0 / r
    return 0.0


def ndcg_at(ranked: list, rel: dict, k: int = 10) -> float:
    """nDCG@k with gain = grade (binary gold → 1). Ideal ranking from all judged grades."""
    dcg = sum(rel.get(d, 0) / math.log2(r + 1) for r, d in enumerate(ranked[:k], start=1))
    ideal = sorted((g for g in rel.values() if g > 0), reverse=True)[:k]
    idcg = sum(g / math.log2(r + 1) for r, g in enumerate(ideal, start=1))
    return dcg / idcg if idcg else 0.0


METRICS = ["ndcg@10", "recall@5", "recall@20", "recall@50", "recall@100", "mrr"]


def all_metrics(ranked: list, gold: set) -> dict:
    rel = {d: 1 for d in gold}
    return {
        "ndcg@10": ndcg_at(ranked, rel, 10),
        "recall@5": recall_at(ranked, gold, 5),
        "recall@20": recall_at(ranked, gold, 20),
        "recall@50": recall_at(ranked, gold, 50),
        "recall@100": recall_at(ranked, gold, 100),
        "mrr": mrr(ranked, gold, 100),
    }
