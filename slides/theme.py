"""Shared look for every slide: 16:9 canvas, palette, fonts, and small builders for titles,
text, bullet lists, images, tables and speaker notes."""
from __future__ import annotations

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Emu, Inches, Pt

W, H = Inches(13.333), Inches(7.5)
FONT = "Segoe UI"
INK, MUTED, ACCENT = RGBColor(0x1D, 0x24, 0x33), RGBColor(0x5B, 0x64, 0x75), RGBColor(0x2B, 0x3A, 0x67)
STUDY, WARN, LIGHT = RGBColor(0x23, 0x75, 0x6F), RGBColor(0xB4, 0x47, 0x4B), RGBColor(0xF3, 0xF5, 0xF9)
RULE, WHITE = RGBColor(0xD9, 0xDD, 0xE5), RGBColor(0xFF, 0xFF, 0xFF)
MARGIN = Inches(0.7)


def new_deck() -> Presentation:
    prs = Presentation()
    prs.slide_width, prs.slide_height = W, H
    return prs


def blank(prs, notes: str = ""):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    if notes:
        slide.notes_slide.notes_text_frame.text = notes
    return slide


def text(slide, s: str, x, y, w, h, size=18, color=INK, bold=False, align=PP_ALIGN.LEFT):
    box = slide.shapes.add_textbox(x, y, w, h)
    tf = box.text_frame
    tf.word_wrap = True
    for i, line in enumerate(s.split("\n")):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        run = p.add_run()
        run.text = line
        run.font.name, run.font.size, run.font.bold = FONT, Pt(size), bold
        run.font.color.rgb = color
    return box


def title(slide, s: str, kicker: str = "", color=ACCENT):
    if kicker:
        text(slide, kicker.upper(), MARGIN, Inches(0.38), Inches(11), Inches(0.35), 11, color, True)
    size = 28 if len(s) <= 50 else 24 if len(s) <= 60 else 22  # keep titles on one line
    text(slide, s, MARGIN, Inches(0.62), W - 2 * MARGIN, Inches(0.9), size, INK, True)
    bar = slide.shapes.add_shape(1, MARGIN, Inches(1.42), Inches(0.9), Emu(38000))
    bar.fill.solid()
    bar.fill.fore_color.rgb = color
    bar.line.fill.background()
    bar.shadow.inherit = False


def bullets(slide, items: list[str], x, y, w, h, size=18, gap=10):
    box = slide.shapes.add_textbox(x, y, w, h)
    tf = box.text_frame
    tf.word_wrap = True
    for i, item in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(gap)
        bullet = p.add_run()
        bullet.text = "•  "
        bullet.font.color.rgb, bullet.font.size, bullet.font.name = ACCENT, Pt(size), FONT
        run = p.add_run()
        run.text = item
        run.font.name, run.font.size, run.font.color.rgb = FONT, Pt(size), INK
    return box


def image(slide, path, x, y, w=None, h=None):
    return slide.shapes.add_picture(str(path), x, y, width=w, height=h)


def panel(slide, x, y, w, h, fill=LIGHT, line=None, rounded=True):
    shp = slide.shapes.add_shape(5 if rounded else 1, x, y, w, h)  # 5 rounded, 1 square
    if rounded:
        shp.adjustments[0] = 0.06
    shp.fill.solid()
    shp.fill.fore_color.rgb = fill
    if line is None:
        shp.line.fill.background()
    else:
        shp.line.color.rgb = line
    shp.shadow.inherit = False
    return shp


def table(slide, rows: list[list[str]], x, y, w, col_widths=None, size=13, header_fill=ACCENT):
    shape = slide.shapes.add_table(len(rows), len(rows[0]), x, y, w, Inches(0.4 * len(rows)))
    tbl = shape.table
    if col_widths:
        for i, cw in enumerate(col_widths):
            tbl.columns[i].width = cw
    for r, row in enumerate(rows):
        for c, val in enumerate(row):
            cell = tbl.cell(r, c)
            cell.text = str(val)
            for para in cell.text_frame.paragraphs:  # multi-line cells: style every line
                for run in para.runs:
                    run.font.name, run.font.size, run.font.bold = FONT, Pt(size), r == 0
                    run.font.color.rgb = WHITE if r == 0 else INK
            cell.fill.solid()
            cell.fill.fore_color.rgb = header_fill if r == 0 else (
                LIGHT if r % 2 == 0 else RGBColor(0xFF, 0xFF, 0xFF))
    return tbl


def stamp(slide, s: str, y=Inches(6.85)):
    """Red label for anything illustrative; kept on-slide so it survives in the video."""
    text(slide, s, MARGIN, y, W - 2 * MARGIN, Inches(0.4), 13, WARN, True)


def footer(slide, n: int):
    text(slide, f"CS4.406 IRE · Aryan Mishra · {n}", MARGIN, Inches(7.05), Inches(8), Inches(0.3),
         10, MUTED)
