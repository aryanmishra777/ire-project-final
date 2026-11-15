#!/usr/bin/env bash
# Run every participant in ~/study/data/questions.csv that has no runs/<pid>.json yet, split
# across WORKERS parallel processes. Each worker gets its own copy of the tool folder because
# the tool rewrites its JSON caches whole, and two processes sharing them would corrupt them.
# Usage: bash study_batch.sh [WORKERS] [extra run_tool.py args, e.g. --venues auto]
set -uo pipefail
WORKERS=${1:-3}; shift || true
EXTRA=("$@")
cd ~/study
mkdir -p data/runs ~/logs
start=$(date +%s)

mapfile -t TODO < <(tail -n +2 data/questions.csv | cut -d, -f1 | while read -r p; do
  [ -f "data/runs/$p.json" ] || echo "$p"; done)
echo "batch start $(date -u +%H:%M:%S): ${#TODO[@]} participant(s), $WORKERS worker(s)" | tee -a ~/BATCH
[ ${#TODO[@]} -eq 0 ] && { echo "nothing to do" | tee -a ~/BATCH; exit 0; }

# Load the model BEFORE any worker starts. After a restart the 18 GB model comes off a cold disk;
# three workers asking at once made Ollama time out ("waiting for llama-server to start").
curl -s -m 900 http://localhost:11434/api/generate \
     -d '{"model": "qwen3.6-moe", "keep_alive": "3h"}' > /dev/null
echo "model loaded $(date -u +%H:%M:%S)" | tee -a ~/BATCH

for ((w = 0; w < WORKERS; w++)); do
  share=()
  for ((i = w; i < ${#TODO[@]}; i += WORKERS)); do share+=("${TODO[$i]}"); done
  [ ${#share[@]} -eq 0 ] && continue
  dir=~/tool_w$w
  [ -d "$dir" ] || rsync -a --exclude venv ~/tool/ "$dir/"
  pids=$(IFS=,; echo "${share[*]}")
  PYTHONIOENCODING=utf-8 ~/tool/venv/bin/python run_tool.py --tool-dir "$dir" \
      --study-dir data --pids "$pids" "${EXTRA[@]}" > ~/logs/worker_$w.log 2>&1 &
  echo "worker $w: $pids" | tee -a ~/BATCH
done
wait
done_n=$(ls data/runs/*.json 2>/dev/null | wc -l)
echo "batch done $(date -u +%H:%M:%S) after $(( $(date +%s) - start ))s; $done_n run file(s) total" | tee -a ~/BATCH
