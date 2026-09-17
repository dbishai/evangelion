"""Looks up verse text from public-domain English Bible translations:

 - UKJV (Updated King James, creationism.org/BibleUKJV/), the default;
 - KJV (classic 1769 standard text), an alternative to UKJV;
 - ASV (1901), another alternative to UKJV for the Gospels;
 - WEB (World English Bible, Updated edition), another alternative to
   UKJV for the Gospels;
 - Brenton's English Septuagint (1851; LXX2012, Michael Paul Johnson's
   2012 American-English spelling/wording update), for Psalms
   specifically -- it translates the actual Greek Septuagint the Coptic
   Church's Psalter uses, natively LXX-numbered, so a reference already
   converted by evangelion.psalm_numbering.septuagint_ref can be looked
   up directly with no Masoretic round-trip. Unlike some other Brenton
   editions, this one doesn't count a Psalm's descriptive title as its
   own verse 1 -- verse 1 is always real content -- which matches
   septuagint_ref()'s own assumption that only the chapter shifts, not
   the verse number.

Used by evangelion.generate (split_harmony(), to cut a multi-book Gospel
harmony reading -- e.g. Palm Sunday's Liturgy Gospel -- back apart into
separately labeled readings) and evangelion.seed_offline_db (to seed the
lectionary database's text, choosing UKJV/KJV/ASV/WEB for Gospels and
UKJV/KJV/WEB/Brenton for Psalms).

Each source's archive is fetched once and cached at its own *_CACHE_PATH;
nothing here touches the network unless that cache is missing."""

import difflib
import re
import zipfile
from pathlib import Path

import requests

USER_AGENT = "evangelion-lectionary/0.1 (personal liturgical-use script; contact: dbishai@outlook.com)"
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
# Downloaded translation zips are cached here, not at the repo root --
# a hidden, git-ignored directory of build-time downloads, same idea as
# pip's or npm's own cache directory.
_CACHE_DIR = _REPO_ROOT / ".cache"

BIBLE_ZIP_URL = "https://www.creationism.org/BibleUKJV/BibleUKJV.zip"
DEFAULT_CACHE_PATH = _CACHE_DIR / "bible_ukjv_cache.zip"

# eBible.org's USFX (XML) downloads -- one file holding the whole
# translation, verse-milestone-marked (see UsfxBibleText). All public
# domain; see each zip's own copr.htm for eBible.org's own notice.
ASV_ZIP_URL = "https://ebible.org/Scriptures/eng-asv_usfx.zip"
ASV_CACHE_PATH = _CACHE_DIR / "bible_asv_cache.zip"
ASV_XML_NAME = "eng-asv_usfx.xml"

# LXX2012 (eng-lxx2012): Michael Paul Johnson's 2012 American-English
# spelling/wording update of Brenton's 1851 translation, same underlying
# text. Its own <d> title elements sit outside any <v> milestone (unlike
# some other Brenton editions), so a Psalm's title is never attributed to
# verse 1 at all -- verse 1 is always the chapter's real first line. Its
# source text also has a stray literal "⌃" (U+2303) after nearly every
# "you"/"You" (an eBible.org export artifact, ~2000 occurrences, not
# present in any other translation here) -- stripped in _parse_usfx's
# final cleanup, same treatment as KJV's "¶".
BRENTON_ZIP_URL = "https://ebible.org/Scriptures/eng-lxx2012_usfx.zip"
BRENTON_CACHE_PATH = _CACHE_DIR / "bible_brenton_cache.zip"
BRENTON_XML_NAME = "eng-lxx2012_usfx.xml"

# eBible.org's "King James Version + Apocrypha" (eng-kjv): the classic 1769
# standard text, distinct from BibleUKJV's modernized spelling above. Its
# source text carries a literal "¶" paragraph-mark character before some
# verses (a KJV typographical convention this edition preserves as plain
# text rather than markup) -- stripped in _parse_usfx's final cleanup since
# it isn't real scripture text; no other translation here has ever been
# observed to contain one, so that strip is a no-op for ASV/Brenton.
KJV_ZIP_URL = "https://ebible.org/Scriptures/eng-kjv_usfx.zip"
KJV_CACHE_PATH = _CACHE_DIR / "bible_kjv_cache.zip"
KJV_XML_NAME = "eng-kjv_usfx.xml"

# The World English Bible, Updated edition (engwebu): a modern-language,
# public-domain translation, Masoretic-numbered like UKJV/KJV/ASV.
WEB_ZIP_URL = "https://ebible.org/Scriptures/engwebu_usfx.zip"
WEB_CACHE_PATH = _CACHE_DIR / "bible_web_cache.zip"
WEB_XML_NAME = "engwebu_usfx.xml"

