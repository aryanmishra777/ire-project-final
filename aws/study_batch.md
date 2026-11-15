# study_batch.sh

## What it does
Runs every participant in `~/study/data/questions.csv` who doesn't have a `runs/<pid>.json` yet,
split across parallel workers (default 3) on the study-runner instance.

## Responsibility
Owns batching and parallelism. The per-question work (two tool runs, venues chosen once) stays
in `study/run_tool.py`. Copying the inputs up and the results back is done from the laptop.

## How
1. Lists participants without a finished run file, then loads the model into the GPU with one
   empty request (kept loaded for 3 hours) before any worker starts.
2. Deals them round-robin to `WORKERS` workers.
3. Gives each worker its own copy of the tool folder, `~/tool_w<i>`, made with `rsync` and
   excluding the shared venv.
4. Starts `run_tool.py --pids <its share>` for every worker in parallel, with any extra
   arguments passed through (e.g. `--venues auto`).
5. Waits for all of them, then appends the batch's start, worker split, end and duration to
   `~/BATCH`.

Usage, on the instance: `bash ~/study_batch.sh 3 --venues auto`.

## Why
- **Workers in parallel.** Most of a participant's run is spent waiting on websites and APIs
  (search, crawling, OpenAlex). Running three at once overlaps that waiting, which is where AWS
  actually saves time. A faster GPU only shortens the LLM steps.
- **A separate tool copy per worker.** The tool keeps its embedding and enrichment caches as
  single JSON files and rewrites them whole. Two processes writing the same file could corrupt
  it. Separate copies avoid that with no change to the tool.
- **Load the model first.** In the first real batch, the instance had just restarted and the
  18 GB model had to come off a cold disk. Three workers requested it at once, and two crashed
  with Ollama's "timed out waiting for llama-server to start". Loading it once, before the
  workers start, removes that race. `study_setup.sh` also raises `OLLAMA_LOAD_TIMEOUT` to
  15 minutes.
- **Safe to rerun.** Finished participants are skipped, so new Form 1 responses can be added to
  `questions.csv` and the same command run again.
