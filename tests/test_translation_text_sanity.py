"""Scans every Psalm/Gospel verse in every translation source for a
character outside a known-good allowlist -- letters, digits, whitespace,
and the punctuation actually observed across UKJV/KJV/ASV/WEB/Brenton
(LXX2012).

Exists because a word-level similarity check (test_offline_scripture.py)
structurally cannot catch this kind of thing: a stray "you⌃ righteous"
(LXX2012's raw eBible.org export carries a literal U+2303 after nearly
every "you", ~2000 times) tokenizes to the exact same words as "you
righteous", and the "ground truth" it's compared against is looked up
from the very same source file, so even a character-exact comparison
would agree. A human reading the rendered page caught it; this test scans
every verse directly instead, so a *future* translation source with its
own export artifact fails loudly here rather than shipping silently.

Not a text-quality check (archaic spelling, unusual words, real
punctuation choices are all fine) -- only flags characters no real verse
in any of the five sources has ever legitimately contained. A genuinely
new, legitimate character (an em-dash variant in some future source,
say) should be added to ALLOWED_PUNCTUATION with a one-line reason, not
silently allowed through by loosening the check.
"""

BOOKS = ("Psalm", "Matthew", "Mark", "Luke", "John")

# Every punctuation character actually observed across UKJV/KJV/ASV/WEB/
# Brenton's Psalm + Gospel text (see this file's own construction). Not
# reasoned out in the abstract -- re-derive by scanning all five sources
# directly if this ever needs revisiting.
ALLOWED_PUNCTUATION = set(",.:;?'’“”!‘-()[]—&")


def _suspicious_chars(text):
    return {
        c for c in text if not (c.isalnum() or c.isspace() or c in ALLOWED_PUNCTUATION)
    }


def _scan(bible, name):
    offenders = []
    for book in BOOKS:
        chapter = 1
        while True:
            try:
                verse_count = bible.verse_count(book, chapter)
            except ValueError:
                break
            for verse in range(1, verse_count + 1):
                try:
                    text = bible.verse(book, chapter, verse)
                except ValueError:
                    continue
                bad = _suspicious_chars(text)
                if bad:
                    offenders.append((book, chapter, verse, bad, text))
            chapter += 1
    assert not offenders, (
        f"{name}: {len(offenders)} verse(s) contain unexpected character(s) "
        f"not in ALLOWED_PUNCTUATION:\n"
        + "\n".join(
            f"  {book} {chapter}:{verse} {sorted(bad)!r}: {text[:100]!r}"
            for book, chapter, verse, bad, text in offenders[:20]
        )
    )


def test_ukjv_text_has_no_unexpected_characters(bible):
    _scan(bible, "UKJV")


def test_kjv_text_has_no_unexpected_characters(kjv_bible):
    _scan(kjv_bible, "KJV")


def test_asv_text_has_no_unexpected_characters(asv_bible):
    _scan(asv_bible, "ASV")


def test_web_text_has_no_unexpected_characters(web_bible):
    _scan(web_bible, "WEB")


def test_brenton_text_has_no_unexpected_characters(brenton_bible):
    _scan(brenton_bible, "Brenton")
