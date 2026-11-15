"""Read the results files and turn them into the numbers and sentences the slides use.

Nothing on a slide is typed by hand: every figure comes from results/ (the LitSearch run) or
study/illustrative/ (the simulated study), and every verdict follows a fixed rule below.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from rewrite_eval.stats import compare

ROOT = Path(__file__).resolve().parent.parent
RES = ROOT / "results"
STUDY = ROOT / "study" / "data"  # the real pilot (study/illustrative/ is the simulated demo)
DRY_RUN = "P01"
VN = {"rephrase": "rephrasing", "expand": "term expansion", "hyde": "HyDE",
      "multi": "multi-query fusion"}
RN = {"bm25": "BM25", "dense": "dense retrieval"}


def _sig(row) -> str:
    return "significant" if row["p_bh"] < 0.05 else "not significant"


def load() -> dict:
    comp = pd.read_csv(RES / "comparisons.csv")
    inter = pd.read_csv(RES / "interaction.csv")
    cost = pd.read_csv(RES / "cost.csv")
    rep = pd.read_csv(RES / "reproduction.csv")
    terms = pd.read_csv(RES / "failure_terms.csv")
    pq = pd.read_csv(RES / "per_query_main.csv")
    f = {"comp": comp, "inter": inter, "cost": cost, "rep": rep, "terms": terms,
         "n_queries": pq["qid"].nunique()}
    nd = comp[(comp.metric == "ndcg@10") & comp.retriever.isin(["bm25", "dense"])]
    f["nd"] = nd
    r50 = comp[(comp.metric == "recall@50") & comp.retriever.isin(["bm25", "dense"])]
    for ret in ("bm25", "dense"):
        sub = nd[nd.retriever == ret].sort_values("delta", ascending=False)
        best = sub.iloc[0]
        f[f"best_{ret}"] = best
        f[f"n_sig_up_{ret}"] = int(((sub.p_bh < 0.05) & (sub.delta > 0)).sum())
        f[f"n_sig_down_{ret}"] = int(((sub.p_bh < 0.05) & (sub.delta < 0)).sum())
        rs = r50[r50.retriever == ret]
        f[f"r50_up_{ret}"] = int(((rs.p_bh < 0.05) & (rs.delta > 0)).sum())
        f[f"r50_range_{ret}"] = (rs.delta.min(), rs.delta.max())
    supported = int(((inter.p_bh < 0.05) & (inter.interaction > 0)).sum())
    f["verdict"] = ("supported" if supported >= 3 else "partly supported" if supported >= 1
                    else "not supported")
    f["n_inter_sig"] = supported
    gap = comp[(comp.metric == "ndcg@10") & (comp.retriever == "dense − bm25")].iloc[0]
    f["raw_gap"] = gap
    f["rep_max_abs_diff"] = float(rep["diff"].abs().max())
    avg = rep[rep.measure.str.startswith("avg")]
    for ret in ("bm25", "dense"):  # judged on the paper's two averaged measures
        f[f"rep_avg_{ret}"] = avg[avg.retriever == ret]["diff"].tolist()
    kept = terms[(terms.n_rare > 0) & ~terms.lost_any]
    lost = terms[(terms.n_rare > 0) & terms.lost_any]
    f["lost_n"], f["kept_n"] = len(lost), len(kept)
    f["lost_delta_bm25"], f["kept_delta_bm25"] = lost.delta_bm25.mean(), kept.delta_bm25.mean()
    f["lost_delta_dense"], f["kept_delta_dense"] = lost.delta_dense.mean(), kept.delta_dense.mean()
    # The predicted failure "shows" only if losing a rare term costs ≥ 0.02 nDCG@10 under BM25.
    f["failure_shows"] = f["lost_delta_bm25"] <= f["kept_delta_bm25"] - 0.02
    f["example"] = terms.sort_values("delta_bm25").iloc[0]  # the single worst BM25 loss
    big = terms[terms.delta_bm25 <= -0.5]
    f["n_big_loss"], f["n_big_loss_lost"] = len(big), int(big.lost_any.sum())
    f["study"] = study_facts()
    f["example_q"] = example_rewrite()
    return f


def example_rewrite(qid: str = "q000") -> tuple[str, str]:
    """A real benchmark question and the rephrase Qwen produced for it, for the motivation slide."""
    from rewrite_eval.config import LLM_PROVIDER
    from rewrite_eval.data import load_queries
    from rewrite_eval.rewrite import lookup
    q = load_queries().set_index("qid").at[qid, "query"]
    return q, lookup(q, "rephrase", LLM_PROVIDER)["output"]


def study_facts() -> dict:
    """Real pilot: P01 is the researcher's own dry-run question, so it is left out of the main
    numbers (and reported separately), exactly as study/analyze_study.py --exclude P01 does."""
    every = pd.read_csv(STUDY / "results" / "study_per_question.csv")
    df = every[every.pid != DRY_RUN]
    s = compare(df.ndcg10_off.to_numpy(), df.ndcg10_on.to_numpy())
    f = df.dropna(subset=["fidelity"])
    rho = f["fidelity"].corr(f["delta_ndcg10"], method="spearman") if len(f) >= 3 else None
    return {"n": len(df), "nd": s, "rho": rho, "n_fid": len(f),
            "fid": f.fidelity.mean() if len(f) else None,
            "all": compare(every.ndcg10_off.to_numpy(), every.ndcg10_on.to_numpy()),
            "worse": df[df.delta_ndcg10 < 0].pid.tolist()}


def headline(f: dict) -> list[str]:
    """Three plain-language findings, each a fixed rule over the result tables."""
    out = []
    for ret in ("bm25", "dense"):
        b = f[f"best_{ret}"]
        up, down = f[f"n_sig_up_{ret}"], f[f"n_sig_down_{ret}"]
        name = {"bm25": "BM25", "dense": "Dense retrieval"}[ret]
        out.append(f"{name}: {up} of 4 rewrites help significantly, {down} hurt; "
                   f"best is {VN[b.variant]} ({b.delta:+.3f} nDCG@10, {_sig(b)}).")
    out.append(f"The hypothesis (rewriting helps BM25 more than dense) is {f['verdict']}: "
               f"{f['n_inter_sig']} of 4 variants show a significant BM25-larger gain.")
    b, d = f["r50_range_bm25"], f["r50_range_dense"]
    out.append(f"Recall@50 rises more consistently: {f['r50_up_bm25']} of 4 rewrites for BM25 "
               f"({b[0]:+.3f} to {b[1]:+.3f}) and {f['r50_up_dense']} of 4 for dense "
               f"({d[0]:+.3f} to {d[1]:+.3f}) improve it significantly.")
    return out


_COUNT = {0: "none", 1: "one", 2: "two", 3: "three", 4: "all four"}


def spoken(f: dict) -> dict:
    """The same findings as headline(), phrased to be read aloud: no symbols or brackets."""
    out = {}
    for ret, name in (("bm25", "BM25"), ("dense", "dense retrieval")):
        b, up = f[f"best_{ret}"], f[f"n_sig_up_{ret}"]
        out[ret] = (f"With {name}, {_COUNT[up]} of the four rewrites "
                    f"help{'s' if up == 1 else ''} significantly and "
                    f"{_COUNT[f[f'n_sig_down_{ret}']]} hurt. The best is {VN[b.variant]}, which "
                    f"adds {b.delta:.3f} to nDCG at ten.")
    out["hypothesis"] = (f"the hypothesis is {f['verdict']}: for {_COUNT[f['n_inter_sig']]} "
                         "of the four rewrites, BM25 gains significantly more than dense "
                         "retrieval.")
    rb, rd = f["r50_range_bm25"], f["r50_range_dense"]
    out["recall"] = (f"Recall at fifty tells a clearer story. {_COUNT[f['r50_up_bm25']].capitalize()}"
                     f" of the rewrites improve it significantly for BM25, by up to {rb[1]:.3f}, "
                     f"and {_COUNT[f['r50_up_dense']]} for dense retrieval, by up to {rd[1]:.3f}.")
    n_r50 = f["r50_up_bm25"] + f["r50_up_dense"]
    out["recall_short"] = ("Recall at fifty rose significantly in "
                           + ("all eight rewrite settings." if n_r50 == 8
                              else f"{n_r50} of the eight rewrite settings."))
    same = f["best_bm25"].variant == f["best_dense"].variant
    best = VN[f["best_bm25"].variant]
    out["best"] = (f"{best[0].upper()}{best[1:]} was the best rewrite for both retrievers."
                   if same else "")
    return out


def fmt_ci(row) -> str:
    return f"{row['delta']:+.3f} [{row['ci_lo']:+.3f}, {row['ci_hi']:+.3f}]"
