"""Unit tests for evangelion.layout's drawing/layout logic -- as opposed to
tests/test_offline_scripture.py and friends, which check the *content* of a
fully rendered PDF. These check the drawing primitives directly: what font
size each character gets drawn at (draw_small_caps), how a paragraph's
words get split into lines (wrap_words), and the page-flow manager's own
bookkeeping (Book.ensure_space/new_page) -- without rendering, reading back,
or text-extracting an actual PDF.

draw_small_caps in particular is regression coverage for a real rendering
bug (see the ~/.claude memory "evangelion-draw-small-caps-digit-bug"): a
bare multi-digit number in small-caps text ("Thout 12") used to draw its
first digit at big_size and the rest at small_size, the same first-char/
rest split a real word gets -- since digits have no case, that read as a
mismatched font size, not a style. _FakeCanvas records exactly which
characters got drawn at which font/size, so these tests would catch that
regression (or a similar one) without needing to render a PDF and measure
glyph sizes from it.
"""

import io

from reportlab.pdfbase.pdfmetrics import stringWidth

from evangelion.fonts import BODY_BOLD, BODY_FONT
from evangelion.layout import CONTENT_TOP, Book, draw_small_caps, wrap_words


class _FakeCanvas:
    """A minimal stand-in for reportlab's Canvas, recording only what
    draw_small_caps actually calls: which (font, size) is active when each
    drawString happens. Not a real canvas -- stringWidth (used by
    draw_small_caps itself to advance x) still goes through reportlab's
    real font metrics, so the widths/positions this test doesn't check are
    still realistic; only the actual ink (font, size, text) is captured."""

    def __init__(self):
        self.calls = []  # (font, size, text)
        self._font = None
        self._size = None
        self.fill_colors = []

    def setFillColor(self, color):
        self.fill_colors.append(color)

    def setFont(self, font, size):
        self._font = font
        self._size = size

    def drawString(self, x, y, text):
        self.calls.append((self._font, self._size, text))


def _draw(text, **kwargs):
    c = _FakeCanvas()
    width = draw_small_caps(c, 0, 0, text, **kwargs)
    return c.calls, width


def test_draw_small_caps_single_word_big_first_letter_only():
    calls, _ = _draw("Thout", big_size=14, small_size=10)
    assert calls == [
        (BODY_BOLD, 14, "T"),
        (BODY_BOLD, 10, "HOUT"),
    ]


def test_draw_small_caps_multi_digit_number_stays_one_size():
    """The regression case: "12" must be drawn as a single call at
    small_size, never split into a big "1" and a small "2"."""
    calls, _ = _draw("Thout 12", big_size=14, small_size=10)
    assert calls == [
        (BODY_BOLD, 14, "T"),
        (BODY_BOLD, 10, "HOUT"),
        (BODY_BOLD, 10, "12"),
    ]


def test_draw_small_caps_single_digit_number_not_oversized():
    """A single-digit "word" ("5") has no `rest` for the old first-char/
    rest split to leave at small_size -- it must still land at small_size,
    not get promoted to big_size just because it was the whole "word"."""
    calls, _ = _draw("Thout 5", big_size=14, small_size=10)
    assert calls == [
        (BODY_BOLD, 14, "T"),
        (BODY_BOLD, 10, "HOUT"),
        (BODY_BOLD, 10, "5"),
    ]


def test_draw_small_caps_every_word_gets_its_own_big_letter():
    calls, _ = _draw("The First Sunday", big_size=14, small_size=10)
    assert calls == [
        (BODY_BOLD, 14, "T"),
        (BODY_BOLD, 10, "HE"),
        (BODY_BOLD, 14, "F"),
        (BODY_BOLD, 10, "IRST"),
        (BODY_BOLD, 14, "S"),
        (BODY_BOLD, 10, "UNDAY"),
    ]


def test_draw_small_caps_lowercases_are_upper_cased():
    calls, _ = _draw("thout", big_size=14, small_size=10)
    assert calls == [(BODY_BOLD, 14, "T"), (BODY_BOLD, 10, "HOUT")]


def test_draw_small_caps_single_letter_word_has_no_rest_call():
    calls, _ = _draw("I", big_size=14, small_size=10)
    assert calls == [(BODY_BOLD, 14, "I")]


def test_draw_small_caps_returns_total_drawn_width():
    _, width = _draw("Thout 12", big_size=14, small_size=10)
    expected = (
        stringWidth("T", BODY_BOLD, 14)
        + stringWidth("HOUT", BODY_BOLD, 10)
        + stringWidth(" ", BODY_BOLD, 10)
        + stringWidth("12", BODY_BOLD, 10)
    )
    assert width == expected


def test_draw_small_caps_default_font_and_color_used():
    c = _FakeCanvas()
    draw_small_caps(c, 0, 0, "Thout")
    assert c.calls[0][0] == BODY_BOLD
    assert c.fill_colors  # setFillColor was called at least once


def test_wrap_words_preserves_all_words_in_order():
    text = "In the beginning God created the heaven and the earth"
    lines = wrap_words(text, BODY_FONT, 11, 200)
    assert [w for line in lines for w in line] == text.split()


def test_wrap_words_no_line_exceeds_width_when_it_can_be_avoided():
    text = "In the beginning God created the heaven and the earth"
    width = 150
    lines = wrap_words(text, BODY_FONT, 11, width)
    for line in lines:
        if len(line) > 1:
            assert stringWidth(" ".join(line), BODY_FONT, 11) <= width


def test_wrap_words_single_overlong_word_placed_alone_not_dropped():
    """A word wider than `width` all by itself still gets its own line --
    wrap_words must not drop it or loop forever trying to fit it."""
    long_word = "Supercalifragilisticexpialidocious"
    lines = wrap_words(f"{long_word} end", BODY_FONT, 11, 5)
    assert lines[0] == [long_word]
    assert [w for line in lines for w in line] == [long_word, "end"]


def test_wrap_words_empty_text_returns_no_lines():
    assert wrap_words("", BODY_FONT, 11, 200) == []


def test_book_ensure_space_starts_new_page_when_it_does_not_fit():
    book = Book(io.BytesIO())
    book.new_page("Test Season")
    assert book.page_no == 1
    book.ensure_space(10**6)  # nothing on a real page is ever this tall
    assert book.page_no == 2
    assert book.y == CONTENT_TOP


def test_book_ensure_space_keeps_page_when_it_fits():
    book = Book(io.BytesIO())
    book.new_page("Test Season")
    assert book.page_no == 1
    book.ensure_space(1)
    assert book.page_no == 1


def test_book_new_page_increments_page_no_and_resets_y():
    book = Book(io.BytesIO())
    book.new_page("Test Season")
    book.y -= 200
    book.new_page()
    assert book.page_no == 2
    assert book.y == CONTENT_TOP


def test_book_new_page_keeps_season_label_when_omitted():
    book = Book(io.BytesIO())
    book.new_page("Thout")
    book.new_page()
    assert book.season_label == "Thout"
