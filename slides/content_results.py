"""Slides 7-12: reproduction check, effects, interaction, per-query wins/losses, cost,
failure analysis. Titles and narration are chosen by rules over the result tables."""
from __future__ import annotations

from pptx.util import Inches

from .facts import RES, RN, VN, headline, spoken
from .theme import (MARGIN, MUTED, WARN, footer, image, panel, table, text, title, bullets,
                    INK, ACCENT)

FIG = RES / "figures"


def _rep_phrase(name: str, diffs: list[float]) -> str:
    """Rule on the two averaged measures: within 2 points = matches, else the signed gap."""
    if max(abs(d) for d in diffs) <= 2:
        return f"{name} matches the paper"
    lo, hi = min(diffs), max(diffs)
    side = "higher" if lo > 0 else "lower" if hi < 0 else "different"
    return f"{name} runs {abs(lo):.0f}–{abs(hi):.0f} points {side}"


def s_reproduction(prs, f):
    e5, bm = _rep_phrase("E5", f["rep_avg_dense"]), _rep_phrase("BM25", f["rep_avg_bm25"])
    s = prs.slides.add_slide(prs.slide_layouts[6])
    s.notes_slide.notes_text_frame.text = (
        "Before trusting any comparison I checked my baselines against LitSearch's Table 3, "
        f"using the paper's own measures. On the two averaged measures, {e5}, and "
        f"{bm.replace('–', ' to ')}. The "
        "paper does not say which BM25 implementation or tokenizer it used; mine stems words "
        "and drops stopwords, which usually adds a few points. The largest single gap, "
        f"{f['rep_max_abs_diff']:.1f} points, is on the author-written broad questions, a "
        "subset of only thirty-five. So the dense baseline reproduces, and BM25 is if anything "
        "a slightly stronger baseline than the paper's, which makes rewriting gains harder.")
    title(s, f"Sanity check: {e5}; {bm}", "Reproduction")
    rep = f["rep"]
    rows = [["Measure (raw question)", "BM25 ours", "BM25 paper", "E5 ours", "E5 paper"]]
    for m in rep.measure.unique():
        b = rep[(rep.retriever == "bm25") & (rep.measure == m)].iloc[0]
        e = rep[(rep.retriever == "dense") & (rep.measure == m)].iloc[0]
        rows.append([m, f"{b.ours:.1f}", f"{b.paper:.1f}", f"{e.ours:.1f}", f"{e.paper:.1f}"])
    table(s, rows, MARGIN, Inches(1.85), Inches(11.9),
          [Inches(3.9), Inches(2.0), Inches(2.0), Inches(2.0), Inches(2.0)], 15)
    text(s, "Recall in %. Broad questions use R@20, specific questions R@5, as in LitSearch "
            "Table 3 (titles + abstracts).", MARGIN, Inches(5.1), Inches(11.5), Inches(0.5), 13,
         MUTED)
    footer(s, 7)


def s_effects(prs, f):
    lines, say = headline(f), spoken(f)
    s = prs.slides.add_slide(prs.slide_layouts[6])
    s.notes_slide.notes_text_frame.text = (
        "This is the main result. Each dot is the change in nDCG at ten compared with the raw "
        f"question, with its ninety-five percent interval. {say['bm25']} {say['dense']} "
        f"{say['recall']}")
    title(s, "What each rewrite does to nDCG@10", "Main result")
    image(s, FIG / "effects_ndcg10.png", MARGIN, Inches(1.75), w=Inches(7.9))
    bullets(s, lines[:2] + [lines[3]], Inches(8.85), Inches(1.8), Inches(3.9), Inches(5.0), 13, 10)
    text(s, "Bars: 95% paired-bootstrap CI. Significance after Benjamini–Hochberg.",
         MARGIN, Inches(5.85), Inches(7.9), Inches(0.4), 12, MUTED)
    footer(s, 8)


def s_interaction(prs, f):
    inter = f["inter"]
    s = prs.slides.add_slide(prs.slide_layouts[6])
    s.notes_slide.notes_text_frame.text = (
        "Now the hypothesis itself. Each small panel shows one kind of rewrite: the left point "
        "is the raw question, the right point the rewritten one, in blue for BM25 and orange "
        "for dense. If the blue line climbs more than the orange one, BM25 gains more. So "
        + spoken(f)["hypothesis"])
    title(s, f"Hypothesis {f['verdict']}: BM25 gains more in {f['n_inter_sig']} of 4 rewrites",
          "Interaction")
    image(s, FIG / "interaction.png", Inches(1.8), Inches(1.6), w=Inches(9.7))
    rows = [["Rewrite", "Gain BM25", "Gain dense", "BM25 − dense [95% CI]", "p (BH)"]]
    for r in inter.itertuples():
        rows.append([VN[r.variant], f"{r.gain_bm25:+.3f}", f"{r.gain_dense:+.3f}",
                     f"{r.interaction:+.3f} [{r.ci_lo:+.3f}, {r.ci_hi:+.3f}]", f"{r.p_bh:.3f}"])
    table(s, rows, MARGIN, Inches(5.05), Inches(11.9),
          [Inches(2.6), Inches(1.9), Inches(1.9), Inches(3.7), Inches(1.8)], 12)
    footer(s, 9)