# Book name (every spelling evangelion's own lectionary data uses) ->
# (BibleUKJV zip filename prefix, chapter-number zero-padding width). Only
# the books evangelion actually ever cites -- the four Gospels and the
# Psalms -- since those are the only ones a reading's "ref" field can name.
BOOK_FILES = {
    "Psalm": ("19Ps", 3),
    "Psalms": ("19Ps", 3),
    "Matthew": ("40Mat", 2),
    "Matt": ("40Mat", 2),
    "Mt": ("40Mat", 2),
    "Mark": ("41Mar", 2),
    "Mk": ("41Mar", 2),
    "Luke": ("42Luk", 2),
    "Lk": ("42Luk", 2),
    "LK": ("42Luk", 2),
    "John": ("43Jhn", 2),
    "Jn": ("43Jhn", 2),
    "JN": ("43Jhn", 2),
}

# The same book names -> USFX's standard 3-letter book codes (used by both
# the ASV and Brenton USFX files).
USFX_BOOK_CODES = {
    "Psalm": "PSA",
    "Psalms": "PSA",
    "Matthew": "MAT",
    "Matt": "MAT",
    "Mt": "MAT",
    "Mark": "MRK",
    "Mk": "MRK",
    "Luke": "LUK",
    "Lk": "LUK",
    "LK": "LUK",
    "John": "JHN",
    "Jn": "JHN",
    "JN": "JHN",
}

# Full display name for a reading's abbreviated book, for the label
# split_harmony() gives each piece of a harmony it separates out.
FULL_BOOK_NAME = {
    "Mt": "Matthew",
    "Matt": "Matthew",
    "Mk": "Mark",
    "Lk": "Luke",
    "LK": "Luke",
    "Jn": "John",
    "JN": "John",
    "Psalm": "Psalm",
    "Matthew": "Matthew",
    "Mark": "Mark",
    "Luke": "Luke",
    "John": "John",
}

_VERSE_RE = re.compile(r"(\d+):(\d+)\s+")
_SEGMENT_SPLIT_RE = re.compile(r"\s*&\s*")
_SEGMENT_BOOK_RE = re.compile(r"^([A-Za-z]+)\b")
# A segment ending "N:M—" with nothing after the em dash ("verse M to the
# end of the chapter", used to split a cross-chapter range into two
# segments, e.g. "Matt 4:23— & Matt 5:1-16") has no end_verse to name;
# OPEN_END_RE recognizes it so parse_ref can fill the chapter's real last
# verse in instead.
_OPEN_END_RE = re.compile(
    r"^(?P<book>[A-Za-z]+)\.?\s+(?P<chapter>\d+)\s*:\s*(?P<verse>\d+)\s*[—-]\s*$"
)
_REF_RE = re.compile(
    r"^(?P<book>[A-Za-z]+)\.?\s+"
    r"(?P<chapter>\d+)\s*:\s*(?P<verse>\d+)"
    r"(?:\s*[-–]\s*(?:(?P<end_chapter>\d+)\s*:\s*)?(?P<end_verse>\d+))?"
    r"(?P<extra>(?:\s*,\s*\d+)*)\s*$"
)
_WORD_RE = re.compile(r"[A-Za-z']+")


def ensure_bible_zip(cache_path=DEFAULT_CACHE_PATH):
    """Return the local path to the BibleUKJV.zip archive, downloading it
    to `cache_path` first if it isn't already cached there."""
    return _ensure_zip(BIBLE_ZIP_URL, cache_path)


def ensure_usfx_zip(url, cache_path):
    """Return the local path to a eBible.org USFX zip (ASV_ZIP_URL/
    BRENTON_ZIP_URL), downloading it to `cache_path` first if it isn't
    already cached there."""
    return _ensure_zip(url, cache_path)


def _ensure_zip(url, cache_path):
    cache_path = Path(cache_path)
    if not cache_path.exists():
        resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=60)
        resp.raise_for_status()
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_bytes(resp.content)
    return cache_path


