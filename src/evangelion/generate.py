#!/usr/bin/env python3
"""
Generates a clean, print-friendly Gospel/Psalm lectionary booklet in the
style of Coptic Orthodox "Divine and Sacred Gospel" service books: red
rubric headers, a restrained red/black line-art border, a Crimson Text
serif, and enlarged drop-cap initials. Only the Psalm and Gospel of each
service are set (Vespers/Matins/Liturgy).

Builds from .cache/offline.sqlite3 (see evangelion.seed_offline_db) --
run `uv run evangelion-seed-offline` once first to build it (needs
network access, to fetch translation text; cached after that, same as
every other build). By default, occasions are every Major/Minor Feast
and every ordinary Sunday; pass --every-day for every day of the year
instead. Occasions fall in two sections, each internally chronological:
the Fixed Cycle (one divider per Coptic month), then the Moveable Cycle
(Great Lent, Holy Pascha, and Pentecost, dated by the Paschalion so their
Coptic day drifts year to year). A Sunday that's already a Major/Minor
Feast is listed once, not twice.

The Table of Contents lists every occasion with its real page number,
resolved by a throwaway measurement pass over the body before the real
render (page numbers depend on how long each occasion's readings run).

Run:
    uv run evangelion-seed-offline                 # once, to seed .cache/offline.sqlite3
    uv run evangelion                              # then build the book
    uv run evangelion --every-day                   # every day of the year
    uv run evangelion --db path/to/other.sqlite3    # a differently-seeded database
Output:
    output/the_holy_gospel_sundays.pdf, or output/the_holy_gospel_all.pdf
    with --every-day (or --output PATH; the directory is created
    automatically)
"""

import argparse
import io
from pathlib import Path

from reportlab.pdfbase.pdfmetrics import stringWidth

from evangelion.bible_source import split_harmony
from evangelion.festal_letters import festal_quote_for
from evangelion.fonts import BODY_BOLD, BODY_FONT, BODY_ITALIC
from evangelion.layout import (
    BODY_LEAD,
    BORDER_IN,
    CONTENT_L,
    CONTENT_R,
    CONTENT_W,
    INK,
    PAGE_H,
    PAGE_W,
    RED,
    Book,
    draw_coptic_cross,
    draw_diamond,
    draw_dropcap_paragraph,
    draw_headpiece,
    draw_page_frame,
    draw_plain_paragraph,
    draw_reference_line,
    draw_rule_band,
    draw_section_label,
    draw_small_caps,
    wrap_words,
)
from evangelion.psalm_numbering import septuagint_ref
from evangelion.seed_offline_db import DEFAULT_OUTPUT_DB, load_offline_seasons

# --------------------------------------------------------------------------
# HIGH-LEVEL PAGE BUILDERS
# --------------------------------------------------------------------------


def title_page(book):
    """Title page. Vertical placement is expressed as fractions of the
    content height (not fixed point offsets) so the composition stays
    balanced across page sizes -- this book is set at a custom 24x34cm trim,
    notably taller than US Letter, and fixed offsets tuned for Letter left
    large dead zones above and below the emblem at the larger size."""
    c = book.c
    draw_page_frame(c)
    cx = PAGE_W / 2
    top = PAGE_H - BORDER_IN
    bottom = BORDER_IN
    content_h = top - bottom

    draw_rule_band(
        c, BORDER_IN + 30, top - content_h * 0.075, PAGE_W - 2 * BORDER_IN - 60
    )

    c.setFillColor(RED)
    c.setFont(BODY_BOLD, 28)
    c.drawCentredString(cx, top - content_h * 0.135, "THE DIVINE AND SACRED GOSPEL")
    c.setFont(BODY_ITALIC, 14)
    c.setFillColor(INK)
    c.drawCentredString(
        cx, top - content_h * 0.158, "Readings for Vespers, Matins & the Divine Liturgy"
    )

    c.setStrokeColor(RED)
    c.setLineWidth(0.7)
    c.line(cx - 110, top - content_h * 0.174, cx + 110, top - content_h * 0.174)

    c.setFont(BODY_FONT, 12)
    c.setFillColor(INK)
    c.drawCentredString(
        cx,
        top - content_h * 0.198,
        "Arranged According to the Seasons of the Coptic Orthodox Church",
    )

    # A large Coptic cross with "IC XC / NI KA" set in its four quadrants --
    # the traditional Orthodox seal (as stamped on the prosphora/Communion
    # bread) rather than a ring emblem.
    my = bottom + content_h * 0.46
    arm = content_h * 0.14
    draw_coptic_cross(c, cx, my, arm)

    label_size = arm * 0.42
    dx, dy = arm * 0.95, arm * 0.78
    c.setFillColor(RED)
    c.setFont(BODY_BOLD, label_size)
    c.drawCentredString(cx - dx, my + dy, "IC")
    c.drawCentredString(cx + dx, my + dy, "XC")
    c.drawCentredString(cx - dx, my - dy - label_size * 0.3, "NI")
    c.drawCentredString(cx + dx, my - dy - label_size * 0.3, "KA")

    draw_rule_band(
        c, BORDER_IN + 30, bottom + content_h * 0.075, PAGE_W - 2 * BORDER_IN - 60
    )
    c.setFont(BODY_FONT, 10)
    c.setFillColor(INK)
    c.drawCentredString(cx, bottom + content_h * 0.05, "Compiled for Liturgical Use")
    c.showPage()


