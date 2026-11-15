"""Slides 1-6: title, motivation, question, related work, setup, evaluation. Speaker notes are
the narration for the video, written as Aryan presenting to the professor."""
from __future__ import annotations

from pptx.util import Inches

from .theme import (ACCENT, H, INK, MARGIN, RULE, W, WHITE, blank, bullets, footer, panel,
                    table, text, title)


def s_title(prs, f):
    s = blank(prs, "Good morning, sir. I'm Aryan Mishra, and this is my final presentation for the "
                   "IRE project. The question is a simple one: when a search system asks a large "
                   "language model to rewrite the user's question before searching, does that "
                   "actually find better papers, and is it worth what it costs?")
    panel(s, 0, 0, W, H, fill=ACCENT, rounded=False)
    text(s, "CS4.406 INFORMATION RETRIEVAL AND EXTRACTION · MONSOON 2026", MARGIN, Inches(2.2),
         Inches(11), Inches(0.4), 13, RULE, True)
    text(s, "Does LLM Query Rewriting Actually\nImprove Scholarly Retrieval?", MARGIN, Inches(2.7),
         Inches(11.5), Inches(2), 40, WHITE, True)
    text(s, "Final presentation · Aryan Mishra (Team Solo Retriever)", MARGIN, Inches(4.75),
         Inches(11), Inches(0.5), 18, RULE)


def s_motivation(prs, f):
    s = blank(prs, "Most retrieval pipelines today put an LLM between the question and the index. "
                   "The question gets rewritten, expanded, or turned into a fake abstract, and "
                   "only then do we search. The trouble is that this step is almost never measured "
                   "on its own. Papers report the whole pipeline beating BM25, so the gain could "
                   "come from the dense retriever or the reranker instead. And the step is not "
                   "free: it adds an LLM call to every query.")
    title(s, "An LLM now sits in front of most search pipelines", "Motivation")
    bullets(s, ["The user's question is rewritten, expanded or turned into a hypothetical answer "
                "before retrieval. Many RAG stacks do this by default.",
                "Its own contribution is rarely isolated: gains are reported for whole pipelines, "
                "so they could come from the retriever, reranker or fusion step.",
                "It costs an LLM call on every query: tokens on the bill and latency on the "
                "critical path.",
                "Scholarly search is built by small academic groups on small budgets, exactly "
                "where an unmeasured default gets copied from paper to paper."],
            MARGIN, Inches(1.8), Inches(11.6), Inches(4.8), 20, 16)
    footer(s, 2)


def s_question(prs, f):
    s = blank(prs, "So the research question is: in scholarly literature search, does LLM query "
                   "rewriting improve retrieval over the raw question, by how much, under which "
                   "retriever, and at what cost. My hypothesis going in was that rewriting helps "
                   "BM25 clearly, because BM25 can only match exact words, and helps a dense "
                   "retriever much less, because the embedding model already handles synonyms.")
    title(s, "Research question and hypothesis", "The question")
    for i, (head, body) in enumerate([
            ("RESEARCH QUESTION", "In scholarly literature search, does LLM query rewriting "
             "improve retrieval over the raw question? By how much, under which retriever, and "
             "at what token and latency cost?"),
            ("HYPOTHESIS", "Rewriting gives a clear gain for BM25, where vocabulary mismatch is "
             "the binding constraint, and a much smaller or insignificant gain for dense "
             "retrieval. The test is the interaction: retriever × rewriting.")]):
        x = MARGIN + i * Inches(6.05)
        panel(s, x, Inches(1.9), Inches(5.75), Inches(3.6))
        text(s, head, x + Inches(0.3), Inches(2.15), Inches(5.2), Inches(0.4), 13, ACCENT, True)
        text(s, body, x + Inches(0.3), Inches(2.6), Inches(5.2), Inches(2.8), 20, INK)
    footer(s, 3)


