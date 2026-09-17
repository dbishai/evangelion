"""Compares evangelion's lectionary data against two real, printed Coptic
Katameros volumes -- an independent source, per the ~/.claude memory
"feedback-test-against-independent-source":
 - "Katameros of the Days: Readings for Week Days and Feasts," St. Mary &
   St. Georges/St. Antony Coptic Orthodox Churches, Ottawa, 1998 (weekdays
   and feasts, no Sundays);
 - "The Katameros of the Sundays," St. Mary Coptic Orthodox Church,
   Ottawa, 2nd edition, 2004 (all Sundays of the Coptic year, including
   Great Lent and Pentecost).

`katameros_reference.json` is a **committed, pre-extracted** snapshot of
both books' own day-by-day / Sunday-by-Sunday Psalm/Gospel assignments
(352 weekdays keyed "Month|N", 38 Sundays keyed "Month|Ordinal") -- not
either scanned PDF itself; no live download happens at test time. See the
~/.claude memory "evangelion-katameros-parmouti-integration" for how the
weekday half was extracted.

Four tests:
 - test_parmouti_seed_matches_katameros: Parmouti's 30 occasions were
   *sourced from* the Days book -- a drift guard expecting an exact
   match, catching a future hand-edit or seed-regeneration mistake.
 - test_weekday_seed_roughly_matches_katameros: an independent-source
   check for every other Fixed Cycle weekday the database has a reference
   entry for. Not strict equality -- MIN_WEEKDAY_MATCH_RATE leaves
   headroom below the observed ~95% match rate.
 - test_sundays_sourced_from_katameros_match_exactly: the 7 Sunday
   occasions sourced directly from the Sundays book (Pashons's Third/
   Fourth, plus 5 previously-entirely-missing ordinals: Thout's Third,
   Meshir's Fourth, Paoni's First and Second, Mesori's Third) -- a drift
   guard, same reasoning as the Parmouti one.
 - test_sunday_seed_roughly_matches_katameros: an independent-source
   check for every other Sunday the database has a reference entry for
   (the pre-existing 31, scraped originally from copticchurch.net) --
   this cross-check found and fixed 14 real citation errors (a
   consistent off-by-one "already-Septuagint-numbered" mislabeling, the
   same bug class documented in copticchurch_net_data_errors.md, plus a
   malformed "79:13:00" and an unrelated verse typo) before this test was
   written; MIN_SUNDAY_MATCH_RATE leaves headroom below the resulting
   ~96%. A few disagreements were deliberately left alone after checking
   real translation text directly -- e.g. the Sundays book's own "Matthew
   4:38-41" for Thout's Second Sunday Vespers Gospel is simply wrong
   (Matthew chapter 4 has only 25 verses); evangelion's existing "Luke
   4:38-41" is correct.
"""

import json
import re
from pathlib import Path

from evangelion.seed_offline_db import load_offline_seasons

REFERENCE_PATH = Path(__file__).resolve().parent / "katameros_reference.json"
MIN_WEEKDAY_MATCH_RATE = 0.85  # observed ~0.95; leaves real headroom
MIN_SUNDAY_MATCH_RATE = 0.85  # observed ~0.96; leaves real headroom

# The 7 Sunday occasions whose reading data came directly from the
# Sundays book (not cross-checked against it after the fact) -- see
# test_sundays_sourced_from_katameros_match_exactly.
SUNDAYS_SOURCED_FROM_KATAMEROS = {
    ("Pashons", "Third"),
    ("Pashons", "Fourth"),
    ("Thout", "Third"),
    ("Meshir", "Fourth"),
    ("Paoni", "First"),
    ("Paoni", "Second"),
    ("Mesori", "Third"),
}


def _load_reference():
    return json.loads(REFERENCE_PATH.read_text())


_BOOK_ALIASES = {
    "Matt": "Matthew",
    "Mt": "Matthew",
    "Mk": "Mark",
    "Lk": "Luke",
    "Jn": "John",
}


