# Human study results

Main analysis: 7 questions (P02, P03, P04, P05, P06, P07, P08); relevance judged blind by the researcher. Excluded from the main analysis: P01.

| Analysis | n | Original | LLM rewrite | Δ | 95% CI | p | wins / losses | MDE |
|---|---|---|---|---|---|---|---|---|
| nDCG@10 | 7 | 0.495 | 0.826 | +0.332 | [+0.065, +0.628] | 0.076 | 5 / 2 | 0.437 |
| P@10 | 7 | 0.657 | 0.957 | +0.300 | [+0.000, +0.643] | 0.250 | 3 / 1 | 0.489 |
| nDCG@10, all incl. excluded | 8 | 0.475 | 0.834 | +0.359 | [+0.110, +0.619] | 0.041 | 6 / 2 | 0.386 |

Fidelity (assessed by the researcher): 7 questions; mean 3.14 / 5; Spearman ρ (fidelity, Δ nDCG@10) = -0.78; questions with a dropped term: 7
