#!/usr/bin/env bash
# One-time setup ON the study-runner instance: Ollama + the exact Qwen model, Python 3.14 (the
# tool's version), the tool's full dependencies, and its Camoufox browser. Progress → ~/STAGE.
set -euo pipefail
mark() { echo "$1 $(date -u +%H:%M:%S)" >> ~/STAGE; }
mkdir -p ~/logs

# Ollama with 3 parallel slots, one per worker
if ! command -v ollama >/dev/null; then
  curl -fsSL https://ollama.com/install.sh | sh > ~/logs/ollama_install.log 2>&1
fi
sudo mkdir -p /etc/systemd/system/ollama.service.d
printf '[Service]\nEnvironment="OLLAMA_NUM_PARALLEL=3"\nEnvironment="OLLAMA_LOAD_TIMEOUT=15m"\n' | sudo tee /etc/systemd/system/ollama.service.d/override.conf >/dev/null
sudo systemctl daemon-reload && sudo systemctl restart ollama && sleep 5
ollama pull hf.co/unsloth/Qwen3.6-35B-A3B-GGUF:UD-IQ4_XS > ~/logs/pull.log 2>&1
printf 'FROM hf.co/unsloth/Qwen3.6-35B-A3B-GGUF:UD-IQ4_XS\nPARAMETER num_ctx 24576\nPARAMETER stop <|im_start|>\nPARAMETER stop <|im_end|>\n' > /tmp/Modelfile
ollama create qwen3.6-moe -f /tmp/Modelfile > ~/logs/create.log 2>&1
mark model_ready

# The tool's Python environment (shared by every worker copy of the tool)
if [ ! -d ~/tool/venv ]; then
  curl -LsSf https://astral.sh/uv/install.sh | sh > /dev/null 2>&1
  ~/.local/bin/uv venv --python 3.14 ~/tool/venv > /dev/null 2>&1
  ~/.local/bin/uv pip install --python ~/tool/venv -r ~/tool/requirements-private.txt > ~/logs/pip.log 2>&1
fi
mark python_ready

# Camoufox (hardened Firefox) for the tool's browser escalation, plus its system libraries
~/tool/venv/bin/python -m camoufox fetch > ~/logs/camoufox.log 2>&1 || true
~/tool/venv/bin/python -m playwright install-deps firefox > ~/logs/browser_deps.log 2>&1 || true
mark setup_done