def _nums(text):
    return re.findall(r"\d+", text or "")


def _book_and_nums(ref):
    m = re.match(r"^([A-Za-z]+)\.?\s+(.*)$", ref.strip())
    if not m:
        return None, []
    book = m.group(1)
    return _BOOK_ALIASES.get(book, book), _nums(m.group(2))


def _refs_agree(ours, katameros):
    """Format-agnostic comparison: same book, same chapter + first verse
    number. Full verse-list formatting differs too much between an
    OCR'd-and-hand-parsed 1998 book and evangelion's own "&"-joined style
    to compare exactly -- see the Katameros-integration memory."""
    ob, on = _book_and_nums(ours)
    kb, kn = _book_and_nums(katameros)
    if ob != kb or not on or not kn:
        return False
    return on[:2] == kn[:2]


def _offline_weekday_readings():
    """{(season_group, title): {service: {kind: ref}}} for every
    every_day=True offline occasion whose title is a bare "<Month> <N>"
    ordinary weekday (major=0) -- skips Sundays/feasts, which this
    Katameros edition (weekdays and feasts only, no Sunday volume) either
    doesn't cover at all (Sundays) or names differently than a plain day
    number (feasts)."""
    out = {}
    for season in load_offline_seasons(every_day=True):
        for occ in season["occasions"]:
            m = re.match(rf"^{re.escape(season['name'])} (\d{{1,2}})$", occ["title"])
            if not m:
                continue
            day = int(m.group(1))
            services = {}
            for service in ("vespers", "matins", "liturgy"):
                svc = occ["services"].get(service) or {}
                entry = {}
                for kind in ("psalm", "gospel"):
                    piece = svc.get(kind)
                    if piece and isinstance(piece, dict):
                        entry[kind] = piece["ref"]
                if entry:
                    services[service] = entry
            out[(season["name"], day)] = services
    return out


_ORDINAL_SUNDAY_RE = re.compile(r"^The (\S+) Sunday of (\S+)$")


def _offline_sunday_readings():
    """{(month, ordinal): {service: {kind: ref}}} for every every_day=True
    offline occasion whose title is an ordinal Sunday ("The First Sunday
    of Thout") -- mirrors _offline_weekday_readings() but keyed the way
    the Sundays book itself organizes its own table of contents (by
    month, then ordinal), not by a specific year's calendar date."""
    out = {}
    for season in load_offline_seasons(every_day=True):
        for occ in season["occasions"]:
            m = _ORDINAL_SUNDAY_RE.match(occ["title"])
            if not m:
                continue
            ordinal, month = m.groups()
            services = {}
            for service in ("vespers", "matins", "liturgy"):
                svc = occ["services"].get(service) or {}
                entry = {}
                for kind in ("psalm", "gospel"):
                    piece = svc.get(kind)
                    if piece and isinstance(piece, dict):
                        entry[kind] = piece["ref"]
                if entry:
                    services[service] = entry
            out[(month, ordinal)] = services
    return out


def test_sundays_sourced_from_katameros_match_exactly():
    reference = _load_reference()
    offline = _offline_sunday_readings()

    mismatches = []
    for month, ordinal in SUNDAYS_SOURCED_FROM_KATAMEROS:
        katameros_svc = reference.get(f"{month}|{ordinal}")
        assert katameros_svc, f"No Katameros reference data for {month} {ordinal}"
        offline_svc = offline.get((month, ordinal))
        assert offline_svc, f"No offline seed data for The {ordinal} Sunday of {month}"
        for service in ("vespers", "matins", "liturgy"):
            for kind in ("psalm", "gospel"):
                ours = offline_svc.get(service, {}).get(kind)
                katameros = katameros_svc.get(service, {}).get(kind)
                if not _refs_agree(ours or "", katameros or ""):
                    mismatches.append((month, ordinal, service, kind, ours, katameros))

    assert not mismatches, (
        f"{len(mismatches)} Sunday reading(s) drifted from their Katameros source "
        f"(month, ordinal, service, kind, offline, katameros):\n"
        + "\n".join(str(m) for m in mismatches)
    )


