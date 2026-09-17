"""Convert Masoretic/KJV Psalm numbering -- what this project's own
lectionary data uses -- to the Septuagint (LXX) numbering the Coptic
Church uses liturgically.

For most psalms this is a simple "chapter minus one" shift, but three spots
merge or split relative to the Masoretic text, per the standard MT<->LXX
concordance table:

    MT 1-8     = LXX 1-8       (unchanged)
    MT 9-10    = LXX 9         (two MT psalms merge into one)
    MT 11-113  = LXX 10-112    (shift down by 1)
    MT 114-115 = LXX 113       (two MT psalms merge into one)
    MT 116     = LXX 114-115   (one MT psalm splits at verse 9/10)
    MT 117-146 = LXX 116-145   (shift down by 1)
    MT 147     = LXX 146-147   (one MT psalm splits at verse 11/12)
    MT 148-150 = LXX 148-150   (unchanged)

Only the chapter number is renumbered; verse numbers are left as scraped.
For the two merged chapters (9/10 and 114/115) there's no single agreed
verse-for-verse correspondence, so re-numbering verses there would just be
another approximation -- out of scope for a citation shift.
"""

import re

# The "Psalm" word is required on the first "&"-joined segment (that's how
# a caller already knows this is a Psalm reference at all -- see
# septuagint_ref()'s docstring), but optional on a later one, e.g.
# "Psalm 17:3 & 17:5".
_SEGMENT_RE = re.compile(r"^(?:Psalm\s+)?(\d+)\s*:\s*(.*)$")
_FIRST_NUM_RE = re.compile(r"\d+")


def _lxx_chapter(mt_chapter, first_verse):
    if mt_chapter <= 9:
        return mt_chapter
    if mt_chapter == 10:
        return 9
    if mt_chapter <= 113:
        return mt_chapter - 1
    if mt_chapter <= 115:
        return 113
    if mt_chapter == 116:
        return 114 if first_verse is not None and first_verse <= 9 else 115
    if mt_chapter <= 146:
        return mt_chapter - 1
    if mt_chapter == 147:
        return 146 if first_verse is not None and first_verse <= 11 else 147
    return mt_chapter


def septuagint_ref(ref):
    """Convert a Masoretic/KJV-numbered Psalm reference (e.g. "Psalm
    96:1-2", or several joined with " & " like "Psalm 65:11 & Psalm
    81:1") to Septuagint (LXX) numbering. Text that isn't a recognized
    "Psalm N:verses" segment is passed through unchanged."""
    if not ref:
        return ref
    segments = re.split(r"\s*&\s*", ref)
    out = []
    for seg in segments:
        m = _SEGMENT_RE.match(seg.strip())
        if not m:
            out.append(seg)
            continue
        chapter, verses = int(m.group(1)), m.group(2)
        first = _FIRST_NUM_RE.search(verses)
        first_verse = int(first.group()) if first else None
        out.append(f"Psalm {_lxx_chapter(chapter, first_verse)}:{verses}")
    return " & ".join(out)


def _mt_chapter(lxx_chapter):
    """Invert _lxx_chapter() at the chapter level. Best-effort at the two
    chapters Septuagint numbering merges two Masoretic psalms into (LXX 9 =
    MT 9 or 10; LXX 113 = MT 114 or 115) -- picks the lower/first of the
    pair, since which verse (and so which of the two) is unrecoverable from
    the chapter number alone. Both of a split psalm's LXX chapters (114/115
    from MT 116; 146/147 from MT 147) map back to the one MT chapter
    unambiguously, no guessing needed."""
    if lxx_chapter <= 8:
        return lxx_chapter
    if lxx_chapter == 9:
        return 9
    if lxx_chapter <= 112:
        return lxx_chapter + 1
    if lxx_chapter == 113:
        return 114
    if lxx_chapter <= 115:
        return 116
    if lxx_chapter <= 145:
        return lxx_chapter + 1
    if lxx_chapter <= 147:
        return 147
    return lxx_chapter


def masoretic_ref(ref):
    """Invert septuagint_ref(): convert a Septuagint-numbered Psalm
    reference -- as printed in the book -- back to Masoretic/KJV numbering,
    so its text can be looked up in a Masoretic-numbered source (see
    evangelion.bible_source). Only usable for round-tripping a reference
    septuagint_ref() itself produced (see _mt_chapter's docstring for the
    two chapters it can't invert exactly); verse numbers are unchanged,
    same as the forward
    direction."""
    if not ref:
        return ref
    segments = re.split(r"\s*&\s*", ref)
    out = []
    for seg in segments:
        m = _SEGMENT_RE.match(seg.strip())
        if not m:
            out.append(seg)
            continue
        chapter, verses = int(m.group(1)), m.group(2)
        out.append(f"Psalm {_mt_chapter(chapter)}:{verses}")
    return " & ".join(out)
