# Reproducing the results

There are two ways to reproduce the numbers:
- **Path A, exact with no LLM.** Uses the released rewrite cache, so it needs no GPU and no API
  key.
- **Path B, full.** Regenerates the rewrites too.

## Setup (both paths)
```bash
uv venv --python 3.12 .venv
# CPU-only machine: install torch from the CPU index first
uv pip install --python .venv torch --index-url https://download.pytorch.org/whl/cpu
uv pip install --python .venv -r requirements.txt
cp .env.example .env
```

## Path A: exact reproduction from the released cache
`data/rewrite_cache.jsonl` holds every rewrite used in the results: 2,388 rows, 597 questions × 4
variants. Each row has the output, token counts, latency, model and date. With it in place,
`rewrite` makes no LLM calls.
```bash
.venv/Scripts/python -m rewrite_eval prepare    # LitSearch download + BM25 index + E5 embeddings
.venv/Scripts/python -m rewrite_eval retrieve   # all 10 cells, scored per question
.venv/Scripts/python -m rewrite_eval analyze    # results/summary.md, CSVs, figures
.venv/Scripts/python -m study.make_illustrative # illustrative (simulated) human-study run
.venv/Scripts/python -m slides.build_deck       # slides/deck.pptx + narration.md
```
Retrieval is deterministic. The statistics use fixed seeds (`STATS_SEED = 2026` in
`rewrite_eval/config.py`), so the CIs and p-values come out identical.

## Path B: regenerate the rewrites
Needs Ollama with the same model:
```bash
ollama pull hf.co/unsloth/Qwen3.6-35B-A3B-GGUF:UD-IQ4_XS
# alias it as qwen3.6-moe with num_ctx 24576 and the two Qwen stop tokens (see aws/remote_run.sh)
.venv/Scripts/python -m rewrite_eval rewrite --workers 2
```
The model file's SHA-256 is `649d7508507b84638732c4f52c24c8b15843c6dca2f3ff793ae07c14a67ebbb3`.
That's the same file on the author's laptop and on the AWS run (`results/remote_blobs.txt`).
Temperature is 0 with a fixed seed, but a different GPU or driver can still change a few words of
a rewrite. Path A is the exact path.

## Hardware and runtimes of the reported run
The reported results were produced on AWS `g6.2xlarge` in ap-south-2:
- one NVIDIA L4 (23 GB), driver 595.112.07;
- 8 vCPUs and 30 GB RAM;
- Ollama 0.40.16 with `OLLAMA_NUM_PARALLEL=2`.

Stage durations (from `results/STAGE`):

| Step | Duration |
|---|---|
| Ollama install + model pull + venv | ~7 min |
| `prepare` (BM25 index 5 s; E5-large-v2 over 64,183 papers on the L4) | 23 min |
| `rewrite` (2,388 Qwen calls, 2 parallel slots) | 36 min |
| `retrieve` (10 cells × 597 questions) | 2 min |
| `analyze` | 17 s |

Compute cost was about 1.7 instance-hours.

The author's laptop (Intel Core Ultra 7 155H, 32 GB, Arc iGPU, CPU-only torch) was also tried:
- **E5 embedding:** the first batches ran at about 34 s each, which projects to 5+ hours. That's
  why the run moved to a GPU.
- **Local Qwen:** about 8–16 s per rewrite, which projects to 6–10 hours.

The 14 rewrites made on the laptop before the move are kept apart in
`data/rewrite_cache_laptop_partial.jsonl` and aren't used in any result.

## Notes on the cost numbers
- **Latency depends on the setup.** `cost.csv` latencies are wall-clock per call on the L4, with
  two calls decoding at once. Single-stream latency would be lower, and on other hardware they
  will differ.
- **Cold-start calls.** The first one or two calls of each variant include loading the model
  (about 11–12 s). That's 2–3 calls out of 597 per variant: it raises the mean latency slightly
  and barely affects the p95.
- **Tokens are hardware-independent.** Token counts are prompt + completion as reported by Ollama.

## The human study
`study/illustrative/` is **simulated** data (see `study/make_illustrative.md`). To run the real
pilot:
1. Collect questions with `study/forms/form1_question.md` into `study/data/questions.csv`
   (columns `pid, area, question`).
2. Run the tool in both conditions:
   `"<tool>/venv/Scripts/python" study/run_tool.py --tool-dir "<tool>" --study-dir study/data`.
3. Make the blind sheets: `.venv/Scripts/python -m study.pool --study-dir study/data`.
4. Send each participant their sheet (Form 2), and save the graded sheets to
   `study/data/ratings/<pid>.csv` and the Part B answers to `study/data/fidelity.csv`.
5. Analyse: `.venv/Scripts/python -m study.analyze_study --study-dir study/data`.
