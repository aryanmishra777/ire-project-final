"""Clone the voice in a reference clip and read a JSON list of texts, one WAV per text.

  <chatterbox-venv>/python video/chatterbox_tts.py notes.json out_dir voice_ref.wav [--limit N]

Runs inside the separate Chatterbox venv (it needs torch and chatterbox-tts, which the project
.venv does not have). Texts are split into sentences, generated one by one, and joined with a
short gap. Files that already exist are skipped, so an interrupted run resumes.
"""
from __future__ import annotations

import argparse
import json
import re
import time
from pathlib import Path

import torch

GAP_S = 0.25  # silence between sentences


def sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", " ".join(text.split()))
    return [p for p in parts if p]


def load_model(device: str):
    # Checkpoints were saved on CUDA; remap them so they load on a CPU-only machine.
    real_load = torch.load
    torch.load = lambda *a, **k: real_load(*a, **{**k, "map_location": torch.device(device)})
    from chatterbox.tts import ChatterboxTTS
    return ChatterboxTTS.from_pretrained(device=device)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("notes_json")
    ap.add_argument("out_dir")
    ap.add_argument("ref_wav")
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--limit", type=int, default=0, help="only the first N sentences (speed test)")
    a = ap.parse_args()
    import torchaudio
    out_dir = Path(a.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    notes = json.loads(Path(a.notes_json).read_text(encoding="utf-8"))
    model = load_model(a.device)
    start, done = time.time(), 0
    for i, text in enumerate(notes, start=1):
        out = out_dir / f"voice_{i:02d}.wav"
        if out.exists() and not a.limit:
            continue
        chunks = []
        for s in sentences(text):
            if a.limit and done >= a.limit:
                return
            wav = model.generate(s, audio_prompt_path=a.ref_wav)
            chunks += [wav, torch.zeros(1, int(GAP_S * model.sr))]
            done += 1
            print(f"slide {i} sentence {done}: {time.time() - start:.0f}s elapsed", flush=True)
        torchaudio.save(str(out), torch.cat(chunks, dim=1), model.sr)


if __name__ == "__main__":
    main()