class _BibleTextBase:
    """Reference parsing shared by every translation backend: turns a
    reference string into (book, chapter, verse) tuples and joins their
    looked-up text, however a subclass actually fetches one verse. See
    BibleText (the BibleUKJV zip) and UsfxBibleText (ASV/Brenton) for the
    two backends."""

    def verse(self, book, chapter, verse):
        """Return one verse's plain text, or raise ValueError if this
        translation doesn't have it (a chapter/verse number, or book, it
        doesn't have)."""
        raise NotImplementedError

    def verse_count(self, book, chapter):
        raise NotImplementedError

    def parse_ref(self, ref):
        """Parse a single-book reference (no " & "-joined segments) into an
        ordered list of (book, chapter, verse) tuples, e.g. "Matthew 6:34 –
        7:12" -> [("Matthew", 6, 34), ..., ("Matthew", 7, 12)], or "Psalm
        18:15, 6" -> [("Psalm", 18, 15), ("Psalm", 18, 6)] (order preserved,
        not sorted -- some readings deliberately quote verses out of
        order). Chapter-crossing ranges need `self` to know how many verses
        are in the chapters in between."""
        ref = ref.strip()
        m = _REF_RE.match(ref)
        if not m:
            m = _OPEN_END_RE.match(ref)
            if not m:
                raise ValueError(f"Unrecognized scripture reference: {ref!r}")
            book = m.group("book")
            chapter = int(m.group("chapter"))
            verse = int(m.group("verse"))
            return self._expand_range(
                book, chapter, verse, chapter, self.verse_count(book, chapter)
            )
        book = m.group("book")
        chapter = int(m.group("chapter"))
        verse = int(m.group("verse"))

        if m.group("end_verse"):
            end_chapter = int(m.group("end_chapter") or chapter)
            end_verse = int(m.group("end_verse"))
            return self._expand_range(book, chapter, verse, end_chapter, end_verse)

        out = [(book, chapter, verse)]
        out.extend(
            (book, chapter, int(extra))
            for extra in re.findall(r",\s*(\d+)", m.group("extra") or "")
        )
        return out

    def _expand_range(self, book, start_chapter, start_verse, end_chapter, end_verse):
        out = []
        c, v = start_chapter, start_verse
        while True:
            out.append((book, c, v))
            if c == end_chapter and v == end_verse:
                break
            if c > end_chapter or (c == end_chapter and v > end_verse):
                # Overshot without ever landing on end_verse -- it's past
                # end_chapter's real last verse (a bad reference), rather
                # than searching indefinitely into later chapters/books.
                raise ValueError(
                    f"{book} {start_chapter}:{start_verse}-{end_chapter}:{end_verse} "
                    f"never reaches {end_chapter}:{end_verse} -- out of range"
                )
            if v >= self.verse_count(book, c):
                c, v = c + 1, 1
            else:
                v += 1
        return out

    def text_for_ref(self, ref):
        """Return the plain text for a reference -- one book (e.g.
        "Matthew 6:34 – 7:12" or "Psalm 18:15, 6" or "Jn 12:12-19"), or
        several " & "-joined segments of the same or different books (e.g.
        "Psalm 80:3 & Psalm 80:1 & Psalm 80:2") -- verses joined with a
        space, in the order the reference lists them. A later segment
        naming no book at all (e.g. "Psalm 17:3 & 17:5") inherits the
        nearest earlier segment's book."""
        segments = _SEGMENT_SPLIT_RE.split(ref.strip())
        out = []
        last_book = None
        for seg in segments:
            m = _SEGMENT_BOOK_RE.match(seg)
            book = m.group(1) if m else None
            if not self._knows_book(book):
                if last_book is None:
                    raise ValueError(f"Reference segment names no book: {seg!r}")
                seg = f"{last_book} {seg}"
            else:
                last_book = book
            out.extend(self.parse_ref(seg))
        # A verse can be a real, deliberately empty entry (a Psalm title
        # that Septuagint versification counts as its own verse -- see
        # _parse_usfx) rather than missing outright; drop it from the
        # joined text instead of leaving a stray double space where it
        # would have gone.
        return " ".join(v for t in out if (v := self.verse(*t)))

    def _knows_book(self, book):
        raise NotImplementedError


class BibleText(_BibleTextBase):
    """Verse lookups against a local copy of the BibleUKJV zip (one file
    per chapter). Chapters are parsed lazily and cached in memory for the
    life of the instance."""

    def __init__(self, zip_path=DEFAULT_CACHE_PATH):
        self._zf = zipfile.ZipFile(zip_path)
        self._chapters = {}  # (book_file_prefix, chapter) -> {verse: text}

    def _knows_book(self, book):
        return book in BOOK_FILES

    def _chapter(self, book, chapter):
        prefix, width = BOOK_FILES[book]
        key = (prefix, chapter)
        if key not in self._chapters:
            name = f"{prefix}{chapter:0{width}d}.htm"
            try:
                raw = self._zf.read(name).decode("utf-8")
            except KeyError:
                raise ValueError(
                    f"No {book} chapter {chapter} in the UKJV text"
                ) from None
            self._chapters[key] = _parse_chapter(raw)
        return self._chapters[key]

    def verse(self, book, chapter, verse):
        try:
            return self._chapter(book, chapter)[verse]
        except KeyError:
            raise ValueError(f"No {book} {chapter}:{verse} in the UKJV text") from None

    def verse_count(self, book, chapter):
        return max(self._chapter(book, chapter))


