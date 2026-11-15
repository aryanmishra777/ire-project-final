#!/usr/bin/env bash
# Runs ON the GPU instance: install Ollama + the exact Qwen model, set up the project, then
# run every experiment step. Each stage logs to ~/ire/results/remote_<stage>.log and writes
# ~/ire/results/STAGE when it finishes, so progress can be checked from the laptop.
set -euo pipefail
cd ~/ire
mark() { echo "$1 $(date -u +%H:%M:%S)" >> results/STAGE; }

# 1. Ollama (GPU), two parallel slots so two rewrites decode at once
if ! command -v ollama >/dev/null; then
  curl -fsSL https://ollama.com/install.sh | sh > results/remote_ollama_install.log 2>&1
fi
sudo mkdir -p /etc/systemd/system/ollama.service.d
printf '[Service]\nEnvironment="OLLAMA_NUM_PARALLEL=2"\n' | sudo tee /etc/systemd/system/ollama.service.d/override.conf >/dev/null
sudo systemctl daemon-reload && sudo systemctl restart ollama && sleep 5
mark ollama_ready

# 2. The same weights as the laptop's qwen3.6-moe, under the same name and settings
ollama pull hf.co/unsloth/Qwen3.6-35B-A3B-GGUF:UD-IQ4_XS > results/remote_pull.log 2>&1
cat > /tmp/Modelfile <<'EOF'
FROM hf.co/unsloth/Qwen3.6-35B-A3B-GGUF:UD-IQ4_XS
PARAMETER num_ctx 24576
PARAMETER stop <|im_start|>
PARAMETER stop <|im_end|>
EOF
ollama create qwen3.6-moe -f /tmp/Modelfile > results/remote_create.log 2>&1
sudo ls /usr/share/ollama/.ollama/models/blobs > results/remote_blobs.txt
mark model_ready

# 3. Python env (CUDA torch comes from plain pip on Linux)
if [ ! -d .venv ]; then
  curl -LsSf https://astral.sh/uv/install.sh | sh > /dev/null 2>&1
  ~/.local/bin/uv venv --python 3.12 .venv > /dev/null 2>&1
  ~/.local/bin/uv pip install --python .venv -r requirements.txt > results/remote_pip.log 2>&1
fi
mark python_ready

# 4. The experiment: embeddings first (GPU free of Qwen), then rewrites, retrieval, analysis
export PYTHONIOENCODING=utf-8
.venv/bin/python -m rewrite_eval prepare > results/remote_prepare.log 2>&1;  mark prepare_done
.venv/bin/python -m rewrite_eval rewrite --workers 2 > results/remote_rewrite.log 2>&1;  mark rewrite_done
.venv/bin/python -m rewrite_eval retrieve > results/remote_retrieve.log 2>&1;  mark retrieve_done
.venv/bin/python -m rewrite_eval analyze > results/remote_analyze.log 2>&1;  mark analyze_done
nvidia-smi --query-gpu=name,driver_version --format=csv,noheader > results/hardware.txt
ollama --version >> results/hardware.txt
mark all_done
