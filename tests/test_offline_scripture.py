"""Checks every Psalm/Gospel section rendered into the lectionary book
(built fresh each test session from .cache/offline.sqlite3 -- see
the offline_pdf_text fixture) against the real public-domain text its own
reference claims to quote, via evangelion.bible_source and the shared
parsing helpers in tests/_pdf_scripture.py. This exercises the real render
path -- section label, reference line, and body text as evangelion.generate
lays them out, including Septuagint renumbering and Gospel-harmony
splitting -- rather than the seed data directly, so it also catches a
rendering-level bug (a reading placed under the wrong label, or the wrong
text landing under a reference) that checking evangelion.seed_offline_db's
own data wouldn't.

Every offline.sqlite3 reading's text *is* one of these real translations --
evangelion.seed_offline_db looked it up from the very same sources this
test does -- so a correct section here should score close to 1.0 against
at least one candidate. MIN_SIMILARITY leaves headroom only for the PDF's
illuminated initial (drawn as a separate glyph, so text extraction splits
it onto its own line) and similar rendering-only noise, not for
translation drift.

A Psalm section's printed reference is always Septuagint-numbered (see
evangelion.generate's unconditional septuagint_ref() call), so its
candidates are: UKJV under lookup_candidates()'s Masoretic inversion (the
seed's psalm_source="ukjv" fallback -- see seed_offline_db's docstring for
why a handful of split-psalm references fall back to this even under the
default psalm_source="brenton"), *and* Brenton looked up directly under
the printed reference with no inversion at all, since Brenton is already
Septuagint-numbered (evangelion.seed_offline_db's default Psalm source --
this is the "won't need masoretic translation" case). A Gospel section's
candidates are UKJV and ASV, both under the printed reference unchanged.
"""

import difflib

from _pdf_scripture import find_sections, lookup_candidates, section_body, words

MIN_SIMILARITY = 0.9


def _check_offline_pdf_text(
    text, bible, brenton_bible, asv_bible, extra_gospel_bible=None
):
    gospel_bibles = (bible, asv_bible) + (
        (extra_gospel_bible,) if extra_gospel_bible else ()
    )
    found = []
    for label, ref, body_start in find_sections(text):
        candidates = []
        if label == "Psalm":
            for lookup_ref in lookup_candidates(label, ref):
                try:
                    candidates.append((lookup_ref, bible.text_for_ref(lookup_ref)))
                except KeyError, ValueError:
                    continue
            try:
                candidates.append((ref, brenton_bible.text_for_ref(ref)))
            except KeyError, ValueError:
                pass
        else:
            for source_bible in gospel_bibles:
                try:
                    candidates.append((ref, source_bible.text_for_ref(ref)))
                except KeyError, ValueError:
                    continue
        if candidates:
            found.append((label, ref, candidates, body_start))

    assert found, (
        "Found no resolvable Psalm/Gospel reference lines anywhere in the "
        "offline PDF -- is offline.sqlite3 actually seeded?"
    )

    failures = []
    for label, ref, candidates, body_start in found:
        body_words = words(section_body(text, body_start))

        lookup_ref, real, ratio = max(
            (
                (
                    lookup_ref,
                    real,
                    difflib.SequenceMatcher(
                        a=body_words, b=words(real), autojunk=False
                    ).ratio(),
                )
                for lookup_ref, real in candidates
            ),
            key=lambda c: c[2],
        )
        if ratio < MIN_SIMILARITY:
            failures.append(
                f"{label} {ref!r} (best candidate: {lookup_ref!r}) only scored "
                f"{ratio:.2f} against the real UKJV text (want >= {MIN_SIMILARITY}).\n"
                f"    PDF:  {section_body(text, body_start)[:150]!r}\n"
                f"    UKJV: {real[:150]!r}"
            )

    assert not failures, (
        f"{len(failures)}/{len(found)} sections failed:\n" + "\n\n".join(failures)
    )


def test_offline_pdf_sections_roughly_match_ukjv(
    bible, brenton_bible, asv_bible, web_bible, offline_pdf_text
):
    _check_offline_pdf_text(
        offline_pdf_text, bible, brenton_bible, asv_bible, extra_gospel_bible=web_bible
    )


def test_offline_every_day_pdf_sections_roughly_match_ukjv(
    bible, brenton_bible, asv_bible, web_bible, offline_every_day_pdf_text
):
    """Same check as test_offline_pdf_sections_roughly_match_ukjv, but
    against the --every-day book -- covers the ordinary (non-Sunday,
    non-feast) weekdays the default book leaves out."""
    _check_offline_pdf_text(
        offline_every_day_pdf_text,
        bible,
        brenton_bible,
        asv_bible,
        extra_gospel_bible=web_bible,
    )


def test_offline_kjv_gospel_pdf_sections_roughly_match_kjv(
    bible, brenton_bible, asv_bible, kjv_bible, offline_kjv_gospel_pdf_text
):
    """Same check, but against a database seeded with gospel_source="kjv"
    -- exercises the classic King James source end to end (seeding, then
    the real render path), not just bible_source.UsfxBibleText's own USFX
    parsing of it."""
    _check_offline_pdf_text(
        offline_kjv_gospel_pdf_text,
        bible,
        brenton_bible,
        asv_bible,
        extra_gospel_bible=kjv_bible,
    )


def test_offline_web_gospel_pdf_sections_roughly_match_web(
    bible, brenton_bible, asv_bible, web_bible, offline_web_gospel_pdf_text
):
    """Same check, but against a database seeded with gospel_source="web"
    -- exercises the World English Bible (Updated edition) source end to
    end (seeding, then the real render path)."""
    _check_offline_pdf_text(
        offline_web_gospel_pdf_text,
        bible,
        brenton_bible,
        asv_bible,
        extra_gospel_bible=web_bible,
    )