def _parse_chapter(raw_html):
    """Parse one BibleUKJV chapter .htm file's body into {verse: text}."""
    marker = 'NOSHADE width="88%">'
    start = raw_html.index(marker) + len(marker)
    end = raw_html.index("<hr", start)
    body = raw_html[start:end]
    body = re.sub(r"<[^>]+>", " ", body)
    body = re.sub(r"\s+", " ", body).strip()

    markers = list(_VERSE_RE.finditer(body))
    verses = {}
    for i, m in enumerate(markers):
        verse = int(m.group(2))
        text_start = m.end()
        text_end = markers[i + 1].start() if i + 1 < len(markers) else len(body)
        verses[verse] = body[text_start:text_end].strip()
    return verses


class UsfxBibleText(_BibleTextBase):
    """Verse lookups against a local eBible.org USFX (XML) translation --
    ASV or Brenton's Septuagint, both one file holding the whole
    translation, downloaded and cached as a zip (see ensure_usfx_zip()) and
    fully parsed once on construction (the files are a few MB, small enough
    that lazy per-chapter parsing -- as BibleText does for BibleUKJV's many
    small files -- isn't worth the extra bookkeeping here).

    A Brenton instance's own chapter/verse numbers *are* already Septuagint
    numbering (it's a translation of the Greek Septuagint) -- so a Psalm
    reference already converted by evangelion.psalm_numbering.
    septuagint_ref() can be looked up here directly, with no Masoretic
    round-trip; see that module and evangelion.seed_offline_db for where
    that conversion actually happens."""

    def __init__(self, zip_path, xml_name):
        with zipfile.ZipFile(zip_path) as zf:
            raw = zf.read(xml_name)
        self._verses = {}  # (book_code, chapter) -> {verse: text}
        _parse_usfx(raw, self._verses)

    def _knows_book(self, book):
        return book in USFX_BOOK_CODES

    def _chapter(self, book, chapter):
        code = USFX_BOOK_CODES.get(book)
        key = (code, chapter)
        if code is None or key not in self._verses:
            raise ValueError(f"No {book} chapter {chapter} in this translation")
        return self._verses[key]

    def verse(self, book, chapter, verse):
        try:
            return self._chapter(book, chapter)[verse]
        except KeyError:
            raise ValueError(
                f"No {book} {chapter}:{verse} in this translation"
            ) from None

    def verse_count(self, book, chapter):
        return max(self._chapter(book, chapter))


def _parse_usfx(raw_xml, verses):
    """Fill `verses` ({(book_code, chapter): {verse: text}}) from one USFX
    XML document's bytes. USFX marks verse boundaries with empty milestone
    elements (<c id="1" />, <v id="1" bcv="PSA.1.1" />, <ve />) rather than
    wrapping each verse's content in its own element, so the actual text is
    scattered across the surrounding elements' own .text/.tail in document
    order; footnotes (<f>), cross-references (<x>), and a Psalm's own
    descriptive title/superscription (<d>, e.g. Brenton's Psalm 30 "For
    the end, a Psalm of David, an utterance of extreme fear.") are all
    excluded from the text a caller ever sees.

    A <d> is a special case worth its own note: it wraps its chapter's
    very first <v> milestone, and different psalms close it two different
    ways --
     - most: the <d> closes with its own <ve />, so in real Septuagint
       versification the title genuinely *is* the whole of verse 1, and
       no other text is ever attributed to verse 1 at all;
     - a few (e.g. Brenton's Psalm 95): the <v id="1"> milestone stays
       open across the </d> boundary, so verse 1's real opening line (in
       the following <p>) is folded in right after the title.
    Excluding <d> outright would leave the first kind of verse 1 with no
    text at all -- not missing, just genuinely empty (its only content
    was the title this function is asked to drop) -- so such a verse is
    still recorded (as "", not left out of the chapter entirely), rather
    than raising as though the verse doesn't exist: a citation that
    starts at "verse 1" ends up starting from its real first sentence,
    same as if the title had never been marked as its own verse at all.
    Every other wrapper (small caps, supplied-word italics, poetry
    lines, ...) is walked through for its text but otherwise ignored."""
    import xml.etree.ElementTree as ET

    root = ET.fromstring(raw_xml)
    for book_elem in root.iter("book"):
        code = book_elem.get("id")
        state = {"chapter": None, "verse": None}

        def emit(text, skip):
            if state["verse"] is None:
                return
            key = (code, state["chapter"])
            dest = verses.setdefault(key, {}).setdefault(state["verse"], [])
            if text and not skip:
                dest.append(text)

        def walk(elem, skip):
            tag = elem.tag
            if tag == "c":
                state["chapter"] = int(elem.get("id"))
                state["verse"] = None
            elif tag == "v":
                # Some editions split one verse across several <v> milestones
                # for versification differences (id "12a", "12b", ... "12x")
                # -- fold them all back into the base verse number, text
                # concatenated in document order same as any other verse.
                state["verse"] = int(re.match(r"\d+", elem.get("id")).group())
                emit(None, False)  # register the verse even if it ends up empty
            elif tag == "ve":
                state["verse"] = None

            this_skip = skip or tag in ("f", "x", "d")
            emit(elem.text, this_skip)
            for child in elem:
                walk(child, this_skip)
                emit(child.tail, this_skip)

        walk(book_elem, False)

    for key, by_verse in verses.items():
        verses[key] = {
            v: re.sub(
                r"\s+", " ", "".join(parts).replace("¶", "").replace("⌃", "")
            ).strip()
            for v, parts in by_verse.items()
        }


