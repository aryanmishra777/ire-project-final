"""Build slides/deck.pptx from the current results and write the narration script.

  python -m slides.build_deck

Outputs: slides/deck.pptx (speaker notes = narration) and slides/narration.md (the same notes
as plain text, one section per slide, for review and for the video).
"""
from __future__ import annotations

from pathlib import Path

from . import content_close, content_intro, content_results
from .facts import load
from .theme import new_deck

OUT = Path(__file__).resolve().parent


def build() -> Path:
    facts = load()
    prs = new_deck()
    for make in content_intro.SLIDES + content_results.SLIDES + content_close.SLIDES:
        make(prs, facts)
    deck = OUT / "deck.pptx"
    prs.save(deck)
    lines = ["# Narration script", "",
             "Speaker notes from deck.pptx, one section per slide. The video reads these aloud.", ""]
    for i, slide in enumerate(prs.slides, start=1):
        lines += [f"## Slide {i}", "", slide.notes_slide.notes_text_frame.text.strip(), ""]
    (OUT / "narration.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {deck} ({len(prs.slides)} slides) and narration.md")
    return deck


if __name__ == "__main__":
    build()
