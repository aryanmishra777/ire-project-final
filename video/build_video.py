"""Turn slides/deck.pptx into a narrated MP4: each slide shown while its speaker notes are read.

  python -m video.build_video [--voice en-IN-PrabhatNeural]
  python -m video.build_video --audio-dir video/voice   # use cloned-voice WAVs (voice_NN.wav)

Steps: PowerPoint (COM) exports every slide as a 1920x1080 PNG; edge-tts reads each slide's
notes into an MP3; ffmpeg pairs each image with its audio and joins the clips.
With --audio-dir the narration is not synthesised here: the WAVs come from
video/chatterbox_tts.py (run in its own venv, on a GPU).
Needs Windows with PowerPoint, ffmpeg on PATH, and internet for edge-tts.
"""
from __future__ import annotations

import argparse
import asyncio
import shutil
import subprocess
from pathlib import Path

import edge_tts
from pptx import Presentation

ROOT = Path(__file__).resolve().parent.parent
DECK = ROOT / "slides" / "deck.pptx"
BUILD = ROOT / "video" / "build"
OUT = ROOT / "video" / "presentation.mp4"
PAUSE_S = 0.7  # silence after each slide's narration


def export_slides(deck: Path, out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    ps = (f"$p = New-Object -ComObject PowerPoint.Application; "
          f"$d = $p.Presentations.Open('{deck}', $true, $false, $false); "
          f"$d.Export('{out_dir}', 'PNG', 1920, 1080); $d.Close(); $p.Quit()")
    subprocess.run(["powershell", "-NoProfile", "-Command", ps], check=True)
    pngs = sorted(out_dir.glob("*.PNG"), key=lambda p: int("".join(filter(str.isdigit, p.stem))))
    if not pngs:
        raise RuntimeError("PowerPoint exported no slides")
    return pngs


async def narrate(notes: list[str], out_dir: Path, voice: str, rate: str) -> list[Path]:
    paths = []
    for i, text in enumerate(notes, start=1):
        path = out_dir / f"voice_{i:02d}.mp3"
        await edge_tts.Communicate(text, voice, rate=rate).save(str(path))
        paths.append(path)
    return paths


def clip(png: Path, mp3: Path, out: Path) -> None:
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-i", str(png), "-i", str(mp3),
        "-af", f"apad=pad_dur={PAUSE_S}", "-c:v", "libx264", "-tune", "stillimage",
        "-pix_fmt", "yuv420p", "-r", "30", "-c:a", "aac", "-b:a", "160k", "-shortest",
        str(out)], check=True)


def build(voice: str, rate: str, audio_dir: Path | None = None) -> Path:
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("ffmpeg not found on PATH")
    BUILD.mkdir(parents=True, exist_ok=True)
    notes = [s.notes_slide.notes_text_frame.text.strip() for s in Presentation(DECK).slides]
    pngs = export_slides(DECK, BUILD / "png")
    if audio_dir:
        mp3s = [audio_dir / f"voice_{i:02d}.wav" for i in range(1, len(pngs) + 1)]
        missing = [m.name for m in mp3s if not m.exists()]
        if missing:
            raise RuntimeError(f"missing narration files in {audio_dir}: {missing}")
    else:
        mp3s = asyncio.run(narrate(notes, BUILD, voice, rate))
    clips = []
    for i, (png, mp3) in enumerate(zip(pngs, mp3s), start=1):
        out = BUILD / f"clip_{i:02d}.mp4"
        clip(png, mp3, out)
        clips.append(out)
        print(f"slide {i}/{len(pngs)} done")
    listing = BUILD / "clips.txt"
    listing.write_text("".join(f"file '{c.as_posix()}'\n" for c in clips), encoding="utf-8")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
                    "-i", str(listing), "-c", "copy", str(OUT)], check=True)
    print(f"wrote {OUT}")
    return OUT


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--voice", default="en-IN-PrabhatNeural",
                    help="any edge-tts voice, e.g. en-IN-NeerjaNeural, en-GB-RyanNeural")
    ap.add_argument("--rate", default="+0%", help="speaking rate, e.g. -5%% or +10%%")
    ap.add_argument("--audio-dir", type=Path, help="folder of voice_NN.wav files to use instead of edge-tts")
    a = ap.parse_args()
    build(a.voice, a.rate, a.audio_dir)