def split_harmony(entry, bible=None):
    """If `entry`'s "ref" is a " & "-joined reading spanning more than one
    book -- a Gospel harmony, like Palm Sunday's Liturgy Gospel -- return a
    list of {"ref", "text"} dicts, one per book, splitting entry["text"]
    (one unbroken paragraph with no seams to split on) at the point each
    segment's real UKJV text best aligns to, via difflib word-level
    matching. Returns [entry] unchanged if there's only one book involved
    (an ordinary multi-verse reading, e.g. "Psalm 80:3 & Psalm 80:1 & Psalm
    80:2"), or if alignment isn't confident enough to trust."""
    segments = _SEGMENT_SPLIT_RE.split(entry["ref"].strip())
    books = [
        (m.group(1) if (m := _SEGMENT_BOOK_RE.match(seg)) else None) for seg in segments
    ]
    if len(set(books)) <= 1:
        return [entry]

    if bible is None:
        try:
            bible = BibleText(ensure_bible_zip())
        except OSError, requests.RequestException, zipfile.BadZipFile:
            return [entry]

    try:
        segment_texts = [bible.text_for_ref(seg) for seg in segments]
    except KeyError, ValueError:
        return [entry]

    offsets = _split_points(entry["text"], segment_texts)
    if offsets is None or offsets != sorted(set(offsets)):
        return [entry]

    bounds = [0, *offsets, len(entry["text"])]
    out = []
    for seg, book, start, end in zip(segments, books, bounds, bounds[1:]):
        piece = entry["text"][start:end].strip()
        if not piece:
            return [entry]
        out.append({"ref": _display_ref(seg, book), "text": piece})
    return out


def _display_ref(seg, book):
    full = FULL_BOOK_NAME.get(book, book)
    return re.sub(rf"^{re.escape(book)}\b", full, seg.strip())


def _split_points(full_text, segment_texts):
    """Locate, inside `full_text`, the char offset each later segment in
    `segment_texts` begins at -- by word-aligning `full_text` against the
    segments' own (differently-worded) reference text with difflib, then
    mapping each segment boundary through the alignment. Returns None if
    either side has no words to align."""
    full_tokens = [
        (m.group(0).lower(), m.start()) for m in _WORD_RE.finditer(full_text)
    ]
    full_words = [w for w, _ in full_tokens]
    if not full_words:
        return None

    ref_words = []
    boundaries = []  # ref_words index where each segment after the first begins
    for seg_text in segment_texts:
        if ref_words:
            boundaries.append(len(ref_words))
        ref_words.extend(m.group(0).lower() for m in _WORD_RE.finditer(seg_text))
    if not ref_words:
        return None

    matcher = difflib.SequenceMatcher(a=ref_words, b=full_words, autojunk=False)
    blocks = [b for b in matcher.get_matching_blocks() if b.size]
    if not blocks:
        return None

    def map_index(ref_idx):
        best = min(
            blocks, key=lambda b: min(abs(ref_idx - b.a), abs(ref_idx - (b.a + b.size)))
        )
        return best.b + (ref_idx - best.a)

    offsets = []
    for ref_idx in boundaries:
        full_idx = max(0, min(map_index(ref_idx), len(full_tokens) - 1))
        offsets.append(full_tokens[full_idx][1])
    return offsets
