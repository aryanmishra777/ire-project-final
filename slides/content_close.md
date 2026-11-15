# content_close.py

## What it does
Builds slides 13–17: the human-study design, the pilot's results, conclusions with practical
recommendations, limitations, and the closing Q&A slide.

## Responsibility
Owns the closing argument and the honest presentation of the human study. Both study slides must
say who judged relevance (the researcher, blind) and that P01 was a dry run, because those are
the two ways the pilot differs from the original plan.

## How
- **Study design:** three panels (two runs → blind rating → fidelity), plus a line stating 7
  participants and 1 dry run, and who supplied what.
- **Study results:** the paired-slope figure from `study/data/results/`, and the main numbers
  with P01 excluded: means, Δ, CI, p, MDE, and which questions got worse. Also the all-in Δ and p,
  and a footnote that relevance was researcher-judged and the result is pilot-sized. The narration
  compares the gain with the best LitSearch gain, and presents the likely reason (long questions
  sent straight to Crossref/arXiv) as an explanation, not a proven result. Fidelity is mentioned
  once replies exist.
- **`study_line()`:** one rule-based sentence summarising the pilot for the conclusions slide,
  significant or not depending on p.
- **`recommendation()`:** for each retriever, recommends the best variant only if it gains
  significantly (BH p < 0.05, Δ > 0), quoting its token cost; otherwise it says to skip the LLM
  call.
- **Limitations:** one benchmark and one LLM, sparse gold labels, untuned prompts, the pilot's
  size and researcher-judged relevance, and the planned cuts.

## Why
- **Changes to the plan stated on the slides.** Researcher judging and the dry run are what a
  reviewer will ask about. Stating them up front is more credible than leaving them to be found.
- **"Not significant" stated plainly.** With 7 questions the randomisation test is coarse. The
  slide reports the direction and the effect size, and says the result isn't a significance claim
  when p ≥ 0.05.
- **The causal story labelled as a hypothesis.** The live tool and LitSearch differ in several
  ways at once (retriever, rewrite prompt, judges), so the pilot can't isolate why the gain is
  larger.
- **Recommendations by rule.** A builder's question is "should I add this step". Tying the answer
  to significance and cost makes it follow from the data.
