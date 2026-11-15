# Narration script

Speaker notes from deck.pptx, one section per slide. The video reads these aloud.

## Slide 1

Good morning, sir. I'm Aryan Mishra, and this is my final presentation for the IRE project. The question is a simple one: when a search system asks a large language model to rewrite the user's question before searching, does that actually find better papers, and is it worth what it costs?

## Slide 2

Here is the problem. Many search systems now add one step before they search: an LLM rewrites the user's question. Take this question from the benchmark. The LLM turns it into a short string of technical terms, and the system searches with that instead of the question. The step has become common, but its effect is rarely measured on its own. Papers usually report a whole pipeline beating a keyword baseline, so the gain could just as well come from a better retriever or a reranker. And the step costs something every time: one extra LLM call per query, which adds tokens and delay. So I wanted to know whether the rewrite step itself helps, and whether it is worth paying for.

## Slide 3

So the research question is: in scholarly literature search, does LLM query rewriting improve retrieval over the raw question, by how much, under which retriever, and at what cost. My hypothesis going in was that rewriting helps BM25 clearly, because BM25 can only match exact words, and helps a dense retriever much less, because the embedding model already handles synonyms.

## Slide 4

Query reformulation is old: Rocchio feedback and BM25 come from the seventies and nineties. doc2query and SPLADE fix vocabulary mismatch on the document side, with no LLM call per query. The closest work to mine is Weller and colleagues at EACL 2024: across twelve datasets they found LLM expansion helps weak retrievers and hurts strong ones. But they only re-rank BM25's top hundred, they have no literature-search benchmark, and they report no cost. LitSearch tests GPT-4o reranking but not rewriting. So I test the question on scholarly search, with full retrieval, and with the cost on the axis.

## Slide 5

The benchmark is LitSearch: 597 real literature-search questions over sixty-four thousand ACL and ICLR papers, using titles and abstracts. The two retrievers are BM25 and E5-large-v2, both baselines in the LitSearch paper, so I can check my numbers against theirs. The rewriter is Qwen 3.6, a 35-billion-parameter mixture-of-experts model that I run locally, at temperature zero, with every call cached. Each question runs in ten cells: two retrievers times the raw question and four kinds of rewrite.

## Slide 6

Every comparison is paired by question, because a hard question is hard for every system. I use a paired bootstrap with ten thousand resamples for the confidence interval, a randomisation test for the p-value, and Benjamini-Hochberg because there are eight comparisons per metric. The hypothesis gets its own test: the per-question difference between the gain under BM25 and the gain under dense retrieval.

## Slide 7

Before trusting any comparison I checked my baselines against LitSearch's Table 3, using the paper's own measures. On the two averaged measures, E5 matches the paper, and BM25 runs 3 to 7 points higher. The paper does not say which BM25 implementation or tokenizer it used; mine stems words and drops stopwords, which usually adds a few points. The largest single gap, 14.3 points, is on the author-written broad questions, a subset of only thirty-five. So the dense baseline reproduces, and BM25 is if anything a slightly stronger baseline than the paper's, which makes rewriting gains harder.

## Slide 8

This is the main result. Each dot is the change in nDCG at ten compared with the raw question, with its ninety-five percent interval. With BM25, two of the four rewrites help significantly and none hurt. The best is HyDE, which adds 0.076 to nDCG at ten. With dense retrieval, one of the four rewrites helps significantly and none hurt. The best is HyDE, which adds 0.040 to nDCG at ten. Recall at fifty tells a clearer story. All four of the rewrites improve it significantly for BM25, by up to 0.088, and all four for dense retrieval, by up to 0.058.

## Slide 9

Now the hypothesis itself. Each small panel shows one kind of rewrite: the left point is the raw question, the right point the rewritten one, in blue for BM25 and orange for dense. If the blue line climbs more than the orange one, BM25 gains more. So the hypothesis is partly supported: for two of the four rewrites, BM25 gains significantly more than dense retrieval.

## Slide 10

An average can hide a lot. This chart counts questions: green is how many got better with the rewrite, red how many got worse. Even where the average moves up, many individual questions get worse; the most losses come from term expansion under BM25, with 114 questions worse off. That is the risk a builder takes on by adding this step.

## Slide 11

Each point is one configuration: quality on the vertical axis, cost on the horizontal. The raw question costs nothing. The rewrites cost between a few dozen and a few hundred tokens per query; HyDE is the most expensive at about 280 tokens, with a ninety-fifth percentile delay of 4.8 seconds on this hardware. A rewrite is worth paying for only if its point sits clearly above the raw question's.

## Slide 12

The failure I expected was a rewrite that turns a specific question into generic words and drops the one rare term that pointed to the right paper. I counted a term as rare if fewer than a hundred papers contain it. It happened in 31 questions, but on average it did no harm: those questions did no worse than the rest. For BM25 those questions changed by +0.026 in nDCG, against +0.018 when every rare term was kept. The big losses come from somewhere else: of the 11 questions where BM25 lost half or more of its nDCG, none had dropped a rare term. Here is the worst one: the rewrite keeps the topic but drops the wording that matched the right paper.

## Slide 13

LitSearch has fixed questions and fixed labels, so you suggested testing with real people. 7 students each gave me one literature question from their own work, in their own words. My tool ran each question twice, once with its LLM rewriting step and once with it bypassed. Both top-ten lists were pooled and shuffled. The participants could not spare the time to rate papers, so I graded every paper myself against their question, without knowing which run found it. I also scored how much of each question the rewrite kept. My own question was a dry run and stays out of the main numbers.

## Slide 14

On real questions the picture changes. Across the 7 participants, the rewrite raised nDCG at ten from 0.49 to 0.83, and 5 of 7 questions improved. With so few questions the test is coarse, p is 0.08, so this is not significant at the five percent level; the smallest effect this pilot could reliably detect is 0.44. The gain is far larger than any on LitSearch, where the best rewrite added 0.08. One likely reason: without the rewrite, the long question goes straight to the Crossref and arXiv search engines, which handle long questions badly. That is my explanation, not something this pilot proves. On the right, my fidelity scores against the gain. The rewrites that kept less of the question gained more, a correlation of minus 0.78. Treat that with care: seven questions, and I made both judgments.

## Slide 15

To sum up. On the benchmark, the hypothesis is partly supported: for two of the four rewrites, BM25 gains significantly more than dense retrieval. HyDE was the best rewrite for both retrievers. Recall at fifty rose significantly in all eight rewrite settings. In my own tool, with real questions, the rewrite helped 5 of 7 people and raised nDCG at ten by 0.33, which is not significant with only seven questions. So my advice is simple: with either retriever, try HyDE first. It gave the biggest gain, for about 280 tokens per query.

## Slide 16

The limits, briefly. It is one benchmark, drawn from NLP and machine learning papers, and one rewriting model. Most LitSearch questions have one or two gold papers, so a relevant paper that is not in the gold set counts as a miss. The prompts were not tuned, which is deliberate, but a tuned prompt might do better. The human study is a small pilot, and both the relevance grades and the fidelity scores are mine rather than the participants'. The grading was blind, but I know the hypothesis and I am not an expert in every topic. And I dropped the DORIS-MAE check, as planned, to make room for the study.

## Slide 17

Everything is reproducible: the code, the cached rewrites, and one command per step. Thank you, sir. I'm happy to take questions.
