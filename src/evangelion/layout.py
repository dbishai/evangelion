"""Page layout constants, decorative drawing primitives, and the page-flow
manager used to typeset the lectionary booklet.

Deliberately restrained: a page frame, a small cross mark, a rule-and-title
headpiece, and a drop cap -- all outline-and-text, no large ink fills, so
the book reproduces cleanly on a red+black duotone press or a home printer.
"""

from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas

from evangelion.fonts import BODY_BOLD, BODY_FONT, BODY_ITALIC

# Trim size: 24 x 34cm, sized to fit inside a 35 x 25cm gold Gospel case
# with 0.5cm clearance per side for the binding.
PAGE_W, PAGE_H = 24 * cm, 34 * cm

RED = colors.HexColor("#A6192E")  # rubric red
INK = colors.HexColor("#161616")  # body text (near-black, prints cleanly)

BORDER_OUT = 0.52 * 72
BORDER_IN = 0.68 * 72
CONTENT_L = BORDER_IN + 16
CONTENT_R = PAGE_W - BORDER_IN - 16
CONTENT_W = CONTENT_R - CONTENT_L
CONTENT_TOP = PAGE_H - BORDER_IN - 16
CONTENT_BOT = BORDER_IN + 28

BODY_SIZE = 11.6
BODY_LEAD = 16.6


# --------------------------------------------------------------------------
# DECORATIVE PRIMITIVES
# --------------------------------------------------------------------------


def draw_diamond(c, cx, cy, r, color, fill=True):
    p = c.beginPath()
    p.moveTo(cx, cy + r)
    p.lineTo(cx + r, cy)
    p.lineTo(cx, cy - r)
    p.lineTo(cx - r, cy)
    p.close()
    if fill:
        c.setFillColor(color)
        c.drawPath(p, fill=1, stroke=0)
    else:
        c.setStrokeColor(color)
        c.drawPath(p, fill=0, stroke=1)


def draw_coptic_cross(c, cx, cy, arm, color=RED):
    """An equal-armed Coptic cross: two solid overlapping bars forming a
    plus shape (not just hairline strokes -- a real filled body reads much
    better at large sizes), each of the four ends capped with a trefoil of
    three small filled dots (a "budded cross") -- the traditional Coptic
    Orthodox cross form, used as a finial on the title page and
    month-divider pages in place of a plain crossbar."""
    bar_w = arm * 0.26
    c.saveState()
    c.setFillColor(color)
    c.rect(cx - bar_w / 2, cy - arm, bar_w, 2 * arm, fill=1, stroke=0)
    c.rect(cx - arm, cy - bar_w / 2, 2 * arm, bar_w, fill=1, stroke=0)

    bud_r = bar_w * 0.62
    back = arm * 0.16  # how far the side buds sit back from the tip, toward center
    inset = bud_r * 1.15  # how far in from the stem centerline the side buds sit
    for dx, dy in [(0, 1), (0, -1), (-1, 0), (1, 0)]:
        tx, ty = cx + dx * arm, cy + dy * arm
        px, py = -dy, dx  # perpendicular to this arm, for the two side buds
        c.circle(tx, ty, bud_r, fill=1, stroke=0)
        bx, by = cx + dx * (arm - back), cy + dy * (arm - back)
        c.circle(bx + px * inset, by + py * inset, bud_r, fill=1, stroke=0)
        c.circle(bx - px * inset, by - py * inset, bud_r, fill=1, stroke=0)
    c.restoreState()


def draw_corner_mark(c, x, y, size, flip_x=1, flip_y=1):
    """A minimal line-art corner flourish: two nested quarter-curves and a
    small diamond tick, in red only."""
    c.saveState()
    c.translate(x, y)
    c.scale(flip_x, flip_y)
    c.setStrokeColor(RED)
    c.setLineWidth(1.0)
    p = c.beginPath()
    p.moveTo(2, 2)
    p.curveTo(size * 0.15, size * 0.55, size * 0.55, size * 0.15, size, 4)
    c.drawPath(p, fill=0, stroke=1)
    c.setLineWidth(0.6)
    p2 = c.beginPath()
    p2.moveTo(size * 0.18, size * 0.10)
    p2.curveTo(
        size * 0.28, size * 0.34, size * 0.44, size * 0.20, size * 0.56, size * 0.34
    )
    c.drawPath(p2, fill=0, stroke=1)
    draw_diamond(c, size * 0.95, 6, 2.6, RED)
    c.setFillColor(RED)
    c.circle(3, 3, 1.6, fill=1, stroke=0)
    c.restoreState()


def draw_page_frame(c):
    """A clean double-rule red border, light on ink: one bolder line and one
    hairline, joined by a small corner mark at each of the four corners."""
    c.saveState()
    c.setStrokeColor(RED)
    c.setLineWidth(1.3)
    c.rect(BORDER_OUT, BORDER_OUT, PAGE_W - 2 * BORDER_OUT, PAGE_H - 2 * BORDER_OUT)
    c.setLineWidth(0.5)
    c.rect(BORDER_IN, BORDER_IN, PAGE_W - 2 * BORDER_IN, PAGE_H - 2 * BORDER_IN)
    fs = 22
    draw_corner_mark(c, BORDER_OUT, BORDER_OUT, fs, 1, 1)
    draw_corner_mark(c, PAGE_W - BORDER_OUT, BORDER_OUT, fs, -1, 1)
    draw_corner_mark(c, BORDER_OUT, PAGE_H - BORDER_OUT, fs, 1, -1)
    draw_corner_mark(c, PAGE_W - BORDER_OUT, PAGE_H - BORDER_OUT, fs, -1, -1)
    c.restoreState()


