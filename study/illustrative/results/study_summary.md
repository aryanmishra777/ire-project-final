# Human study results (ILLUSTRATIVE)

> **ILLUSTRATIVE: simulated responses, not real participants.** These numbers only demonstrate the analysis pipeline.

Main analysis: 15 questions (P01, P02, P03, P04, P05, P06, P07, P08, P09, P10, P11, P12, P13, P14, P15); relevance judged by each participant.

| Analysis | n | Original | LLM rewrite | Δ | 95% CI | p | wins / losses | MDE |
|---|---|---|---|---|---|---|---|---|
| nDCG@10 | 15 | 0.823 | 0.814 | -0.009 | [-0.084, +0.061] | 0.821 | 8 / 7 | 0.108 |
| P@10 | 15 | 0.827 | 0.840 | +0.013 | [-0.067, +0.087] | 0.871 | 6 / 5 | 0.112 |

Fidelity (rated by participants): 15 questions; mean 3.60 / 5; Spearman ρ (fidelity, Δ nDCG@10) = 0.34; questions with a dropped term: 3
