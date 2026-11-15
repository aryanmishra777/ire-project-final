"""Turn per-query scores into every table, figure and the results summary.

Outputs land in results/ (figures in results/figures/). Cross-check runs (tag != "main")
only get the core tables, since the reproduction, cost and failure views describe the
main run.
"""
from __future__ import annotations

import pandas as pd

from . import figures, tables
from .config import RESULTS_DIR
from .failure import failure_terms, write_examples


def analyze(tag: str = "main") -> None:
    pq = pd.read_csv(RESULTS_DIR / f"per_query_{tag}.csv")
    provider = pd.read_parquet(RESULTS_DIR / f"runs_{tag}.parquet",
                               columns=["provider"])["provider"].iloc[0]
    sfx = "" if tag == "main" else f"_{tag}"

    main = pq.groupby(["retriever", "variant"]).mean(numeric_only=True).reset_index()
    main.to_csv(RESULTS_DIR / f"main_table{sfx}.csv", index=False)
    comp, wide = tables.comparisons(pq)
    comp.to_csv(RESULTS_DIR / f"comparisons{sfx}.csv", index=False)
    inter = tables.interaction(wide)
    inter.to_csv(RESULTS_DIR / f"interaction{sfx}.csv", index=False)
    if tag != "main":
        print(comp[comp.metric == "ndcg@10"].round(4).to_string())
        return

    rep = tables.reproduction(pq)
    rep.to_csv(RESULTS_DIR / "reproduction.csv", index=False)
    tables.subgroups(pq).to_csv(RESULTS_DIR / "subgroups.csv", index=False)
    timing = pd.read_csv(RESULTS_DIR / f"retrieval_timing_{tag}.csv")
    cst = tables.cost(timing, pq, provider)
    cst.to_csv(RESULTS_DIR / "cost.csv", index=False)
    terms, term_summary = failure_terms(pq, provider)
    terms.to_csv(RESULTS_DIR / "failure_terms.csv", index=False)
    write_examples(terms, RESULTS_DIR / "failure_examples.md")

    figures.effects(comp, "ndcg@10", "effects_ndcg10.png", "Δ nDCG@10 vs raw question")
    figures.effects(comp, "recall@50", "effects_recall50.png", "Δ recall@50 vs raw question")
    figures.interaction(pq)
    figures.pareto(cst)
    figures.win_loss(comp)

    sections = [("Reproduction", rep.to_markdown(index=False)),
                ("Cell means", main.round(4).to_markdown(index=False)),
                ("Rewrite vs raw", comp.round(4).to_markdown(index=False)),
                ("Interaction (nDCG@10)", inter.round(4).to_markdown(index=False)),
                ("Cost", cst.round(4).to_markdown(index=False)),
                ("Rare-term loss (rephrase)", term_summary.round(4).to_markdown())]
    body = "\n\n".join(f"## {name}\n\n{table}" for name, table in sections)
    out = RESULTS_DIR / "summary.md"
    out.write_text(f"# Results summary (rewrites from {provider})\n\n{body}\n", encoding="utf-8")
    print(out.read_text(encoding="utf-8"))
