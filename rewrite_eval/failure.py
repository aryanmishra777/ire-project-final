"""Failure analysis: does the rephrase rewrite drop rare, discriminating query terms, and
does losing them cost retrieval quality?"""
from __future__ import annotations

import re

import pandas as pd

from .data import load_corpus, load_queries
from .rewrite import RewriteCache, lookup

# Split on hyphens and punctuation like BM25's tokenizer does, so "health-related" counts as
# "health" + "related" and a rewrite that keeps both words is not scored as losing a term.
_TOKEN = re.compile(r"[a-z0-9]{2,}")


def _stems(text: str, stemmer, stop: set) -> set:
    return {stemmer.stemWord(t) for t in _TOKEN.findall(text.lower()) if t not in stop}


def document_frequencies(stemmer, stop: set) -> dict[str, int]:
    corpus = load_corpus()
    df_count: dict[str, int] = {}
    for t, a in zip(corpus["title"], corpus["abstract"]):
        for s in _stems(f"{t} {a}", stemmer, stop):
            df_count[s] = df_count.get(s, 0) + 1
    return df_count


def failure_terms(pq: pd.DataFrame, provider: str, rare_df: int = 100):
    """A query term is rare if fewer than `rare_df` of the 64k abstracts contain it.

    Returns per-query rows (rare terms, lost terms, Δ nDCG@10 per retriever) and a summary of
    mean Δ for queries that lost at least one rare term vs those that kept all of them.
    """
    import Stemmer
    from bm25s.stopwords import STOPWORDS_EN

    stemmer, stop = Stemmer.Stemmer("english"), set(STOPWORDS_EN)
    df_count = document_frequencies(stemmer, stop)
    cache, queries, rows = RewriteCache(), load_queries(), []
    for qid, q in zip(queries["qid"], queries["query"]):
        try:
            rw = lookup(q, "rephrase", provider, cache=cache)["output"]
        except KeyError:
            continue
        rare = {s for s in _stems(q, stemmer, stop) if 0 < df_count.get(s, 0) < rare_df}
        lost = rare - _stems(rw, stemmer, stop)
        rows.append({"qid": qid, "query": q, "rewrite": rw, "n_rare": len(rare),
                     "n_lost": len(lost), "lost_terms": " ".join(sorted(lost))})
    terms = pd.DataFrame(rows)
    wide = pq.pivot_table(index="qid", columns=["retriever", "variant"], values="ndcg@10")
    for ret in ("bm25", "dense"):
        terms[f"delta_{ret}"] = terms["qid"].map(wide[(ret, "rephrase")] - wide[(ret, "raw")])
    terms["lost_any"] = terms["n_lost"] > 0
    summary = (terms[terms.n_rare > 0].groupby("lost_any")[["delta_bm25", "delta_dense"]]
               .agg(["mean", "count"]))
    return terms, summary


def write_examples(terms: pd.DataFrame, path, n: int = 6) -> None:
    worst = terms.sort_values("delta_bm25").head(n)
    with open(path, "w", encoding="utf-8") as f:
        f.write("# Largest BM25 nDCG@10 losses under the rephrase rewrite\n\n")
        for r in worst.itertuples():
            f.write(f"- **{r.qid}** (Δ BM25 {r.delta_bm25:+.3f}, Δ dense {r.delta_dense:+.3f})\n"
                    f"  - question: {r.query}\n  - rewrite: {r.rewrite}\n"
                    f"  - rare terms lost: {r.lost_terms or 'none'}\n")