TOC_HEADER_ROW_H = 22
TOC_HEADER_GAP = 9  # extra air above every season header but the first
TOC_OCCASION_ROW_H = 15.5
TOC_BULLET_R = 1.7


def toc_page(book, seasons, season_pages=None, occasion_pages_map=None):
    """Draw a paginated Table of Contents: one small-caps season header --
    name, hairline rule, page number -- per season, then one diamond-bulleted,
    dotted-leader row per occasion. ``season_pages`` / ``occasion_pages_map``
    are {id(season|occasion): page_no} lookups from a prior measurement pass
    (see measure_page_numbers); when omitted the page number column is left
    blank -- used for the measurement pass itself, so it consumes exactly
    the same number of pages as the real one will."""
    season_pages = season_pages or {}
    occasion_pages_map = occasion_pages_map or {}

    book.new_page("Table of Contents")
    c = book.c
    bottom = draw_headpiece(
        c,
        CONTENT_L,
        book.y,
        CONTENT_W,
        "TABLE OF CONTENTS",
        "Order of Readings",
        height=68,
    )
    book.y = bottom - 28

    for i, season in enumerate(seasons):
        if i > 0:
            book.y -= TOC_HEADER_GAP
        book.ensure_space(TOC_HEADER_ROW_H)

        name_w = draw_small_caps(
            c,
            CONTENT_L,
            book.y,
            season["name"],
            font=BODY_BOLD,
            big_size=15,
            small_size=11,
            color=RED,
        )

        page_str = str(season_pages.get(id(season), ""))
        c.setFont(BODY_BOLD, 10)
        pagenum_w = stringWidth(page_str, BODY_BOLD, 10)

        rule_x1 = CONTENT_L + name_w + 10
        rule_x2 = CONTENT_R - pagenum_w - 10
        if rule_x2 > rule_x1:
            c.setStrokeColor(RED)
            c.setLineWidth(0.7)
            c.line(rule_x1, book.y + 3.5, rule_x2, book.y + 3.5)

        c.setFillColor(RED)
        c.drawRightString(CONTENT_R, book.y, page_str)
        book.y -= TOC_HEADER_ROW_H

        for occ in season["occasions"]:
            book.ensure_space(TOC_OCCASION_ROW_H)
            page_str = str(occasion_pages_map.get(id(occ), ""))

            draw_diamond(c, CONTENT_L + 5, book.y + 3, TOC_BULLET_R, RED)

            row_x = CONTENT_L + 15
            row_x += draw_small_caps(
                c,
                row_x,
                book.y,
                occ["title"],
                font=BODY_FONT,
                big_size=10.4,
                small_size=7.9,
                color=INK,
            )

            pagenum_w = stringWidth(page_str, BODY_ITALIC, 9)
            leader_x1 = row_x + 6
            leader_x2 = CONTENT_R - pagenum_w - 4
            if leader_x2 > leader_x1:
                c.setStrokeColor(RED)
                c.setDash(0.8, 2.4)
                c.setLineWidth(0.6)
                c.line(leader_x1, book.y + 3, leader_x2, book.y + 3)
                c.setDash()

            c.setFont(BODY_ITALIC, 9)
            c.setFillColor(RED)
            c.drawRightString(CONTENT_R, book.y, page_str)
            book.y -= TOC_OCCASION_ROW_H

    c.showPage()


