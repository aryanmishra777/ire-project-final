"""Build the final report PDF from results/ and study/data/results/ (no hand-typed numbers).

  python -m report.build_report [--out "../Final Report - Aryan Mishra.pdf"]

Fills report/template.html, inlines report/style.css and the figures, then prints the page with
headless Microsoft Edge. Repo and video links are placeholders until the real ones exist.
"""
from __future__ import annotations

import argparse
import base64
import re
import subprocess
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RES, STUDY, HERE = ROOT / "results", ROOT / "study" / "data", Path(__file__).resolve().parent
EDGE = Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")
NAMES = {"rephrase": "Rephrase", "expand": "Term expansion", "hyde": "HyDE abstract",
         "multi": "Multi-query + RRF"}


def sgn(x: float, d: int = 3) -> str:
    return f"{x:+.{d}f}".replace("-", "\u2212")


def p_txt(p: float) -> str:
    return "<0.001" if p < 0.001 else f"{p:.3f}"


def img(path: Path) -> str:
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode()


def effect_rows(cmp: pd.DataFrame) -> str:
    rows = []
    for v, name in NAMES.items():
        cells = []
        for metric in ("ndcg@10", "recall@50"):
            for r in ("bm25", "dense"):
                x = cmp[(cmp.metric == metric) & (cmp.retriever == r) & (cmp.variant == v)].iloc[0]
                cls = ' class="sig"' if x.p_bh < 0.05 else ""
                tip = f" [{sgn(x.ci_lo)}, {sgn(x.ci_hi)}]" if metric == "ndcg@10" else ""
                cells.append(f"<td{cls}>{sgn(x.delta)}{tip}</td>")
        rows.append(f"<tr><td>{name}</td>{''.join(cells)}</tr>")
    return "".join(rows)


def interaction_rows(it: pd.DataFrame) -> str:
    out = []
    for v, name in NAMES.items():
        x = it[it.variant == v].iloc[0]
        cls = ' class="sig"' if x.p_bh < 0.05 else ""
        out.append(f"<tr><td>{name}</td><td>{sgn(x.gain_bm25)}</td><td>{sgn(x.gain_dense)}</td>"
                   f"<td{cls}>{sgn(x.interaction)} [{sgn(x.ci_lo)}, {sgn(x.ci_hi)}]</td>"
                   f"<td{cls}>{p_txt(x.p_bh)}</td></tr>")
    return "".join(out)


def cost_rows(cost: pd.DataFrame) -> str:
    c = cost[cost.retriever == "bm25"].set_index("variant")
    return "".join(f"<tr><td>{n}</td><td>{c.loc[v, 'tokens_per_query']:.0f}</td>"
                   f"<td>{c.loc[v, 'completion_tokens']:.0f}</td>"
                   f"<td>{c.loc[v, 'llm_latency_p95_s']:.1f} s</td></tr>" for v, n in NAMES.items())


def study_facts() -> dict[str, str]:
    q = pd.read_csv(STUDY / "results" / "study_per_question.csv")
    main = q[q.pid != "P01"]
    md = (STUDY / "results" / "study_summary.md").read_text(encoding="utf-8")
    row = re.search(r"\| nDCG@10 \| (\d+) \| ([\d.]+) \| ([\d.]+) \| ([+\d.\-]+) \| \[([^\]]+)\] \| ([\d.]+)"
                    r" \| (\d+) / (\d+) \| ([\d.]+)", md)
    n, off, on, d, ci, p, w, l, mde = row.groups()
    rho = re.search(r"\u03c1 \(fidelity, \u0394 nDCG@10\) = ([\-\d.]+)", md).group(1)
    return {"s_n": n, "s_off": off, "s_on": on, "s_d": d, "s_ci": ci.replace("-", "\u2212"),
            "s_p": p, "s_w": w, "s_l": l, "s_mde": mde, "s_rho": rho.replace("-", "\u2212"),
            "s_fid": f"{main.fidelity.mean():.1f}", "s_total": str(len(q))}


def build_values() -> dict[str, str]:
    cmp, it = pd.read_csv(RES / "comparisons.csv"), pd.read_csv(RES / "interaction.csv")
    cost, rep = pd.read_csv(RES / "cost.csv"), pd.read_csv(RES / "reproduction.csv")
    main, ft = pd.read_csv(RES / "main_table.csv").set_index(["retriever", "variant"]), \
        pd.read_csv(RES / "failure_terms.csv")
    big = ft[ft.delta_bm25 <= -0.5]
    nd = cmp[cmp.metric == "ndcg@10"]
    g = lambda r, v: nd[(nd.retriever == r) & (nd.variant == v)].iloc[0]
    avg = rep[rep.measure.str.startswith("avg")]
    gap = lambda r: avg[avg.retriever == r]["diff"].abs().max()
    losses = int(nd[(nd.retriever == "bm25") & (nd.variant == "expand")].losses.iloc[0])
    vals = {
        "ndcg_raw_bm25": f"{main.loc[('bm25', 'raw'), 'ndcg@10']:.3f}",
        "ndcg_raw_dense": f"{main.loc[('dense', 'raw'), 'ndcg@10']:.3f}",
        "hyde_bm25": sgn(g("bm25", "hyde").delta), "hyde_dense": sgn(g("dense", "hyde").delta),
        "n_sig_bm25": str(int(nd[nd.retriever == "bm25"].significant.sum())),
        "n_sig_dense": str(int(nd[nd.retriever == "dense"].significant.sum())),
        "n_r50_sig": str(int(cmp[(cmp.metric == "recall@50") & cmp.variant.isin(NAMES)].significant.sum())),
        "n_inter_sig": str(int((it.p_bh < 0.05).sum())),
        "gap_e5": f"{gap('dense'):.1f}", "gap_bm25_max": f"{gap('bm25'):.1f}",
        "n_lost": str(int(ft.lost_any.sum())), "n_ft": str(len(ft)), "n_big": str(len(big)),
        "n_big_lost": str(int(big.lost_any.sum())), "expand_losses": str(losses),
        "tok_hyde": f"{cost[cost.variant == 'hyde'].tokens_per_query.iloc[0]:.0f}",
        "p95_hyde": f"{cost[cost.variant == 'hyde'].llm_latency_p95_s.iloc[0]:.1f}",
        "effect_rows": effect_rows(cmp), "inter_rows": interaction_rows(it), "cost_rows": cost_rows(cost),
        "fig_effects": img(RES / "figures" / "effects_ndcg10.png"),
        "fig_pareto": img(RES / "figures" / "pareto.png"),
        "fig_study": img(STUDY / "results" / "study_figure.png"),
        "css": (HERE / "style.css").read_text(encoding="utf-8"),
    }
    return vals | study_facts()


def render(out: Path) -> None:
    html = (HERE / "template.html").read_text(encoding="utf-8")
    for k, v in build_values().items():
        html = html.replace(f"[[{k}]]", v)
    left = re.findall(r"\[\[\w+\]\]", html)
    if left:
        raise RuntimeError(f"unfilled placeholders: {left}")
    page = HERE / "report.html"
    page.write_text(html, encoding="utf-8")
    subprocess.run([str(EDGE), "--headless", "--disable-gpu", "--no-pdf-header-footer",
                    f"--print-to-pdf={out}", page.as_uri()], check=True)
    print(f"wrote {out}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=ROOT.parent / "Final Report - Aryan Mishra.pdf")
    render(ap.parse_args().out)
