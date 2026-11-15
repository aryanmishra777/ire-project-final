"""Slides 13-17: human-study design, pilot results, conclusions, limitations, questions.
The study slides state who judged relevance (the researcher, blind) and that P01 is a dry run."""
from __future__ import annotations

from pptx.util import Inches

from .facts import RN, STUDY, VN, headline, spoken
from .theme import (ACCENT, INK, MARGIN, MUTED, STUDY as TEAL, W, WHITE, H, blank, bullets,
                    footer, image, panel, text, title)


def s_study_design(prs, f):
    n = f["study"]["n"]
    s = blank(prs, "LitSearch has fixed questions and fixed labels, so you suggested testing with "
                   f"real people. {n} students each gave me one literature question from their own "
                   "work, in their own words. My tool ran each question twice, once with its LLM "
                   "rewriting step and once with it bypassed. Both top-ten lists were pooled and "
                   "shuffled. The participants could not spare the time to rate papers, so I "
                   "graded every paper myself against their question, without knowing which run "
                   "found it. I also scored how much of each question the rewrite kept. My own "
                   "question was a dry run and stays out of the main numbers.")
    title(s, "Human study: real questions, blind ratings", "Study design", TEAL)
    steps = [("1  Two runs", "Each participant's own question runs through my literature-review "
              "tool twice (Crossref + arXiv + suggested venues): rewriting on, and bypassed."),
             ("2  Blind rating", "Both top-10 lists pooled, deduplicated and shuffled. Every paper "
              "graded 0 / 1 / 2 against the participant's question, by me, source hidden."),
             ("3  Fidelity", "I compare each rewrite with the original question: how much of "
              "it survives (1–5), and what was dropped?")]
    for i, (head, body) in enumerate(steps):
        x = MARGIN + i * Inches(4.05)
        panel(s, x, Inches(1.9), Inches(3.75), Inches(3.0), line=TEAL)
        text(s, head, x + Inches(0.25), Inches(2.1), Inches(3.3), Inches(0.5), 18, TEAL, True)
        text(s, body, x + Inches(0.25), Inches(2.7), Inches(3.3), Inches(2.1), 15, INK)
    text(s, f"{n} participants + 1 researcher dry run · questions from participants · relevance "
            "(blind) and fidelity judged by the researcher · same metrics and paired tests as "
            "the benchmark", MARGIN, Inches(5.25), Inches(11.9), Inches(0.8), 15, MUTED)
    footer(s, 13)


def s_study_results(prs, f):
    st, nd = f["study"], f["study"]["nd"]
    sig = "significant" if nd["p"] < 0.05 else "not significant at the five percent level"
    rho = st["rho"]
    trend = "less" if rho is not None and rho < 0 else "more"
    fid = (f" On the right, my fidelity scores against the gain. The rewrites that kept {trend} "
           f"of the question gained more, a correlation of {'minus ' if rho < 0 else ''}"
           f"{abs(rho):.2f}. Treat that with care: seven questions, and I made both judgments."
           if rho is not None else "")
    s = blank(prs, f"On real questions the picture changes. Across the {st['n']} participants, "
                   f"the rewrite raised nDCG at ten from {nd['mean_a']:.2f} to {nd['mean_b']:.2f}, "
                   f"and {nd['wins']} of {st['n']} questions improved. With so few questions the "
                   f"test is coarse, p is {nd['p']:.2f}, so this is {sig}; the smallest effect "
                   f"this pilot could reliably detect is {nd['mde']:.2f}. The gain is far larger "
                   f"than any on LitSearch, where the best rewrite added "
                   f"{f['best_bm25'].delta:.2f}. One likely reason: without the rewrite, the long "
                   "question goes straight to the Crossref and arXiv search engines, which handle "
                   "long questions badly. That is my explanation, not something this pilot "
                   "proves." + fid)
    title(s, f"Pilot: in the live tool, the rewrite helped {nd['wins']} of {st['n']} questions",
          "Human study results", TEAL)
    image(s, STUDY / "results" / "study_figure.png", MARGIN, Inches(1.65), w=Inches(8.3))
    a = st["all"]
    text(s, f"{st['n']} participants (P01 excluded)\nnDCG@10: {nd['mean_a']:.3f} → "
            f"{nd['mean_b']:.3f}\nΔ {nd['delta']:+.3f}\n95% CI [{nd['ci_lo']:+.3f}, "
            f"{nd['ci_hi']:+.3f}]\np = {nd['p']:.3f}\nDetectable ≈ {nd['mde']:.2f}\n"
            f"Worse: {', '.join(st['worse']) or 'none'}\n\nWith P01: Δ {a['delta']:+.3f}, "
            f"p = {a['p']:.3f}", Inches(9.3), Inches(1.8), Inches(3.5), Inches(4.0), 14, INK)
    text(s, "Relevance (blind) and fidelity judged by the researcher. Pilot-sized: read the "
            "direction, not a significance claim.",
         MARGIN, Inches(6.2), Inches(11.9), Inches(0.6), 13, MUTED)
    footer(s, 14)