def draw_running_header(c, season_label, page_no):
    c.saveState()
    c.setFont(BODY_ITALIC, 8.6)
    c.setFillColor(RED)
    c.drawCentredString(PAGE_W / 2, PAGE_H - BORDER_OUT + 10, season_label.upper())
    c.setFont(BODY_FONT, 8.5)
    c.setFillColor(INK)
    c.drawCentredString(PAGE_W / 2, BORDER_OUT - 16, str(page_no))
    c.restoreState()


def draw_rule_band(c, x, y, w, height=18):
    """A plain hairline rule spanning a title/season page, with a diamond
    tick at each end -- used above and below big display type in place of a
    filled ornament band."""
    c.saveState()
    c.setStrokeColor(RED)
    c.setLineWidth(0.9)
    c.line(x, y + height / 2, x + w, y + height / 2)
    draw_diamond(c, x + 5, y + height / 2, 3.6, RED)
    draw_diamond(c, x + w - 5, y + height / 2, 3.6, RED)
    c.restoreState()


def draw_headpiece(
    c, x, top_y, w, main_title, sub_title=None, height=68, title_size=None
):
    """
    A restrained title banner: a thin red rectangle (double rule), a small
    cross mark in the clear space above it, and the occasion title in bold
    red with an italic black subtitle beneath -- no fills, so it costs
    almost no ink. ``title_size`` overrides the title's starting (pre-fit)
    font size -- e.g. for a Major/Minor Feast's larger, subtitle-less title.
    """
    cross_space = 14
    box_top = top_y - cross_space
    box_h = height - cross_space
    y = box_top - box_h
    cx = x + w / 2

    c.saveState()
    c.setStrokeColor(RED)
    c.setLineWidth(1.2)
    c.rect(x, y, w, box_h, fill=0, stroke=1)
    c.setLineWidth(0.5)
    c.rect(x + 4, y + 4, w - 8, box_h - 8, fill=0, stroke=1)

    avail = w - 44
    if sub_title:
        size1 = title_size or 17
        while stringWidth(main_title, BODY_BOLD, size1) > avail and size1 > 9:
            size1 -= 0.5
        c.setFillColor(RED)
        c.setFont(BODY_BOLD, size1)
        c.drawCentredString(cx, y + box_h * 0.60, main_title)
        c.setFont(BODY_ITALIC, 10.6)
        c.setFillColor(INK)
        c.drawCentredString(cx, y + box_h * 0.28, sub_title)
    else:
        size1 = title_size or 19
        while stringWidth(main_title, BODY_BOLD, size1) > avail and size1 > 10:
            size1 -= 0.5
        c.setFillColor(RED)
        c.setFont(BODY_BOLD, size1)
        c.drawCentredString(cx, y + box_h / 2 - size1 * 0.32, main_title)

    draw_coptic_cross(c, x + 16, y + box_h / 2, 6)
    draw_coptic_cross(c, x + w - 16, y + box_h / 2, 6)
    c.restoreState()
    return y  # bottom of headpiece


def draw_section_label(c, x, y, w, text, small=None):
    """Small red rule + centered caption used for 'VESPERS / MATINS / LITURGY'.
    The gap in the rule is sized to the text itself (plus a fixed margin),
    not a fixed fraction of the content width -- otherwise a short word
    like "VESPERS" leaves a big empty gap around it while a long one like
    "THE DIVINE LITURGY" barely has room to breathe."""
    c.saveState()
    c.setFont(BODY_BOLD, 12)
    half_gap = stringWidth(text, BODY_BOLD, 12) / 2 + 14
    cx = x + w / 2
    c.setStrokeColor(RED)
    c.setLineWidth(0.8)
    c.line(x, y, cx - half_gap, y)
    c.line(cx + half_gap, y, x + w, y)
    draw_diamond(c, cx - half_gap + 7, y, 3.0, RED)
    draw_diamond(c, cx + half_gap - 7, y, 3.0, RED)
    c.setFillColor(RED)
    c.drawCentredString(cx, y - 4, text)
    if small:
        c.setFont(BODY_ITALIC, 9.3)
        c.setFillColor(INK)
        c.drawCentredString(x + w / 2, y - 18, small)
    c.restoreState()
    return y - (30 if small else 16)


def draw_reference_line(c, x, y, w, ref_text):
    c.saveState()
    c.setFont(BODY_ITALIC, 9.6)
    c.setFillColor(RED)
    c.drawCentredString(x + w / 2, y, ref_text)
    c.restoreState()
    return y - 15