def season_divider(book, season):
    """Coptic-month divider page: a Coptic-cross ornament, the month name
    in large type, and a long excerpt from a Festal Letter of St. Athanasius
    (or another Pope of Alexandria -- see evangelion.festal_letters) --
    flowed top-down with the Book's normal page-aware cursor, so a long
    quote paginates safely instead of risking overflow."""
    book.new_page(season["name"])
    start_page = book.page_no
    c = book.c
    cx = PAGE_W / 2

    book.y -= 26
    draw_coptic_cross(c, cx, book.y, 15)
    book.y -= 40

    draw_rule_band(c, BORDER_IN + 40, book.y, PAGE_W - 2 * BORDER_IN - 80)
    book.y -= 36

    c.setFillColor(RED)
    title_size = 36
    wrap_w = CONTENT_W - 80

    def _wrapped_lines(size):
        lines = wrap_words(season["name"].upper(), BODY_BOLD, size, wrap_w)
        widest = max(stringWidth(" ".join(line), BODY_BOLD, size) for line in lines)
        return lines, widest

    wrapped, widest = _wrapped_lines(title_size)
    while (len(wrapped) > 2 or widest > wrap_w) and title_size > 20:
        title_size -= 1
        wrapped, widest = _wrapped_lines(title_size)
    c.setFont(BODY_BOLD, title_size)
    for line in wrapped:
        c.drawCentredString(cx, book.y, " ".join(line))
        book.y -= title_size + 6
    book.y += 6

    draw_rule_band(c, BORDER_IN + 40, book.y - 14, PAGE_W - 2 * BORDER_IN - 80)
    book.y -= 54

    quote = festal_quote_for(season["name"])
    if quote:
        indent = 55
        draw_plain_paragraph(
            book,
            f"“{quote['text']}”",
            CONTENT_L + indent,
            CONTENT_W - 2 * indent,
            font=BODY_ITALIC,
            size=12.5,
            lead=18.5,
            color=INK,
        )
        book.y -= 10
        c.setFont(BODY_BOLD, 10)
        c.setFillColor(RED)
        c.drawRightString(
            CONTENT_R - indent,
            book.y,
            f"— {quote['author']}, {quote['source']}".upper(),
        )
        book.y -= 10

    book.y -= 16
    draw_rule_band(c, BORDER_IN + 30, book.y, PAGE_W - 2 * BORDER_IN - 60)
    c.showPage()
    return start_page


# service -> ordered list of (kind, label, style); style is 'verse' (short
# italic quotation, e.g. a Psalm) or 'gospel' (drop-cap incipit).
SERVICE_ORDER = [
    (
        "vespers",
        "VESPERS",
        [("psalm", "Psalm", "verse"), ("gospel", "Gospel", "gospel")],
    ),
    ("matins", "MATINS", [("psalm", "Psalm", "verse"), ("gospel", "Gospel", "gospel")]),
    (
        "liturgy",
        "THE DIVINE LITURGY",
        [("psalm", "Psalm", "verse"), ("gospel", "Gospel", "gospel")],
    ),
]


def labeled_pieces(reading_label, style, entry):
    """Expand one SERVICE_ORDER (reading_label, style, entry) slot into the
    actual (label, style, piece) reading(s) occasion_pages draws for it.
    `entry` is normally a single {"ref","text"} dict, or a list of them
    where a service interleaves a Psalm verse partway through a Gospel
    harmony (see evangelion.seed_offline_db). Each is further split by book
    via bible_source.split_harmony where its ref spans more than one. A
    piece whose ref turns out to be a Psalm verse is relabeled as a Psalm
    rather than inheriting the Gospel slot's label/style."""
    if not entry:
        return
    for one_entry in entry if isinstance(entry, list) else [entry]:
        if not one_entry:
            continue
        for piece in split_harmony(one_entry):
            if not piece:
                continue
            if piece["ref"].startswith("Psalm"):
                yield "Psalm", "verse", piece
            else:
                yield reading_label, style, piece


def _capitalize_first(text):
    """Uppercase just the first letter of `text`, leaving everything else
    untouched -- a Psalm reading is often a verse *range* starting
    mid-sentence in the source translation (e.g. a verse continuing a
    previous verse's clause, "and wine makes glad..."), but is presented
    here as its own standalone quotation, so it should still open with a
    capital regardless of what the source translation's own verse text
    happened to start with. Deliberately not str.capitalize() -- that
    also lowercases the rest of the string, which would mangle "LORD"
    and other legitimate all-caps text elsewhere in the verse."""
    for i, ch in enumerate(text):
        if ch.isalpha():
            return text[:i] + ch.upper() + text[i + 1 :]
    return text


def draw_labeled_reading(book, label, entry, style):
    if not entry or not entry.get("text"):
        return
    needed = BODY_LEAD * (4 if style == "gospel" else 2)
    book.ensure_space(needed)
    book.c.setFont(BODY_BOLD, 9.8)
    book.c.setFillColor(RED)
    book.c.drawString(CONTENT_L, book.y, label)
    ref = septuagint_ref(entry["ref"]) if label == "Psalm" else entry["ref"]
    book.y = draw_reference_line(book.c, CONTENT_L, book.y, CONTENT_W, ref)

    if style == "gospel":
        # Extra clearance so the drop-cap box doesn't crash into the label
        # row's descenders (e.g. the "p" in "Gospel").
        book.y -= 6
        paragraphs = entry["text"].split("\n\n")
        first = True
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            if first:
                draw_dropcap_paragraph(book, para, CONTENT_L, CONTENT_W)
                first = False
            else:
                draw_plain_paragraph(book, para, CONTENT_L, CONTENT_W)
            book.y -= 6
        book.y -= 10
    else:  # verse
        draw_plain_paragraph(
            book,
            _capitalize_first(entry["text"]),
            CONTENT_L,
            CONTENT_W,
            font=BODY_ITALIC,
            size=11,
            lead=14.4,
            color=INK,
        )
        book.y -= 8