def recommendation(f, ret: str) -> str:
    b = f[f"best_{ret}"]
    tok = f["cost"].set_index(["retriever", "variant"]).loc[(ret, b.variant), "tokens_per_query"]
    if b.p_bh < 0.05 and b.delta > 0:
        return (f"With {RN[ret]}: {VN[b.variant]} is worth trying "
                f"({b.delta:+.3f} nDCG@10 for ~{tok:.0f} tokens per query).")
    return f"With {RN[ret]}: no rewrite gives a significant gain; skip the extra LLM call."


def study_line(f) -> str:
    st, nd = f["study"], f["study"]["nd"]
    sig = "significant" if nd["p"] < 0.05 else "not significant"
    return (f"Live-tool pilot ({st['n']} people, relevance judged blind by me): the rewrite raised "
            f"nDCG@10 by {nd['delta']:+.2f}, {nd['wins']} of {st['n']} improved "
            f"(p = {nd['p']:.2f}, {sig}).")


def spoken_close(f) -> str:
    """The conclusions read aloud: same rules as the bullets, phrased for speech."""
    say, st, nd = spoken(f), f["study"], f["study"]["nd"]
    sig = "significant" if nd["p"] < 0.05 else "not significant with only seven questions"
    b, d = f["best_bm25"], f["best_dense"]
    if b.variant == d.variant and b.p_bh < 0.05 and d.p_bh < 0.05:
        tok = f["cost"].set_index("variant").loc[b.variant, "tokens_per_query"].iloc[0]
        advice = (f"So my advice is simple: with either retriever, try {VN[b.variant]} first. "
                  f"It gave the biggest gain, for about {tok:.0f} tokens per query.")
    else:
        advice = "So my advice depends on the retriever: " + " ".join(
            recommendation(f, r) for r in ("bm25", "dense"))
    h = say["hypothesis"]
    return (f"To sum up. On the benchmark, {h} {say['best']} {say['recall_short']} In my own "
            "tool, with "
            f"real questions, the rewrite helped {nd['wins']} of {st['n']} people and raised nDCG "
            f"at ten by {nd['delta']:.2f}, which is {sig}. {advice}")


def s_conclusions(prs, f):
    lines = headline(f) + [study_line(f)]
    recs = [recommendation(f, r) for r in ("bm25", "dense")]
    s = blank(prs, spoken_close(f))
    title(s, "Conclusions", "Summary")
    bullets(s, lines, MARGIN, Inches(1.75), Inches(11.9), Inches(2.8), 14, 6)
    panel(s, MARGIN, Inches(4.55), Inches(11.9), Inches(1.9))
    text(s, "WHAT TO DO IN PRACTICE", MARGIN + Inches(0.3), Inches(4.7), Inches(8), Inches(0.4),
         12, ACCENT, True)
    text(s, "\n".join(recs), MARGIN + Inches(0.3), Inches(5.1), Inches(11.3), Inches(1.3), 17, INK)
    footer(s, 15)


def s_limitations(prs, f):
    s = blank(prs, "The limits, briefly. It is one benchmark, drawn from NLP and machine "
                   "learning papers, and one rewriting model. Most LitSearch questions have one "
                   "or two gold papers, so a relevant paper that is not in the gold set counts "
                   "as a miss. The prompts were not tuned, which is deliberate, but a tuned "
                   "prompt might do better. The human study is a small pilot, and both the "
                   "relevance grades and the fidelity scores are mine rather than the "
                   "participants'. The grading was blind, but I know the hypothesis and I am not "
                   "an expert in every topic. And I dropped "
                   "the DORIS-MAE check, as planned, to make room for the study.")
    title(s, "Limitations and next steps", "Scope")
    bullets(s, ["One benchmark (ACL + ICLR papers) and one rewriting LLM (Qwen 3.6, local)",
                "Sparse gold labels: most questions have 1–2 gold papers, so unlabelled relevant "
                "papers count as misses",
                "Prompts deliberately untuned; a tuned prompt could do better",
                f"Human study: a {f['study']['n']}-person pilot; relevance (blind) and fidelity "
                "judged by the researcher, who knows the hypothesis and is not expert in every "
                "topic",
                "Dropped as planned: DORIS-MAE generalisation check, SPLADE / doc2query arm"],
            MARGIN, Inches(1.85), Inches(11.9), Inches(4.6), 19, 12)
    footer(s, 16)


def s_thanks(prs, f):
    s = blank(prs, "Everything is reproducible: the code, the cached rewrites, and one command "
                   "per step. Thank you, sir. I'm happy to take questions.")
    panel(s, 0, 0, W, H, fill=ACCENT, rounded=False)
    text(s, "Thank you. Questions?", MARGIN, Inches(2.6), Inches(11), Inches(1), 40, WHITE, True)
    text(s, "Code, cached rewrites and results: ire-project-final/\n"
            "python -m rewrite_eval prepare | rewrite | retrieve | analyze",
         MARGIN, Inches(3.8), Inches(11.5), Inches(1.2), 18, WHITE)


SLIDES = [s_study_design, s_study_results, s_conclusions, s_limitations, s_thanks]
