"""Unit tests for evangelion.bible_source's reference-parsing and USFX-
parsing logic, against small synthetic fixtures -- no network access, no
real BibleUKJV/ASV/Brenton download, and (mostly) not even the real zip
file formats. Complements the full-book integration tests elsewhere (which
exercise this code against real translation text) with fast, precise
coverage of the specific edge cases this module has actually gotten wrong
during development -- especially _parse_usfx, the single most-revised
piece of code this project has had (see the ~/.claude memory
"evangelion-brenton-psalm-title-bug" for the two wrong attempts before the
real fix).
"""

import pytest

from evangelion.bible_source import (
    FULL_BOOK_NAME,
    UsfxBibleText,
    _BibleTextBase,
    _display_ref,
    _parse_usfx,
    split_harmony,
)


class _FakeBible(_BibleTextBase):
    """A tiny in-memory translation for testing parse_ref/_expand_range/
    text_for_ref in isolation, independent of any real translation's file
    format or the network."""

    def __init__(self, chapters):
        # {(book, chapter): {verse: text}}
        self._chapters = chapters

    def _knows_book(self, book):
        return any(b == book for b, _ in self._chapters)

    def verse(self, book, chapter, verse):
        try:
            return self._chapters[(book, chapter)][verse]
        except KeyError:
            raise ValueError(f"No {book} {chapter}:{verse}") from None

    def verse_count(self, book, chapter):
        try:
            return max(self._chapters[(book, chapter)])
        except KeyError:
            raise ValueError(f"No {book} chapter {chapter}") from None


@pytest.fixture
def bible():
    return _FakeBible(
        {
            ("Psalm", 1): {1: "one", 2: "two", 3: "three", 4: "four", 5: "five"},
            ("Psalm", 2): {1: "psalm two verse one"},
            ("Matthew", 1): {1: "Matt 1:1", 2: "Matt 1:2", 3: "Matt 1:3"},
            ("Matthew", 2): {1: "Matt 2:1", 2: "Matt 2:2"},
            ("Mark", 1): {1: "Mark 1:1", 2: "Mark 1:2"},
        }
    )


# --------------------------------------------------------------------------
# parse_ref / _expand_range
# --------------------------------------------------------------------------


def test_parse_ref_single_verse(bible):
    assert bible.parse_ref("Psalm 1:3") == [("Psalm", 1, 3)]


def test_parse_ref_range_within_chapter(bible):
    assert bible.parse_ref("Psalm 1:2-4") == [
        ("Psalm", 1, 2),
        ("Psalm", 1, 3),
        ("Psalm", 1, 4),
    ]


def test_parse_ref_comma_extra_verse_preserves_order(bible):
    # Deliberately out of numeric order -- some readings quote like this.
    assert bible.parse_ref("Psalm 1:4, 2") == [("Psalm", 1, 4), ("Psalm", 1, 2)]


def test_parse_ref_crosses_chapter_boundary(bible):
    assert bible.parse_ref("Matthew 1:2-2:1") == [
        ("Matthew", 1, 2),
        ("Matthew", 1, 3),
        ("Matthew", 2, 1),
    ]


def test_parse_ref_open_ended_dash_fills_to_last_verse(bible):
    assert bible.parse_ref("Psalm 1:3—") == [
        ("Psalm", 1, 3),
        ("Psalm", 1, 4),
        ("Psalm", 1, 5),
    ]


def test_parse_ref_accepts_trailing_period_after_book(bible):
    assert bible.parse_ref("Matthew. 1:1") == [("Matthew", 1, 1)]


def test_parse_ref_accepts_whitespace_around_colon(bible):
    assert bible.parse_ref("Psalm 1 : 3") == [("Psalm", 1, 3)]


def test_parse_ref_unrecognized_format_raises(bible):
    with pytest.raises(ValueError, match="Unrecognized"):
        bible.parse_ref("not a reference")


def test_expand_range_overshoot_raises_instead_of_looping(bible):
    """Psalm 1 only has 5 verses -- a range asking for verse 9 must raise
    cleanly, not search indefinitely into later chapters."""
    with pytest.raises(ValueError, match="never reaches"):
        bible.parse_ref("Psalm 1:2-9")


# --------------------------------------------------------------------------
# text_for_ref
# --------------------------------------------------------------------------


