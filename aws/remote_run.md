# remote_run.sh

## What it does
Runs on the AWS GPU instance and does the whole experiment in one go:
1. installs Ollama;
2. installs the same Qwen model the laptop uses;
3. builds the Python environment;
4. runs `prepare` → `rewrite` → `retrieve` → `analyze`.

## Responsibility
Owns everything that happens on the cloud machine. It doesn't launch or terminate the instance,
and it doesn't copy results back. Those steps are done from the laptop with the commands at the
end of this file, so cost-bearing actions stay visible and deliberate.

## How
- **Ollama:** installed with the official script and configured with `OLLAMA_NUM_PARALLEL=2`
  through a systemd override, so two rewrites decode at the same time.
- **Model:** pulls `hf.co/unsloth/Qwen3.6-35B-A3B-GGUF:UD-IQ4_XS` and recreates the alias
  `qwen3.6-moe` with the laptop's settings: `num_ctx 24576` and Qwen's two stop tokens.
  `num_gpu 39` is left out because it's specific to the laptop's iGPU, and the L4 holds every
  layer.
- **Weights check:** the list of model blobs goes to `results/remote_blobs.txt`. That proves the
  weights' SHA-256 (`649d7508…`) matches the laptop's copy.
- **Python:** uv creates a Python 3.12 venv and installs `requirements.txt`. On Linux, plain pip
  gets the CUDA build of torch.
- **Experiment:** runs the four steps in order, each logging to `results/remote_<step>.log`.
  After each finished stage it appends a line to `results/STAGE`, so the laptop can check
  progress with one `cat`.
- **Hardware record:** writes the GPU, driver and Ollama version to `results/hardware.txt` for
  the README.

## Why
- **Embeddings before rewrites.** E5 and Qwen would otherwise share the 23 GB GPU. Running E5
  while Qwen isn't loaded avoids running out of GPU memory.
- **Pull from Hugging Face, not upload from the laptop.** It's the same file (verified by
  hash), and AWS downloads it at about 100 MB/s versus hours of home upload.
- **Two parallel slots, not more.** The 18 GB model plus a 24K context per slot has to fit in
  23 GB. Two slots roughly double throughput without risking an out-of-memory crash halfway
  through the run.
- **`set -euo pipefail` and stage markers.** A failure stops the script at that step instead of
  running later steps on missing inputs, and `STAGE` shows exactly where it stopped.

## Laptop-side commands (run from `ire-project-final/`)
```bash
# progress
ssh -i ~/.ssh/ns3-key.pem ubuntu@$(cat aws/ip.txt) "cat ~/ire/results/STAGE"
# copy results back
scp -i ~/.ssh/ns3-key.pem -r ubuntu@$(cat aws/ip.txt):~/ire/results/. results/
scp -i ~/.ssh/ns3-key.pem ubuntu@$(cat aws/ip.txt):~/ire/data/rewrite_cache.jsonl data/
# tear down (stops all billing)
aws ec2 terminate-instances --region ap-south-2 --instance-ids $(cat aws/instance-id.txt)
aws ec2 wait instance-terminated --region ap-south-2 --instance-ids $(cat aws/instance-id.txt)
aws ec2 delete-security-group --region ap-south-2 --group-id $(cat aws/sg-id.txt)
```