def s_winloss(prs, f):
    nd = f["nd"]
    worst = nd.sort_values("losses", ascending=False).iloc[0]
    s = prs.slides.add_slide(prs.slide_layouts[6])
    s.notes_slide.notes_text_frame.text = (
        "An average can hide a lot. This chart counts questions: green is how many got better "
        "with the rewrite, red how many got worse. Even where the average moves up, many "
        f"individual questions get worse; the most losses come from {VN[worst.variant]} under "
        f"{RN[worst.retriever]}, with {int(worst.losses)} questions worse off. That is the "
        "risk a builder takes on by adding this step.")
    title(s, "Per question, rewriting is a gamble", "Wins and losses")
    image(s, FIG / "win_loss.png", Inches(1.6), Inches(1.7), w=Inches(10.1))
    footer(s, 10)


def s_cost(prs, f):
    c = f["cost"]
    s = prs.slides.add_slide(prs.slide_layouts[6])
    hyde = c[(c.variant == "hyde")].iloc[0]
    s.notes_slide.notes_text_frame.text = (
        "Each point is one configuration: quality on the vertical axis, cost on the horizontal. "
        "The raw question costs nothing. The rewrites cost between a few dozen and a few "
        f"hundred tokens per query; HyDE is the most expensive at about "
        f"{hyde.tokens_per_query:.0f} tokens, with a ninety-fifth percentile delay of "
        f"{hyde.llm_latency_p95_s:.1f} seconds on this hardware. A rewrite is worth paying for "
        "only if its point sits clearly above the raw question's.")
    title(s, "What the gain costs", "Cost frontier")
    image(s, FIG / "pareto.png", MARGIN, Inches(1.7), w=Inches(8.3))
    rows = [["Query form", "Tokens / query", "p95 latency (s)"]]
    for r in c[c.retriever == "bm25"].itertuples():
        rows.append([r.variant, f"{r.tokens_per_query:.0f}", f"{r.llm_latency_p95_s:.1f}"])
    table(s, rows, Inches(9.25), Inches(1.9), Inches(3.45),
          [Inches(1.35), Inches(1.1), Inches(1.0)], 12)
    text(s, "Latency measured for local Qwen 3.6 on one NVIDIA L4 (2 parallel slots).",
         MARGIN, Inches(5.95), Inches(11), Inches(0.4), 12, MUTED)
    footer(s, 11)


def s_failure(prs, f):
    ex = f["example"]
    s = prs.slides.add_slide(prs.slide_layouts[6])
    shows = f["failure_shows"]
    verdict = ("and on average it did cost retrieval quality" if shows else
               "but on average it did no harm: those questions did no worse than the rest")
    lost_big = f["n_big_loss_lost"]
    lost_big = "none" if lost_big == 0 else str(lost_big)
    s.notes_slide.notes_text_frame.text = (
        "The failure I expected was a rewrite that turns a specific question into generic words "
        "and drops the one rare term that pointed to the right paper. I counted a term as rare "
        f"if fewer than a hundred papers contain it. It happened in {f['lost_n']} questions, "
        f"{verdict}. For BM25 those questions changed by {f['lost_delta_bm25']:+.3f} in nDCG, "
        f"against {f['kept_delta_bm25']:+.3f} when every rare term was kept. The big losses come "
        f"from somewhere else: of the {f['n_big_loss']} questions where BM25 lost half or more "
        f"of its nDCG, {lost_big} had dropped a rare term. Here is the worst one: "
        "the rewrite keeps the topic but drops the wording that matched the right paper.")
    title(s, "Dropping a rare term: a real cost on average" if shows else
          "Dropping a rare term: rare, and not costly on average", "Failure analysis")
    rows = [["Rephrase kept…", "Questions", "Δ nDCG@10 BM25", "Δ nDCG@10 dense"],
            ["every rare term", str(f["kept_n"]), f"{f['kept_delta_bm25']:+.3f}",
             f"{f['kept_delta_dense']:+.3f}"],
            ["lost ≥ 1 rare term", str(f["lost_n"]), f"{f['lost_delta_bm25']:+.3f}",
             f"{f['lost_delta_dense']:+.3f}"]]
    table(s, rows, MARGIN, Inches(1.85), Inches(11.9),
          [Inches(3.5), Inches(2.4), Inches(3.0), Inches(3.0)], 15)
    panel(s, MARGIN, Inches(3.55), Inches(11.9), Inches(2.9))
    text(s, f"Question: {ex.query}", MARGIN + Inches(0.3), Inches(3.75), Inches(11.3),
         Inches(0.9), 15, INK)
    text(s, f"Rewrite: {ex.rewrite}", MARGIN + Inches(0.3), Inches(4.75), Inches(11.3),
         Inches(0.8), 15, ACCENT)
    lost = ex.lost_terms if isinstance(ex.lost_terms, str) and ex.lost_terms else "none"
    text(s, f"Worst BM25 loss ({ex.qid}) · rare terms lost: {lost} · Δ nDCG@10 BM25 "
            f"{ex.delta_bm25:+.3f}, dense {ex.delta_dense:+.3f}", MARGIN + Inches(0.3),
         Inches(5.65), Inches(11.3), Inches(0.5), 14, WARN, True)
    footer(s, 12)


SLIDES = [s_reproduction, s_effects, s_interaction, s_winloss, s_cost, s_failure]
