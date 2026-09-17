"""Shared PDF-section-parsing helpers for test_offline_scripture.py: parses
(label, reference, body) sections directly out of a rendered book's own
extracted text -- the same way a reader would, not from any data source
that fed the render -- and checks each section's body against the real
public-domain translation text for its reference.
"""

import re

from evangelion.psalm_numbering import masoretic_ref

LABELS = ("Psalm", "Gospel")
SECTION_HEADERS = ("VESPERS", "MATINS", "THE DIVINE LITURGY")
SECTION_START_RE = re.compile(r"(?m)^(Psalm|Gospel)\n(.+)$")
NEXT_SECTION_RE = re.compile(r"(?m)^(?:" + "|".join(LABELS + SECTION_HEADERS) + r")$")
# A reading that's the last one before a season divider or a new occasion's
# own headpiece (rather than another reading on the same occasion's page)
# has no next Psalm/Gospel/service-header line to stop NEXT_SECTION_RE at
# until the *following* occasion's -- both a divider's own big title (e.g.
# "APIP") and an occasion's headpiece title (e.g. "THE FIRST SUNDAY OF
# APIP") are their own all-caps line, though, distinct from this book's
# only other all-caps-only lines: a drop-cap paragraph's own first letter,
# always exactly one character alone on its line. TITLE_LINE_RE matches the
# former (3+ letters) and not the latter, so it's a second, earlier place
# to stop looking for a body's end.
TITLE_LINE_RE = re.compile(r"(?m)^[A-Z][A-Z '—-]{2,}$")
WORD_RE = re.compile(r"[A-Za-z']+")

# The two chapters Septuagint numbering merges two Masoretic psalms into
# (see evangelion.psalm_numbering's module docstring) are inherently
# ambiguous to invert -- masoretic_ref()/_mt_chapter() picks the lower half
# of the pair, but the higher half is an equally valid candidate.
_AMBIGUOUS_MT_ALTERNATE = {9: 10, 10: 9, 114: 115, 115: 114}
_CHAPTER_RE = re.compile(r"(?<=Psalm )\d+")


def words(text):
    return [w.lower() for w in WORD_RE.findall(text)]


def find_sections(text):
    """Yield (label, ref, body_start) for every "Psalm"/"Gospel" section
    start in `text` -- a label line immediately followed by its reference
    line."""
    for m in SECTION_START_RE.finditer(text):
        yield m.group(1), m.group(2).strip(), m.end()


def section_body(text, body_start):
    """The text of one section, from just after its reference line to
    whichever comes first: the next section/service-header line, the next
    all-caps title line (see TITLE_LINE_RE), or the end of `text`. Assumes
    per-page running headers/page numbers have already been stripped from
    `text` (see conftest.py's _page_text)."""
    ends = [
        m.start()
        for m in (
            NEXT_SECTION_RE.search(text, body_start),
            TITLE_LINE_RE.search(text, body_start),
        )
        if m
    ]
    return text[body_start : min(ends) if ends else len(text)]


def lookup_candidates(label, ref):
    """Candidate Masoretic references to try looking a section's text up
    under, best first. For a Gospel, just `ref` itself. For a Psalm: first,
    the normal reading -- un-Septuagint the printed reference once, the way
    evangelion.generate itself Septuagint'd it going the other direction --
    then a second candidate for the case where a reference was already
    Septuagint-numbered before evangelion.generate got to it, so it needs a
    second inversion; then, for either of those that landed on one of the
    two merge-ambiguous chapters, one more candidate trying the other half
    of that merge. Harmless (just an unused extra candidate) for a
    consistently Masoretic-numbered source; only actually needed for a
    handful of inconsistently-numbered citations in the lectionary
    structure data (see evangelion.seed_offline_db's docstring)."""
    if label != "Psalm":
        return [ref]
    candidates = []
    for c in (masoretic_ref(ref), masoretic_ref(masoretic_ref(ref))):
        if c not in candidates:
            candidates.append(c)
    for c in list(candidates):
        m = _CHAPTER_RE.search(c)
        alt_chapter = m and _AMBIGUOUS_MT_ALTERNATE.get(int(m.group()))
        if alt_chapter:
            alt = _CHAPTER_RE.sub(str(alt_chapter), c)
            if alt not in candidates:
                candidates.append(alt)
    return candidates
