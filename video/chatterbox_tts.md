# chatterbox_tts.py

## What it does
Reads the deck's speaker notes (a JSON list, one string per slide) and writes `voice_NN.wav` for
each slide in a voice cloned from a 15–30 s reference recording.

## Responsibility
Owns speech synthesis with Chatterbox only. It doesn't read the deck, build frames or touch ffmpeg;
`build_video.py` does that and picks up the WAVs with `--audio-dir`. It runs in a separate venv
(torch and `chatterbox-tts`), never in the project `.venv`.

## How
1. `sentences()` splits each slide's notes at sentence ends.
2. `load_model()` loads `ChatterboxTTS` on the chosen device. `torch.load` is wrapped so checkpoints
   saved on CUDA map onto a CPU-only machine.
3. Each sentence is generated with `audio_prompt_path` set to the reference clip, then joined with
   0.25 s of silence and saved at the model's sample rate (24 kHz).
4. A slide whose WAV already exists is skipped, so an interrupted run resumes. `--limit N` generates
   only N sentences, for speed tests.

## Why
- **Sentence by sentence.** Long inputs make Chatterbox drift or cut off; short chunks keep the
  voice steady and let the run resume.
- **Separate venv and script.** Its pinned torch would conflict with the project's pins, and the
  synthesis can run on a rented GPU (about 6x real time on CPU, much faster on an L4).
- **Reference clip stays out of git.** It is a recording of a real voice; it is excluded through
  `.git/info/exclude`.
