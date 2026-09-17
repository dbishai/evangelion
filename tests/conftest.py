from pathlib import Path

import pytest
import requests
from pypdf import PdfReader

from evangelion.bible_source import (
    ASV_CACHE_PATH,
    ASV_XML_NAME,
    ASV_ZIP_URL,
    BRENTON_CACHE_PATH,
    BRENTON_XML_NAME,
    BRENTON_ZIP_URL,
    KJV_CACHE_PATH,
    KJV_XML_NAME,
    KJV_ZIP_URL,
    WEB_CACHE_PATH,
    WEB_XML_NAME,
    WEB_ZIP_URL,
    BibleText,
    UsfxBibleText,
    ensure_bible_zip,
    ensure_usfx_zip,
)
from evangelion.generate import build
from evangelion.seed_offline_db import DEFAULT_OUTPUT_DB, seed_offline_db


def _page_text(page):
    """One page's extracted text, with its running header/page-number pair
    (evangelion.layout.draw_running_header -- always the first two text
    draws on every page but the title page, so always the first two
    extracted lines) stripped, so a reading that spans a page break doesn't
    get that noise spliced into the middle of its own body text. The title
    page has no running header, so it's identified and left alone by its
    second line not being a bare page number."""
    lines = page.extract_text().split("\n")
    if len(lines) >= 2 and lines[1].strip().isdigit():
        return "\n".join(lines[2:])
    return "\n".join(lines)


def _pdf_text(pdf_path):
    return "\n".join(_page_text(page) for page in PdfReader(pdf_path).pages)


@pytest.fixture(scope="session")
def bible():
    """A BibleText backed by the cached BibleUKJV.zip (see
    evangelion.bible_source), downloading it once to DEFAULT_CACHE_PATH and
    reusing that cached copy on every later run. Skips (rather than
    failing) any test that uses it if the zip isn't already cached and
    can't be downloaded -- e.g. a sandboxed CI run with no network."""
    try:
        zip_path = ensure_bible_zip()
    except requests.RequestException as e:
        pytest.skip(f"BibleUKJV.zip isn't cached and couldn't be downloaded: {e}")
    return BibleText(zip_path)


@pytest.fixture(scope="session")
def brenton_bible():
    """A UsfxBibleText backed by the cached Brenton English Septuagint zip
    -- natively LXX-numbered, Psalms (and the rest of the OT/Apocrypha)
    only, no NT. Skips any test that uses it if it isn't cached and can't
    be downloaded."""
    try:
        zip_path = ensure_usfx_zip(BRENTON_ZIP_URL, BRENTON_CACHE_PATH)
    except requests.RequestException as e:
        pytest.skip(f"Brenton zip isn't cached and couldn't be downloaded: {e}")
    return UsfxBibleText(zip_path, BRENTON_XML_NAME)


@pytest.fixture(scope="session")
def asv_bible():
    """A UsfxBibleText backed by the cached ASV (1901) zip -- full Bible,
    Masoretic-numbered Psalms same as UKJV. Skips any test that uses it if
    it isn't cached and can't be downloaded."""
    try:
        zip_path = ensure_usfx_zip(ASV_ZIP_URL, ASV_CACHE_PATH)
    except requests.RequestException as e:
        pytest.skip(f"ASV zip isn't cached and couldn't be downloaded: {e}")
    return UsfxBibleText(zip_path, ASV_XML_NAME)


@pytest.fixture(scope="session")
def kjv_bible():
    """A UsfxBibleText backed by the cached classic King James (1769) zip
    -- full Bible, Masoretic-numbered Psalms same as UKJV/ASV. Skips any
    test that uses it if it isn't cached and can't be downloaded."""
    try:
        zip_path = ensure_usfx_zip(KJV_ZIP_URL, KJV_CACHE_PATH)
    except requests.RequestException as e:
        pytest.skip(f"KJV zip isn't cached and couldn't be downloaded: {e}")
    return UsfxBibleText(zip_path, KJV_XML_NAME)


