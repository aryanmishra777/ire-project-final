# build_video.py

## What it does
Turns `slides/deck.pptx` into `video/presentation.mp4`. Each slide is shown while its speaker
notes are read aloud, as if presenting to the professor.

## Responsibility
Owns rendering, voice and assembly. It doesn't write any content: the words are the deck's
speaker notes, built by `slides/build_deck.py`.

## How
1. **Frames:** PowerPoint, driven over COM from PowerShell, exports every slide as a
   1920 × 1080 PNG into `video/build/png/`.
2. **Voice:** `edge-tts` reads each slide's notes into `voice_NN.mp3`. The default voice is
   `en-IN-PrabhatNeural`; any edge-tts voice can be passed with `--voice`, and the speed with
   `--rate`.
3. **Clips:** ffmpeg pairs each PNG with its MP3, adds 0.7 s of silence, and encodes H.264 + AAC
   at 30 fps.
4. **Join:** the ffmpeg concat demuxer stitches the clips without re-encoding.

## Why
- **PowerPoint renders the frames.** The video then looks exactly like the deck, with the same
  fonts and layout. A separate renderer (LibreOffice, or matplotlib redraws) would differ subtly.
- **Neural TTS from the notes.** The narration is regenerated automatically whenever results
  change. A recorded voiceover would go stale after any rerun. Swap in a real recording later if
  you want: replace the MP3s in `video/build/` and rerun the clip and join steps.
- **One clip per slide, then a lossless concat.** One slide can be re-rendered without rebuilding
  the rest, and joining same-format clips needs no second encode.
- **A short pause after each slide.** It gives the viewer a beat to read the slide before the
  next one starts.