def test_sunday_seed_roughly_matches_katameros():
    reference = _load_reference()
    offline = _offline_sunday_readings()

    checked = 0
    matched = 0
    mismatches = []
    for (month, ordinal), services in offline.items():
        if (month, ordinal) in SUNDAYS_SOURCED_FROM_KATAMEROS:
            continue  # sourced from this same book -- covered by the exact-match test
        katameros_svc = reference.get(f"{month}|{ordinal}")
        if not katameros_svc:
            continue
        for service in ("vespers", "matins", "liturgy"):
            for kind in ("psalm", "gospel"):
                ours = services.get(service, {}).get(kind)
                katameros = katameros_svc.get(service, {}).get(kind)
                if not ours or not katameros:
                    continue
                checked += 1
                if _refs_agree(ours, katameros):
                    matched += 1
                else:
                    mismatches.append((month, ordinal, service, kind, ours, katameros))

    assert checked > 100, (
        f"Expected a substantial Sunday sample, only checked {checked}"
    )
    rate = matched / checked
    assert rate >= MIN_SUNDAY_MATCH_RATE, (
        f"Only {matched}/{checked} ({rate:.1%}) Sunday readings matched the Katameros "
        f"(want >= {MIN_SUNDAY_MATCH_RATE:.0%}); mismatches:\n"
        + "\n".join(str(m) for m in mismatches)
    )


def test_parmouti_seed_matches_katameros():
    reference = _load_reference()
    offline = _offline_weekday_readings()

    parmouti_days = {day for (season, day) in offline if season == "Parmouti"}
    assert parmouti_days == set(range(1, 31)), (
        f"Expected all 30 Parmouti days in the offline database, got {sorted(parmouti_days)}"
    )

    mismatches = []
    for day in range(1, 31):
        katameros_svc = reference.get(f"Parmouti|{day}")
        assert katameros_svc, f"No Katameros reference data for Parmouti {day}"
        offline_svc = offline[("Parmouti", day)]
        for service in ("vespers", "matins", "liturgy"):
            for kind in ("psalm", "gospel"):
                ours = offline_svc.get(service, {}).get(kind)
                katameros = katameros_svc.get(service, {}).get(kind)
                if ours != katameros:
                    mismatches.append((day, service, kind, ours, katameros))

    assert not mismatches, (
        f"{len(mismatches)} Parmouti reading(s) drifted from their Katameros source "
        f"(day, service, kind, offline, katameros):\n"
        + "\n".join(str(m) for m in mismatches)
    )


def test_weekday_seed_roughly_matches_katameros():
    reference = _load_reference()
    offline = _offline_weekday_readings()

    checked = 0
    matched = 0
    mismatches = []
    for (season, day), services in offline.items():
        if season == "Parmouti":
            continue  # sourced from this same book -- covered by the exact-match test
        katameros_svc = reference.get(f"{season}|{day}")
        if not katameros_svc:
            continue
        for service in ("vespers", "matins", "liturgy"):
            for kind in ("psalm", "gospel"):
                ours = services.get(service, {}).get(kind)
                katameros = katameros_svc.get(service, {}).get(kind)
                if not ours or not katameros:
                    continue
                checked += 1
                if _refs_agree(ours, katameros):
                    matched += 1
                else:
                    mismatches.append((season, day, service, kind, ours, katameros))

    assert checked > 100, (
        f"Expected a substantial weekday sample, only checked {checked}"
    )
    rate = matched / checked
    assert rate >= MIN_WEEKDAY_MATCH_RATE, (
        f"Only {matched}/{checked} ({rate:.1%}) weekday readings matched the Katameros "
        f"(want >= {MIN_WEEKDAY_MATCH_RATE:.0%}); first 20 mismatches:\n"
        + "\n".join(str(m) for m in mismatches[:20])
    )