def draw_small_caps(
    c, x, y, text, font=BODY_BOLD, big_size=14, small_size=10, color=RED
):
    """Draw `text` in small caps: every letter capitalized, but only the
    first letter of each word set at `big_size` -- the rest of that word
    runs at `small_size` on the same baseline. A word with no leading
    letter to make big -- a bare Coptic day number like the "14" in
    "Thout 14" -- is drawn entirely at `small_size` instead: letter-casing
    doesn't apply to digits, and singling out just its first digit as
    "big" (as a naive first-char/rest split would) reads as a mismatched
    font size, not a style. Returns the total width drawn, so callers can
    position whatever follows."""
    c.setFillColor(color)
    x0 = x
    for i, word in enumerate(text.upper().split(" ")):
        if i > 0:
            c.setFont(font, small_size)
            space_w = stringWidth(" ", font, small_size)
            x += space_w
        if not word:
            continue
        if not word[0].isalpha():
            c.setFont(font, small_size)
            c.drawString(x, y, word)
            x += stringWidth(word, font, small_size)
            continue
        first, rest = word[0], word[1:]
        c.setFont(font, big_size)
        c.drawString(x, y, first)
        x += stringWidth(first, font, big_size)
        if rest:
            c.setFont(font, small_size)
            c.drawString(x, y, rest)
            x += stringWidth(rest, font, small_size)
    return x - x0


def wrap_words(text, font, size, width):
    words = text.split()
    lines, cur = [], []
    for wd in words:
        trial = " ".join(cur + [wd])
        if stringWidth(trial, font, size) <= width or not cur:
            cur.append(wd)
        else:
            lines.append(cur)
            cur = [wd]
    if cur:
        lines.append(cur)
    return lines


def draw_plain_paragraph(
    book, text, x, w, font=BODY_FONT, size=BODY_SIZE, lead=BODY_LEAD, color=INK
):
    """Flow a paragraph line by line, breaking to a new page (via
    book.ensure_space) whenever a line would run past the bottom margin --
    so a reading longer than the remaining space on the current page
    continues cleanly on the next one instead of overrunning the border."""
    for line_words in wrap_words(text, font, size, w):
        book.ensure_space(lead)
        book.c.setFont(font, size)
        book.c.setFillColor(color)
        book.c.drawString(x, book.y, " ".join(line_words))
        book.y -= lead


def draw_dropcap_paragraph(
    book, text, x, w, cap_lines=3, font=BODY_FONT, size=BODY_SIZE, lead=BODY_LEAD
):
    """Flow a paragraph with an oversized red initial, like an illuminated
    Gospel incipit -- an outlined letter cell rather than a filled block, to
    keep the page ink-light. Paginates line by line like
    draw_plain_paragraph; only the first cap_lines lines run indented
    beside the initial."""
    text = text.strip().lstrip("\"'‘’“”")
    first_char, rest = text[0], text[1:].lstrip()

    cap_h = lead * cap_lines * 0.92
    cap_w = cap_h * 0.78
    gap = 8
    indent_x = x + cap_w + gap
    indent_w = w - cap_w - gap

    words = rest.split()
    lines, cur, li = [], [], 0
    while words:
        avail_w = indent_w if li < cap_lines else w
        wd = words[0]
        trial = " ".join(cur + [wd])
        if stringWidth(trial, font, size) <= avail_w or not cur:
            cur.append(words.pop(0))
        else:
            lines.append((li, cur))
            li += 1
            cur = []
    if cur:
        lines.append((li, cur))

    # Guarantee the whole cap block (its first cap_lines rows) fits before
    # drawing it, so it's never split across a page break.
    book.ensure_space(cap_h + lead * 0.2)
    top = book.y + lead * 0.78

    c = book.c
    c.saveState()
    c.setStrokeColor(RED)
    c.setLineWidth(0.9)
    c.rect(x, top - cap_h, cap_w, cap_h, fill=0, stroke=1)
    c.setFillColor(RED)
    c.setFont(BODY_BOLD, cap_h * 0.72)
    c.drawCentredString(x + cap_w / 2, top - cap_h * 0.74, first_char)
    c.restoreState()

    for li, lw in lines:
        book.ensure_space(lead)
        lx = indent_x if li < cap_lines else x
        book.c.setFont(font, size)
        book.c.setFillColor(INK)
        book.c.drawString(lx, book.y, " ".join(lw))
        book.y -= lead


# --------------------------------------------------------------------------
# PAGE-FLOW MANAGER
# --------------------------------------------------------------------------


class Book:
    def __init__(self, path):
        self.c = canvas.Canvas(path, pagesize=(PAGE_W, PAGE_H))
        self.season_label = ""
        self.page_no = 0
        self.y = CONTENT_TOP

    def new_page(self, season_label=None):
        if season_label is not None:
            self.season_label = season_label
        self.page_no += 1
        draw_page_frame(self.c)
        draw_running_header(self.c, self.season_label, self.page_no)
        self.y = CONTENT_TOP

    def ensure_space(self, needed):
        if self.y - needed < CONTENT_BOT:
            self.c.showPage()
            self.new_page()

    def save(self):
        self.c.showPage()
        self.c.save()