def occasion_pages(book, season, occasion):
    book.new_page(season["name"])
    start_page = book.page_no
    c = book.c
    if occasion.get("category") in ("major", "minor"):
        # One of the Coptic Church's seven Major or seven Minor Feasts of
        # the Lord: its own name carries the day, so skip the subtitle
        # entirely and let the title run larger in the space it frees up.
        subtitle, title_size = None, 24
    else:
        subtitle, title_size = season["name"], None
    bottom = draw_headpiece(
        c,
        CONTENT_L,
        book.y,
        CONTENT_W,
        occasion["title"].upper(),
        subtitle,
        height=68,
        title_size=title_size,
    )
    book.y = bottom - 26

    for key, label, readings in SERVICE_ORDER:
        svc = occasion["services"].get(key)
        if not svc:
            continue
        book.ensure_space(70)
        book.y = draw_section_label(book.c, CONTENT_L, book.y, CONTENT_W, label)
        for kind, reading_label, style in readings:
            entry = svc.get(kind)
            for piece_label, piece_style, piece in labeled_pieces(
                reading_label, style, entry
            ):
                draw_labeled_reading(book, piece_label, piece, piece_style)

    c.showPage()
    return start_page


# --------------------------------------------------------------------------
# MAIN
# --------------------------------------------------------------------------


def measure_page_numbers(seasons):
    """Render the body (season dividers + occasion pages) once to a
    throwaway in-memory PDF -- preceded by a same-length blank-page-number
    TOC, so the offset matches the real document -- just to learn which
    page number each season divider and occasion actually lands on. Page
    numbers depend on how long each occasion's readings run, so there's no
    way to know them before laying the body out at least once."""
    book = Book(io.BytesIO())
    title_page(book)
    toc_page(book, seasons)
    season_pages, occasion_pages_map = {}, {}
    for season in seasons:
        season_pages[id(season)] = season_divider(book, season)
        for occ in season["occasions"]:
            occasion_pages_map[id(occ)] = occasion_pages(book, season, occ)
    book.save()
    return season_pages, occasion_pages_map


def build(output_path=None, every_day=False, db_path=None):
    if output_path is None:
        output_path = f"output/the_holy_gospel_{'all' if every_day else 'sundays'}.pdf"
    if not Path(db_path or DEFAULT_OUTPUT_DB).exists():
        raise SystemExit(
            f"No lectionary database at {db_path or DEFAULT_OUTPUT_DB} -- "
            "run `uv run evangelion-seed-offline` first to build it "
            "(needs network access, to fetch translation text)."
        )
    kwargs = {"db_path": db_path} if db_path else {}
    seasons = load_offline_seasons(every_day=every_day, **kwargs)

    season_pages, occasion_pages_map = measure_page_numbers(seasons)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    book = Book(output_path)
    title_page(book)
    toc_page(book, seasons, season_pages, occasion_pages_map)
    for season in seasons:
        season_divider(book, season)
        for occ in season["occasions"]:
            occasion_pages(book, season, occ)
    book.save()
    print(f"Wrote {output_path}")


def main():
    ap = argparse.ArgumentParser(
        description="Build the ornate Coptic Gospel lectionary PDF."
    )
    ap.add_argument(
        "--output",
        default=None,
        help="Output PDF path (default: output/the_holy_gospel_sundays.pdf, or "
        "output/the_holy_gospel_all.pdf with --every-day).",
    )
    ap.add_argument(
        "--every-day",
        action="store_true",
        help="Print every day of the year, not just Sundays and Major/Minor Feasts.",
    )
    ap.add_argument(
        "--db",
        default=None,
        help="SQLite database to build from (default: .cache/offline.sqlite3, "
        "built by `uv run evangelion-seed-offline`). Point this at a database "
        "seeded with different --psalm-source/--gospel-source options (see "
        "`uv run evangelion-seed-offline --help`) to build from those instead.",
    )
    args = ap.parse_args()

    build(
        output_path=args.output,
        every_day=args.every_day,
        db_path=args.db,
    )


if __name__ == "__main__":
    main()