def test_text_for_ref_single_segment(bible):
    assert bible.text_for_ref("Psalm 1:1") == "one"


def test_text_for_ref_joins_multiple_segments_with_space(bible):
    assert bible.text_for_ref("Psalm 1:1 & Psalm 1:3") == "one three"


def test_text_for_ref_shorthand_segment_inherits_previous_book(bible):
    """A later segment can drop the book name ("Psalm 1:1 & 1:3"), but
    still needs its own chapter:verse."""
    assert bible.text_for_ref("Psalm 1:1 & 1:3") == "one three"


def test_text_for_ref_crosses_books(bible):
    assert bible.text_for_ref("Psalm 1:1 & Matthew 1:1") == "one Matt 1:1"


def test_text_for_ref_first_segment_names_no_book_raises(bible):
    with pytest.raises(ValueError, match="names no book"):
        bible.text_for_ref("1:1")


def test_text_for_ref_drops_empty_verse_without_stray_space(bible):
    """A verse can be genuinely, deliberately empty (a Brenton Psalm title
    verse -- see _parse_usfx) rather than missing; joining across it must
    not leave a double space."""
    b = _FakeBible({("Psalm", 9): {1: "", 2: "real content"}})
    assert b.text_for_ref("Psalm 9:1-2") == "real content"


# --------------------------------------------------------------------------
# _parse_usfx
# --------------------------------------------------------------------------

_USFX_HEADER = '<?xml version="1.0"?><usfx>'
_USFX_FOOTER = "</usfx>"


def _usfx(book_body, book_id="PSA"):
    return f'{_USFX_HEADER}<book id="{book_id}">{book_body}</book>{_USFX_FOOTER}'


def test_parse_usfx_title_only_verse_is_empty_not_missing():
    """Most psalms: <d> closes with its own <ve/> -- the title genuinely
    *is* the whole of verse 1, and it's excluded, leaving "" rather than
    no entry at all."""
    xml = _usfx(
        '<c id="1" />'
        '<d style="d"><v id="1" bcv="PSA.1.1" />A title only.\n<ve /></d>'
        '<p style="p"><v id="2" bcv="PSA.1.2" />Real verse two.\n<ve /></p>'
    )
    verses = {}
    _parse_usfx(xml, verses)
    assert verses[("PSA", 1)][1] == ""
    assert verses[("PSA", 1)][2] == "Real verse two."


def test_parse_usfx_title_merged_with_content_drops_only_title():
    """A few psalms (e.g. real Brenton Psalm 95): the <v id="1"> milestone
    stays open across the </d> boundary, so the real opening line follows
    right after the title under the same verse -- only the title portion
    should be excluded, not the real content after it."""
    xml = _usfx(
        '<c id="1" />'
        '<d style="d"><v id="1" bcv="PSA.1.1" />A title.\n</d>'
        '<p style="p">Real opening line.\n<ve />'
        '<v id="2" bcv="PSA.1.2" />Verse two.\n<ve /></p>'
    )
    verses = {}
    _parse_usfx(xml, verses)
    assert verses[("PSA", 1)][1] == "Real opening line."


def test_parse_usfx_two_verse_title_both_excluded():
    """A handful of psalms split a longer historical title across two <v>
    milestones, both still inside <d> -- both must be empty, and the real
    content starts fresh at verse 3."""
    xml = _usfx(
        '<c id="1" />'
        '<d style="d"><v id="1" bcv="PSA.1.1" />Part one.\n<ve />'
        '<v id="2" bcv="PSA.1.2" />Part two.\n<ve /></d>'
        '<p style="p"><v id="3" bcv="PSA.1.3" />Real content.\n<ve /></p>'
    )
    verses = {}
    _parse_usfx(xml, verses)
    assert verses[("PSA", 1)][1] == ""
    assert verses[("PSA", 1)][2] == ""
    assert verses[("PSA", 1)][3] == "Real content."


def test_parse_usfx_excludes_footnotes_and_cross_references():
    xml = _usfx(
        '<c id="1" />'
        '<v id="1" bcv="PSA.1.1" />Before'
        '<f caller="+"><fr>1.1</fr><ft>a footnote</ft></f>'
        " after"
        '<x caller="+"><xt>a cross-ref</xt></x>'
        ".\n<ve />"
    )
    verses = {}
    _parse_usfx(xml, verses)
    text = verses[("PSA", 1)][1]
    assert "footnote" not in text
    assert "cross-ref" not in text
    assert text == "Before after."


