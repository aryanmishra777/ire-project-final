"""Score the human study: per question nDCG@10 and P@10 for the rewrite-on and rewrite-off
runs from blind relevance labels, the paired test, and (when replies exist) fidelity vs gain.

  python -m study.analyze_study --study-dir study/data --exclude P01 --judge researcher

Inputs  <study>/key.csv, <study>/ratings/<pid>.csv, optional <study>/fidelity.csv
Outputs <study>/results/study_per_question.csv, study_summary.md, study_figure.png
If <study>/ILLUSTRATIVE.txt exists, every output is stamped as simulated data.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from rewrite_eval.metrics import ndcg_at, precision_at
from rewrite_eval.stats import compare

STAMP = "ILLUSTRATIVE: simulated responses, not real participants"
C_OFF, C_ON, INK, MUTED, GRID = "#8a92a1", "#7a4fbf", "#1d2433", "#5b6475", "#e4e7ec"
JUDGE = {"participants": "relevance judged by each participant",
         "researcher": "relevance judged blind by the researcher"}


def per_question(study: Path) -> pd.DataFrame:
    key = pd.read_csv(study / "key.csv")
    rows = []
    for pid, k in key.groupby("pid"):
        sheet = study / "ratings" / f"{pid}.csv"
        if not sheet.exists():
            continue  # not graded yet
        grades = pd.read_csv(sheet).set_index("item")["grade"]
        rel = {item: int(g) for item, g in grades.items()}
        out = {"pid": pid}
        for cond in ("on", "off"):
            ranked = k[k[f"rank_{cond}"].notna()].sort_values(f"rank_{cond}")["item"].tolist()
            out[f"ndcg10_{cond}"] = ndcg_at(ranked, rel, 10)
            out[f"p10_{cond}"] = precision_at(ranked, rel, 10)
        out["n_pooled"], out["n_relevant"] = len(rel), sum(g > 0 for g in rel.values())
        rows.append(out)
    df = pd.DataFrame(rows)
    fid_path = study / "fidelity.csv"
    fid = (pd.read_csv(fid_path)[["pid", "fidelity", "dropped_term"]] if fid_path.exists()
           else pd.DataFrame(columns=["pid", "fidelity", "dropped_term"]))
    df = df.merge(fid, on="pid", how="left")
    df["fidelity"] = pd.to_numeric(df["fidelity"], errors="coerce")
    df["delta_ndcg10"] = df["ndcg10_on"] - df["ndcg10_off"]
    return df


def figure(df: pd.DataFrame, path: Path, stamp: str | None, judge: str) -> None:
    has_fid = df.fidelity.notna().sum() >= 3
    fig, axes = plt.subplots(1, 2 if has_fid else 1, figsize=(7.6, 4.2) if has_fid else (4.6, 3.4),
                             dpi=200, squeeze=False)
    a = axes[0][0]
    for _, r in df.iterrows():
        a.plot([0, 1], [r.ndcg10_off, r.ndcg10_on], color=GRID, linewidth=1.2, zorder=1)
    label_y, last = {}, -1.0
    for pid, y in sorted(zip(df.pid, df.ndcg10_on), key=lambda t: t[1]):
        label_y[pid] = last = max(y, last + 0.045)  # push labels apart so they never overlap
    for _, r in df.iterrows():
        a.annotate(r.pid, (1, r.ndcg10_on), xytext=(1.08, label_y[r.pid]), fontsize=7,
                   color=MUTED, va="center", arrowprops={"arrowstyle": "-", "color": "#a7aebb",
                                                         "linewidth": 0.8, "shrinkA": 0,
                                                         "shrinkB": 3})
    a.scatter([0] * len(df), df.ndcg10_off, color=C_OFF, s=30, zorder=2)
    a.scatter([1] * len(df), df.ndcg10_on, color=C_ON, s=30, zorder=2)
    a.set_xticks([0, 1], ["original question", "LLM rewrite"])
    a.set_xlim(-0.4, 1.5)
    a.set_ylabel(f"nDCG@10 ({'researcher' if judge == 'researcher' else 'participant'} labels)")
    if has_fid:
        b = axes[0][1]
        b.axhline(0, color=MUTED, linewidth=1)
        b.scatter(df.fidelity, df.delta_ndcg10, color=C_ON, s=34, edgecolor="white", zorder=2)
        b.set_xlabel("fidelity (1 = meaning lost, 5 = fully kept)")
        b.set_ylabel("Δ nDCG@10 (rewrite − original)")
        b.set_xticks([1, 2, 3, 4, 5])
    for ax in fig.axes:
        ax.spines[["top", "right"]].set_visible(False)
        ax.tick_params(colors=MUTED, labelsize=8.5)
        ax.grid(axis="y", color=GRID)
        ax.set_axisbelow(True)
    if stamp:
        fig.suptitle(stamp, color="#b4474b", fontsize=10, fontweight="bold")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def _row(name: str, s: dict) -> str:
    return (f"| {name} | {s['n']} | {s['mean_a']:.3f} | {s['mean_b']:.3f} | {s['delta']:+.3f} | "
            f"[{s['ci_lo']:+.3f}, {s['ci_hi']:+.3f}] | {s['p']:.3f} | {s['wins']} / "
            f"{s['losses']} | {s['mde']:.3f} |")


def analyze_study(study: Path, exclude: tuple[str, ...] = (), judge: str = "participants",
                  fid_by: str = "participants") -> str:
    illustrative = (study / "ILLUSTRATIVE.txt").exists()
    out = study / "results"
    out.mkdir(exist_ok=True)
    every = per_question(study)
    df = every[~every.pid.isin(exclude)]
    every.to_csv(out / "study_per_question.csv", index=False)
    figure(df, out / "study_figure.png", STAMP if illustrative else None, judge)
    lines = [f"# Human study results{' (ILLUSTRATIVE)' if illustrative else ''}", ""]
    if illustrative:
        lines += [f"> **{STAMP}.** These numbers only demonstrate the analysis pipeline.", ""]
    lines += [f"Main analysis: {len(df)} questions ({', '.join(df.pid)}); {JUDGE[judge]}."
              + (f" Excluded from the main analysis: {', '.join(exclude)}." if exclude else ""),
              "", "| Analysis | n | Original | LLM rewrite | Δ | 95% CI | p | wins / losses | MDE |",
              "|---|---|---|---|---|---|---|---|---|",
              _row("nDCG@10", compare(df.ndcg10_off.to_numpy(), df.ndcg10_on.to_numpy())),
              _row("P@10", compare(df.p10_off.to_numpy(), df.p10_on.to_numpy()))]
    if exclude:
        lines.append(_row("nDCG@10, all incl. excluded",
                          compare(every.ndcg10_off.to_numpy(), every.ndcg10_on.to_numpy())))
    f = df.dropna(subset=["fidelity"])
    if len(f) >= 3:
        rho = f["fidelity"].corr(f["delta_ndcg10"], method="spearman")
        who = "assessed by the researcher" if fid_by == "researcher" else "rated by participants"
        lines += ["", f"Fidelity ({who}): {len(f)} questions; mean {f.fidelity.mean():.2f} / 5; "
                  f"Spearman ρ (fidelity, Δ nDCG@10) = {rho:.2f}; questions with a dropped term: "
                  f"{int(f.dropped_term.fillna('').astype(str).str.strip().ne('').sum())}"]
    else:
        lines += ["", f"Fidelity replies so far: {len(f)} (analysis needs at least 3)."]
    text = "\n".join(lines) + "\n"
    (out / "study_summary.md").write_text(text, encoding="utf-8")
    return text


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--study-dir", default="study/data")
    ap.add_argument("--exclude", default="", help="pids left out of the main analysis, e.g. P01")
    ap.add_argument("--judge", default="participants", choices=sorted(JUDGE))
    ap.add_argument("--fidelity-by", default="participants", choices=sorted(JUDGE))
    a = ap.parse_args()
    print(analyze_study(Path(a.study_dir), tuple(p for p in a.exclude.split(",") if p), a.judge,
                        a.fidelity_by))
