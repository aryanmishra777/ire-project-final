# theme.py

## What it does
Defines the deck's look (16:9 canvas, palette, font, margins) and small builders that every
slide uses: `title`, `text`, `bullets`, `image`, `panel`, `table`, `stamp` and `footer`.

## Responsibility
Owns presentation primitives only. It has no content and reads no results, so every slide looks
consistent and restyling the deck means editing one file.

## How
- `new_deck()` makes a 13.333 × 7.5 in (16:9) presentation. `blank()` adds a slide on the empty
  layout and stores the speaker notes.
- `title()` draws a small upper-case kicker, the title and a short accent bar.
- `bullets()` draws accent-coloured bullet glyphs with consistent spacing. `table()` draws a
  header-shaded, zebra-striped table with optional column widths.
- `panel()` is a rounded, shadowless background card.
- `stamp()` writes a red line for illustrative content, placed on the slide itself so it also
  appears in the exported video frames.

## Why
- **Segoe UI everywhere.** The video is rendered by PowerPoint on Windows, where Segoe UI is
  always present, so the exported frames look exactly like the deck.
- **The same palette as the reports and figures.** Indigo is the main accent and teal marks the
  human study. Red is reserved for the "illustrative" stamp, so the warning colour means one thing
  only.
- **Builders, not a PowerPoint template.** python-pptx placeholders differ between templates.
  Drawing every element explicitly gives the same result on any machine.