def s_related(prs, f):
    s = blank(prs, "Query reformulation is old: Rocchio feedback and BM25 come from the seventies "
                   "and nineties. doc2query and SPLADE fix vocabulary mismatch on the document "
                   "side, with no LLM call per query. The closest work to mine is Weller and "
                   "colleagues at EACL 2024: across twelve datasets they found LLM expansion helps "
                   "weak retrievers and hurts strong ones. But they only re-rank BM25's top "
                   "hundred, they have no literature-search benchmark, and they report no cost. "
                   "LitSearch tests GPT-4o reranking but not rewriting. So I test the question on "
                   "scholarly search, with full retrieval, and with the cost on the axis.")
    title(s, "Related work and the gap", "Background")
    rows = [["Line of work", "Representative work", "What it leaves open"],
            ["Classical reformulation", "Rocchio feedback; BM25 (Robertson & Zaragoza)",
             "No LLM; the baseline to beat"],
            ["Expansion without per-query LLM", "doc2query (Nogueira & Lin); SPLADE (Formal et al.)",
             "Cheaper rival on the cost axis"],
            ["LLM query rewriting", "HyDE (Gao et al.); Jagerman et al.; Ma et al.; Mackie et al.",
             "Mostly one retriever; cost rarely reported"],
            ["Closest prior work", "Weller et al., EACL 2024: expansion helps weak retrievers, "
             "hurts strong ones (24 models, 12 datasets)",
             "Re-ranks BM25 top-100 only; no literature search; no cost"],
            ["Scholarly benchmarks", "LitSearch (Ajith et al., EMNLP 2024); DORIS-MAE; BEIR",
             "LitSearch tests GPT-4o reranking, not rewriting"]]
    table(s, rows, MARGIN, Inches(1.85), Inches(11.9),
          [Inches(3.1), Inches(5.0), Inches(3.8)], 13)
    footer(s, 4)


def s_setup(prs, f):
    s = blank(prs, f"The benchmark is LitSearch: {f['n_queries']} real literature-search questions "
                   "over sixty-four thousand ACL and ICLR papers, using titles and abstracts. "
                   "The two retrievers are BM25 and E5-large-v2, both baselines in the LitSearch "
                   "paper, so I can check my numbers against theirs. The rewriter is Qwen 3.6, "
                   "a 35-billion-parameter mixture-of-experts model that I run locally, at "
                   "temperature zero, with every call cached. Each question runs in ten cells: "
                   "two retrievers times the raw question and four kinds of rewrite.")
    title(s, "Experiment: 2 retrievers × 5 query forms", "Method")
    bullets(s, [f"LitSearch: {f['n_queries']} questions, 64,183 ACL + ICLR papers "
                "(title + abstract)",
                "BM25 (bm25s) and E5-large-v2 (exact cosine)",
                "Rewriter: Qwen 3.6 35B-A3B via Ollama, temperature 0, every call cached",
                "Top 100 per cell; nDCG@10, recall@5/20/50/100, MRR"],
            MARGIN, Inches(1.85), Inches(5.6), Inches(4.6), 17, 12)
    rows = [["Query form", "How it is searched"],
            ["Raw question", "As written (baseline)"],
            ["Rephrase", "Rewrite replaces the question"],
            ["Term expansion", "Question + LLM term list"],
            ["HyDE abstract", "BM25: question + abstract;\ndense: mean of the two vectors"],
            ["Multi-query", "Question + 3 LLM queries, fused by RRF"]]
    table(s, rows, Inches(6.75), Inches(1.85), Inches(5.9), [Inches(2.0), Inches(3.9)], 14)
    footer(s, 5)


def s_stats(prs, f):
    s = blank(prs, "Every comparison is paired by question, because a hard question is hard for "
                   "every system. I use a paired bootstrap with ten thousand resamples for the "
                   "confidence interval, a randomisation test for the p-value, and "
                   "Benjamini-Hochberg because there are eight comparisons per metric. The "
                   "hypothesis gets its own test: the per-question difference between the gain "
                   "under BM25 and the gain under dense retrieval.")
    title(s, "How a difference counts as real", "Evaluation")
    bullets(s, ["Paired by question: the same question is hard or easy for every system",
                "95% CI from a paired bootstrap (10,000 resamples)",
                "p-value from a paired randomisation test (Smucker et al., 2007)",
                "Benjamini–Hochberg across the 8 rewrite-vs-raw tests per metric",
                "Interaction tested directly: (gain under BM25) − (gain under dense), per question",
                "Minimum detectable effect reported, so a null reads as \"no effect larger than X\""],
            MARGIN, Inches(1.85), Inches(11.8), Inches(4.8), 19, 12)
    footer(s, 6)


SLIDES = [s_title, s_motivation, s_question, s_related, s_setup, s_stats]
