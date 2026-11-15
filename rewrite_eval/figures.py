"""The four result figures. Palette: BM25 blue, dense orange (validated for colour-vision
deficiency); every series is also labelled directly, so colour is never the only cue."""
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .config import FIG_DIR
from .tables import REWRITES

COLORS = {"bm25": "#3f5fbf", "dense": "#d9822b"}
LABELS = {"bm25": "BM25", "dense": "Dense (E5-large-v2)"}
VNAMES = {"raw": "Raw question", "rephrase": "Rephrase", "expand": "Term expansion",
          "hyde": "HyDE abstract", "multi": "Multi-query + RRF"}
INK, MUTED, GRID = "#1d2433", "#5b6475", "#e4e7ec"


def _style(ax):
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color(GRID)
    ax.tick_params(colors=MUTED, labelsize=9)
    ax.yaxis.label.set_color(MUTED)
    ax.xaxis.label.set_color(MUTED)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def _save(fig, name: str):
    fig.tight_layout()
    fig.savefig(FIG_DIR / name)
    plt.close(fig)


def effects(comp: pd.DataFrame, metric: str, fname: str, ylabel: str):
    """Δ vs raw with 95% bootstrap CIs, one point per retriever × variant."""
    c = comp[(comp.metric == metric) & comp.retriever.isin(["bm25", "dense"])]
    fig, ax = plt.subplots(figsize=(7.2, 3.6), dpi=200)
    x = np.arange(len(REWRITES))
    for i, ret in enumerate(("bm25", "dense")):
        s = c[c.retriever == ret].set_index("variant").loc[REWRITES]
        xs = x + (i - 0.5) * 0.26
        ax.errorbar(xs, s["delta"], yerr=[s["delta"] - s["ci_lo"], s["ci_hi"] - s["delta"]],
                    fmt="o", ms=7, color=COLORS[ret], elinewidth=2, capsize=0,
                    label=LABELS[ret], markeredgecolor="white", markeredgewidth=1.5)
        for xx, d in zip(xs, s["delta"]):
            ax.annotate(f"{d:+.3f}", (xx, d), xytext=(7, 0), textcoords="offset points",
                        fontsize=7.5, color=INK, va="center")
    ax.axhline(0, color=MUTED, linewidth=1)
    ax.set_xticks(x, [VNAMES[v] for v in REWRITES])
    ax.set_ylabel(ylabel)
    _style(ax)
    ax.legend(frameon=False, fontsize=8.5)
    _save(fig, fname)


def interaction(pq: pd.DataFrame, metric: str = "ndcg@10"):
    """Raw → rewritten slope per retriever, one small multiple per variant."""
    means = pq.groupby(["retriever", "variant"])[metric].mean()
    fig, axes = plt.subplots(1, len(REWRITES), figsize=(8.4, 2.9), dpi=200, sharey=True)
    for ax, v in zip(axes, REWRITES):
        for ret in ("bm25", "dense"):
            ys = [means[(ret, "raw")], means[(ret, v)]]
            ax.plot([0, 1], ys, color=COLORS[ret], linewidth=2, marker="o", ms=6,
                    markeredgecolor="white", markeredgewidth=1.2)
            ax.annotate(f"{ys[1]:.3f}", (1, ys[1]), xytext=(5, 0), textcoords="offset points",
                        fontsize=7.5, color=INK, va="center")
        ax.set_xticks([0, 1], ["raw", "rewritten"])
        ax.set_xlim(-0.25, 1.45)
        ax.set_title(VNAMES[v], fontsize=9, color=INK)
        _style(ax)
    axes[0].set_ylabel(f"mean {metric}")
    for ret, name in (("bm25", "BM25 "), ("dense", "Dense ")):
        axes[0].text(0, means[(ret, "raw")], name, color=COLORS[ret], fontsize=8,
                     ha="right", va="center")
    _save(fig, "interaction.png")


def pareto(cst: pd.DataFrame):
    """Quality (recall@50) against LLM tokens and against p95 added latency."""
    fig, axes = plt.subplots(1, 2, figsize=(8.4, 3.4), dpi=200, sharey=True)
    for ax, xcol, xlabel in ((axes[0], "tokens_per_query", "LLM tokens per query"),
                             (axes[1], "llm_latency_p95_s", "p95 added LLM latency (s)")):
        for ret in ("bm25", "dense"):
            s = cst[cst.retriever == ret]
            ax.scatter(s[xcol], s["recall@50"], s=46, color=COLORS[ret], label=LABELS[ret],
                       edgecolor="white", linewidth=1.2, zorder=3)
            for _, r in s.iterrows():
                ax.annotate(VNAMES[r.variant].split(" ")[0], (r[xcol], r["recall@50"]),
                            xytext=(5, 3), textcoords="offset points", fontsize=7, color=MUTED)
        ax.set_xlabel(xlabel)
        _style(ax)
    axes[0].set_ylabel("mean recall@50")
    axes[0].legend(frameon=False, fontsize=8)
    _save(fig, "pareto.png")


def win_loss(comp: pd.DataFrame, metric: str = "ndcg@10"):
    """Per-query wins and losses against raw, for every cell."""
    c = comp[(comp.metric == metric) & comp.retriever.isin(["bm25", "dense"])]
    labels, wins, losses = [], [], []
    for ret in ("bm25", "dense"):
        for v in REWRITES:
            r = c[(c.retriever == ret) & (c.variant == v)].iloc[0]
            labels.append(f"{'BM25' if ret == 'bm25' else 'Dense'} · {VNAMES[v]}")
            wins.append(int(r["wins"]))
            losses.append(-int(r["losses"]))
    fig, ax = plt.subplots(figsize=(7.2, 3.2), dpi=200)
    y = np.arange(len(labels))[::-1]
    ax.barh(y, wins, color="#3f8f5f", height=0.6)
    ax.barh(y, losses, color="#b4474b", height=0.6)
    for yy, w, l in zip(y, wins, losses):
        ax.text(w + 3, yy, str(w), va="center", fontsize=7.5, color=INK)
        ax.text(l - 3, yy, str(-l), va="center", ha="right", fontsize=7.5, color=INK)
    ax.set_yticks(y, labels, fontsize=8)
    ax.axvline(0, color=MUTED, linewidth=1)
    ax.set_xlabel(f"queries where {metric} got worse  ←   →  queries where it improved")
    _style(ax)
    ax.grid(axis="y", visible=False)
    lim = max(max(wins), -min(losses)) + 40
    ax.set_xlim(-lim, lim)
    _save(fig, "win_loss.png")