@pytest.fixture(scope="session")
def web_bible():
    """A UsfxBibleText backed by the cached World English Bible (Updated
    edition) zip -- full Bible, Masoretic-numbered Psalms same as
    UKJV/KJV/ASV. Skips any test that uses it if it isn't cached and can't
    be downloaded."""
    try:
        zip_path = ensure_usfx_zip(WEB_ZIP_URL, WEB_CACHE_PATH)
    except requests.RequestException as e:
        pytest.skip(f"WEB zip isn't cached and couldn't be downloaded: {e}")
    return UsfxBibleText(zip_path, WEB_XML_NAME)


@pytest.fixture(scope="session")
def default_offline_db():
    """Ensure .cache/offline.sqlite3 (the database `evangelion` itself
    builds from by default) exists, building it if missing -- same
    download-once-and-cache-or-skip pattern as the translation-zip
    fixtures above, since seeding it needs all of UKJV/Brenton's zips."""
    if not Path(DEFAULT_OUTPUT_DB).exists():
        try:
            seed_offline_db(DEFAULT_OUTPUT_DB, log=lambda *a: None)
        except requests.RequestException as e:
            pytest.skip(f"{DEFAULT_OUTPUT_DB} isn't cached and couldn't be built: {e}")
    return DEFAULT_OUTPUT_DB


@pytest.fixture(scope="session")
def offline_pdf_text(tmp_path_factory, default_offline_db):
    """Build the real lectionary book (no network needed once
    default_offline_db's own translation text is already baked in) once
    per test session, and return its full text (see _pdf_text) -- so
    tests check what the PDF actually renders, not just evangelion.
    seed_offline_db's own seed data. Sundays and Major/Minor Feasts only,
    evangelion's own default (--every-day off)."""
    pdf_path = tmp_path_factory.mktemp("evangelion") / "offline.pdf"
    build(output_path=str(pdf_path))
    return _pdf_text(str(pdf_path))


@pytest.fixture(scope="session")
def offline_every_day_pdf_text(tmp_path_factory, default_offline_db):
    """Same as offline_pdf_text, but every day of the year (--every-day)
    -- covers the ordinary weekdays offline_pdf_text's default leaves out."""
    pdf_path = tmp_path_factory.mktemp("evangelion") / "offline_every_day.pdf"
    build(output_path=str(pdf_path), every_day=True)
    return _pdf_text(str(pdf_path))


@pytest.fixture(scope="session")
def offline_kjv_gospel_pdf_text(tmp_path_factory, kjv_bible):
    """Same book as offline_pdf_text (Sundays and Major/Minor Feasts only),
    but seeded with the classic KJV for Gospels instead of the default UKJV
    -- exercises the KJV source end to end (seeding, then the real render
    path) rather than just bible_source.UsfxBibleText's own parsing.
    Depends on the `kjv_bible` fixture only to let pytest skip this one too
    when the network/cache dependency it needs isn't available."""
    db_path = tmp_path_factory.mktemp("evangelion") / "offline_kjv.sqlite3"
    seed_offline_db(str(db_path), gospel_source="kjv", log=lambda *a: None)
    pdf_path = tmp_path_factory.mktemp("evangelion") / "offline_kjv.pdf"
    build(output_path=str(pdf_path), db_path=str(db_path))
    return _pdf_text(str(pdf_path))


@pytest.fixture(scope="session")
def offline_web_gospel_pdf_text(tmp_path_factory, web_bible):
    """Same book as offline_pdf_text, but seeded with the World English
    Bible (Updated edition) for Gospels instead of the default UKJV --
    exercises the WEB source end to end (seeding, then the real render
    path)."""
    db_path = tmp_path_factory.mktemp("evangelion") / "offline_web.sqlite3"
    seed_offline_db(str(db_path), gospel_source="web", log=lambda *a: None)
    pdf_path = tmp_path_factory.mktemp("evangelion") / "offline_web.pdf"
    build(output_path=str(pdf_path), db_path=str(db_path))
    return _pdf_text(str(pdf_path))