def test_parse_usfx_includes_supplied_word_and_small_caps_wrappers():
    xml = _usfx(
        '<c id="1" />'
        '<v id="1" bcv="PSA.1.1" />The <add>LORD</add> said <sc>selah</sc>.\n<ve />'
    )
    verses = {}
    _parse_usfx(xml, verses)
    assert verses[("PSA", 1)][1] == "The LORD said selah."


def test_parse_usfx_folds_sub_verse_ids_into_base_verse():
    """Some editions split one verse across several <v> milestones for
    versification differences (id "12a", "12b", ...) -- these fold back
    into the base verse number, concatenated in document order."""
    xml = _usfx(
        '<c id="1" />'
        '<v id="4a" bcv="PSA.1.4" />Part A.\n'
        '<v id="4b" bcv="PSA.1.4" />Part B.\n<ve />'
    )
    verses = {}
    _parse_usfx(xml, verses)
    assert verses[("PSA", 1)][4] == "Part A. Part B."


def test_parse_usfx_multiple_chapters():
    xml = _usfx(
        '<c id="1" /><v id="1" bcv="PSA.1.1" />Chapter one.\n<ve />'
        '<c id="2" /><v id="1" bcv="PSA.2.1" />Chapter two.\n<ve />'
    )
    verses = {}
    _parse_usfx(xml, verses)
    assert verses[("PSA", 1)][1] == "Chapter one."
    assert verses[("PSA", 2)][1] == "Chapter two."


def test_usfx_bible_text_end_to_end(tmp_path):
    """UsfxBibleText's own constructor (zip + xml name), not just the
    lower-level _parse_usfx function."""
    import zipfile

    xml = _usfx('<c id="1" /><v id="1" bcv="PSA.1.1" />Hello world.\n<ve />')
    zip_path = tmp_path / "fake.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("fake.xml", xml)
    b = UsfxBibleText(str(zip_path), "fake.xml")
    assert b.verse("Psalm", 1, 1) == "Hello world."


# --------------------------------------------------------------------------
# split_harmony
# --------------------------------------------------------------------------


def test_split_harmony_single_book_returns_entry_unchanged(bible):
    entry = {"ref": "Psalm 1:1 & Psalm 1:2", "text": "whatever paraphrase"}
    assert split_harmony(entry, bible=bible) == [entry]


def test_split_harmony_splits_multi_book_paragraph(bible):
    entry = {
        "ref": "Matthew 1:1 & Mark 1:1",
        "text": "Matt 1:1 Mark 1:1",  # a "paraphrase" that happens to align cleanly
    }
    pieces = split_harmony(entry, bible=bible)
    assert len(pieces) == 2
    assert pieces[0]["ref"] == "Matthew 1:1"
    assert pieces[1]["ref"] == "Mark 1:1"
    assert "Matt 1:1" in pieces[0]["text"]
    assert "Mark 1:1" in pieces[1]["text"]


def test_split_harmony_falls_back_when_bible_cannot_resolve_segment(bible):
    entry = {"ref": "Matthew 1:1 & John 1:1", "text": "some paragraph"}
    # `bible` fixture doesn't know "John" -- text_for_ref should raise and
    # split_harmony should fall back to returning the entry unchanged.
    assert split_harmony(entry, bible=bible) == [entry]


# --------------------------------------------------------------------------
# _display_ref
# --------------------------------------------------------------------------


def test_display_ref_expands_abbreviation():
    assert _display_ref("Mt 21:1-17", "Mt") == "Matthew 21:1-17"


def test_display_ref_leaves_full_name_unchanged():
    assert _display_ref("Psalm 80:3", "Psalm") == "Psalm 80:3"


def test_full_book_name_covers_every_book_files_abbreviation():
    """Every abbreviation split_harmony might encounter has a display
    name -- otherwise _display_ref silently falls back to the raw
    abbreviation instead of expanding it."""
    for abbrev in ("Mt", "Matt", "Mk", "Lk", "LK", "Jn", "JN", "Psalm"):
        assert abbrev in FULL_BOOK_NAME
