#!/usr/bin/env python3
"""
Builds evangelion's lectionary database (.cache/offline.sqlite3 by
default -- not committed, rebuilt on demand, same as the translation zips
it's built from) from data hardcoded in this script plus real
public-domain translation text. No Gregorian or Coptic date is stored
anywhere -- an occasion is identified by its season/divider and title
alone, the same way the book's own Table of Contents presents it.

Two kinds of data go into the seed:

 - The *lectionary structure* (which occasions exist, which Fixed- or
   Moveable-Cycle season each belongs to, which of the Coptic Church's
   Major/Minor Feasts it is, and which Psalm/Gospel reference belongs to
   which service, in what order) is hardcoded in the _OCCASIONS_TSV /
   _READINGS_TSV constants below, as plain tab-separated text -- there's
   no way to derive this from scripture itself. Parmouti's occasions come
   from the printed Katameros book (Katameros of the Days: Readings for
   Week Days and Feasts, St. Mary & St. Georges/St. Antony, Ottawa, 1998),
   since that Coptic month always falls inside the movable Great
   Lent-through-Pentecost season every year.

   A service's readings are stored as an explicit *sequence* (the `seq`
   column), not one row per kind, because a Gospel harmony (e.g. Palm
   Sunday's Liturgy Gospel: Matthew+Mark+Luke, then a Psalm verse, then
   John) needs several rows in order; load_offline_seasons() re-assembles
   that sequence into the {"psalm": ..., "gospel": ...} shape
   occasion_pages() expects. See evangelion.generate.labeled_pieces(),
   which further splits any row spanning several books via
   evangelion.bible_source.split_harmony.

 - The actual *verse text* for each reference is looked up fresh at seed
   time (see evangelion.bible_source), picked per kind by
   `psalm_source`/`gospel_source` -- UKJV, KJV, ASV, WEB, or (Psalms only)
   Brenton's English Septuagint. A reference that doesn't resolve is
   skipped, same as any other occasion with a missing reading.

   Psalm text defaults to Brenton's English Septuagint rather than UKJV.
   evangelion.generate always *labels* a Psalm reading with its Septuagint
   (LXX) reference (the Coptic Church's Psalter is Septuagint, not
   Masoretic), but the stored `reference` column stays Masoretic-numbered,
   since that's what septuagint_ref() expects to convert. UKJV/KJV are
   Masoretic, so looking their text up under that reference and simply
   relabelling it at render time would mismatch verse-for-verse. Brenton
   is already LXX-numbered, so it's looked up via septuagint_ref(reference)
   instead, giving text that genuinely matches the printed label. Pass
   psalm_source="ukjv" or "kjv" for plain Masoretic Psalms text instead.

   Gospel text defaults to the World English Bible (Updated edition);
   pass gospel_source="ukjv", "asv", or "kjv" for UKJV, the ASV (1901),
   or the classic King James (1769) instead.

Only "psalm" and "gospel" readings are seeded -- the only kinds
evangelion.generate ever renders (see its SERVICE_ORDER).

Run:
    uv run evangelion-seed-offline
"""

import argparse
import sqlite3

from evangelion.bible_source import (
    _CACHE_DIR,
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
from evangelion.psalm_numbering import septuagint_ref

DEFAULT_OUTPUT_DB = str(_CACHE_DIR / "offline.sqlite3")

PSALM_SOURCES = ("brenton", "ukjv", "kjv", "web")
GOSPEL_SOURCES = ("ukjv", "asv", "kjv", "web")


def _build_bible(source):
    if source == "ukjv":
        return BibleText(ensure_bible_zip())
    if source == "brenton":
        return UsfxBibleText(
            ensure_usfx_zip(BRENTON_ZIP_URL, BRENTON_CACHE_PATH), BRENTON_XML_NAME
        )
    if source == "asv":
        return UsfxBibleText(ensure_usfx_zip(ASV_ZIP_URL, ASV_CACHE_PATH), ASV_XML_NAME)
    if source == "kjv":
        return UsfxBibleText(ensure_usfx_zip(KJV_ZIP_URL, KJV_CACHE_PATH), KJV_XML_NAME)
    if source == "web":
        return UsfxBibleText(ensure_usfx_zip(WEB_ZIP_URL, WEB_CACHE_PATH), WEB_XML_NAME)
    raise ValueError(f"Unknown Bible source: {source!r}")


OFFLINE_SCHEMA = """
CREATE TABLE IF NOT EXISTS occasions (
    id            INTEGER PRIMARY KEY,  -- defines display order
    season_group  TEXT NOT NULL,        -- divider: Coptic month, or a Moveable Cycle season
    title         TEXT NOT NULL,
    category      TEXT,                 -- 'major' | 'minor' | 'other' | NULL
    major         INTEGER NOT NULL      -- 1 for a Sunday or feast, 0 for an ordinary day
);

CREATE TABLE IF NOT EXISTS readings (
    occasion_id   INTEGER NOT NULL,
    service       TEXT NOT NULL,        -- 'vespers' | 'matins' | 'liturgy'
    seq           INTEGER NOT NULL,     -- order within (occasion_id, service) -- see
                                         -- load_offline_seasons() for why a service can have
                                         -- more than one same-kind run
    kind          TEXT NOT NULL,        -- 'psalm' | 'gospel', of this entry alone
    reference     TEXT,
    text          TEXT
);
"""

_OCCASIONS_TSV = """\
0	Thout	Thout 1		0
1	Thout	Thout 2		0
2	Thout	Thout 3		0
3	Thout	Thout 4		0
4	Thout	Thout 5		0
5	Thout	Thout 6		0
6	Thout	Thout 7		0
7	Thout	Thout 8		0
8	Thout	Thout 9		0
9	Thout	Thout 10		0
10	Thout	Thout 11		0
11	Thout	Thout 12		0
12	Thout	Thout 13		0
13	Thout	Thout 14		0
14	Thout	Thout 15		0
15	Thout	Thout 16		0
16	Thout	Feast of the Cross		1
17	Thout	Feast of the Cross		0
18	Thout	Feast of the Cross		0
19	Thout	Thout 20		0
20	Thout	Thout 21		0
21	Thout	Thout 22		0
22	Thout	Thout 23		0
23	Thout	Thout 24		0
24	Thout	Thout 25		0
25	Thout	Thout 26		0
26	Thout	Thout 27		0
27	Thout	Thout 28		0
28	Thout	Thout 29		0
29	Thout	Thout 30		0
30	Thout	The First Sunday of Thout		1
31	Thout	The Second Sunday of Thout		1
32	Thout	The Third Sunday of Thout		1
33	Thout	The Fourth Sunday of Thout		1
34	Paopi	Paopi 1		0
35	Paopi	Paopi 2		0
36	Paopi	Paopi 3		0
37	Paopi	Paopi 4		0
38	Paopi	Paopi 5		0
39	Paopi	Paopi 6		0
40	Paopi	Paopi 7		0
41	Paopi	Paopi 8		0
42	Paopi	Paopi 9		0
43	Paopi	Paopi 10		0
44	Paopi	Paopi 11		0
45	Paopi	Paopi 12		0
46	Paopi	Paopi 13		0
47	Paopi	Paopi 14		0
48	Paopi	Paopi 15		0
49	Paopi	Paopi 16		0
50	Paopi	Paopi 17		0
51	Paopi	Paopi 18		0
52	Paopi	Paopi 19		0
53	Paopi	Paopi 20		0
54	Paopi	Paopi 21		0
55	Paopi	Paopi 22		0
56	Paopi	Paopi 23		0
57	Paopi	Paopi 24		0
58	Paopi	Paopi 25		0
59	Paopi	Paopi 26		0
60	Paopi	Paopi 27		0
61	Paopi	Paopi 28		0
62	Paopi	Paopi 29		0
63	Paopi	Paopi 30		0
64	Paopi	The First Sunday of Paopi		1
65	Paopi	The Second Sunday of Paopi		1
66	Paopi	The Third Sunday of Paopi		1
67	Paopi	The Fourth Sunday of Paopi		1
68	Paopi	The Fifth Sunday of Paopi		1
69	Hathor	Hathor 1		0
70	Hathor	Hathor 2		0
71	Hathor	Hathor 3		0
72	Hathor	Hathor 4		0
73	Hathor	Hathor 5		0
74	Hathor	Hathor 6		0
75	Hathor	Hathor 7		0
76	Hathor	Hathor 8		0
77	Hathor	Hathor 9		0
78	Hathor	Hathor 10		0
79	Hathor	Hathor 11		0
80	Hathor	Hathor 12		0
81	Hathor	Hathor 13		0
82	Hathor	Hathor 14		0
83	Hathor	Hathor 15		0
84	Hathor	Hathor 16 of Christmas Fast		0
85	Hathor	Hathor 17		0
86	Hathor	Hathor 18		0
87	Hathor	Hathor 19		0
88	Hathor	Hathor 20		0
89	Hathor	Hathor 21		0
90	Hathor	Hathor 22		0
91	Hathor	Hathor 23		0
92	Hathor	Hathor 24		0
93	Hathor	Hathor 25		0
94	Hathor	Hathor 26		0
95	Hathor	Hathor 27		0
96	Hathor	Hathor 28		0
97	Hathor	Hathor 29		0
98	Hathor	Hathor 30		0
99	Hathor	The First Sunday of Hathor		1
100	Hathor	The Second Sunday of Hathor		1
101	Hathor	The Third Sunday of Hathor		1
102	Hathor	The Fourth Sunday of Hathor		1
103	Koiak	Koiak 1		0
104	Koiak	Koiak 2		0
105	Koiak	Koiak 3		0
106	Koiak	Koiak 4		0
107	Koiak	Koiak 5		0
108	Koiak	Koiak 6		0
109	Koiak	Koiak 7		0
110	Koiak	Koiak 8		0
111	Koiak	Koiak 9		0
112	Koiak	Koiak 10		0
113	Koiak	Koiak 11		0
114	Koiak	Koiak 12		0
115	Koiak	Koiak 13		0
116	Koiak	Koiak 14		0
117	Koiak	Koiak 15		0
118	Koiak	Koiak 16		0
119	Koiak	Koiak 17		0
120	Koiak	Koiak 18		0
121	Koiak	Koiak 19		0
122	Koiak	Koiak 20		0
123	Koiak	Koiak 21		0
124	Koiak	Koiak 22		0
125	Koiak	Koiak 23		0
126	Koiak	Koiak 24		0
127	Koiak	Koiak 25		0
128	Koiak	Koiak 26		0
129	Koiak	Koiak 27		0
130	Koiak	Christmas Paramoune		0
131	Koiak	Nativity of Our Lord Jesus Christ	major	1
132	Koiak	Koiak 30		0
133	Koiak	The First Sunday of Koiak		1
134	Koiak	The Second Sunday of Koiak		1
135	Koiak	The Third Sunday of Koiak		1
136	Koiak	The Fourth Sunday of Koiak		1
137	Tobi	Tobi 1		0
138	Tobi	Tobi 2		0
139	Tobi	Tobi 3		0
140	Tobi	Tobi 4		0
141	Tobi	Tobi 5		0
142	Tobi	Circumcision of Our Lord Jesus Christ	minor	1
143	Tobi	Tobi 7		0
144	Tobi	Tobi 8		0
145	Tobi	Tobi 9		0
146	Tobi	Epiphany Paramoune		0
147	Tobi	Theophany of Our Lord	major	1
148	Tobi	The Second Day of Feast of Epiphany		0
149	Tobi	Wedding at Cana of Galilee	minor	1
150	Tobi	Tobi 14		0
151	Tobi	Tobi 15		0
152	Tobi	Tobi 17		0
153	Tobi	Tobi 18		0
154	Tobi	Tobi 19		0
155	Tobi	Tobi 20		0
156	Tobi	Tobi 21		0
157	Tobi	Tobi 22		0
158	Tobi	Tobi 23		0
159	Tobi	Tobi 24		0
160	Tobi	Tobi 25		0
161	Tobi	Tobi 26		0
162	Tobi	Tobi 27		0
163	Tobi	Tobi 28		0
164	Tobi	Tobi 29		0
165	Tobi	Tobi 30		0
166	Tobi	The First Sunday of Tobi		1
167	Tobi	The Second Sunday of Tobi		1
168	Tobi	The Third Sunday of Tobi		1
169	Tobi	The Fourth Sunday of Tobi		1
170	Tobi	The Fifth Sunday of Tobi		1
171	Meshir	Meshir 1		0
172	Meshir	Meshir 2		0
173	Meshir	Meshir 3		0
174	Meshir	Meshir 4		0
175	Meshir	Meshir 5		0
176	Meshir	Meshir 6		0
177	Meshir	Meshir 7		0
178	Meshir	Presentation of Our Lord into the Temple	minor	1
179	Meshir	Meshir 9		0
180	Meshir	Meshir 10		0
181	Meshir	Meshir 11		0
182	Meshir	Meshir 12		0
183	Meshir	Meshir 13		0
184	Meshir	Meshir 14		0
185	Meshir	Meshir 15		0
186	Meshir	Meshir 16		0
187	Meshir	Meshir 17		0
188	Meshir	Jonah's Feast		0
189	Meshir	Meshir 19		0
190	Meshir	Meshir 20		0
191	Meshir	Meshir 21		0
192	Meshir	Meshir 22		0
193	Meshir	Meshir 23		0
194	Meshir	Meshir 24		0
195	Meshir	Meshir 25		0
196	Meshir	Meshir 26		0
197	Meshir	Meshir 27		0
198	Meshir	Meshir 28		0
199	Meshir	Meshir 29		0
200	Meshir	Meshir 30		0
201	Meshir	The First Sunday of Meshir		1
202	Meshir	The Second Sunday of Meshir		1
203	Meshir	The Third Sunday of Meshir		1
204	Meshir	The Fourth Sunday of Meshir		1
205	Paremhotep	Paremhotep 1		0
206	Paremhotep	Paremhotep 2		0
207	Paremhotep	Paremhotep 3		0
208	Paremhotep	Paremhotep 4		0
209	Paremhotep	Paremhotep 5		0
210	Paremhotep	Paremhotep 6		0
211	Paremhotep	Paremhotep 7		0
212	Paremhotep	Paremhotep 8		0
213	Paremhotep	Paremhotep 9		0
214	Paremhotep	Paremhotep 10		0
215	Paremhotep	Paremhotep 11		0
216	Paremhotep	Paremhotep 12		0
217	Paremhotep	Paremhotep 13		0
218	Paremhotep	Paremhotep 14		0
219	Paremhotep	Paremhotep 15		0
220	Paremhotep	Paremhotep 16		0
221	Paremhotep	Paremhotep 17		0
222	Paremhotep	Paremhotep 18		0
223	Paremhotep	Paremhotep 19		0
224	Paremhotep	Paremhotep 20		0
225	Paremhotep	Paremhotep 21		0
226	Paremhotep	Paremhotep 22		0
227	Paremhotep	Paremhotep 23		0
228	Paremhotep	Paremhotep 24		0
229	Paremhotep	Paremhotep 25		0
230	Paremhotep	Paremhotep 27		0
231	Paremhotep	Paremhotep 28		0
232	Paremhotep	Feast of Annunciation	major	1
233	Parmouti	Parmouti 1		0
234	Parmouti	Parmouti 2		0
235	Parmouti	Parmouti 3		0
236	Parmouti	Parmouti 4		0
237	Parmouti	Parmouti 5		0
238	Parmouti	Parmouti 6		0
239	Parmouti	Parmouti 7		0
240	Parmouti	Parmouti 8		0
241	Parmouti	Parmouti 9		0
242	Parmouti	Parmouti 10		0
243	Parmouti	Parmouti 11		0
244	Parmouti	Parmouti 12		0
245	Parmouti	Parmouti 13		0
246	Parmouti	Parmouti 14		0
247	Parmouti	Parmouti 15		0
248	Parmouti	Parmouti 16		0
249	Parmouti	Parmouti 17		0
250	Parmouti	Parmouti 18		0
251	Parmouti	Parmouti 19		0
252	Parmouti	Parmouti 20		0
253	Parmouti	Parmouti 21		0
254	Parmouti	Parmouti 22		0
255	Parmouti	Parmouti 23		0
256	Parmouti	Parmouti 24		0
257	Parmouti	Parmouti 25		0
258	Parmouti	Parmouti 26		0
259	Parmouti	Parmouti 27		0
260	Parmouti	Parmouti 28		0
261	Parmouti	Parmouti 29		0
262	Parmouti	Parmouti 30		0
263	Pashons	Pashons 1		0
264	Pashons	Pashons 2		0
265	Pashons	Pashons 3		0
266	Pashons	Pashons 4		0
267	Pashons	Pashons 5		0
268	Pashons	Pashons 6		0
269	Pashons	Pashons 7		0
270	Pashons	Pashons 8		0
271	Pashons	Pashons 9		0
272	Pashons	Pashons 10		0
273	Pashons	Pashons 11		0
274	Pashons	Pashons 12		0
275	Pashons	Pashons 13		0
276	Pashons	Pashons 14		0
277	Pashons	Pashons 15		0
278	Pashons	Pashons 16		0
279	Pashons	Pashons 17		0
280	Pashons	Pashons 18		0
281	Pashons	Pashons 19		0
282	Pashons	Pashons 20		0
283	Pashons	Pashons 21		0
284	Pashons	Pashons 22		0
285	Pashons	Pashons 23		0
286	Pashons	Flight into Egypt	minor	1
287	Pashons	Pashons 25		0
288	Pashons	Pashons 26		0
289	Pashons	Pashons 27		0
290	Pashons	Pashons 28		0
291	Pashons	Pashons 29		0
292	Pashons	Pashons 30		0
293	Pashons	The Third Sunday of Pashons		1
294	Pashons	The Fourth Sunday of Pashons		1
295	Paoni	Paoni 1		0
296	Paoni	Paoni 2		0
297	Paoni	Paoni 3		0
298	Paoni	Paoni 4		0
299	Paoni	Paoni 5		0
300	Paoni	Paoni 6		0
301	Paoni	Paoni 7		0
302	Paoni	Paoni 8		0
303	Paoni	Paoni 9		0
304	Paoni	Paoni 10		0
305	Paoni	Paoni 11		0
306	Paoni	Paoni 12		0
307	Paoni	Paoni 13		0
308	Paoni	Paoni 14		0
309	Paoni	Paoni 15		0
310	Paoni	Paoni 16		0
311	Paoni	Paoni 17		0
312	Paoni	Paoni 18		0
313	Paoni	Paoni 19		0
314	Paoni	Paoni 20		0
315	Paoni	Paoni 21		0
316	Paoni	Paoni 22		0
317	Paoni	Paoni 23		0
318	Paoni	Paoni 24		0
319	Paoni	Paoni 25		0
320	Paoni	Paoni 26		0
321	Paoni	Paoni 27		0
322	Paoni	Paoni 28		0
323	Paoni	Paoni 29		0
324	Paoni	Paoni 30		0
325	Paoni	The First Sunday of Paoni		1
326	Paoni	The Second Sunday of Paoni		1
327	Paoni	The Third Sunday of Paoni		1
328	Paoni	The Fourth Sunday of Paoni		1
329	Apip	Apip 1		0
330	Apip	Apip 2		0
331	Apip	Apip 3		0
332	Apip	Apip 4		0
333	Apip	Feast of the Apostles	other	1
334	Apip	Apip 6		0
335	Apip	Apip 7		0
336	Apip	Apip 8		0
337	Apip	Apip 9		0
338	Apip	Apip 10		0
339	Apip	Apip 11		0
340	Apip	Apip 12		0
341	Apip	Apip 13		0
342	Apip	Apip 14		0
343	Apip	Apip 15		0
344	Apip	Apip 16		0
345	Apip	Apip 17		0
346	Apip	Apip 18		0
347	Apip	Apip 19		0
348	Apip	Apip 20		0
349	Apip	Apip 21		0
350	Apip	Apip 22		0
351	Apip	Apip 23		0
352	Apip	Apip 24		0
353	Apip	Apip 25		0
354	Apip	Apip 26		0
355	Apip	Apip 27		0
356	Apip	Apip 28		0
357	Apip	Apip 29		0
358	Apip	Apip 30		0
359	Apip	The First Sunday of Apip		1
360	Apip	The Second Sunday of Apip		1
361	Apip	The Third Sunday of Apip		1
362	Apip	The Fourth Sunday of Apip		1
363	Mesori	Fast of the Holy Theotokos		0
364	Mesori	Mesori 2		0
365	Mesori	Mesori 3		0
366	Mesori	Mesori 4		0
367	Mesori	Mesori 5		0
368	Mesori	Mesori 6		0
369	Mesori	Mesori 7		0
370	Mesori	Mesori 8		0
371	Mesori	Mesori 9		0
372	Mesori	Mesori 10		0
373	Mesori	Mesori 11		0
374	Mesori	Mesori 12		0
375	Mesori	Feast of the Transfiguration	minor	1
376	Mesori	Mesori 14		0
377	Mesori	Mesori 15		0
378	Mesori	Dormition of the Holy Theotokos	other	1
379	Mesori	Mesori 17		0
380	Mesori	Mesori 18		0
381	Mesori	Mesori 19		0
382	Mesori	Mesori 20		0
383	Mesori	Mesori 21		0
384	Mesori	Mesori 22		0
385	Mesori	Mesori 23		0
386	Mesori	Mesori 24		0
387	Mesori	Mesori 25		0
388	Mesori	Mesori 26		0
389	Mesori	Mesori 27		0
390	Mesori	Mesori 28		0
391	Mesori	Mesori 29		0
392	Mesori	Mesori 30		0
393	Mesori	The First Sunday of Mesori		1
394	Mesori	The Second Sunday of Mesori		1
395	Mesori	The Third Sunday of Mesori		1
396	Mesori	The Fourth Sunday of Mesori		1
397	Mesori	The Fifth Sunday of Mesori		1
398	Pi Kogi Enavot	Pi Kogi Enavot 1		0
399	Pi Kogi Enavot	Pi Kogi Enavot 2		0
400	Pi Kogi Enavot	Pi Kogi Enavot 3		0
401	Pi Kogi Enavot	Pi Kogi Enavot 4		0
402	Pi Kogi Enavot	Pi Kogi Enavot 5		0
403	Fast of Nineveh	Fast of Nineveh		0
404	Fast of Nineveh	Tuesday of Ninevah's Fast		0
405	Fast of Nineveh	Wednesday of Ninevah's Fast		0
406	The Great Fast	Saturday of the Week Before Great Lent		0
407	The Great Fast	Sunday of the Week Before Great Lent		1
408	The Great Fast	Beginning of the Holy Great Fast		0
409	The Great Fast	Tuesday of the First Week of Great Lent		0
410	The Great Fast	Wednesday of the First Week of Great Lent		0
411	The Great Fast	Thursday of the First Week of Great Lent		0
412	The Great Fast	Friday of the First Week of Great Lent		0
413	The Great Fast	Saturday of the First Week of Great Lent		0
414	The Great Fast	Sunday of the First Week of Great Lent		1
415	The Great Fast	Monday of the Second Week of Great Lent		0
416	The Great Fast	Tuesday of the Second Week of Great Lent		0
417	The Great Fast	Wednesday of the Second Week of Great Lent		0
418	The Great Fast	Thursday of the Second Week of Great Lent		0
419	The Great Fast	Feast of the Cross		0
420	The Great Fast	Saturday of the Second Week of Great Lent		0
421	The Great Fast	Sunday of the Second Week of Great Lent		1
422	The Great Fast	Monday of the Third Week of Great Lent		0
423	The Great Fast	Tuesday of the Third Week of Great Lent		0
424	The Great Fast	Wednesday of the Third Week of Great Lent		0
425	The Great Fast	Thursday of the Third Week of Great Lent		0
426	The Great Fast	Friday of the Third Week of Great Lent		0
427	The Great Fast	Saturday of the Third Week of Great Lent		0
428	The Great Fast	Sunday of the Third Week of Great Lent		1
429	The Great Fast	Monday of the Fourth Week of Great Lent		0
430	The Great Fast	Tuesday of the Fourth Week of Great Lent		0
431	The Great Fast	Wednesday of the Fourth Week of Great Lent		0
432	The Great Fast	Thursday of the Fourth Week of Great Lent		0
433	The Great Fast	Friday of the Fourth Week of Great Lent		0
434	The Great Fast	Saturday of the Fourth Week of Great Lent		0
435	The Great Fast	Sunday of the Fourth Week of Great Lent		1
436	The Great Fast	Monday of the Fifth Week of Great Lent		0
437	The Great Fast	Tuesday of the Fifth Week of Great Lent		0
438	The Great Fast	Thursday of the Fifth Week of Great Lent		0
439	The Great Fast	Friday of the Fifth Week of Great Lent		0
440	The Great Fast	Saturday of the Fifth Week of Great Lent		0
441	The Great Fast	Sunday of the Fifth Week of Great Lent		1
442	The Great Fast	Monday of the Sixth Week of Great Lent		0
443	The Great Fast	Tuesday of the Sixth Week of Great Lent		0
444	The Great Fast	Wednesday of the Sixth Week of Great Lent		0
445	The Great Fast	Thursday of the Sixth Week of Great Lent		0
446	The Great Fast	Friday of the Sixth Week of Great Lent		0
447	The Great Fast	Saturday of the Sixth Week of Great Lent		0
448	The Great Fast	Sunday of the Sixth Week of Great Lent		1
449	The Great Fast	Monday of the Seventh Week of Great Lent		0
450	The Great Fast	Tuesday of the Seventh Week of Great Lent		0
451	The Great Fast	Wednesday of the Seventh Week of Great Lent		0
452	The Great Fast	Thursday of the Seventh Week of Great Lent		0
453	The Great Fast	Friday of the Seventh Week of Great Lent		0
454	The Great Fast	Lazarus Saturday of Great Lent		0
455	Holy Pascha	Palm Sunday	major	1
456	Holy Pascha	Monday of Holy Week		0
457	Holy Pascha	Tuesday of Holy Week		0
458	Holy Pascha	Wednesday of Holy Week		0
459	Holy Pascha	Covenant Thursday	minor	1
460	Holy Pascha	Good Friday		0
461	Holy Pascha	Bright Saturday	minor	1
462	Holy Pascha	Feast of the Resurrection	major	1
463	Pentecost	Monday of the First Week of Pentecost		0
464	Pentecost	Tuesday of the First Week of Pentecost		0
465	Pentecost	Wednesday of the First Week of Pentecost		0
466	Pentecost	Thursday of the First Week of Pentecost		0
467	Pentecost	Friday of the First Week of Pentecost		0
468	Pentecost	Saturday of the First Week of Pentecost		0
469	Pentecost	Thomas Sunday	minor	1
470	Pentecost	Monday of the Second Week of Pentecost		0
471	Pentecost	Tuesday of the Second Week of Pentecost		0
472	Pentecost	Wednesday of the Second Week of Pentecost		0
473	Pentecost	Thursday of the Second Week of Pentecost		0
474	Pentecost	Friday of the Second Week of Pentecost		0
475	Pentecost	Saturday of the Second Week of Pentecost		0
476	Pentecost	Sunday of the Second Week of Pentecost		1
477	Pentecost	Monday of the Third Week of Pentecost		0
478	Pentecost	Tuesday of the Third Week of Pentecost		0
479	Pentecost	Wednesday of the Third Week of Pentecost		0
480	Pentecost	Thursday of the Third Week of Pentecost		0
481	Pentecost	Friday of the Third Week of Pentecost		0
482	Pentecost	Saturday of the Third Week of Pentecost		0
483	Pentecost	Sunday of the Third Week of Pentecost		1
484	Pentecost	Monday of the Fourth Week of Pentecost		0
485	Pentecost	Tuesday of the Fourth Week of Pentecost		0
486	Pentecost	Wednesday of the Fourth Week of Pentecost		0
487	Pentecost	Thursday of the Fourth Week of Pentecost		0
488	Pentecost	Friday of the Fourth Week of Pentecost		0
489	Pentecost	Saturday of the Fourth Week of Pentecost		0
490	Pentecost	Sunday of the Fourth Week of Pentecost		1
491	Pentecost	Monday of the Fifth Week of Pentecost		0
492	Pentecost	Wednesday of the Fifth Week of Pentecost		0
493	Pentecost	Thursday of the Fifth Week of Pentecost		0
494	Pentecost	Friday of the Fifth Week of Pentecost		0
495	Pentecost	Saturday of the Fifth Week of Pentecost		0
496	Pentecost	Sunday of the Fifth Week of Pentecost		1
497	Pentecost	Monday of the Sixth Week of Pentecost		0
498	Pentecost	Tuesday of the Sixth Week of Pentecost		0
499	Pentecost	Wednesday of the Sixth Week of Pentecost		0
500	Pentecost	Feast of the Ascension	major	1
501	Pentecost	Friday of the Sixth Week of Pentecost		0
502	Pentecost	Saturday of the Sixth Week of Pentecost		0
503	Pentecost	Sunday of the Sixth Week of Pentecost		1
504	Pentecost	Monday of the Seventh Week of Pentecost		0
505	Pentecost	Tuesday of the Seventh Week of Pentecost		0
506	Pentecost	Wednesday of the Seventh Week of Pentecost		0
507	Pentecost	Thursday of the Seventh Week of Pentecost		0
508	Pentecost	Friday of the Seventh Week of Pentecost		0
509	Pentecost	Saturday of the Seventh Week of Pentecost		0
510	Pentecost	Feast of Pentecost	major	1
"""

_READINGS_TSV = """\
0	vespers	0	psalm	Psalm 96:1-2
0	vespers	1	gospel	Matt 13:44-52
0	matins	0	psalm	Psalm 98:1
0	matins	1	gospel	Mk 2:18-22
0	liturgy	0	psalm	Psalm 65:11|Psalm 81:1
0	liturgy	1	gospel	Lk 4:14-30
1	vespers	0	psalm	Psalm 52:8-9
1	vespers	1	gospel	Matt 14:1-12
1	matins	0	psalm	Psalm 92:10|Psalm 92:14|Psalm 92:15
1	matins	1	gospel	Lk 9:7-12
1	liturgy	0	psalm	Psalm 92:12-13
1	liturgy	1	gospel	Mk 6:14-29
2	vespers	0	psalm	Psalm 110:4|Psalm 110:7
2	vespers	1	gospel	Matthew 16:13-19
2	matins	0	psalm	Psalm 73:23-24|Psalm 73:28|Psalm 9:14
2	matins	1	gospel	John 15:17-25
2	liturgy	0	psalm	Psalm 107:32|Psalm 107:41-42
2	liturgy	1	gospel	John 10:1-16
3	vespers	0	psalm	Psalm 105:14-15
3	vespers	1	gospel	Lk 11:37-51
3	matins	0	psalm	Psalm 105:26|Psalm 105:27|Psalm 105:45
3	matins	1	gospel	Matt 17:1-9
3	liturgy	0	psalm	Psalm 99:6-7
3	liturgy	1	gospel	Matt 23:13-26
4	vespers	0	psalm	Psalm 68:25-26
4	vespers	1	gospel	Matt 26:6 - 13
4	matins	0	psalm	Psalm 8:2 - 3
4	matins	1	gospel	Jn 4:15 - 24
4	liturgy	0	psalm	Psalm 45:14 - 15
4	liturgy	1	gospel	Matt 25:1 - 13
5	vespers	0	psalm	Psalm 105:14-15
5	vespers	1	gospel	Lk 11:37-51
5	matins	0	psalm	Psalm 105:26|Psalm 105:27|Psalm 105:45
5	matins	1	gospel	Matt 17:1-9
5	liturgy	0	psalm	Psalm 99:6-7
5	liturgy	1	gospel	Matt 23:13-26
6	vespers	0	psalm	Psalm 110:4,5|Psalm 110:7
6	vespers	1	gospel	Matt 16:13 -19
6	matins	0	psalm	Psalm 73:23|Psalm 73:24|Psalm 73:28|Psalm 9: 14
6	matins	1	gospel	Jn 15:17-25
6	liturgy	0	psalm	Psalm 107:32|Psalm 107:41|Psalm 107:42
6	liturgy	1	gospel	Jn 10:1-16
7	vespers	0	psalm	Psalm 105:14-15
7	vespers	1	gospel	Lk 11:37-51
7	matins	0	psalm	Psalm 105:26|Psalm 105:27|Psalm 105:45
7	matins	1	gospel	Matt 17:1-9
7	liturgy	0	psalm	Psalm 99:6-7
7	liturgy	1	gospel	Matt 23:13-26
8	vespers	0	psalm	Psalm 89:19-21
8	vespers	1	gospel	Matt 10:34-42
8	matins	0	psalm	Psalm 132:9|Psalm 132:10|Psalm 132:17|Psalm 132:18
8	matins	1	gospel	Lk 6:17-23
8	liturgy	0	psalm	Psalm 99:6-7
8	liturgy	1	gospel	Jn 16:20-33
9	vespers	0	psalm	Psalm 68:25-26
9	vespers	1	gospel	Matthew 26:6-13
9	matins	0	psalm	Psalm 8:2-3
9	matins	1	gospel	John 4:15-24
9	liturgy	0	psalm	Psalm 45:14-15
9	liturgy	1	gospel	Matthew 25:1-13
10	vespers	0	psalm	Psalm 4:6-8
10	vespers	1	gospel	Matt 16:24-28
10	matins	0	psalm	Psalm 5:11|Psalm 5:12
10	matins	1	gospel	Matt 10:34-42
10	liturgy	0	psalm	Psalm 68:35|Psalm 68:3
10	liturgy	1	gospel	Lk 12:4-12
11	vespers	0	psalm	Psalm 32:11|Psalm 32:6
11	vespers	1	gospel	Matt 25:14-23
11	matins	0	psalm	Psalm 112:1-2
11	matins	1	gospel	Lk 6:17-23
11	liturgy	0	psalm	Psalm 19:4|Psalm 132:9,10
11	liturgy	1	gospel	Matt 16:13-19
12	vespers	0	psalm	Psalm 132:9,10,17,18
12	vespers	1	gospel	Matt 4:23—|Matt 5:1-16
12	matins	0	psalm	Psalm 110:4|Psalm 110:5|Psalm 110:7
12	matins	1	gospel	Lk 6:17-23
12	liturgy	0	psalm	Psalm 73:23|Psalm 73:24|Psalm 73:28
12	liturgy	1	gospel	Jn 10:1-16
13	vespers	0	psalm	Psalm 40:2-3
13	vespers	1	gospel	Matt 7:22-25
13	matins	0	psalm	Psalm 89:24|Psalm 89:19
13	matins	1	gospel	Lk 13:23-30
13	liturgy	0	psalm	Psalm 61:1-3
13	liturgy	1	gospel	Lk 14:25-35
14	vespers	0	psalm	Psalm 5:11-12
14	vespers	1	gospel	Matt 10:24-33
14	matins	0	psalm	Psalm 34:19-20
14	matins	1	gospel	Jn 12:20-26
14	liturgy	0	psalm	Psalm 21:3|Psalm 21:5
14	liturgy	1	gospel	Lk 10:1-20
15	vespers	0	psalm	Psalm 84:3-4
15	vespers	1	gospel	Lk 7:1-10
15	matins	0	psalm	Psalm 26:8|Psalm 26:7
15	matins	1	gospel	Lk 19:1-10
15	liturgy	0	psalm	Psalm 65:1-2
15	liturgy	1	gospel	Matt 16:13-19
16	vespers	0	psalm	Psalm 4:6-8
16	vespers	1	gospel	Jn 8:28-42
16	matins	0	psalm	Psalm 60:4-5
16	matins	1	gospel	Jn 12:26-36
16	liturgy	0	psalm	Psalm 65:1-2
16	liturgy	1	gospel	Jn 10:22-38
17	vespers	0	psalm	Psalm 99:9|Psalm 99:5
17	vespers	1	gospel	Jn 4:19-24
17	matins	0	psalm	Psalm 118:28|Psalm 118:16
17	matins	1	gospel	Jn 3:14-21
17	liturgy	0	psalm	Psalm 145:1-2
17	liturgy	1	gospel	Jn 6:35-46
18	vespers	0	psalm	Psalm 45:6,17
18	vespers	1	gospel	Matt 16:21-26
18	matins	0	psalm	Psalm 74:2|Psalm 74:12
18	matins	1	gospel	Mk 8:34—|Mk 9:1-1
18	liturgy	0	psalm	Psalm 62:2|Psalm 62:3|Psalm 62:5
18	liturgy	1	gospel	Lk 14:25-32
19	vespers	0	psalm	Psalm 68:25-26
19	vespers	1	gospel	Matt 26:6 - 13
19	matins	0	psalm	Psalm 8:2 - 3
19	matins	1	gospel	Jn 4:15 - 24
19	liturgy	0	psalm	Psalm 45:14 - 15
19	liturgy	1	gospel	Matt 25:1 - 13
20	vespers	0	psalm	Psalm 64:10
20	vespers	1	gospel	Mk 4:21-25
20	matins	0	psalm	Psalm 70:5
20	matins	1	gospel	Mk 3:22-27
20	liturgy	0	psalm	Psalm 16:10-11
20	liturgy	1	gospel	Mk 3:28-35
21	vespers	0	psalm	Psalm 4:6-8
21	vespers	1	gospel	Matt 16:24-28
21	matins	0	psalm	Psalm 5:11|Psalm 5:12
21	matins	1	gospel	Matt 10:34-42
21	liturgy	0	psalm	Psalm 68:35|Psalm 68:3
21	liturgy	1	gospel	Lk 12:4-12
22	vespers	0	psalm	Psalm 64:10
22	vespers	1	gospel	Mk 4:21-25
22	matins	0	psalm	Psalm 70:5
22	matins	1	gospel	Mk 3:22-27
22	liturgy	0	psalm	Psalm 16:10-11
22	liturgy	1	gospel	Mk 3:28-35
23	vespers	0	psalm	Psalm 5:11-12
23	vespers	1	gospel	Matthew 10:24-33
23	matins	0	psalm	Psalm 34:19-20
23	matins	1	gospel	John 12:20-26
23	liturgy	0	psalm	Psalm 21:3|Psalm 21:5
23	liturgy	1	gospel	Luke 10:1-20
24	vespers	0	psalm	Psalm 105:14-15
24	vespers	1	gospel	Lk 11:37-51
24	matins	0	psalm	Psalm 105:26|Psalm 105:27|Psalm 105:45
24	matins	1	gospel	Matt 17:1-9
24	liturgy	0	psalm	Psalm 99:6-7
24	liturgy	1	gospel	Matt 23:13-36
25	vespers	0	psalm	Psalm 9:11,14
25	vespers	1	gospel	Mk 14:3-9
25	matins	0	psalm	Psalm 102:19-21
25	matins	1	gospel	Mk 12:41-44
25	liturgy	0	psalm	Psalm 102:13|Psalm 102:16|Psalm 102:17
25	liturgy	1	gospel	Lk 1:1-25
26	vespers	0	psalm	Psalm 4:3,6,7
26	vespers	1	gospel	Matt 10:24-33
26	matins	0	psalm	Psalm 113:1-2
26	matins	1	gospel	Mk 8:34—|Mk 9:1-1
26	liturgy	0	psalm	Psalm 66:12-14
26	liturgy	1	gospel	Lk 21:12-19
27	vespers	0	psalm	Psalm 4:3,6,7
27	vespers	1	gospel	Matt 10:24-33
27	matins	0	psalm	Psalm 113:1-2
27	matins	1	gospel	Mk 8:34—|Mk 9:1-1
27	liturgy	0	psalm	Psalm 66:12-14
27	liturgy	1	gospel	Lk 21:12-19
28	vespers	0	psalm	Psalm 68:25-26
28	vespers	1	gospel	Matt 26:6 - 13
28	matins	0	psalm	Psalm 8:2 - 3
28	matins	1	gospel	Jn 4:15 - 24
28	liturgy	0	psalm	Psalm 45:14 - 15
28	liturgy	1	gospel	Matt 25:1 - 13
29	vespers	0	psalm	Psalm 132:9,10,17,18
29	vespers	1	gospel	Matt 4:23—|Matt 5:1-16
29	matins	0	psalm	Psalm 110:4|Psalm 110:5|Psalm 110:7
29	matins	1	gospel	Lk 6:17-23
29	liturgy	0	psalm	Psalm 73:23|Psalm 73:24|Psalm 73:28
29	liturgy	1	gospel	Jn 10:1-16
30	vespers	0	psalm	Psalm 30:4,10
30	vespers	1	gospel	Mt 11:11-19
30	matins	0	psalm	Psalm 31:1|Psalm 31:19
30	matins	1	gospel	Mt 21:23-27
30	liturgy	0	psalm	Psalm 31:23|Psalm 31:19
30	liturgy	1	gospel	Lk 7:28-35
31	vespers	0	psalm	Psalm 7:10,11
31	vespers	1	gospel	Lk 4:38-41
31	matins	0	psalm	Psalm 8:1|Psalm 8:4
31	matins	1	gospel	Mk 1:35-39
31	liturgy	0	psalm	Psalm 21:1-2
31	liturgy	1	gospel	Lk 10:21-28
32	vespers	0	psalm	Psalm 9:1-2
32	vespers	1	gospel	Mark 1:29-34
32	matins	0	psalm	Psalm 9:10-11
32	matins	1	gospel	Matthew 8:5-13
32	liturgy	0	psalm	Psalm 18:46,49
32	liturgy	1	gospel	Luke 19:1-10
33	vespers	0	psalm	Psalm 33:4-5
33	vespers	1	gospel	Mt 9:18-26
33	matins	0	psalm	Psalm 33:20-21
33	matins	1	gospel	Mt 15:21-28
33	liturgy	0	psalm	Psalm 28:8-9
33	liturgy	1	gospel	Lk 7:36-50
34	vespers	0	psalm	Psalm 68:25-26
34	vespers	1	gospel	Matthew 26:6-13
34	matins	0	psalm	Psalm 8:2-3
34	matins	1	gospel	John 4:15-24
34	liturgy	0	psalm	Psalm 45:14-15
34	liturgy	1	gospel	Matthew 25:1-13
35	vespers	0	psalm	Psalm 110:4,5|Psalm 110:7
35	vespers	1	gospel	Matt 16:13 -19
35	matins	0	psalm	Psalm 73:23|Psalm 73:24|Psalm 73:28|Psalm 9: 14
35	matins	1	gospel	Jn 15:17-25
35	liturgy	0	psalm	Psalm 107:32|Psalm 107:41|Psalm 107:42
35	liturgy	1	gospel	Jn 10:1-16
36	vespers	0	psalm	Psalm 132:9,10,17,18
36	vespers	1	gospel	Matt 4:23—|Matt 5:1-16
36	matins	0	psalm	Psalm 110:4|Psalm 110:5|Psalm 110:7
36	matins	1	gospel	Lk 6:17-23
36	liturgy	0	psalm	Psalm 73:23|Psalm 73:24|Psalm 73:28
36	liturgy	1	gospel	Jn 10:1-16
37	vespers	0	psalm	Psalm 34:19-20
37	vespers	1	gospel	Matt 16:24-28
37	matins	0	psalm	Psalm 37:39-40
37	matins	1	gospel	Mk 13:9-13
37	liturgy	0	psalm	Psalm 97:11-12
37	liturgy	1	gospel	Lk 11:53—|Lk 12:1-12
38	vespers	0	psalm	Psalm 132:9,10,17,18
38	vespers	1	gospel	Matt 4:23—|Matt 5:1-16
38	matins	0	psalm	Psalm 110:4|Psalm 110:5|Psalm 110:7
38	matins	1	gospel	Lk 6:17-23
38	liturgy	0	psalm	Psalm 73:23|Psalm 73:24|Psalm 73:28
38	liturgy	1	gospel	Jn 10:1-16
39	vespers	0	psalm	Psalm 4:7-8
39	vespers	1	gospel	Matt 19:1-12
39	matins	0	psalm	Psalm 104:15,24
39	matins	1	gospel	Jn 4:43-54
39	liturgy	0	psalm	Psalm 77:14-16
39	liturgy	1	gospel	John 2:1-11
40	vespers	0	psalm	Psalm 65:4-5
40	vespers	1	gospel	Matt 24:42-47
40	matins	0	psalm	Psalm 37:17|Psalm 37:18|Psalm 37:29
40	matins	1	gospel	Mk 13:33-37
40	liturgy	0	psalm	Psalm 37:30-31
40	liturgy	1	gospel	Lk 16:1-12
41	vespers	0	psalm	Psalm 18:34|Psalm 18:39
41	vespers	1	gospel	Matthew 8:5-13
41	matins	0	psalm	Psalm 68:35|Psalm 68:3
41	matins	1	gospel	Luke 12:4-12
41	liturgy	0	psalm	Psalm 45:3-4
41	liturgy	1	gospel	Matthew 12:9-23
42	vespers	0	psalm	Psalm 132:9,10,17,18
42	vespers	1	gospel	Matt 4:23—|Matt 5:1-16
42	matins	0	psalm	Psalm 110:4|Psalm 110:5|Psalm 110:7
42	matins	1	gospel	Lk 6:17-23
42	liturgy	0	psalm	Psalm 73:23|Psalm 73:24|Psalm 73:28
42	liturgy	1	gospel	Jn 10:1-16
43	vespers	0	psalm	Psalm 34:19-20
43	vespers	1	gospel	Matt 16:24-28
43	matins	0	psalm	Psalm 37:39-40
43	matins	1	gospel	Mk 13:9-13
43	liturgy	0	psalm	Psalm 97:11-12
43	liturgy	1	gospel	Lk 11:53—|Lk 12:1-12
44	vespers	0	psalm	Psalm 110:4,5|Psalm 110:7
44	vespers	1	gospel	Matt 16:13 -19
44	matins	0	psalm	Psalm 73:23|Psalm 73:24|Psalm 73:28|Psalm 9: 14
44	matins	1	gospel	Jn 15:17-25
44	liturgy	0	psalm	Psalm 107:32|Psalm 107:41|Psalm 107:42
44	liturgy	1	gospel	Jn 10:1-16
45	vespers	0	psalm	Psalm 22:22-23
45	vespers	1	gospel	Matt 9:9-13
45	matins	0	psalm	Psalm 40:9-10
45	matins	1	gospel	Mk 2:13-17
45	liturgy	0	psalm	Psalm 68:11-12
45	liturgy	1	gospel	Lk 5:27-32
46	vespers	0	psalm	Psalm 65:4-5
46	vespers	1	gospel	Matt 24:42-47
46	matins	0	psalm	Psalm 37:17|Psalm 37:18|Psalm 37:29
46	matins	1	gospel	Mk 13:33-37
46	liturgy	0	psalm	Psalm 37:30-31
46	liturgy	1	gospel	Lk 16:1-12
47	vespers	0	psalm	Psalm 68:35|Psalm 68:3
47	vespers	1	gospel	Lk 10:1-20
47	matins	0	psalm	Psalm 145:10-12
47	matins	1	gospel	Jn 1:43-51
47	liturgy	0	psalm	Psalm 32:1-2
47	liturgy	1	gospel	Jn 3:1-21
48	vespers	0	psalm	Psalm 18:34|Psalm 18:39
48	vespers	1	gospel	Matthew 10:16-23
48	matins	0	psalm	Psalm 45:3|Psalm 45:6
48	matins	1	gospel	Luke 7:11-17
48	liturgy	0	psalm	Psalm 91:13|Psalm 91:11
48	liturgy	1	gospel	Luke 10:21-24
49	vespers	0	psalm	Psalm 89:36|Psalm 89:29
49	vespers	1	gospel	Lk 9:18-27
49	matins	0	psalm	Psalm 107:32|Psalm 107:41|Psalm 107:42
49	matins	1	gospel	Mk 8:22-29
49	liturgy	0	psalm	Psalm 110:4|Psalm 110:5|Psalm 110:7
49	liturgy	1	gospel	Matt 16:13 - 19
50	vespers	0	psalm	Psalm 110:4,5|Psalm 110:7
50	vespers	1	gospel	Matt 16:13 -19
50	matins	0	psalm	Psalm 73:23|Psalm 73:24|Psalm 73:28|Psalm 9: 14
50	matins	1	gospel	Jn 15:17-25
50	liturgy	0	psalm	Psalm 107:32|Psalm 107:41|Psalm 107:42
50	liturgy	1	gospel	Jn 10:1-16
51	vespers	0	psalm	Psalm 89:36|Psalm 89:29
51	vespers	1	gospel	Lk 9:18-27
51	matins	0	psalm	Psalm 107:32|Psalm 107:41|Psalm 107:42
51	matins	1	gospel	Mk 8:22-29
51	liturgy	0	psalm	Psalm 110:4|Psalm 110:5|Psalm 110:7
51	liturgy	1	gospel	Matt 16:13 - 19
52	vespers	0	psalm	Psalm 18:34,39
52	vespers	1	gospel	Matt 10:16-23
52	matins	0	psalm	Psalm 45:3|Psalm 45:6
52	matins	1	gospel	Lk 7:11-17
52	liturgy	0	psalm	Psalm 91:13|Psalm 91:11
52	liturgy	1	gospel	Lk 10:21-24
53	vespers	0	psalm	Psalm 32:11|Psalm 32:6
53	vespers	1	gospel	Lk 22:24 - 30
53	matins	0	psalm	Psalm 33:1|Psalm 33:12
53	matins	1	gospel	Matt 25:14 - 23
53	liturgy	0	psalm	Psalm 132:9|Psalm 132:10|Psalm 132:1|Psalm 132:2
53	liturgy	1	gospel	Mark 9:33 - 41
54	vespers	0	psalm	Psalm 105:14-15
54	vespers	1	gospel	Lk 11:37-51
54	matins	0	psalm	Psalm 105:26|Psalm 105:27|Psalm 105:45
54	matins	1	gospel	Matt 17:1-9
54	liturgy	0	psalm	Psalm 99:6-7
54	liturgy	1	gospel	Matt 23:13-36
55	vespers	0	psalm	Psalm 105:1-3
55	vespers	1	gospel	Luke 9:1-6
55	matins	0	psalm	Psalm 68:24|Psalm 68:26
55	matins	1	gospel	Luke 17:5-10
55	liturgy	0	psalm	Psalm 96:2-3
55	liturgy	1	gospel	Luke 10:1-20
56	vespers	0	psalm	Psalm 89:19-21
56	vespers	1	gospel	Matt 10:34-42
56	matins	0	psalm	Psalm 132:9|Psalm 132:10|Psalm 132:17|Psalm 132:18
56	matins	1	gospel	Lk 6:17-23
56	liturgy	0	psalm	Psalm 99:6-7
56	liturgy	1	gospel	Jn 16:20-33
57	vespers	0	psalm	Psalm 32:11|33:1|32:6
57	vespers	1	gospel	Matt 25:14 - 23
57	matins	0	psalm	Psalm 33:1|Psalm 33:12
57	matins	1	gospel	Lk 19:11 - 19
57	liturgy	0	psalm	Psalm 34:19|Psalm 68:3
57	liturgy	1	gospel	Lk 12:32 - 44
58	vespers	0	psalm	Psalm 65:4-5
58	vespers	1	gospel	Matt 24:42-47
58	matins	0	psalm	Psalm 37:17|Psalm 37:18|Psalm 37:29
58	matins	1	gospel	Mk 13:33-37
58	liturgy	0	psalm	Psalm 37:30-31
58	liturgy	1	gospel	Lk 16:1-12
59	vespers	0	psalm	Psalm 5:11-12
59	vespers	1	gospel	Matt 10:24-33
59	matins	0	psalm	Psalm 34:19-20
59	matins	1	gospel	Jn 12:20-26
59	liturgy	0	psalm	Psalm 21:3|Psalm 21:5
59	liturgy	1	gospel	Lk 10:1-20
60	vespers	0	psalm	Psalm 112:1-2
60	vespers	1	gospel	Matt 25:14-23
60	matins	0	psalm	Psalm 132:1|Psalm 132:2|Psalm 132:9|Psalm 132:10
60	matins	1	gospel	Lk 6:17-23
60	liturgy	0	psalm	Psalm 1:1
60	liturgy	1	gospel	Matt 4:23— - Matt 5:1-16
61	vespers	0	psalm	Psalm 18:34,39
61	vespers	1	gospel	Matt 8:5-13
61	matins	0	psalm	Psalm 68:35|Psalm 68:3
61	matins	1	gospel	Lk 12:4-12
61	liturgy	0	psalm	Psalm 45:3-4
61	liturgy	1	gospel	Matt 12:9-23
62	vespers	0	psalm	Psalm 46:1|Psalm 46:7
62	matins	0	psalm	Psalm 146:1|Psalm 146:5
62	matins	1	gospel	Matthew 4:18-22
62	liturgy	0	psalm	Psalm 78:5|Psalm 135:5
62	liturgy	1	gospel	Mark 10:35-45
63	vespers	0	psalm	Psalm 40:9|Psalm 40:2
63	vespers	1	gospel	Mk 6:6-13
63	matins	0	psalm	Psalm 105:1-3
63	matins	1	gospel	Mark 10:17-30
63	liturgy	0	psalm	Psalm 96:1|Psalm 96:2
63	liturgy	1	gospel	Mk 1:1-11
64	vespers	0	psalm	Psalm 67:1-2
64	vespers	1	gospel	Mt 14:15-21
64	matins	0	psalm	Psalm 63:1-2
64	matins	1	gospel	Mt 28:1-20
64	liturgy	0	psalm	Psalm 34:1-2
64	liturgy	1	gospel	Mk 2:1-12
65	vespers	0	psalm	Psalm 37:3-4
65	vespers	1	gospel	Mt 17:24-27
65	matins	0	psalm	Psalm 63:6|Psalm 63:3|Psalm 63:4
65	matins	1	gospel	Mk 16:2-8
65	liturgy	0	psalm	Psalm 66:1-2,4
65	liturgy	1	gospel	Lk 5:1-11
66	vespers	0	psalm	Psalm 71:5-7
66	vespers	1	gospel	Mk 4:35-41
66	matins	0	psalm	Psalm 57:8-9
66	matins	1	gospel	Lk 24:1-12
66	liturgy	0	psalm	Psalm 71:7-8
66	liturgy	1	gospel	Mt 12:22-28
67	vespers	0	psalm	Psalm 119:7-8
67	vespers	1	gospel	Mt 14:22-26
67	matins	0	psalm	Psalm 35:18|Psalm 35:28
67	matins	1	gospel	Jn 20:1-18
67	liturgy	0	psalm	Psalm 79:13
67	liturgy	1	gospel	Lk 7:11-17
68	vespers	0	psalm	Psalm 144:5,7
68	vespers	1	gospel	Lk 7:36-50
68	matins	0	psalm	Psalm 72:6-7
68	matins	1	gospel	Lk 11:20-28
68	liturgy	0	psalm	Psalm 45:10-11
68	liturgy	1	gospel	Lk 1:26-38
69	vespers	0	psalm	Psalm 110:4,5|Psalm 110:7
69	vespers	1	gospel	Matt 16:13 -19
69	matins	0	psalm	Psalm 73:23|Psalm 73:24|Psalm 73:28|Psalm 9: 14
69	matins	1	gospel	Jn 15:17-25
69	liturgy	0	psalm	Psalm 107:32|Psalm 107:41|Psalm 107:42
69	liturgy	1	gospel	Jn 10:1-16
70	vespers	0	psalm	Psalm 89:36|Psalm 89:29
70	vespers	1	gospel	Lk 9:18-27
70	matins	0	psalm	Psalm 107:32|Psalm 107:41|Psalm 107:42
70	matins	1	gospel	Mk 8:22-29
70	liturgy	0	psalm	Psalm 110:4|Psalm 110:5|Psalm 110:7
70	liturgy	1	gospel	Matt 16:13 - 19
71	vespers	0	psalm	Psalm 32:11|Psalm 32:6
71	vespers	1	gospel	Matt 25:14-23
71	matins	0	psalm	Psalm 112:1-2
71	matins	1	gospel	Lk 6:17-23
71	liturgy	0	psalm	Psalm 19:4|132:9,10
71	liturgy	1	gospel	Matt 16:13-19
72	vespers	0	psalm	Psalm 89:19-21
72	vespers	1	gospel	Matt 10:34-42
72	matins	0	psalm	Psalm 132:9|Psalm 132:10|Psalm 132:17|Psalm 132:18
72	matins	1	gospel	Lk 6:17-23
72	liturgy	0	psalm	Psalm 99:6-7
72	liturgy	1	gospel	Jn 16:20-33
73	vespers	0	psalm	Psalm 46:1,9
73	vespers	1	gospel	Mk 1:16-22
73	matins	0	psalm	Psalm 146:1|Psalm 146:5
73	matins	1	gospel	Matt 4:18-22
73	liturgy	0	psalm	Psalm 78:5|Psalm 135:5
73	liturgy	1	gospel	Mk 10:35-45
74	vespers	0	psalm	Psalm 132:9-10|Psalm 132:17-18
74	vespers	1	gospel	Matthew 4:23-25|Matthew 5:1-16
74	matins	0	psalm	Psalm 110:4-6
74	matins	1	gospel	Luke 6:17-23
74	liturgy	0	psalm	Psalm 73:23-24|Psalm 73:28|Psalm 9:14
74	liturgy	1	gospel	John 10:1-16
75	vespers	0	psalm	Psalm 34:17,18
75	vespers	1	gospel	Matt 10:16-22
75	matins	0	psalm	Psalm 34:19|Psalm 34:20
75	matins	1	gospel	Mk 8:34—|Mk 9:1-1
75	liturgy	0	psalm	Psalm 97:11|Psalm 97:12
75	liturgy	1	gospel	Lk 21:12-19
76	vespers	0	psalm	Psalm 68:17
76	vespers	1	gospel	Mk 8:34—|Mk 9:1-1
76	matins	0	psalm	Psalm 33:6|Psalm 33:9
76	matins	1	gospel	Jn 12:26-36
76	liturgy	0	psalm	Psalm 80:1-3
76	liturgy	1	gospel	Jn 1:43-51
77	vespers	0	psalm	Psalm 32:11|Psalm 32:6
77	vespers	1	gospel	Matt 25:14-23
77	matins	0	psalm	Psalm 112:1-2
77	matins	1	gospel	Lk 6:17-23
77	liturgy	0	psalm	Psalm 19:4|132:9,10
77	liturgy	1	gospel	Matt 16:13-19
78	vespers	0	psalm	Psalm 68:25-26
78	vespers	1	gospel	Matt 26:6 - 13
78	matins	0	psalm	Psalm 8:2 - 3
78	matins	1	gospel	Jn 4:15 - 24
78	liturgy	0	psalm	Psalm 45:14 - 15
78	liturgy	1	gospel	Matt 25:1 - 13
79	vespers	0	psalm	Psalm 4:3,6,7
79	vespers	1	gospel	Matt 10:24-33
79	matins	0	psalm	Psalm 113:1-2
79	matins	1	gospel	Mk 8:34—|Mk 9:1-1
79	liturgy	0	psalm	Psalm 66:12-14
79	liturgy	1	gospel	Lk 21:12-19
80	vespers	0	psalm	Psalm 148:1-2
80	vespers	1	gospel	Matt 13:44-52
80	matins	0	psalm	Psalm 104:4|Psalm 104:3
80	matins	1	gospel	Lk 15:3-10
80	liturgy	0	psalm	Psalm 103:20-21
80	liturgy	1	gospel	Matt 13:24-43
81	vespers	0	psalm	Psalm 110:4|Psalm 110:7
81	vespers	1	gospel	Matthew 16:13-19
81	matins	0	psalm	Psalm 73:23-24|Psalm 73:28|Psalm 9:14
81	matins	1	gospel	John 15:17-25
81	liturgy	0	psalm	Psalm 107:32|Psalm 107:41-42
81	liturgy	1	gospel	John 10:1-16
82	vespers	0	psalm	Psalm 89:19-21
82	vespers	1	gospel	Matt 10:34-42
82	matins	0	psalm	Psalm 132:9|Psalm 132:10|Psalm 132:17|Psalm 132:18
82	matins	1	gospel	Lk 6:17-23
82	liturgy	0	psalm	Psalm 99:6-7
82	liturgy	1	gospel	Jn 16:20-33
83	vespers	0	psalm	Psalm 68:35|Psalm 68:3
83	vespers	1	gospel	Matt 10:16-23
83	matins	0	psalm	Psalm 97:11-12
83	matins	1	gospel	Mk 13:9-13
83	liturgy	0	psalm	Psalm 34:19-20
83	liturgy	1	gospel	Lk 11:53—|Lk 12:1-12
84	vespers	0	psalm	Psalm 112:6|Psalm 112:7|Psalm 112:9
84	vespers	1	gospel	Matt 24:42-47
84	matins	0	psalm	Psalm 92:10|Psalm 92:14|Psalm 92:15
84	matins	1	gospel	Lk 19:11 - 19
84	liturgy	0	psalm	Psalm 92:12-13
84	liturgy	1	gospel	Lk 12:32 - 44
85	vespers	0	psalm	Psalm 132:9,10,17,18
85	vespers	1	gospel	Matt 4:23—|Matt 5:1-16
85	matins	0	psalm	Psalm 110:4|Psalm 110:5|Psalm 110:7
85	matins	1	gospel	Lk 6:17-23
85	liturgy	0	psalm	Psalm 73:23|Psalm 73:24|Psalm 73:28
85	liturgy	1	gospel	Jn 10:1-16
86	vespers	0	psalm	Psalm 68:11,35
86	vespers	1	gospel	Mk 3:7-21
86	matins	0	psalm	Psalm 145:10-12
86	matins	1	gospel	Lk 6:12-23
86	liturgy	0	psalm	Psalm 19:1|Psalm 19:4
86	liturgy	1	gospel	Matt 10:1-15
87	vespers	0	psalm	Psalm 37:39-40
87	vespers	1	gospel	Matt 16:24-28
87	matins	0	psalm	Psalm 37:39-40
87	matins	1	gospel	Mk 13:9-13
87	liturgy	0	psalm	Psalm 97:11-12
87	liturgy	1	gospel	Lk 11:53—|Lk 12:1-12
88	vespers	0	psalm	Psalm 40:9|Psalm 40:2
88	vespers	1	gospel	Mark 6:6-13
88	matins	0	psalm	Psalm 105:1-3
88	matins	1	gospel	Mark 10:17-30
88	liturgy	0	psalm	Psalm 96:1-2
88	liturgy	1	gospel	Mark 1:1-11
89	vespers	0	psalm	Psalm 132:9,10,17,18
89	vespers	1	gospel	Matt 4:23—|Matt 5:1-16
89	matins	0	psalm	Psalm 110:4|Psalm 110:5|Psalm 110:7
89	matins	1	gospel	Lk 6:17-23
89	liturgy	0	psalm	Psalm 73:23|Psalm 73:24|Psalm 73:28
89	liturgy	1	gospel	Jn 10:1-16
90	vespers	0	psalm	Psalm 4:3,6,7
90	vespers	1	gospel	Matt 10:24-33
90	matins	0	psalm	Psalm 113:1-2
90	matins	1	gospel	Mk 8:34—|Mk 9:1-1
90	liturgy	0	psalm	Psalm 66:12-14
90	liturgy	1	gospel	Lk 21:12-19
91	vespers	0	psalm	Psalm 89:19-21
91	vespers	1	gospel	Matt 10:34-42
91	matins	0	psalm	Psalm 132:9|Psalm 132:10|Psalm 132:17|Psalm 132:18
91	matins	1	gospel	Lk 6:17-23
91	liturgy	0	psalm	Psalm 99:6-7
91	liturgy	1	gospel	Jn 16:20-33
92	vespers	0	psalm	Psalm 97:7-8
92	vespers	1	gospel	Matt 11:25-30
92	matins	0	psalm	Psalm 138:1-2
92	matins	1	gospel	Matt 12:1-8
92	liturgy	0	psalm	Psalm 132:9|Psalm 132:10|Psalm 132:17|Psalm 132:18
92	liturgy	1	gospel	Jn 1:1-17
93	vespers	0	psalm	Psalm 18:34,39
93	vespers	1	gospel	Matt 8:5-13
93	matins	0	psalm	Psalm 68:35|Psalm 68:3
93	matins	1	gospel	Lk 12:4-12
93	liturgy	0	psalm	Psalm 45:3-4
93	liturgy	1	gospel	Matt 12:9-23
94	vespers	0	psalm	Psalm 4:3,6,7
94	vespers	1	gospel	Matt 10:24-33
94	matins	0	psalm	Psalm 113:1-2
94	matins	1	gospel	Mk 8:34—|Mk 9:1-1
94	liturgy	0	psalm	Psalm 66:12-14
94	liturgy	1	gospel	Lk 21:12-19
95	vespers	0	psalm	Psalm 46:1|Psalm 46:7
95	matins	0	psalm	Psalm 146:1|Psalm 146:5
95	matins	1	gospel	Matthew 4:18-22
95	liturgy	0	psalm	Psalm 78:5|Psalm 135:5
95	liturgy	1	gospel	Mark 10:35-45
96	vespers	0	psalm	Psalm 89:19-21
96	vespers	1	gospel	Matt 10:34-42
96	matins	0	psalm	Psalm 132:9|Psalm 132:10|Psalm 132:17|Psalm 132:18
96	matins	1	gospel	Lk 6:17-23
96	liturgy	0	psalm	Psalm 99:6-7
96	liturgy	1	gospel	Jn 16:20-33
97	vespers	0	psalm	Psalm 89:36|Psalm 89:29
97	vespers	1	gospel	Lk 9:18-27
97	matins	0	psalm	Psalm 107:32|Psalm 107:41|Psalm 107:42
97	matins	1	gospel	Mk 8:22-29
97	liturgy	0	psalm	Psalm 110:4|Psalm 110:5|Psalm 110:7
97	liturgy	1	gospel	Matt 16:13 - 19
98	vespers	0	psalm	Psalm 110:4,5|Psalm 110:7
98	vespers	1	gospel	Matt 16:13 -19
98	matins	0	psalm	Psalm 73:23|Psalm 73:24|Psalm 73:28|Psalm 9: 14
98	matins	1	gospel	Jn 15:17-25
98	liturgy	0	psalm	Psalm 107:32|Psalm 107:41|Psalm 107:42
98	liturgy	1	gospel	Jn 10:1-16
99	vespers	0	psalm	Psalm 18:15|Psalm 18:6
99	vespers	1	gospel	Mt 14:15-21
99	matins	0	psalm	Psalm 65:9-10
99	matins	1	gospel	Mt 28:1-20
99	liturgy	0	psalm	Psalm 90:5|Psalm 90:7
99	liturgy	1	gospel	Lk 8:4-15
100	vespers	0	psalm	Psalm 104:13-14
100	vespers	1	gospel	Lk 12:27-31
100	matins	0	psalm	Psalm 67:6-7
100	matins	1	gospel	Mk 16:2-8
100	liturgy	0	psalm	Psalm 104:16|Psalm 104:10
100	liturgy	1	gospel	Mt 13:1-9
101	vespers	0	psalm	Psalm 86:2-4
101	vespers	1	gospel	Mt 11:25-30
101	matins	0	psalm	Psalm 113:3-4
101	matins	1	gospel	Lk 24:1-12
101	liturgy	0	psalm	Psalm 86:15-16
101	liturgy	1	gospel	Lk 14:25-35
102	vespers	0	psalm	Psalm 86:12|Psalm 86:10
102	vespers	1	gospel	Mt 17:14-21
102	matins	0	psalm	Psalm 143:8
102	matins	1	gospel	Jn 20:1-18
102	liturgy	0	psalm	Psalm 100:3
102	liturgy	1	gospel	Mk 10:17-31
103	vespers	0	psalm	Psalm 132:9, 10, 17, 18
103	vespers	1	gospel	Matt 4:23-5:16
103	matins	0	psalm	Psalm 110:4,5,7
103	matins	1	gospel	LK 6:17-23
103	liturgy	0	psalm	Psalm 73:23, 24, 28
103	liturgy	1	gospel	JN 10:1-16
104	vespers	0	psalm	Psalm 112:6,7,9
104	vespers	1	gospel	Matt 24:42-47
104	matins	0	psalm	Psalm 92:10|Psalm 92:14|Psalm 92:15
104	matins	1	gospel	Lk 19:11-19
104	liturgy	0	psalm	Psalm 92:12 - 13
104	liturgy	1	gospel	Lk 12:32 - 44
105	vespers	0	psalm	Psalm 87:3,5,7
105	vespers	1	gospel	Lk 10:38-52
105	matins	0	psalm	Psalm 48:8|Psalm 48:1
105	matins	1	gospel	Matt 12:35-50
105	liturgy	0	psalm	Psalm 45:12-13
105	liturgy	1	gospel	Lk 1:39-56
106	vespers	0	psalm	Psalm 68:11|Psalm 68:35
106	vespers	1	gospel	Mark 3:7-21
106	matins	0	psalm	Psalm 145:10-12
106	matins	1	gospel	Luke 6:12-23
106	liturgy	0	psalm	Psalm 19:1|Psalm 19:4
106	liturgy	1	gospel	Matthew 10:1-15
107	vespers	0	psalm	Psalm 105:14-15
107	vespers	1	gospel	Lk 11:37-51
107	matins	0	psalm	Psalm 105:26|Psalm 105:27|Psalm 105:45
107	matins	1	gospel	Matt 17:1-9
107	liturgy	0	psalm	Psalm 99:6-7
107	liturgy	1	gospel	Matt 23:13-36
108	vespers	0	psalm	Psalm 110:4,5|Psalm 110:7
108	vespers	1	gospel	Matt 16:13 -19
108	matins	0	psalm	Psalm 73:23|Psalm 73:24|Psalm 73:28|Psalm 9: 14
108	matins	1	gospel	Jn 15:17-25
108	liturgy	0	psalm	Psalm 107:32|Psalm 107:41|Psalm 107:42
108	liturgy	1	gospel	Jn 10:1-16
109	vespers	0	psalm	Psalm 32:11|Psalm 32:6
109	vespers	1	gospel	Lk 22:24 - 30
109	matins	0	psalm	Psalm 33:1|Psalm 33:12
109	matins	1	gospel	Matt 25:14 - 23
109	liturgy	0	psalm	Psalm 132:9|Psalm 132:10|Psalm 132:1|Psalm 132:2
109	liturgy	1	gospel	Mark 9:33 - 41
110	vespers	0	psalm	Psalm 34:19-20
110	vespers	1	gospel	Matt 16:24-28
110	matins	0	psalm	Psalm 37:39-40
110	matins	1	gospel	Mk 13:9-13
110	liturgy	0	psalm	Psalm 97:11-12
110	liturgy	1	gospel	Lk 11:53—|Lk 12:1-12
111	vespers	0	psalm	Psalm 32:11|33:1|32:6
111	vespers	1	gospel	Matt 25:14 - 23
111	matins	0	psalm	Psalm 33:1|Psalm 33:12
111	matins	1	gospel	Lk 19:11 - 19
111	liturgy	0	psalm	Psalm 34:19|Psalm 68:3
111	liturgy	1	gospel	Lk 12:32 - 44
112	vespers	0	psalm	Psalm 89:19-21
112	vespers	1	gospel	Matt 10:34-42
112	matins	0	psalm	Psalm 132:9|Psalm 132:10|Psalm 132:17|Psalm 132:18
112	matins	1	gospel	Lk 6:17-23
112	liturgy	0	psalm	Psalm 99:6-7
112	liturgy	1	gospel	Jn 16:20-33
113	vespers	0	psalm	Psalm 112:6-7|Psalm 112:9
113	vespers	1	gospel	Matthew 24:42-47
113	matins	0	psalm	Psalm 92:10|Psalm 92:14|Psalm 92:15
113	matins	1	gospel	Luke 19:11-19
113	liturgy	0	psalm	Psalm 92:12-13
113	liturgy	1	gospel	Luke 12:32-44
114	vespers	0	psalm	Psalm 65:4-5
114	vespers	1	gospel	Matt 24:42-47
114	matins	0	psalm	Psalm 37:17|Psalm 37:18|Psalm 37:29
114	matins	1	gospel	Mk 13:33-37
114	liturgy	0	psalm	Psalm 37:30-31
114	liturgy	1	gospel	Lk 16:1-12
115	vespers	0	psalm	Psalm 9:11,14
115	vespers	1	gospel	Mk 14:3-9
115	matins	0	psalm	Psalm 102:19-21
115	matins	1	gospel	Mk 12:41-44
115	liturgy	0	psalm	Psalm 102:13|Psalm 102:16|Psalm 102:17
115	liturgy	1	gospel	Lk 1:1-25
116	vespers	0	psalm	Psalm 4:6-8
116	vespers	1	gospel	Matt 16:24-28
116	matins	0	psalm	Psalm 5:11|Psalm 5:12
116	matins	1	gospel	Matt 10:34-42
116	liturgy	0	psalm	Psalm 68:35|Psalm 68:3
116	liturgy	1	gospel	Lk 12:4-12
117	vespers	0	psalm	Psalm 132:9,10,17,18
117	vespers	1	gospel	Matt 4:23—|Matt 5:1-16
117	matins	0	psalm	Psalm 110:4|Psalm 110:5|Psalm 110:7
117	matins	1	gospel	Lk 6:17-23
117	liturgy	0	psalm	Psalm 73:23|Psalm 73:24|Psalm 73:28
117	liturgy	1	gospel	Jn 10:1-16
118	vespers	0	psalm	Psalm 46:1,9
118	vespers	1	gospel	Mk 1:16-22
118	matins	0	psalm	Psalm 146:1|Psalm 146:5
118	matins	1	gospel	Matt 4:18-22
118	liturgy	0	psalm	Psalm 78:5|Psalm 135:5
118	liturgy	1	gospel	Mk 10:35-45
119	vespers	0	psalm	Psalm 40:2-3
119	vespers	1	gospel	Matt 7:22-25
119	matins	0	psalm	Psalm 89:24|Psalm 89:19
119	matins	1	gospel	Lk 13:23-30
119	liturgy	0	psalm	Psalm 61:1-3
119	liturgy	1	gospel	Lk 14:25-35
120	vespers	0	psalm	Psalm 105:1-3
120	vespers	1	gospel	Luke 9:1-6
120	matins	0	psalm	Psalm 68:24|Psalm 68:26
120	matins	1	gospel	Luke 17:5-10
120	liturgy	0	psalm	Psalm 96:2-3
120	liturgy	1	gospel	Luke 10:1-20
121	vespers	0	psalm	Psalm 89:19-21
121	vespers	1	gospel	Matt 10:34-42
121	matins	0	psalm	Psalm 132:9|Psalm 132:10|Psalm 132:17|Psalm 132:18
121	matins	1	gospel	Lk 6:17-23
121	liturgy	0	psalm	Psalm 99:6-7
121	liturgy	1	gospel	Jn 16:20-33
122	vespers	0	psalm	Psalm 105:14-15
122	vespers	1	gospel	Lk 11:37-51
122	matins	0	psalm	Psalm 105:26|Psalm 105:27|Psalm 105:45
122	matins	1	gospel	Matt 17:1-9
122	liturgy	0	psalm	Psalm 99:6-7
122	liturgy	1	gospel	Matt 23:13-36
123	vespers	0	psalm	Psalm 68:11,35
123	vespers	1	gospel	Mk 3:7-21
123	matins	0	psalm	Psalm 145:10-12
123	matins	1	gospel	Lk 6:12-23
123	liturgy	0	psalm	Psalm 19:1|Psalm 19:4
123	liturgy	1	gospel	Matt 10:1-15
124	vespers	0	psalm	Psalm 34:7-8
124	vespers	1	gospel	Matt 16:24-28
124	matins	0	psalm	Psalm 97:7-8
124	matins	1	gospel	Matt 18:10-20
124	liturgy	0	psalm	Psalm 138:1-2
124	liturgy	1	gospel	Lk 1:26-38
125	vespers	0	psalm	Psalm 105:14-15
125	vespers	1	gospel	Lk 11:37-51
125	matins	0	psalm	Psalm 105:26|Psalm 105:27|Psalm 105:45
125	matins	1	gospel	Matt 17:1-9
125	liturgy	0	psalm	Psalm 99:6-7
125	liturgy	1	gospel	Matt 23:13-36
126	vespers	0	psalm	Psalm 19:1,4
126	vespers	1	gospel	Jn 15:7 - 16
126	matins	0	psalm	Psalm 45:1 - 2
126	matins	1	gospel	Jn 1:1 - 17
126	liturgy	0	psalm	Psalm 139:17 - 18
126	liturgy	1	gospel	John 21:15 - 25
127	vespers	0	psalm	Psalm 32:11|Psalm 32:6
127	vespers	1	gospel	Luke 22:24-30
127	matins	0	psalm	Psalm 33:1|Psalm 33:12
127	matins	1	gospel	Matthew 25:14-23
127	liturgy	0	psalm	Psalm 132:9-10|Psalm 132:1-2
127	liturgy	1	gospel	Mark 9:33-41
128	vespers	0	psalm	Psalm 68:25-26
128	vespers	1	gospel	Matt 26:6 - 13
128	matins	0	psalm	Psalm 8:2 - 3
128	matins	1	gospel	Jn 4:15 - 24
128	liturgy	0	psalm	Psalm 45:14 - 15
128	liturgy	1	gospel	Matt 25:1 - 13
129	vespers	0	psalm	Psalm 89:19-21
129	vespers	1	gospel	Matt 10:34-42
129	matins	0	psalm	Psalm 132:9|Psalm 132:10|Psalm 132:17|Psalm 132:18
129	matins	1	gospel	Lk 6:17-23
129	liturgy	0	psalm	Psalm 99:6-7
129	liturgy	1	gospel	Jn 16:20-33
130	vespers	0	psalm	Psalm 50:2,23
130	vespers	1	gospel	Matt 1:1-17
130	matins	0	psalm	Psalm 76:1|Psalm 76:2
130	matins	1	gospel	Matt 1:18-25
130	liturgy	0	psalm	Psalm 110:3
130	liturgy	1	gospel	Lk 2:1-20
131	vespers	0	psalm	Psalm 72:10
131	vespers	1	gospel	Lk 3:23-38
131	matins	0	psalm	Psalm 72:15-15
131	matins	1	gospel	Jn 1:14-17
131	liturgy	0	psalm	Psalm 2:7-8
131	liturgy	1	gospel	Matt 2:1-12
132	vespers	0	psalm	Psalm 72:1-2
132	vespers	1	gospel	Matt 12:15-23
132	matins	0	psalm	Psalm 72:11|Psalm 72:19
132	matins	1	gospel	Matt 22:41-46
132	liturgy	0	psalm	Psalm 72:17
132	liturgy	1	gospel	Jn 1:1-13
133	vespers	0	psalm	Psalm 13:1,6
133	vespers	1	gospel	Mk 14:3-9
133	matins	0	psalm	Psalm 102:19|Psalm 102:21
133	matins	1	gospel	Mk 12:41-44
133	liturgy	0	psalm	Psalm 102:13|Psalm 102:16
133	liturgy	1	gospel	Lk 1:1-25
134	vespers	0	psalm	Psalm 144:5,7
134	vespers	1	gospel	Lk 7:36-50
134	matins	0	psalm	Psalm 72:6-7
134	matins	1	gospel	Lk 11:20-28
134	liturgy	0	psalm	Psalm 45:10-11
134	liturgy	1	gospel	Lk 1:26-38
135	vespers	0	psalm	Psalm 132:13,15
135	vespers	1	gospel	Mk 1:23-31
135	matins	0	psalm	Psalm 85:7|Psalm 85:8
135	matins	1	gospel	Mt 15:21-31
135	liturgy	0	psalm	Psalm 85:10-11
135	liturgy	1	gospel	Lk 1:39-56
136	vespers	0	psalm	Psalm 87:5
136	vespers	1	gospel	Lk 8:1-3
136	matins	0	psalm	Psalm 96:11-13
136	matins	1	gospel	Mk 3:28-35
136	liturgy	0	psalm	Psalm 80:1-3
136	liturgy	1	gospel	Lk 1:57-80
137	vespers	0	psalm	Psalm 5:11-12
137	vespers	1	gospel	Matt 10:24-33
137	matins	0	psalm	Psalm 34:19-20
137	matins	1	gospel	Jn 12:20-26
137	liturgy	0	psalm	Psalm 21:3|Psalm 21:5
137	liturgy	1	gospel	Lk 10:1-20
138	vespers	0	psalm	Psalm 110:4|Psalm 110:7
138	vespers	1	gospel	Matthew 16:13-19
138	matins	0	psalm	Psalm 73:23-24|Psalm 73:28|Psalm 9:14
138	matins	1	gospel	John 15:17-25
138	liturgy	0	psalm	Psalm 107:32|Psalm 107:41-42
138	liturgy	1	gospel	John 10:1-16
139	vespers	0	psalm	Psalm 115:12-13
139	vespers	1	gospel	Matt 18:1 - 7
139	matins	0	psalm	Psalm 119:130|Psalm 119:141
139	matins	1	gospel	Matt 18:10-20
139	liturgy	0	psalm	Psalm 113:1|Psalm 113:2
139	liturgy	1	gospel	Matt 2:13 - 23
140	vespers	0	psalm	Psalm 19:1,4
140	vespers	1	gospel	Jn 15:7 - 16
140	matins	0	psalm	Psalm 45:1 - 2
140	matins	1	gospel	Jn 1:1 - 17
140	liturgy	0	psalm	Psalm 139:17 - 18
140	liturgy	1	gospel	John 21:15 - 25
141	vespers	0	psalm	Psalm 18:34,39
141	vespers	1	gospel	Matt 8:5-13
141	matins	0	psalm	Psalm 68:35|Psalm 68:3
141	matins	1	gospel	Lk 12:4-12
141	liturgy	0	psalm	Psalm 45:3-4
141	liturgy	1	gospel	Matt 12:9-23
142	vespers	0	psalm	Psalm 116:16 - 19
142	vespers	1	gospel	Lk 2:15 - 20
142	matins	0	psalm	Psalm 66:13 - 15
142	matins	1	gospel	Lk 2:40 - 52
142	liturgy	0	psalm	Psalm 50:14|Psalm 50:23
142	liturgy	1	gospel	Lk 2:21 - 39
143	vespers	0	psalm	Psalm 132:9,10,17,18
143	vespers	1	gospel	Matt 4:23—|Matt 5:1-16
143	matins	0	psalm	Psalm 110:4|Psalm 110:5|Psalm 110:7
143	matins	1	gospel	Lk 6:17-23
143	liturgy	0	psalm	Psalm 73:23|Psalm 73:24|Psalm 73:28
143	liturgy	1	gospel	Jn 10:1-16
144	vespers	0	psalm	Psalm 110:4,5|Psalm 110:7
144	vespers	1	gospel	Matt 16:13 -19
144	matins	0	psalm	Psalm 73:23|Psalm 73:24|Psalm 73:28|Psalm 9: 14
144	matins	1	gospel	Jn 15:17-25
144	liturgy	0	psalm	Psalm 107:32|Psalm 107:41|Psalm 107:42
144	liturgy	1	gospel	Jn 10:1-16
145	vespers	0	psalm	Psalm 112:1-2
145	vespers	1	gospel	Matthew 24:14-23
145	matins	0	psalm	Psalm 132:1-2|Psalm 132:9-10
145	matins	1	gospel	Luke 6:17-23
145	liturgy	0	psalm	Psalm 1:1
145	liturgy	1	gospel	Matthew 4:23-25|Matthew 5:1-16
146	vespers	0	psalm	Psalm 42:2,11
146	vespers	1	gospel	Matt 4:12 - 22
146	matins	0	psalm	Psalm 42:7|Psalm 42:8
146	matins	1	gospel	Jn 3:22 - 29
146	liturgy	0	psalm	Psalm 45:2
146	liturgy	1	gospel	Lk 3:1 - 18
147	vespers	0	psalm	Psalm 42:6,11
147	vespers	1	gospel	Matt 3:1 - 12
147	matins	0	psalm	Psalm 29:3 - 4
147	matins	1	gospel	Mk 1:1 - 11
147	liturgy	0	psalm	Psalm 118:26|Psalm 118:28
147	liturgy	1	gospel	Jn 1:18 - 34
148	vespers	0	psalm	Psalm 42:1,6
148	vespers	1	gospel	Lk 3:21 - 22
148	matins	0	psalm	Psalm 34:11|Psalm 34:5
148	matins	1	gospel	Matt 3:13 - 17
148	liturgy	0	psalm	Psalm 104:1|Psalm 104:2
148	liturgy	1	gospel	Jn 1:35 - 51
149	vespers	0	psalm	Psalm 4:7-8
149	vespers	1	gospel	Matt 19:1 - 12
149	matins	0	psalm	Psalm 104:15|Psalm 104:24
149	matins	1	gospel	Jn 4:43 - 54
149	liturgy	0	psalm	Psalm 77:14 - 16
149	liturgy	1	gospel	Jn 2:1 - 11
150	vespers	0	psalm	Psalm 65:4-5
150	vespers	1	gospel	Matt 24:42-47
150	matins	0	psalm	Psalm 37:17|Psalm 37:18|Psalm 37:29
150	matins	1	gospel	Mk 13:33-37
150	liturgy	0	psalm	Psalm 37:30-31
150	liturgy	1	gospel	Lk 16:1-12
151	vespers	0	psalm	Psalm 105:14-15
151	vespers	1	gospel	Lk 11:37-51
151	matins	0	psalm	Psalm 105:26|Psalm 105:27|Psalm 105:45
151	matins	1	gospel	Matt 17:1-9
151	liturgy	0	psalm	Psalm 99:6-7
151	liturgy	1	gospel	Matt 23:13-36
152	vespers	0	psalm	Psalm 112:6,7,9
152	vespers	1	gospel	Matt 24:42-47
152	matins	0	psalm	Psalm 92:10|Psalm 92:14|Psalm 92:15
152	matins	1	gospel	Lk 19:11-19
152	liturgy	0	psalm	Psalm 92:12 - 13
152	liturgy	1	gospel	Lk 12:32 - 44
153	vespers	0	psalm	Psalm 89:19-21
153	vespers	1	gospel	Matt 10:34-42
153	matins	0	psalm	Psalm 132:9|Psalm 132:10|Psalm 132:17|Psalm 132:18
153	matins	1	gospel	Lk 6:17-23
153	liturgy	0	psalm	Psalm 99:6-7
153	liturgy	1	gospel	Jn 16:20-33
154	vespers	0	psalm	Psalm 4:3,6,7
154	vespers	1	gospel	Matt 10:24-33
154	matins	0	psalm	Psalm 113:1-2
154	matins	1	gospel	Mk 8:34—|Mk 9:1-1
154	liturgy	0	psalm	Psalm 66:12-14
154	liturgy	1	gospel	Lk 21:12-19
155	vespers	0	psalm	Psalm 5:11-12
155	vespers	1	gospel	Matt 10:24-33
155	matins	0	psalm	Psalm 34:19-20
155	matins	1	gospel	Jn 12:20-26
155	liturgy	0	psalm	Psalm 21:3|Psalm 21:5
155	liturgy	1	gospel	Lk 10:1-20
156	vespers	0	psalm	Psalm 87:3,5,7
156	vespers	1	gospel	Lk 10:38-52
156	matins	0	psalm	Psalm 48:8|Psalm 48:1
156	matins	1	gospel	Matt 12:35-50
156	liturgy	0	psalm	Psalm 45:12-13
156	liturgy	1	gospel	Lk 1:39-56
157	vespers	0	psalm	Psalm 32:11|33:1|32:6
157	vespers	1	gospel	Matt 25:14 - 23
157	matins	0	psalm	Psalm 33:1|Psalm 33:12
157	matins	1	gospel	Lk 19:11 - 19
157	liturgy	0	psalm	Psalm 34:19|Psalm 68:3
157	liturgy	1	gospel	Lk 12:32 - 44
158	vespers	0	psalm	Psalm 89:19-21
158	vespers	1	gospel	Matthew 10:34-42
158	matins	0	psalm	Psalm 132:9-10|Psalm 132:17-18
158	matins	1	gospel	Luke 6:17-23
158	liturgy	0	psalm	Psalm 99:6-7
158	liturgy	1	gospel	John 16:20-33
159	vespers	0	psalm	Psalm 68:25-26
159	vespers	1	gospel	Matt 26:6 - 13
159	matins	0	psalm	Psalm 8:2 - 3
159	matins	1	gospel	Jn 4:15 - 24
159	liturgy	0	psalm	Psalm 45:14 - 15
159	liturgy	1	gospel	Matt 25:1 - 13
160	vespers	0	psalm	Psalm 65:4-5
160	vespers	1	gospel	Matt 24:42-47
160	matins	0	psalm	Psalm 37:17|Psalm 37:18|Psalm 37:29
160	matins	1	gospel	Mk 13:33-37
160	liturgy	0	psalm	Psalm 37:30-31
160	liturgy	1	gospel	Lk 16:1-12
161	vespers	0	psalm	Psalm 32:11|33:1|32:6
161	vespers	1	gospel	Matt 10:34 - 42
161	matins	0	psalm	Psalm 33:1|Psalm 33:12
161	matins	1	gospel	Lk 6:17 - 23
161	liturgy	0	psalm	Psalm 34:19 - 20
161	liturgy	1	gospel	Matt 4:23—|Matt 5:1-16
162	vespers	0	psalm	Psalm 4:6-8
162	vespers	1	gospel	Matt 16:24-28
162	matins	0	psalm	Psalm 5:11|Psalm 5:12
162	matins	1	gospel	Matt 10:34-42
162	liturgy	0	psalm	Psalm 68:35|Psalm 68:3
162	liturgy	1	gospel	Lk 12:4-12
163	vespers	0	psalm	Psalm 68:35|Psalm 68:3
163	vespers	1	gospel	Matt 10:16-23
163	matins	0	psalm	Psalm 97:11-12
163	matins	1	gospel	Mk 13:9-13
163	liturgy	0	psalm	Psalm 34:19-20
163	liturgy	1	gospel	Lk 11:53—|Lk 12:1-12
164	vespers	0	psalm	Psalm 69:25-26
164	vespers	1	gospel	Matt 26:6-13
164	matins	0	psalm	Psalm 8:2-3
164	matins	1	gospel	John 4:15-24
164	liturgy	0	psalm	Psalm 45:14-15
164	liturgy	1	gospel	Matt 25:1-13
165	vespers	0	psalm	Psalm 68:25-26
165	vespers	1	gospel	Matthew 26:6-13
165	matins	0	psalm	Psalm 8:2-3
165	matins	1	gospel	John 4:15-24
165	liturgy	0	psalm	Psalm 45:14-15
165	liturgy	1	gospel	Matthew 25:1-13
166	vespers	0	psalm	Psalm 47:1-2
166	vespers	1	gospel	Lk 4:40-44
166	matins	0	psalm	Psalm 93:1-2
166	matins	1	gospel	Lk 4:31-37
166	liturgy	0	psalm	Psalm 98:2-3
166	liturgy	1	gospel	Mt 2:13-23
167	vespers	0	psalm	Psalm 98:3,9
167	vespers	1	gospel	Mt 14:22-36
167	matins	0	psalm	Psalm 97:1-2
167	matins	1	gospel	Mk 3:7-12
167	liturgy	0	psalm	Psalm 84:7|Psalm 65:2
167	liturgy	1	gospel	Luke 11:27-36
168	vespers	0	psalm	Psalm 77:18-19
168	vespers	1	gospel	Jn 5:1-18
168	matins	0	psalm	Psalm 97:6|Psalm 97:4
168	matins	1	gospel	Jn 3:1-21
168	liturgy	0	psalm	Psalm 66:12|Psalm 66:8
168	liturgy	1	gospel	Jn 3:22-36
169	vespers	0	psalm	Psalm 78:20,23
169	vespers	1	gospel	Jn 5:31-46
169	matins	0	psalm	Psalm 80:7|Psalm 80:18
169	matins	1	gospel	Jn 6:47-58
169	liturgy	0	psalm	Psalm 36:9-10
169	liturgy	1	gospel	Jn 9:1-38
170	vespers	0	psalm	Psalm 15:1-2
170	vespers	1	gospel	Jn 4:46-53
170	matins	0	psalm	Psalm 24:3-4
170	matins	1	gospel	Jn 3:17-21
170	liturgy	0	psalm	Psalm 96:7|Psalm 96:9
170	liturgy	1	gospel	Jn 6:5-14
171	vespers	0	psalm	Psalm 32:11|Psalm 32:6
171	vespers	1	gospel	Matt 25:14-23
171	matins	0	psalm	Psalm 112:1-2
171	matins	1	gospel	Lk 6:17-23
171	liturgy	0	psalm	Psalm 19:4|132:9,10
171	liturgy	1	gospel	Matt 16:13-19
172	vespers	0	psalm	Psalm 32:11|Psalm 32:6
172	vespers	1	gospel	Lk 22:24 - 30
172	matins	0	psalm	Psalm 33:1|Psalm 33:12
172	matins	1	gospel	Matt 25:14 - 23
172	liturgy	0	psalm	Psalm 132:9|Psalm 132:10|Psalm 132:1|Psalm 132:2
172	liturgy	1	gospel	Matt 9:33 - 41
173	vespers	0	psalm	Psalm 65:4-5
173	vespers	1	gospel	Matt 24:42-47
173	matins	0	psalm	Psalm 37:17|Psalm 37:18|Psalm 37:29
173	matins	1	gospel	Mk 13:33-37
173	liturgy	0	psalm	Psalm 37:30-31
173	liturgy	1	gospel	Lk 16:1-12
174	vespers	0	psalm	Psalm 105:1-3
174	vespers	1	gospel	Lk 9:1-6
174	matins	0	psalm	Psalm 68:24|Psalm 68:26
174	matins	1	gospel	Lk 17:5-10
174	liturgy	0	psalm	Psalm 96:2-3
174	liturgy	1	gospel	Lk 10:1-20
175	vespers	0	psalm	Psalm 112:1-2
175	vespers	1	gospel	Matt 25:14-23
175	matins	0	psalm	Psalm 132:1|Psalm 132:2|Psalm 132:9|Psalm 132:10
175	matins	1	gospel	Lk 6:17-23
175	liturgy	0	psalm	Psalm 1:1
175	liturgy	1	gospel	Matt 4:23—|Matt 5:1-16
176	vespers	0	psalm	Psalm 68:35|Psalm 68:3
176	vespers	1	gospel	Matt 10:16-23
176	matins	0	psalm	Psalm 97:11-12
176	matins	1	gospel	Mk 13:9-13
176	liturgy	0	psalm	Psalm 34:19-20
176	liturgy	1	gospel	Lk 11:53—|Lk 12:1-12
177	vespers	0	psalm	Psalm 110:4|Psalm 110:7
177	vespers	1	gospel	Matthew 16:13-19
177	matins	0	psalm	Psalm 73:23-24|Psalm 73:28|Psalm 9:14
177	matins	1	gospel	John 15:17-25
177	liturgy	0	psalm	Psalm 107:32|Psalm 107:41-42
177	liturgy	1	gospel	John 10:1-16
178	vespers	0	psalm	Psalm 116:16 - 19
178	vespers	1	gospel	Lk 2:15 - 20
178	matins	0	psalm	Psalm 66:13 - 15
178	matins	1	gospel	Lk 2:40 - 52
178	liturgy	0	psalm	Psalm 50:14|Psalm 50:23
178	liturgy	1	gospel	Lk 2:21 - 39
179	vespers	0	psalm	Psalm 40:2-3
179	vespers	1	gospel	Matt 7:22-25
179	matins	0	psalm	Psalm 89:24|Psalm 89:19
179	matins	1	gospel	Lk 13:23-30
179	liturgy	0	psalm	Psalm 61:1-3
179	liturgy	1	gospel	Lk 14:25-35
180	vespers	0	psalm	Psalm 68:11,35
180	vespers	1	gospel	Mk 3:7-21
180	matins	0	psalm	Psalm 145:10-12
180	matins	1	gospel	Lk 6:12-23
180	liturgy	0	psalm	Psalm 19:1|Psalm 19:4
180	liturgy	1	gospel	Matt 10:1-15
181	vespers	0	psalm	Psalm 89:36|Psalm 89:29
181	vespers	1	gospel	Lk 9:18-27
181	matins	0	psalm	Psalm 107:32|Psalm 107:41|Psalm 107:42
181	matins	1	gospel	Mk 8:22-29
181	liturgy	0	psalm	Psalm 110:4|Psalm 110:5|Psalm 110:7
181	liturgy	1	gospel	Matt 16:13 - 19
182	vespers	0	psalm	Psalm 65:4-5
182	vespers	1	gospel	Matt 24:42-47
182	matins	0	psalm	Psalm 37:17|Psalm 37:18|Psalm 37:29
182	matins	1	gospel	Mk 13:33-37
182	liturgy	0	psalm	Psalm 37:30-31
182	liturgy	1	gospel	Lk 16:1-12
183	vespers	0	psalm	Psalm 4:6-8
183	vespers	1	gospel	Matt 16:24-28
183	matins	0	psalm	Psalm 5:11|Psalm 5:12
183	matins	1	gospel	Matt 10:34-42
183	liturgy	0	psalm	Psalm 68:35|Psalm 68:3
183	liturgy	1	gospel	Lk 12:4-12
184	vespers	0	psalm	Psalm 132:9-10|Psalm 132:17-18
184	vespers	1	gospel	Matthew 4:23-25|Matthew 5:1-16
184	matins	0	psalm	Psalm 110:4-6
184	matins	1	gospel	Luke 6:17-23
184	liturgy	0	psalm	Psalm 73:23-24|Psalm 73:28|Psalm 9:14
184	liturgy	1	gospel	John 10:1-16
185	vespers	0	psalm	Psalm 112:6-7|Psalm 112:9
185	vespers	1	gospel	Matthew 24:42-47
185	matins	0	psalm	Psalm 92:10|Psalm 92:14|Psalm 92:15
185	matins	1	gospel	Luke 19:11-19
185	liturgy	0	psalm	Psalm 92:12-13
185	liturgy	1	gospel	Luke 12:32-44
186	vespers	0	psalm	Psalm 9:11|Psalm 9:14
186	vespers	1	gospel	Mark 14:3-9
186	matins	0	psalm	Psalm 102:19-21
186	matins	1	gospel	Mark 12:41-44
186	liturgy	0	psalm	Psalm 102:13|Psalm 102:16-17
186	liturgy	1	gospel	Luke 1:1-25
187	vespers	0	psalm	Psalm 4:6-8
187	vespers	1	gospel	Matthew 16:24-28
187	matins	0	psalm	Psalm 5:11-12
187	matins	1	gospel	Matthew 10:34-42
187	liturgy	0	psalm	Psalm 68:35|Psalm 68:3
187	liturgy	1	gospel	Luke 12:4-12
188	matins	0	psalm	Psalm 29:10-11
188	matins	1	gospel	Mark 8:10-21
188	liturgy	0	psalm	Psalm 118:5|Psalm 118:18
188	liturgy	1	gospel	John 2:12-25
189	vespers	0	psalm	Psalm 65:4-5
189	vespers	1	gospel	Matt 24:42-47
189	matins	0	psalm	Psalm 37:17|Psalm 37:18|Psalm 37:29
189	matins	1	gospel	Mk 13:33-37
189	liturgy	0	psalm	Psalm 37:30-31
189	liturgy	1	gospel	Lk 16:1-12
190	vespers	0	psalm	Psalm 89:36|Psalm 89:29
190	vespers	1	gospel	Lk 9:18-27
190	matins	0	psalm	Psalm 107:32|Psalm 107:41|Psalm 107:42
190	matins	1	gospel	Mk 8:22-29
190	liturgy	0	psalm	Psalm 110:4|Psalm 110:5|Psalm 110:7
190	liturgy	1	gospel	Matt 16:13 - 19
191	vespers	0	psalm	Psalm 68:11|Psalm 68:35
191	vespers	1	gospel	Mark 3:7-21
191	matins	0	psalm	Psalm 145:10-12
191	matins	1	gospel	Luke 6:12-23
191	liturgy	0	psalm	Psalm 19:1|Psalm 19:4
191	liturgy	1	gospel	Matthew 10:1-15
192	vespers	0	psalm	Psalm 89:19-21
192	vespers	1	gospel	Matt 10:34-42
192	matins	0	psalm	Psalm 132:9|Psalm 132:10|Psalm 132:17|Psalm 132:18
192	matins	1	gospel	Lk 6:17-23
192	liturgy	0	psalm	Psalm 99:6-7
192	liturgy	1	gospel	Jn 16:20-33
193	vespers	0	psalm	Psalm 4:6-8
193	vespers	1	gospel	Matt 16:24-28
193	matins	0	psalm	Psalm 5:11|Psalm 5:12
193	matins	1	gospel	Matt 10:34-42
193	liturgy	0	psalm	Psalm 68:35|Psalm 68:3
193	liturgy	1	gospel	Lk 12:4-12
194	vespers	0	psalm	Psalm 89:19-21
194	vespers	1	gospel	Matt 10:34-42
194	matins	0	psalm	Psalm 132:9|Psalm 132:10|Psalm 132:17|Psalm 132:18
194	matins	1	gospel	Lk 6:17-23
194	liturgy	0	psalm	Psalm 99:6-7
194	liturgy	1	gospel	Jn 16:20-33
195	vespers	0	psalm	Psalm 18:34,39
195	vespers	1	gospel	Matt 10:16-23
195	matins	0	psalm	Psalm 45:3|Psalm 45:6
195	matins	1	gospel	Lk 7:11-17
195	liturgy	0	psalm	Psalm 91:13|Psalm 91:11
195	liturgy	1	gospel	Lk 10:21-24
196	vespers	0	psalm	Psalm 105:14-15
196	vespers	1	gospel	Lk 11:37-51
196	matins	0	psalm	Psalm 105:26|Psalm 105:27|Psalm 105:45
196	matins	1	gospel	Matt 17:1-9
196	liturgy	0	psalm	Psalm 99:6-7
196	liturgy	1	gospel	Matt 23:13-36
197	vespers	0	psalm	Psalm 132:9-10|Psalm 132:17-18
197	vespers	1	gospel	Matthew 4:23-25|Matthew 5:1-16
197	matins	0	psalm	Psalm 110:4-6
197	matins	1	gospel	Luke 6:17-23
197	liturgy	0	psalm	Psalm 73:23-24|Psalm 73:28|Psalm 9:14
197	liturgy	1	gospel	John 10:1-16
198	vespers	0	psalm	Psalm 18:34|Psalm 18:39
198	vespers	1	gospel	Matthew 10:16-23
198	matins	0	psalm	Psalm 45:3|Psalm 45:6
198	matins	1	gospel	Luke 7:11-17
198	liturgy	0	psalm	Psalm 91:13|Psalm 91:11
198	liturgy	1	gospel	Luke 10:21-24
199	vespers	0	psalm	Psalm 19:1|Psalm 19:4
199	vespers	1	gospel	John 15:7-16
199	matins	0	psalm	Psalm 45:1-2
199	matins	1	gospel	John 1:1-17
199	liturgy	0	psalm	Psalm 139:17-18
199	liturgy	1	gospel	John 21:15-25
200	vespers	0	psalm	Psalm 35:10|Psalm 35:27
200	vespers	1	gospel	Luke 7:18-28
200	matins	0	psalm	Psalm 51:8|Psalm 51:19
200	matins	1	gospel	John 3:25-36
200	liturgy	0	psalm	Psalm 34:19|Psalm 34:15
200	liturgy	1	gospel	Matthew 11:2-10
201	vespers	0	psalm	Psalm 82:8|Psalm 82:6
201	vespers	1	gospel	Jn 6:15-21
201	matins	0	psalm	Psalm 119:105|Psalm 119:135
201	matins	1	gospel	Jn 8:51-59
201	liturgy	0	psalm	Psalm 96:6|Psalm 96:4
201	liturgy	1	gospel	Jn 6:22-27
202	vespers	0	psalm	Psalm 15:1-2
202	vespers	1	gospel	Jn 4:46-53
202	matins	0	psalm	Psalm 24:3-4
202	matins	1	gospel	Jn 3:17-21
202	liturgy	0	psalm	Psalm 96:7|Psalm 96:9
202	liturgy	1	gospel	Jn 6:5-14
203	vespers	0	psalm	Psalm 17:15|Psalm 17:3
203	vespers	1	gospel	Jn 5:39-47
203	matins	0	psalm	Psalm 89:52|Psalm 89:49
203	matins	1	gospel	Jn 12:44-50
203	liturgy	0	psalm	Psalm 89:1|Psalm 89:6
203	liturgy	1	gospel	Jn 6:27-46
204	vespers	0	psalm	Psalm 92:4-5
204	vespers	1	gospel	Luke 17:1-10
204	matins	0	psalm	Psalm 89:11|Psalm 89:1
204	matins	1	gospel	Luke 17:11-19
204	liturgy	0	psalm	Psalm 24:1-2
204	liturgy	1	gospel	Luke 19:1-10
205	vespers	0	psalm	Psalm 4:3|Psalm 4:6-7
205	vespers	1	gospel	Matthew 10:24-33
205	matins	0	psalm	Psalm 113:1-2
205	matins	1	gospel	Mark 8:34-38|Mark 9:1
205	liturgy	0	psalm	Psalm 66:12-14
205	liturgy	1	gospel	Luke 21:12-19
206	vespers	0	psalm	Psalm 89:19-21
206	vespers	1	gospel	Matthew 10:34-42
206	matins	0	psalm	Psalm 132:9-10|Psalm 132:17-18
206	matins	1	gospel	Luke 6:17-23
206	liturgy	0	psalm	Psalm 99:6-7
206	liturgy	1	gospel	John 16:20-33
207	vespers	0	psalm	Psalm 89:36|Psalm 89:29
207	vespers	1	gospel	Luke 9:18-27
207	matins	0	psalm	Psalm 107:32|Psalm 107:41|Psalm 107:42
207	matins	1	gospel	Mark 8:22-29
207	liturgy	0	psalm	Psalm 110:4|Psalm 110:5|Psalm 110:7
207	liturgy	1	gospel	Matthew 16:13-19
208	vespers	0	psalm	Psalm 32:11|Psalm 32:6
208	vespers	1	gospel	Matthew 25:14-23
208	matins	0	psalm	Psalm 112:1-2
208	matins	1	gospel	Luke 6:17-23
208	liturgy	0	psalm	Psalm 19:4|Psalm 132:9-10
208	liturgy	1	gospel	Matthew 16:13-19
209	vespers	0	psalm	Psalm 89:19-21
209	vespers	1	gospel	Matthew 10:34-42
209	matins	0	psalm	Psalm 132:9-10|Psalm 132:17-18
209	matins	1	gospel	Luke 6:17-23
209	liturgy	0	psalm	Psalm 99:6-7
209	liturgy	1	gospel	John 16:20-33
210	vespers	0	psalm	Psalm 46:1|Psalm 46:7
210	matins	0	psalm	Psalm 146:1|Psalm 146:5
210	matins	1	gospel	Matthew 4:18-22
210	liturgy	0	psalm	Psalm 78:5|Psalm 135:5
210	liturgy	1	gospel	Mark 10:35-45
211	vespers	0	psalm	Psalm 4:3|Psalm 4:6-7
211	vespers	1	gospel	Matthew 10:24-33
211	matins	0	psalm	Psalm 113:1-2
211	matins	1	gospel	Mark 8:34-38|Mark 9:1
211	liturgy	0	psalm	Psalm 66:12-14
211	liturgy	1	gospel	Luke 21:12-19
212	vespers	0	psalm	Psalm 68:11|Psalm 68:35
212	vespers	1	gospel	Mark 3:7-21
212	matins	0	psalm	Psalm 145:10-12
212	matins	1	gospel	Luke 6:12-23
212	liturgy	0	psalm	Psalm 19:1|Psalm 19:4
212	liturgy	1	gospel	Matthew 10:1-15
213	vespers	0	psalm	Psalm 65:4-5
213	vespers	1	gospel	Matthew 24:42-47
213	matins	0	psalm	Psalm 37:17-18|Psalm 37:29
213	matins	1	gospel	Mark 13:33-37
213	liturgy	0	psalm	Psalm 37:30-31
213	liturgy	1	gospel	Luke 16:1-12
214	vespers	0	psalm	Psalm 4:6-8
214	vespers	1	gospel	John 4:19-24
214	matins	0	psalm	Psalm 118:28|Psalm 118:16
214	matins	1	gospel	John 3:14-21
214	liturgy	0	psalm	Psalm 65:1-2
214	liturgy	1	gospel	John 6:35-46
215	vespers	0	psalm	Psalm 64:10
215	vespers	1	gospel	Mark 4:21-25
215	matins	0	psalm	Psalm 70:5
215	matins	1	gospel	Mark 3:22-27
215	liturgy	0	psalm	Psalm 16:10-11
215	liturgy	1	gospel	Mark 3:28-35
216	vespers	0	psalm	Psalm 89:36|Psalm 89:29
216	vespers	1	gospel	Luke 9:18-27
216	matins	0	psalm	Psalm 107:32|Psalm 107:41|Psalm 107:42
216	matins	1	gospel	Mark 8:22-29
216	liturgy	0	psalm	Psalm 110:4|Psalm 110:5|Psalm 110:7
216	liturgy	1	gospel	Matthew 16:13-19
217	vespers	0	psalm	Psalm 34:19-20
217	vespers	1	gospel	Matthew 16:24-28
217	matins	0	psalm	Psalm 37:39-40
217	liturgy	0	psalm	Psalm 97:11-12
217	liturgy	1	gospel	Luke 11:53-54|Luke 12:1-12
218	vespers	0	psalm	Psalm 64:10
218	vespers	1	gospel	Mark 4:21-25
218	matins	0	psalm	Psalm 70:5
218	matins	1	gospel	Mark 3:22-27
218	liturgy	0	psalm	Psalm 16:10-11
218	liturgy	1	gospel	Mark 3:28-35
219	vespers	0	psalm	Psalm 68:25-26
219	vespers	1	gospel	Matthew 26:6-13
219	matins	0	psalm	Psalm 8:2-3
219	matins	1	gospel	John 4:15-24
219	liturgy	0	psalm	Psalm 45:14-15
219	liturgy	1	gospel	Matthew 25:1-13
220	vespers	0	psalm	Psalm 89:36|Psalm 89:29
220	vespers	1	gospel	Luke 9:18-27
220	matins	0	psalm	Psalm 107:32|Psalm 107:41|Psalm 107:42
220	matins	1	gospel	Mark 8:22-29
220	liturgy	0	psalm	Psalm 110:4|Psalm 110:5|Psalm 110:7
220	liturgy	1	gospel	Matthew 16:13-19
221	vespers	0	psalm	Psalm 89:19-21
221	vespers	1	gospel	Matthew 10:34-42
221	matins	0	psalm	Psalm 132:9-10|Psalm 132:17-18
221	matins	1	gospel	Luke 6:17-23
221	liturgy	0	psalm	Psalm 99:6-7
221	liturgy	1	gospel	John 16:20-33
222	vespers	0	psalm	Psalm 18:34|Psalm 18:39
222	vespers	1	gospel	Matthew 10:16-23
222	matins	0	psalm	Psalm 45:3|Psalm 45:6
222	matins	1	gospel	Luke 7:11-17
222	liturgy	0	psalm	Psalm 91:13|Psalm 91:11
222	liturgy	1	gospel	Luke 10:21-24
223	vespers	0	psalm	Psalm 5:11-12
223	vespers	1	gospel	Matthew 10:24-33
223	matins	0	psalm	Psalm 34:19-20
223	matins	1	gospel	John 12:20-26
223	liturgy	0	psalm	Psalm 21:3|Psalm 21:5
223	liturgy	1	gospel	Luke 10:1-20
224	vespers	0	psalm	Psalm 89:36|Psalm 89:29
224	vespers	1	gospel	Luke 9:18-27
224	matins	0	psalm	Psalm 107:32|Psalm 107:41|Psalm 107:42
224	matins	1	gospel	Mark 8:22-29
224	liturgy	0	psalm	Psalm 110:4|Psalm 110:5|Psalm 110:7
224	liturgy	1	gospel	Matthew 16:13-19
225	vespers	0	psalm	Psalm 99:6|Psalm 99:7
225	vespers	1	gospel	Luke 9:28-36
225	matins	0	psalm	Psalm 104:31-32
225	matins	1	gospel	Matthew 17:1-9
225	liturgy	0	psalm	Psalm 87:1-2|Psalm 87:5
225	liturgy	1	gospel	Mark 9:2-13
226	vespers	0	psalm	Psalm 110:4|Psalm 110:7
226	vespers	1	gospel	Matthew 16:13-19
226	matins	0	psalm	Psalm 73:23-24|Psalm 73:28|Psalm 9:14
226	matins	1	gospel	John 15:17-25
226	liturgy	0	psalm	Psalm 107:32|Psalm 107:41-42
226	liturgy	1	gospel	John 10:1-16
227	vespers	0	psalm	Psalm 105:14-15
227	vespers	1	gospel	Luke 11:37-51
227	matins	0	psalm	Psalm 105:26-27|Psalm 105:45
227	matins	1	gospel	Matthew 17:1-9
227	liturgy	0	psalm	Psalm 99:6-7
227	liturgy	1	gospel	Matthew 23:14-36
228	vespers	0	psalm	Psalm 89:36|Psalm 89:29
228	vespers	1	gospel	Luke 9:18-27
228	matins	0	psalm	Psalm 107:32|Psalm 107:41|Psalm 107:42
228	matins	1	gospel	Mark 8:22-29
228	liturgy	0	psalm	Psalm 110:4|Psalm 110:5|Psalm 110:7
228	liturgy	1	gospel	Matthew 16:13-19
229	vespers	0	psalm	Psalm 68:35|Psalm 68:3
229	vespers	1	gospel	Luke 10:1-20
229	matins	0	psalm	Psalm 145:10-12
229	matins	1	gospel	John 1:43-51
229	liturgy	0	psalm	Psalm 32:1-2
229	liturgy	1	gospel	John 3:1-21
230	vespers	0	psalm	Psalm 112:1-2
230	vespers	1	gospel	Matthew 24:14-23
230	matins	0	psalm	Psalm 132:1-2|Psalm 132:9-10
230	matins	1	gospel	Luke 6:17-23
230	liturgy	0	psalm	Psalm 1:1
230	liturgy	1	gospel	Matthew 4:23-25|Matthew 5:1-16
231	vespers	0	psalm	Psalm 84:3-4
231	vespers	1	gospel	Luke 7:1-10
231	matins	0	psalm	Psalm 26:8|Psalm 26:7
231	matins	1	gospel	Luke 19:1-10
231	liturgy	0	psalm	Psalm 65:1-2
231	liturgy	1	gospel	Matthew 16:13-19
232	vespers	0	psalm	Psalm 144:5,7
232	vespers	1	gospel	Lk 7:36-50
232	matins	0	psalm	Psalm 72:6-7
232	matins	1	gospel	Lk 11:20-28
232	liturgy	0	psalm	Psalm 45:10-11
232	liturgy	1	gospel	Lk 1:26-38
233	vespers	0	psalm	Psalm 65:4-5
233	vespers	1	gospel	Matthew 24:42-47
233	matins	0	psalm	Psalm 37:17-18|Psalm 37:29
233	matins	1	gospel	Mark 13:33-37
233	liturgy	0	psalm	Psalm 37:30-31
233	liturgy	1	gospel	Luke 16:1-12
234	vespers	0	psalm	Psalm 18:34|Psalm 18:39
234	vespers	1	gospel	Matthew 10:16-23
234	matins	0	psalm	Psalm 45:3|Psalm 45:6
234	matins	1	gospel	Luke 7:11-17
234	liturgy	0	psalm	Psalm 91:13|Psalm 91:11
234	liturgy	1	gospel	Luke 10:21-24
235	vespers	0	psalm	Psalm 110:4|Psalm 110:7
235	vespers	1	gospel	Matthew 16:13-19
235	matins	0	psalm	Psalm 73:23-24|Psalm 73:28|Psalm 9:14
235	matins	1	gospel	John 15:17-25
235	liturgy	0	psalm	Psalm 107:32|Psalm 107:41-42
235	liturgy	1	gospel	John 10:1-16
236	vespers	0	psalm	Psalm 4:3|Psalm 4:6-7
236	vespers	1	gospel	Matthew 10:24-33
236	matins	0	psalm	Psalm 113:1-2
236	matins	1	gospel	Mark 8:34-38|Mark 9:1
236	liturgy	0	psalm	Psalm 66:12-14
236	liturgy	1	gospel	Luke 21:12-19
237	vespers	0	psalm	Psalm 105:14-15
237	vespers	1	gospel	Luke 11:37-51
237	matins	0	psalm	Psalm 105:26-27|Psalm 105:45
237	matins	1	gospel	Matthew 17:1-9
237	liturgy	0	psalm	Psalm 99:6-7
237	liturgy	1	gospel	Matthew 23:14-36
238	vespers	0	psalm	Psalm 68:25-26
238	vespers	1	gospel	Matthew 26:6-13
238	matins	0	psalm	Psalm 8:2-3
238	matins	1	gospel	John 4:15-24
238	liturgy	0	psalm	Psalm 45:14-15
238	liturgy	1	gospel	Matthew 25:1-13
239	vespers	0	psalm	Psalm 105:14-15
239	vespers	1	gospel	Luke 11:37-51
239	matins	0	psalm	Psalm 105:26-27|Psalm 105:45
239	matins	1	gospel	Matthew 17:1-9
239	liturgy	0	psalm	Psalm 99:6-7
239	liturgy	1	gospel	Matthew 23:14-36
240	vespers	0	psalm	Psalm 68:25-26
240	vespers	1	gospel	Matthew 26:6-13
240	matins	0	psalm	Psalm 8:2-3
240	matins	1	gospel	John 4:15-24
240	liturgy	0	psalm	Psalm 45:14-15
240	liturgy	1	gospel	Matthew 25:1-13
241	vespers	0	psalm	Psalm 32:11|Psalm 33:1|Psalm 32:6
241	vespers	1	gospel	Matthew 25:14-23
241	matins	0	psalm	Psalm 33:1|Psalm 33:12
241	matins	1	gospel	Luke 19:11-19
241	liturgy	0	psalm	Psalm 34:19|Psalm 68:3
241	liturgy	1	gospel	Luke 12:32-44
242	vespers	0	psalm	Psalm 65:4-5
242	vespers	1	gospel	Matthew 24:42-47
242	matins	0	psalm	Psalm 37:17-18|Psalm 37:29
242	matins	1	gospel	Mark 13:33-37
242	liturgy	0	psalm	Psalm 37:30-31
242	liturgy	1	gospel	Luke 16:1-12
243	vespers	0	psalm	Psalm 68:25-26
243	vespers	1	gospel	Matthew 26:6-13
243	matins	0	psalm	Psalm 8:2-3
243	matins	1	gospel	John 4:15-24
243	liturgy	0	psalm	Psalm 45:14-15
243	liturgy	1	gospel	Matthew 25:1-13
244	vespers	0	psalm	Psalm 110:4|Psalm 110:7
244	vespers	1	gospel	Matthew 16:13-19
244	matins	0	psalm	Psalm 73:23-24|Psalm 73:28|Psalm 9:14
244	matins	1	gospel	John 15:17-25
244	liturgy	0	psalm	Psalm 107:32|Psalm 107:41-42
244	liturgy	1	gospel	John 10:1-16
245	vespers	0	psalm	Psalm 4:3|Psalm 4:6-7
245	vespers	1	gospel	Matthew 10:24-33
245	matins	0	psalm	Psalm 113:1-2
245	matins	1	gospel	Mark 8:34-38|Mark 9:1
245	liturgy	0	psalm	Psalm 66:12-14
245	liturgy	1	gospel	Luke 21:12-19
246	vespers	0	psalm	Psalm 89:36|Psalm 89:29
246	vespers	1	gospel	Luke 9:18-27
246	matins	0	psalm	Psalm 107:32|Psalm 107:41|Psalm 107:42
246	matins	1	gospel	Mark 8:22-29
246	liturgy	0	psalm	Psalm 110:4|Psalm 110:5|Psalm 110:7
246	liturgy	1	gospel	Matthew 16:13-19
247	vespers	0	psalm	Psalm 5:11-12
247	vespers	1	gospel	Matthew 10:24-33
247	matins	0	psalm	Psalm 34:19-20
247	matins	1	gospel	John 12:20-26
247	liturgy	0	psalm	Psalm 21:3|Psalm 21:5
247	liturgy	1	gospel	Luke 10:1-20
248	vespers	0	psalm	Psalm 19:1|Psalm 19:4
248	vespers	1	gospel	John 15:7-16
248	matins	0	psalm	Psalm 45:1-2
248	matins	1	gospel	John 1:1-17
248	liturgy	0	psalm	Psalm 139:17-18
248	liturgy	1	gospel	John 21:15-25
249	vespers	0	psalm	Psalm 68:11|Psalm 68:35
249	vespers	1	gospel	Mark 3:7-21
249	matins	0	psalm	Psalm 145:10-12
249	matins	1	gospel	Luke 6:12-23
249	liturgy	0	psalm	Psalm 19:1|Psalm 19:4
249	liturgy	1	gospel	Matthew 10:1-15
250	vespers	0	psalm	Psalm 4:6-8
250	vespers	1	gospel	Matthew 16:24-28
250	matins	0	psalm	Psalm 5:11-12
250	matins	1	gospel	Matthew 10:34-42
250	liturgy	0	psalm	Psalm 68:35|Psalm 68:3
250	liturgy	1	gospel	Luke 12:4-12
251	vespers	0	psalm	Psalm 89:19-21
251	vespers	1	gospel	Matthew 10:34-42
251	matins	0	psalm	Psalm 132:9-10|Psalm 132:17-18
251	matins	1	gospel	Luke 6:17-23
251	liturgy	0	psalm	Psalm 99:6-7
251	liturgy	1	gospel	John 16:20-33
252	vespers	0	psalm	Psalm 18:34|Psalm 18:39
252	vespers	1	gospel	Matthew 10:16-23
252	matins	0	psalm	Psalm 45:3|Psalm 45:6
252	matins	1	gospel	Luke 7:11-17
252	liturgy	0	psalm	Psalm 91:13|Psalm 91:11
252	liturgy	1	gospel	Luke 10:21-24
253	vespers	0	psalm	Psalm 64:10
253	vespers	1	gospel	Mark 4:21-25
253	matins	0	psalm	Psalm 70:5
253	matins	1	gospel	Mark 3:22-27
253	liturgy	0	psalm	Psalm 16:10-11
253	liturgy	1	gospel	Mark 3:28-35
254	vespers	0	psalm	Psalm 89:36|Psalm 89:29
254	vespers	1	gospel	Luke 9:18-27
254	matins	0	psalm	Psalm 107:32|Psalm 107:41|Psalm 107:42
254	matins	1	gospel	Mark 8:22-29
254	liturgy	0	psalm	Psalm 110:4|Psalm 110:5|Psalm 110:7
254	liturgy	1	gospel	Matthew 16:13-19
255	vespers	0	psalm	Psalm 34:17-18
255	vespers	1	gospel	Matthew 10:16-22
255	matins	0	psalm	Psalm 34:19-20
255	matins	1	gospel	Mark 8:34-38|Mark 9:1
255	liturgy	0	psalm	Psalm 97:11-12
255	liturgy	1	gospel	Luke 21:12-19
256	vespers	0	psalm	Psalm 18:34|Psalm 18:39
256	vespers	1	gospel	Matthew 10:16-23
256	matins	0	psalm	Psalm 45:3|Psalm 45:6
256	matins	1	gospel	Luke 7:11-17
256	liturgy	0	psalm	Psalm 91:13|Psalm 91:11
256	liturgy	1	gospel	Luke 10:21-24
257	vespers	0	psalm	Psalm 68:25-26
257	vespers	1	gospel	Matthew 26:6-13
257	matins	0	psalm	Psalm 8:2-3
257	matins	1	gospel	John 4:15-24
257	liturgy	0	psalm	Psalm 45:14-15
257	liturgy	1	gospel	Matthew 25:1-13
258	vespers	0	psalm	Psalm 18:34|Psalm 18:39
258	vespers	1	gospel	Matthew 10:16-23
258	matins	0	psalm	Psalm 45:3|Psalm 45:6
258	matins	1	gospel	Luke 7:11-17
258	liturgy	0	psalm	Psalm 91:13|Psalm 91:11
258	liturgy	1	gospel	Luke 10:21-24
259	vespers	0	psalm	Psalm 4:6-8
259	vespers	1	gospel	Matthew 16:24-28
259	matins	0	psalm	Psalm 5:11-12
259	matins	1	gospel	Matthew 10:34-42
259	liturgy	0	psalm	Psalm 68:35|Psalm 68:3
259	liturgy	1	gospel	Luke 12:4-12
260	vespers	0	psalm	Psalm 18:34|Psalm 18:39
260	vespers	1	gospel	Matthew 8:5-13
260	matins	0	psalm	Psalm 68:35|Psalm 68:3
260	matins	1	gospel	Luke 12:4-12
260	liturgy	0	psalm	Psalm 45:3-4
260	liturgy	1	gospel	Matthew 12:9-23
261	vespers	0	psalm	Psalm 5:11-12
261	vespers	1	gospel	Matthew 10:24-33
261	matins	0	psalm	Psalm 34:19-20
261	matins	1	gospel	John 12:20-26
261	liturgy	0	psalm	Psalm 21:3|Psalm 21:5
261	liturgy	1	gospel	Luke 10:1-20
262	vespers	0	psalm	Psalm 40:9|Psalm 40:2
262	vespers	1	gospel	Mark 6:6-13
262	matins	0	psalm	Psalm 105:1-3
262	matins	1	gospel	Mark 10:17-30
262	liturgy	0	psalm	Psalm 96:1-2
262	liturgy	1	gospel	Mark 1:1-11
263	vespers	0	psalm	Psalm 87:3|Psalm 87:5|Psalm 87:7
263	vespers	1	gospel	Luke 10:38-42
263	matins	0	psalm	Psalm 48:8|Psalm 48:1
263	matins	1	gospel	Matthew 12:35-50
263	liturgy	0	psalm	Psalm 45:12-13
263	liturgy	1	gospel	Luke 1:39-56
264	vespers	0	psalm	Psalm 40:2-3
264	vespers	1	gospel	Matthew 7:22-25
264	matins	0	psalm	Psalm 89:24|Psalm 89:19
264	matins	1	gospel	Luke 13:23-30
264	liturgy	0	psalm	Psalm 61:1-3
264	liturgy	1	gospel	Luke 14:25-35
265	vespers	0	psalm	Psalm 5:11-12
265	vespers	1	gospel	Matthew 10:24-33
265	matins	0	psalm	Psalm 34:19-20
265	matins	1	gospel	John 12:20-26
265	liturgy	0	psalm	Psalm 21:3|Psalm 21:5
265	liturgy	1	gospel	Luke 10:1-20
266	vespers	0	psalm	Psalm 89:36|Psalm 89:29
266	vespers	1	gospel	Luke 9:18-27
266	matins	0	psalm	Psalm 107:32|Psalm 107:41|Psalm 107:42
266	matins	1	gospel	Mark 8:22-29
266	liturgy	0	psalm	Psalm 110:4|Psalm 110:5|Psalm 110:7
266	liturgy	1	gospel	Matthew 16:13-19
267	vespers	0	psalm	Psalm 105:14-15
267	vespers	1	gospel	Luke 11:37-51
267	matins	0	psalm	Psalm 105:26-27|Psalm 105:45
267	matins	1	gospel	Matthew 17:1-9
267	liturgy	0	psalm	Psalm 99:6-7
267	liturgy	1	gospel	Matthew 23:14-36
268	vespers	0	psalm	Psalm 34:17-18
268	vespers	1	gospel	Matthew 10:16-22
268	matins	0	psalm	Psalm 34:19-20
268	matins	1	gospel	Mark 8:34-38|Mark 9:1
268	liturgy	0	psalm	Psalm 97:11-12
268	liturgy	1	gospel	Luke 21:12-19
269	vespers	0	psalm	Psalm 110:4|Psalm 110:7
269	vespers	1	gospel	Matthew 16:13-19
269	matins	0	psalm	Psalm 73:23-24|Psalm 73:28|Psalm 9:14
269	matins	1	gospel	John 15:17-25
269	liturgy	0	psalm	Psalm 107:32|Psalm 107:41-42
269	liturgy	1	gospel	John 10:1-16
270	vespers	0	psalm	Psalm 34:17-18
270	vespers	1	gospel	Matthew 10:16-22
270	matins	0	psalm	Psalm 34:19-20
270	matins	1	gospel	Mark 8:34-38|Mark 9:1
270	liturgy	0	psalm	Psalm 97:11-12
270	liturgy	1	gospel	Luke 21:12-19
271	vespers	0	psalm	Psalm 84:3-4
271	vespers	1	gospel	Luke 7:1-10
271	matins	0	psalm	Psalm 26:8|Psalm 26:7
271	matins	1	gospel	Luke 19:1-10
271	liturgy	0	psalm	Psalm 65:1-2
271	liturgy	1	gospel	Matthew 16:13-19
272	vespers	0	psalm	Psalm 4:3|Psalm 4:6|Psalm 4:7
272	vespers	1	gospel	Matthew 11:25-30
272	matins	0	psalm	Psalm 113:1-2
272	matins	1	gospel	Mark 10:13-16
272	liturgy	0	psalm	Psalm 66:12-14
272	liturgy	1	gospel	Matthew 18:10-20
273	vespers	0	psalm	Psalm 89:19-21
273	vespers	1	gospel	Matthew 10:34-42
273	matins	0	psalm	Psalm 132:9-10|Psalm 132:17-18
273	matins	1	gospel	Luke 6:17-23
273	liturgy	0	psalm	Psalm 99:6-7
273	liturgy	1	gospel	John 16:20-33
274	vespers	0	psalm	Psalm 132:9-10|Psalm 132:17-18
274	vespers	1	gospel	Matthew 4:23-25|Matthew 5:1-16
274	matins	0	psalm	Psalm 110:4-6
274	matins	1	gospel	Luke 6:17-23
274	liturgy	0	psalm	Psalm 73:23-24|Psalm 73:28|Psalm 9:14
274	liturgy	1	gospel	John 10:1-16
275	vespers	0	psalm	Psalm 32:11|Psalm 33:1|Psalm 32:6
275	vespers	1	gospel	Matthew 25:14-23
275	matins	0	psalm	Psalm 33:1|Psalm 33:12
275	matins	1	gospel	Luke 19:11-19
275	liturgy	0	psalm	Psalm 34:19|Psalm 68:3
275	liturgy	1	gospel	Luke 12:32-44
276	vespers	0	psalm	Psalm 40:2-3
276	vespers	1	gospel	Matthew 7:22-25
276	matins	0	psalm	Psalm 89:24|Psalm 89:19
276	matins	1	gospel	Luke 13:23-30
276	liturgy	0	psalm	Psalm 61:1-3
276	liturgy	1	gospel	Luke 14:25-35
277	vespers	0	psalm	Psalm 22:22-23
277	vespers	1	gospel	Matthew 9:9-13
277	matins	0	psalm	Psalm 40:9-10
277	matins	1	gospel	Mark 2:13-17
277	liturgy	0	psalm	Psalm 68:11-12
277	liturgy	1	gospel	Luke 5:27-32
278	vespers	0	psalm	Psalm 19:1|Psalm 19:4
278	vespers	1	gospel	John 15:7-16
278	matins	0	psalm	Psalm 45:1-2
278	matins	1	gospel	John 1:1-17
278	liturgy	0	psalm	Psalm 139:17-18
278	liturgy	1	gospel	John 21:15-25
279	vespers	0	psalm	Psalm 89:19-21
279	vespers	1	gospel	Matthew 10:34-42
279	matins	0	psalm	Psalm 132:9-10|Psalm 132:17-18
279	matins	1	gospel	Luke 6:17-23
279	liturgy	0	psalm	Psalm 99:6-7
279	liturgy	1	gospel	John 16:20-33
280	vespers	0	psalm	Psalm 112:1-2
280	vespers	1	gospel	Matthew 24:14-23
280	matins	0	psalm	Psalm 132:1-2|Psalm 132:9-10
280	matins	1	gospel	Luke 6:17-23
280	liturgy	0	psalm	Psalm 1:1
280	liturgy	1	gospel	Matthew 4:23-25|Matthew 5:1-16
281	vespers	0	psalm	Psalm 32:11|Psalm 33:1|Psalm 32:6
281	vespers	1	gospel	Matthew 25:14-23
281	matins	0	psalm	Psalm 33:1|Psalm 33:12
281	matins	1	gospel	Luke 19:11-19
281	liturgy	0	psalm	Psalm 34:19|Psalm 68:3
281	liturgy	1	gospel	Luke 12:32-44
282	vespers	0	psalm	Psalm 65:4-5
282	vespers	1	gospel	Matthew 24:42-47
282	matins	0	psalm	Psalm 37:17-18|Psalm 37:29
282	matins	1	gospel	Mark 13:33-37
282	liturgy	0	psalm	Psalm 37:30-31
282	liturgy	1	gospel	Luke 16:1-12
283	vespers	0	psalm	Psalm 40:2-3
283	vespers	1	gospel	Matthew 7:22-25
283	matins	0	psalm	Psalm 89:24|Psalm 89:19
283	matins	1	gospel	Luke 13:23-30
283	liturgy	0	psalm	Psalm 61:1-3
283	liturgy	1	gospel	Luke 14:25-35
284	vespers	0	psalm	Psalm 5:11-12
284	vespers	1	gospel	Matthew 10:24-33
284	matins	0	psalm	Psalm 34:19-20
284	matins	1	gospel	John 12:20-26
284	liturgy	0	psalm	Psalm 21:3|Psalm 21:5
284	liturgy	1	gospel	Luke 10:1-20
285	vespers	0	psalm	Psalm 40:9|Psalm 40:2
285	vespers	1	gospel	Mark 6:6-13
285	matins	0	psalm	Psalm 105:1-3
285	matins	1	gospel	Mark 10:17-30
285	liturgy	0	psalm	Psalm 96:1-2
285	liturgy	1	gospel	Mark 1:1-11
286	vespers	0	psalm	Psalm 118:1,2
286	vespers	1	gospel	Jn 3:31-36
286	matins	0	psalm	Psalm 118:18|Psalm 118:19
286	matins	1	gospel	Mk 4:35-41
286	liturgy	0	psalm	Psalm 34:5|Psalm 34:8
286	liturgy	1	gospel	Jn 12:44-48
287	vespers	0	psalm	Psalm 18:34|Psalm 18:39
287	vespers	1	gospel	Matthew 8:5-13
287	matins	0	psalm	Psalm 68:35|Psalm 68:3
287	matins	1	gospel	Luke 12:4-12
287	liturgy	0	psalm	Psalm 45:3-4
287	liturgy	1	gospel	Matthew 12:9-23
288	vespers	0	psalm	Psalm 68:11|Psalm 68:35
288	vespers	1	gospel	Mark 3:7-21
288	matins	0	psalm	Psalm 145:10-12
288	matins	1	gospel	Luke 6:12-23
288	liturgy	0	psalm	Psalm 19:1|Psalm 19:4
288	liturgy	1	gospel	John 20:24-31
289	vespers	0	psalm	Psalm 89:19-21
289	vespers	1	gospel	Matthew 10:34-42
289	matins	0	psalm	Psalm 132:9-10|Psalm 132:17-18
289	matins	1	gospel	Luke 6:17-23
289	liturgy	0	psalm	Psalm 99:6-7
289	liturgy	1	gospel	John 16:20-33
290	vespers	0	psalm	Psalm 132:9-10|Psalm 132:17-18
290	vespers	1	gospel	Matthew 4:23-25|Matthew 5:1-16
290	matins	0	psalm	Psalm 110:4-6
290	matins	1	gospel	Luke 6:17-23
290	liturgy	0	psalm	Psalm 73:23-24|Psalm 73:28|Psalm 9:14
290	liturgy	1	gospel	John 10:1-16
291	vespers	0	psalm	Psalm 40:2-3
291	vespers	1	gospel	Matthew 7:22-25
291	matins	0	psalm	Psalm 89:24|Psalm 89:19
291	matins	1	gospel	Luke 13:23-30
291	liturgy	0	psalm	Psalm 61:1-3
291	liturgy	1	gospel	Luke 14:25-35
292	vespers	0	psalm	Psalm 110:4|Psalm 110:7
292	vespers	1	gospel	Matthew 16:13-19
292	matins	0	psalm	Psalm 73:23-24|Psalm 73:28|Psalm 9:14
292	matins	1	gospel	John 15:17-25
292	liturgy	0	psalm	Psalm 107:32|Psalm 107:41-42
292	liturgy	1	gospel	John 10:1-16
293	vespers	0	psalm	Psalm 79:13|Psalm 79:9
293	vespers	1	gospel	Matt 22:34-40
293	matins	0	psalm	Psalm 74:12|Psalm 74:2
293	matins	1	gospel	Lk 24:1-12
293	liturgy	0	psalm	Psalm 68:26|Psalm 68:19
293	liturgy	1	gospel	Lk 10:25-37
294	vespers	0	psalm	Psalm 46:10-11
294	vespers	1	gospel	Matt 22:41-46
294	matins	0	psalm	Psalm 47:6-7
294	matins	1	gospel	Jn 20:1-18
294	liturgy	0	psalm	Psalm 66:4|Psalm 66:1-2
294	liturgy	1	gospel	Lk 4:1-13
295	vespers	0	psalm	Psalm 5:11-12
295	vespers	1	gospel	Matthew 10:24-33
295	matins	0	psalm	Psalm 34:19-20
295	matins	1	gospel	John 12:20-26
295	liturgy	0	psalm	Psalm 21:3|Psalm 21:5
295	liturgy	1	gospel	Luke 10:1-20
296	vespers	0	psalm	Psalm 35:10|Psalm 35:27
296	vespers	1	gospel	Luke 7:18-28
296	matins	0	psalm	Psalm 51:8|Psalm 51:19
296	matins	1	gospel	John 3:25-36
296	liturgy	0	psalm	Psalm 34:19|Psalm 34:15
296	liturgy	1	gospel	Matthew 11:2-10
297	vespers	0	psalm	Psalm 89:19-21
297	vespers	1	gospel	Matthew 10:34-42
297	matins	0	psalm	Psalm 132:9-10|Psalm 132:17-18
297	matins	1	gospel	Luke 6:17-23
297	liturgy	0	psalm	Psalm 99:6-7
297	liturgy	1	gospel	John 16:20-33
298	vespers	0	psalm	Psalm 68:35|Psalm 68:3
298	vespers	1	gospel	Matthew 10:16-23
298	matins	0	psalm	Psalm 97:11-12
298	matins	1	gospel	Mark 13:9-13
298	liturgy	0	psalm	Psalm 34:19-20
298	liturgy	1	gospel	Luke 11:53-54|Luke 12:1-12
299	vespers	0	psalm	Psalm 32:11|Psalm 33:1|Psalm 32:6
299	vespers	1	gospel	Matthew 25:14-23
299	matins	0	psalm	Psalm 33:1|Psalm 33:12
299	matins	1	gospel	Luke 19:11-19
299	liturgy	0	psalm	Psalm 34:19|Psalm 68:3
299	liturgy	1	gospel	Luke 12:32-44
300	vespers	0	psalm	Psalm 18:34|Psalm 18:39
300	vespers	1	gospel	Matthew 10:16-23
300	matins	0	psalm	Psalm 45:3|Psalm 45:6
300	matins	1	gospel	Luke 7:11-17
300	liturgy	0	psalm	Psalm 91:13|Psalm 91:11
300	liturgy	1	gospel	Luke 10:21-24
301	vespers	0	psalm	Psalm 34:17-18
301	vespers	1	gospel	Matthew 10:16-22
301	matins	0	psalm	Psalm 34:19-20
301	matins	1	gospel	Mark 8:34-38|Mark 9:1
301	liturgy	0	psalm	Psalm 97:11-12
301	liturgy	1	gospel	Luke 21:12-19
302	vespers	0	psalm	Psalm 105:23|Psalm 105:27
302	vespers	1	gospel	Matthew 4:12-17
302	matins	0	psalm	Psalm 106:21-22|Psalm 106:4
302	matins	1	gospel	Matthew 12:15-23
302	liturgy	0	psalm	Psalm 105:36|Psalm 105:38
302	liturgy	1	gospel	Matthew 2:13-23
303	vespers	0	psalm	Psalm 105:14-15
303	vespers	1	gospel	Luke 11:37-51
303	matins	0	psalm	Psalm 105:26-27|Psalm 105:45
303	matins	1	gospel	Matthew 17:1-9
303	liturgy	0	psalm	Psalm 99:6-7
303	liturgy	1	gospel	Matthew 23:14-36
304	vespers	0	psalm	Psalm 4:3|Psalm 4:6-7
304	vespers	1	gospel	Matthew 10:24-33
304	matins	0	psalm	Psalm 113:1-2
304	matins	1	gospel	Mark 8:34-38|Mark 9:1
304	liturgy	0	psalm	Psalm 66:12-14
304	liturgy	1	gospel	Luke 21:12-19
305	vespers	0	psalm	Psalm 4:6-8
305	vespers	1	gospel	Matthew 16:24-28
305	matins	0	psalm	Psalm 5:11-12
305	matins	1	gospel	Matthew 10:34-42
305	liturgy	0	psalm	Psalm 68:35|Psalm 68:3
305	liturgy	1	gospel	Luke 12:4-12
306	vespers	0	psalm	Psalm 149:1-2
306	vespers	1	gospel	Matthew 13:44-52
306	matins	0	psalm	Psalm 104:4|Psalm 104:3
306	matins	1	gospel	Luke 15:3-10
306	liturgy	0	psalm	Psalm 103:20-21
306	liturgy	1	gospel	Matthew 13:24-43
307	vespers	0	psalm	Psalm 34:7-8
307	vespers	1	gospel	Matthew 16:24-28
307	matins	0	psalm	Psalm 97:7-9
307	matins	1	gospel	Matthew 18:10-20
307	liturgy	0	psalm	Psalm 138:1-2
307	liturgy	1	gospel	Matthew 25:31-46
308	vespers	0	psalm	Psalm 89:19-21
308	vespers	1	gospel	Matt 10:34-42
308	matins	0	psalm	Psalm 132:9|Psalm 132:10|Psalm 132:17|Psalm 132:18
308	matins	1	gospel	Lk 6:17-23
308	liturgy	0	psalm	Psalm 99:6-7
308	liturgy	1	gospel	Jn 16:20-33
309	vespers	0	psalm	Psalm 68:35|Psalm 68:3
309	vespers	1	gospel	Matt 10:16-23
309	matins	0	psalm	Psalm 97:11-12
309	matins	1	gospel	Mk 13:9-13
309	liturgy	0	psalm	Psalm 34:19-20
309	liturgy	1	gospel	Lk 11:53—|Lk 12:1-12
310	vespers	0	psalm	Psalm 112:6,7,9
310	vespers	1	gospel	Matt 24:42-47
310	matins	0	psalm	Psalm 92:10|Psalm 92:14|Psalm 92:15
310	matins	1	gospel	Lk 19:11-19
310	liturgy	0	psalm	Psalm 92:12 - 13
310	liturgy	1	gospel	Lk 12:32 - 44
311	vespers	0	psalm	Psalm 32:11|33:1|32:6
311	vespers	1	gospel	Matt 25:14 - 23
311	matins	0	psalm	Psalm 33:1|Psalm 33:12
311	matins	1	gospel	Lk 19:11 - 19
311	liturgy	0	psalm	Psalm 34:19|Psalm 68:3
311	liturgy	1	gospel	Lk 12:32 - 44
312	vespers	0	psalm	Psalm 89:36|Psalm 89:29
312	vespers	1	gospel	Lk 9:18-27
312	matins	0	psalm	Psalm 107:32|Psalm 107:41|Psalm 107:42
312	matins	1	gospel	Mk 8:22-29
312	liturgy	0	psalm	Psalm 110:4|Psalm 110:5|Psalm 110:7
312	liturgy	1	gospel	Matt 16:13 - 19
313	vespers	0	psalm	Psalm 34:17,18
313	vespers	1	gospel	Matt 10:16-22
313	matins	0	psalm	Psalm 34:19|Psalm 34:20
313	matins	1	gospel	Mk 8:34—|Mk 9:1-1
313	liturgy	0	psalm	Psalm 97:11|Psalm 97:12
313	liturgy	1	gospel	Lk 21:12-19
314	vespers	0	psalm	Psalm 105:14-15
314	vespers	1	gospel	Luke 11:37-51
314	matins	0	psalm	Psalm 105:26-27|Psalm 105:45
314	matins	1	gospel	Matthew 17:1-9
314	liturgy	0	psalm	Psalm 99:6-7
314	liturgy	1	gospel	Matthew 23:14-36
315	vespers	0	psalm	Psalm 87:3,5,7
315	vespers	1	gospel	Lk 10:38-42
315	matins	0	psalm	Psalm 48:8|Psalm 48:1
315	matins	1	gospel	Matt 12:35-50
315	liturgy	0	psalm	Psalm 45:12-13
315	liturgy	1	gospel	Lk 1:39-56
316	vespers	0	psalm	Psalm 4:3,6,7
316	vespers	1	gospel	Matt 10:24-33
316	matins	0	psalm	Psalm 113:1-2
316	matins	1	gospel	Mk 8:34—|Mk 9:1-1
316	liturgy	0	psalm	Psalm 66:12-14
316	liturgy	1	gospel	Lk 21:12-19
317	vespers	0	psalm	Psalm 32:11|33:1|32:6
317	vespers	1	gospel	Matt 25:14 - 23
317	matins	0	psalm	Psalm 33:1|Psalm 33:12
317	matins	1	gospel	Lk 19:11 - 19
317	liturgy	0	psalm	Psalm 34:19|Psalm 68:3
317	liturgy	1	gospel	Lk 12:32 - 44
318	vespers	0	psalm	Psalm 40:2-3
318	vespers	1	gospel	Matt 7:22-25
318	matins	0	psalm	Psalm 89:24|Psalm 89:19
318	matins	1	gospel	Lk 13:23-30
318	liturgy	0	psalm	Psalm 61:1-3
318	liturgy	1	gospel	Lk 14:25-35
319	vespers	0	psalm	Psalm 5:11-12
319	vespers	1	gospel	Matt 10:24-33
319	matins	0	psalm	Psalm 34:19-20
319	matins	1	gospel	Jn 12:20-26
319	liturgy	0	psalm	Psalm 21:3|Psalm 21:5
319	liturgy	1	gospel	Lk 10:1-20
320	vespers	0	psalm	Psalm 105:14-15
320	vespers	1	gospel	LK 11:37-51
320	matins	0	psalm	Psalm 105:26,27,45
320	matins	1	gospel	Matt 17:1-9
320	liturgy	0	psalm	Psalm 99:6-7
320	liturgy	1	gospel	Matt. 23:13-36
321	vespers	0	psalm	Psalm 40:9|Psalm 40:2
321	vespers	1	gospel	Mark 6:6-13
321	matins	0	psalm	Psalm 105:1-3
321	matins	1	gospel	Mark 10:17-30
321	liturgy	0	psalm	Psalm 96:1-2
321	liturgy	1	gospel	Mark 1:1-11
322	vespers	0	psalm	Psalm 110:4,5|Psalm 110:7
322	vespers	1	gospel	Matt 16:13 -19
322	matins	0	psalm	Psalm 73:23|Psalm 73:24|Psalm 73:28|Psalm 9: 14
322	matins	1	gospel	Jn 15:17-25
322	liturgy	0	psalm	Psalm 107:32|Psalm 107:41|Psalm 107:42
322	liturgy	1	gospel	Jn 10:1-16
323	vespers	0	psalm	Psalm 65:4-5
323	vespers	1	gospel	Matt 24:42-47
323	matins	0	psalm	Psalm 37:17,18,29
323	matins	1	gospel	Mark 13:33-37
323	liturgy	0	psalm	Psalm 37:30-31
323	liturgy	1	gospel	Lk 16:1-12
324	vespers	0	psalm	Psalm 52:8-9
324	vespers	1	gospel	Lk 7:28-35
324	matins	0	psalm	Psalm 92:10|Psalm 92:14|Psalm 92:15
324	matins	1	gospel	Matt 11:11-19
324	liturgy	0	psalm	Psalm 92:12 - 13
324	liturgy	1	gospel	Lk 1:57 - 80
325	vespers	0	psalm	Psalm 9:10
325	vespers	1	gospel	Matthew 17:1-13
325	matins	0	psalm	Psalm 67:1-2
325	matins	1	gospel	Matthew 28:1-20
325	liturgy	0	psalm	Psalm 143:10,8
325	liturgy	1	gospel	Luke 11:1-13
326	vespers	0	psalm	Psalm 16:7-8
326	vespers	1	gospel	Luke 4:38-41
326	matins	0	psalm	Psalm 34:1-2
326	matins	1	gospel	Mark 16:2-8
326	liturgy	0	psalm	Psalm 13:6,5
326	liturgy	1	gospel	Luke 5:17-26
327	vespers	0	psalm	Psalm 6:2|Psalm 38:15
327	vespers	1	gospel	Mt 7:7-12
327	matins	0	psalm	Psalm 38:21-22
327	matins	1	gospel	Lk 24:1-12
327	liturgy	0	psalm	Psalm 61:5|Psalm 61:8
327	liturgy	1	gospel	Mt 12:22-37
328	vespers	0	psalm	Psalm 84:8|Psalm 84:4
328	vespers	1	gospel	Mt 5:34-48
328	matins	0	psalm	Psalm 61:5|Psalm 61:8
328	matins	1	gospel	Jn 20:1-18
328	liturgy	0	psalm	Psalm 69:32-33|Psalm 69:30
328	liturgy	1	gospel	Lk 6:27-38
329	vespers	0	psalm	Psalm 68:25-26
329	vespers	1	gospel	Matt 26:6 - 13
329	matins	0	psalm	Psalm 8:2 - 3
329	matins	1	gospel	Jn 4:15 - 24
329	liturgy	0	psalm	Psalm 45:14 - 15
329	liturgy	1	gospel	Matt 25:1 - 13
330	vespers	0	psalm	Psalm 40:9|Psalm 40:2
330	vespers	1	gospel	Mk 6:6-13
330	matins	0	psalm	Psalm 105:1-3
330	matins	1	gospel	Mark 10:17-30
330	liturgy	0	psalm	Psalm 96:1|Psalm 96:2
330	liturgy	1	gospel	Mk 1:1-11
331	vespers	0	psalm	Psalm 110:4,5|Psalm 110:7
331	vespers	1	gospel	Matt 16:13 -19
331	matins	0	psalm	Psalm 73:23|Psalm 73:24|Psalm 73:28|Psalm 9: 14
331	matins	1	gospel	Jn 15:17-25
331	liturgy	0	psalm	Psalm 107:32|Psalm 107:41|Psalm 107:42
331	liturgy	1	gospel	Jn 10:1-16
332	vespers	0	psalm	Psalm 68:35|Psalm 68:3
332	vespers	1	gospel	Matthew 10:16-23
332	matins	0	psalm	Psalm 97:11-12
332	matins	1	gospel	Mark 13:9-13
332	liturgy	0	psalm	Psalm 34:19-20
332	liturgy	1	gospel	Luke 11:53-54|Luke 12:1-12
333	vespers	0	psalm	Psalm 68:11,35
333	vespers	1	gospel	Mk 3:7-21
333	matins	0	psalm	Psalm 145:10-12
333	matins	1	gospel	Lk 6:12-23
333	liturgy	0	psalm	Psalm 19:1|Psalm 19:4
333	liturgy	1	gospel	Matt 10:1-15
334	vespers	0	psalm	Psalm 5:11-12
334	vespers	1	gospel	Matt 10:24-33
334	matins	0	psalm	Psalm 34:19-20
334	matins	1	gospel	Jn 12:20-26
334	liturgy	0	psalm	Psalm 21:3|Psalm 21:5
334	liturgy	1	gospel	Lk 10:1-20
335	vespers	0	psalm	Psalm 32:11|Psalm 32:6
335	vespers	1	gospel	Lk 22:24 - 30
335	matins	0	psalm	Psalm 33:1|Psalm 33:12
335	matins	1	gospel	Matt 25:14 - 23
335	liturgy	0	psalm	Psalm 132:9|Psalm 132:10|Psalm 132:1|Psalm 132:2
335	liturgy	1	gospel	Matt 9:33 - 41
336	vespers	0	psalm	Psalm 4:3,6,7
336	vespers	1	gospel	Matt 10:24-33
336	matins	0	psalm	Psalm 113:1-2
336	matins	1	gospel	Mk 8:34—|Mk 9:1-1
336	liturgy	0	psalm	Psalm 66:12-14
336	liturgy	1	gospel	Lk 21:12-19
337	vespers	0	psalm	Psalm 40:9|Psalm 40:2
337	vespers	1	gospel	Mk 6:6-13
337	matins	0	psalm	Psalm 105:1-3
337	matins	1	gospel	Mark 10:17-30
337	liturgy	0	psalm	Psalm 96:1|Psalm 96:2
337	liturgy	1	gospel	Mk 1:1-11
338	vespers	0	psalm	Psalm 89:19-21
338	vespers	1	gospel	Matt 10:34-42
338	matins	0	psalm	Psalm 132:9|Psalm 132:10|Psalm 132:17|Psalm 132:18
338	matins	1	gospel	Lk 6:17-23
338	liturgy	0	psalm	Psalm 99:6-7
338	liturgy	1	gospel	Jn 16:20-33
339	vespers	0	psalm	Psalm 4:6-8
339	vespers	1	gospel	Matthew 16:24-28
339	matins	0	psalm	Psalm 5:11-12
339	matins	1	gospel	Matthew 10:34-42
339	liturgy	0	psalm	Psalm 68:35|Psalm 68:3
339	liturgy	1	gospel	Luke 12:4-12
340	vespers	0	psalm	Psalm 68:65|Psalm 68:3
340	vespers	1	gospel	Matt 10:16-23
340	matins	0	psalm	Psalm 97:11-12
340	matins	1	gospel	Mk 13:9-13
340	liturgy	0	psalm	Psalm 34:19-20
340	liturgy	1	gospel	Lk 11:53—|Lk 12:1-12
341	vespers	0	psalm	Psalm 89:19-21
341	vespers	1	gospel	Matt 10:34-42
341	matins	0	psalm	Psalm 132:9|Psalm 132:10|Psalm 132:17|Psalm 132:18
341	matins	1	gospel	Lk 6:17-23
341	liturgy	0	psalm	Psalm 99:6-7
341	liturgy	1	gospel	Jn 16:20-33
342	vespers	0	psalm	Psalm 110:4,5|Psalm 110:7
342	vespers	1	gospel	Matt 16:13-19
342	matins	0	psalm	Psalm 73:23|Psalm 73:24|Psalm 73:28|Psalm 9: 14
342	matins	1	gospel	Jn 15:17-25
342	liturgy	0	psalm	Psalm 107:32|Psalm 107:41|Psalm 107:42
342	liturgy	1	gospel	Jn 10:1-16
343	vespers	0	psalm	Psalm 40:2-3
343	vespers	1	gospel	Matt 7:22-25
343	matins	0	psalm	Psalm 89:24|Psalm 89:19
343	matins	1	gospel	Lk 13:23-30
343	liturgy	0	psalm	Psalm 61:1-3
343	liturgy	1	gospel	Lk 14:25-35
344	vespers	0	psalm	Psalm 19:1,4
344	vespers	1	gospel	Jn 15:7 - 16
344	matins	0	psalm	Psalm 45:1 - 2
344	matins	1	gospel	Jn 1:1 - 17
344	liturgy	0	psalm	Psalm 139:17 - 18
344	liturgy	1	gospel	John 21:15 - 25
345	vespers	0	psalm	Psalm 68:25-26
345	vespers	1	gospel	Matt 26:6 - 13
345	matins	0	psalm	Psalm 8:2 - 3
345	matins	1	gospel	Jn 4:15 - 24
345	liturgy	0	psalm	Psalm 45:14 - 15
345	liturgy	1	gospel	Matt 25:1 - 13
346	vespers	0	psalm	Psalm 68:11|Psalm 68:35
346	vespers	1	gospel	Mark 3:7-21
346	matins	0	psalm	Psalm 145:10-12
346	matins	1	gospel	Luke 6:12-23
346	liturgy	0	psalm	Psalm 19:1|Psalm 19:4
346	liturgy	1	gospel	Matthew 10:1-15
347	vespers	0	psalm	Psalm 4:3,6,7
347	vespers	1	gospel	Matt 10:24-33
347	matins	0	psalm	Psalm 113:1-2
347	matins	1	gospel	Mk 8:34—|Mk 9:1-1
347	liturgy	0	psalm	Psalm 66:12-14
347	liturgy	1	gospel	Lk 21:12-19
348	vespers	0	psalm	Psalm 18:34,39
348	vespers	1	gospel	Matt 10:16-23
348	matins	0	psalm	Psalm 45:3|Psalm 45:6
348	matins	1	gospel	Lk 7:11-17
348	liturgy	0	psalm	Psalm 91:13|Psalm 91:11
348	liturgy	1	gospel	Lk 10:21-24
349	vespers	0	psalm	Psalm 34:19-20
349	vespers	1	gospel	Matt 16:24-28
349	matins	0	psalm	Psalm 37:39-40
349	matins	1	gospel	Mk 19:9-13
349	liturgy	0	psalm	Psalm 97:11-12
349	liturgy	1	gospel	Lk 11:53—|Lk 12:1-12
350	vespers	0	psalm	Psalm 4:6-8
350	vespers	1	gospel	Matt 16:24-28
350	matins	0	psalm	Psalm 5:11|Psalm 5:12
350	matins	1	gospel	Matt 10:34-42
350	liturgy	0	psalm	Psalm 68:35|Psalm 68:3
350	liturgy	1	gospel	Lk 12:4-12
351	vespers	0	psalm	Psalm 46:1,9
351	vespers	1	gospel	Mk 1:16-22
351	matins	0	psalm	Psalm 146:1|Psalm 146:5
351	matins	1	gospel	Matt 4:18-22
351	liturgy	0	psalm	Psalm 78:5|Psalm 135:5
351	liturgy	1	gospel	Mk 10:35-45
352	vespers	0	psalm	Psalm 68:65|Psalm 68:3
352	vespers	1	gospel	Matt 10:16-23
352	matins	0	psalm	Psalm 97:11-12
352	matins	1	gospel	Mk 13:9-13
352	liturgy	0	psalm	Psalm 34:19-20
352	liturgy	1	gospel	Lk 11:53—|Lk 12:1-12
353	vespers	0	psalm	Psalm 18:34|Psalm 18:39
353	vespers	1	gospel	Matthew 8:5-13
353	matins	0	psalm	Psalm 68:35|Psalm 68:3
353	matins	1	gospel	Luke 12:4-12
353	liturgy	0	psalm	Psalm 45:3-4
353	liturgy	1	gospel	Matthew 12:9-23
354	vespers	0	psalm	Psalm 105:14-15
354	vespers	1	gospel	Lk 11:37-51
354	matins	0	psalm	Psalm 105:26|Psalm 105:27|Psalm 105:45
354	matins	1	gospel	Matt 17:1-9
354	liturgy	0	psalm	Psalm 99:6-7
354	liturgy	1	gospel	Matt 23:13-26
355	vespers	0	psalm	Psalm 34:17,18
355	vespers	1	gospel	Matt 10:16-22
355	matins	0	psalm	Psalm 34:19|Psalm 34:20
355	matins	1	gospel	Mk 8:34—|Mk 9:1-1
355	liturgy	0	psalm	Psalm 97:11|Psalm 97:12
355	liturgy	1	gospel	Lk 21:12-19
356	vespers	0	psalm	Psalm 68:25-26
356	vespers	1	gospel	Matt 26:6 - 13
356	matins	0	psalm	Psalm 8:2 - 3
356	matins	1	gospel	Jn 4:15 - 24
356	liturgy	0	psalm	Psalm 45:14 - 15
356	liturgy	1	gospel	Matt 25:1 - 13
357	vespers	0	psalm	Psalm 68:11,35
357	vespers	1	gospel	Mk 3:7-21
357	matins	0	psalm	Psalm 145:10-12
357	matins	1	gospel	Lk 6:12-23
357	liturgy	0	psalm	Psalm 19:1|Psalm 19:4
357	liturgy	1	gospel	Matt 10:1-15
358	vespers	0	psalm	Psalm 4:3,6,7
358	vespers	1	gospel	Matt 10:24-33
358	matins	0	psalm	Psalm 113:1-2
358	matins	1	gospel	Mk 8:34—|Mk 9:1-1
358	liturgy	0	psalm	Psalm 66:12-14
358	liturgy	1	gospel	Lk 21:12-19
359	vespers	0	psalm	Psalm 20:6,9
359	vespers	1	gospel	Lk 9:1-6
359	matins	0	psalm	Psalm 31:23|Psalm 31:19
359	matins	1	gospel	Mt 28:1-20
359	liturgy	0	psalm	Psalm 89:7
359	liturgy	1	gospel	Lk 10:1-20
360	vespers	0	psalm	Psalm 128:1,5
360	vespers	1	gospel	Lk 16:1-18
360	matins	0	psalm	Psalm 41:1-2
360	matins	1	gospel	Mk 16:2-8
360	liturgy	0	psalm	Psalm 119:1-2
360	liturgy	1	gospel	Mt 18:1-9
361	vespers	0	psalm	Psalm 52:9|Psalm 52:8
361	vespers	1	gospel	Lk 14:7-15
361	matins	0	psalm	Psalm 134:1-2
361	matins	1	gospel	Lk 24:1-12
361	liturgy	0	psalm	Psalm 145:17-18
361	liturgy	1	gospel	Lk 9:10-17
362	vespers	0	psalm	Psalm 59:9-10,17
362	vespers	1	gospel	Lk 7:1-10
362	matins	0	psalm	Psalm 86:12-13
362	matins	1	gospel	Jn 20:1-18
362	liturgy	0	psalm	Psalm 40:5|Psalm 40:16
362	liturgy	1	gospel	Jn 11:1-45
363	vespers	0	psalm	Psalm 68:65|Psalm 68:3
363	vespers	1	gospel	Matt 10:16-23
363	matins	0	psalm	Psalm 97:11-12
363	matins	1	gospel	Mk 13:9-13
363	liturgy	0	psalm	Psalm 34:19-20
363	liturgy	1	gospel	Lk 11:53—|Lk 12:1-12
364	vespers	0	psalm	Psalm 68:25-26
364	vespers	1	gospel	Matthew 26:6-13
364	matins	0	psalm	Psalm 8:2-3
364	matins	1	gospel	John 4:15-24
364	liturgy	0	psalm	Psalm 45:14-15
364	liturgy	1	gospel	Matthew 25:1-13
365	vespers	0	psalm	Psalm 40:2-3
365	vespers	1	gospel	Matt 7:22-25
365	matins	0	psalm	Psalm 89:24|Psalm 89:19
365	matins	1	gospel	Lk 13:23-30
365	liturgy	0	psalm	Psalm 61:1-3
365	liturgy	1	gospel	Lk 14:25-35
366	vespers	0	psalm	Psalm 105:14-15
366	vespers	1	gospel	Lk 11:37-51
366	matins	0	psalm	Psalm 105:26|Psalm 105:27|Psalm 105:45
366	matins	1	gospel	Matt 17:1-9
366	liturgy	0	psalm	Psalm 99:6-7
366	liturgy	1	gospel	Matt 23:13-26
367	vespers	0	psalm	Psalm 32:11|33:1|32:6
367	vespers	1	gospel	Matt 10:34 - 42
367	matins	0	psalm	Psalm 33:1|Psalm 33:12
367	matins	1	gospel	Lk 6:17 - 23
367	liturgy	0	psalm	Psalm 34:19 - 20
367	liturgy	1	gospel	Matt 3:23—|Matt 5:1-16
368	vespers	0	psalm	Psalm 68:25-26
368	vespers	1	gospel	Matt 26:6 - 13
368	matins	0	psalm	Psalm 8:2 - 3
368	matins	1	gospel	Jn 4:15 - 24
368	liturgy	0	psalm	Psalm 45:14 - 15
368	liturgy	1	gospel	Matt 25:1 - 13
369	vespers	0	psalm	Psalm 9:11,14
369	vespers	1	gospel	Mk 14:-39
369	matins	0	psalm	Psalm 102:19-21
369	matins	1	gospel	Mk 12:41-44
369	liturgy	0	psalm	Psalm 102:13|Psalm 102:16|Psalm 102:17
369	liturgy	1	gospel	Lk 1:1-25
370	vespers	0	psalm	Psalm 4:3,6,7
370	vespers	1	gospel	Matt 11:25-30
370	matins	0	psalm	Psalm 112:1-2
370	matins	1	gospel	Mk 10:13-16
370	liturgy	0	psalm	Psalm 66:12-14
370	liturgy	1	gospel	Matt 18:10-20
371	vespers	0	psalm	Psalm 68:35|Psalm 68:3
371	vespers	1	gospel	Matthew 10:16-23
371	matins	0	psalm	Psalm 97:11-12
371	matins	1	gospel	Mark 13:9-13
371	liturgy	0	psalm	Psalm 34:19-20
371	liturgy	1	gospel	Luke 11:53-54|Luke 12:1-12
372	vespers	0	psalm	Psalm 46:1,9
372	vespers	1	gospel	Mk 1:16-22
372	matins	0	psalm	Psalm 146:1|Psalm 146:5
372	matins	1	gospel	Matt 4:18-22
372	liturgy	0	psalm	Psalm 78:5|Psalm 135:5
372	liturgy	1	gospel	Mk 10:35-45
373	vespers	0	psalm	Psalm 89:19-21
373	vespers	1	gospel	Matt 10:34-42
373	matins	0	psalm	Psalm 132:9|Psalm 132:10|Psalm 132:17|Psalm 132:18
373	matins	1	gospel	Lk 6:17-23
373	liturgy	0	psalm	Psalm 99:6-7
373	liturgy	1	gospel	Jn 16:20-33
374	vespers	0	psalm	Psalm 4:6-8
374	vespers	1	gospel	Jn 8:28-42
374	matins	0	psalm	Psalm 60:4-5
374	matins	1	gospel	Jn 12:26-36
374	liturgy	0	psalm	Psalm 65:1-2
374	liturgy	1	gospel	Jn 10:22-38
375	vespers	0	psalm	Psalm 99:6-7
375	vespers	1	gospel	Lk 9:28-36
375	matins	0	psalm	Psalm 104:31-32
375	matins	1	gospel	Matt 17:1-9
375	liturgy	0	psalm	Psalm 87:1|Psalm 87:2|Psalm 87:5
375	liturgy	1	gospel	Mk 9:2-13
376	vespers	0	psalm	Psalm 132:9,10,17,18
376	vespers	1	gospel	Matt 4:23—|Matt 5:1-16
376	matins	0	psalm	Psalm 110:4|Psalm 110:5|Psalm 110:7
376	matins	1	gospel	Lk 6:17-23
376	liturgy	0	psalm	Psalm 73:23|Psalm 73:24|Psalm 73:28
376	liturgy	1	gospel	Jn 10:1-16
377	vespers	0	psalm	Psalm 68:25-26
377	vespers	1	gospel	Matt 26:6 - 13
377	matins	0	psalm	Psalm 8:2 - 3
377	matins	1	gospel	Jn 4:15 - 24
377	liturgy	0	psalm	Psalm 45:14 - 15
377	liturgy	1	gospel	Matt 25:1 - 13
378	vespers	0	psalm	Psalm 87:3,5,7
378	vespers	1	gospel	Lk 10:38-52
378	matins	0	psalm	Psalm 48:8|Psalm 48:1
378	matins	1	gospel	Matt 12:35-50
378	liturgy	0	psalm	Psalm 45:12-13
378	liturgy	1	gospel	Lk 1:39-56
379	vespers	0	psalm	Psalm 34:19-20
379	vespers	1	gospel	Mk 1:16-22
379	matins	0	psalm	Psalm 37:39-40
379	matins	1	gospel	Matt 4:18-22
379	liturgy	0	psalm	Psalm 97:11-12
379	liturgy	1	gospel	Mk 10:35-45
380	vespers	0	psalm	Psalm 110:4,5|Psalm 110:7
380	vespers	1	gospel	Matt 16:13 -19
380	matins	0	psalm	Psalm 73:23|Psalm 73:24|Psalm 73:28|Psalm 9: 14
380	matins	1	gospel	Jn 15:17-25
380	liturgy	0	psalm	Psalm 107:32|Psalm 107:41|Psalm 107:42
380	liturgy	1	gospel	Jn 10:1-16
381	vespers	0	psalm	Psalm 34:19-20
381	vespers	1	gospel	Mk 1:16-22
381	matins	0	psalm	Psalm 37:39-40
381	matins	1	gospel	Matt 4:18-22
381	liturgy	0	psalm	Psalm 97:11-12
381	liturgy	1	gospel	Mk 10:35-45
382	vespers	0	psalm	Psalm 4:3,6,7
382	vespers	1	gospel	Matt 10:24-33
382	matins	0	psalm	Psalm 113:1-2
382	matins	1	gospel	Mk 8:34—|Mk 9:1-1
382	liturgy	0	psalm	Psalm 66:12-14
382	liturgy	1	gospel	Lk 21:12-19
383	vespers	0	psalm	Psalm 68:25-26
383	vespers	1	gospel	Matt 26:6 - 13
383	matins	0	psalm	Psalm 8:2 - 3
383	matins	1	gospel	Jn 4:15 - 24
383	liturgy	0	psalm	Psalm 45:14 - 15
383	liturgy	1	gospel	Matt 25:1 - 13
384	vespers	0	psalm	Psalm 105:14-15
384	vespers	1	gospel	Lk 11:37-51
384	matins	0	psalm	Psalm 105:26|Psalm 105:27|Psalm 105:45
384	matins	1	gospel	Matt 17:1-9
384	liturgy	0	psalm	Psalm 99:6-7
384	liturgy	1	gospel	Matt 23:13-26
385	vespers	0	psalm	Psalm 34:17-18
385	vespers	1	gospel	Matthew 10:16-22
385	matins	0	psalm	Psalm 34:19-20
385	matins	1	gospel	Mark 8:34-38|Mark 9:1
385	liturgy	0	psalm	Psalm 97:11-12
385	liturgy	1	gospel	Luke 21:12-19
386	vespers	0	psalm	Psalm 89:19-21
386	vespers	1	gospel	Matt 10:34-42
386	matins	0	psalm	Psalm 132:9|Psalm 132:10|Psalm 132:17|Psalm 132:18
386	matins	1	gospel	Lk 6:17-23
386	liturgy	0	psalm	Psalm 99:6-7
386	liturgy	1	gospel	Jn 16:20-33
387	vespers	0	psalm	Psalm 42:1
387	vespers	1	gospel	Matt 25:14-23
387	matins	0	psalm	Psalm 34:5|Psalm 34:7
387	matins	1	gospel	Lk 19:11-19
387	liturgy	0	psalm	Psalm 104:1|Psalm 104:2|Psalm 104:4
387	liturgy	1	gospel	Lk 12:32-44
388	vespers	0	psalm	Psalm 31:23|Psalm 31:19
388	vespers	1	gospel	Matt 10:24-33
388	matins	0	psalm	Psalm 145:10|Psalm 145:11|Psalm 145:19|Psalm 145:20
388	matins	1	gospel	12:20-26
388	liturgy	0	psalm	Psalm 149:5|Psalm 149:9
388	liturgy	1	gospel	Lk 21:12-19
389	vespers	0	psalm	Psalm 34:17,18
389	vespers	1	gospel	Matt 10:16-22
389	matins	0	psalm	Psalm 34:19|Psalm 34:20
389	matins	1	gospel	Mk 8:34—|Mk 9:1-1
389	liturgy	0	psalm	Psalm 97:11|Psalm 97:12
389	liturgy	1	gospel	Lk 21:12-19
390	vespers	0	psalm	Psalm 47:8-9
390	vespers	1	gospel	Jn 15:7-16
390	matins	0	psalm	Psalm 105:3-4
390	matins	1	gospel	Lk 16:19-31
390	liturgy	0	psalm	Psalm 105:8-10
390	liturgy	1	gospel	Mk 12:18-27
391	vespers	0	psalm	Psalm 132:9,10,17,18
391	vespers	1	gospel	Matt 15:1-11
391	matins	0	psalm	Psalm 110:4|Psalm 110:5|Psalm 110:7
391	matins	1	gospel	Matt 15:12-20
391	liturgy	0	psalm	Psalm 68:19
391	liturgy	1	gospel	Jn 8:21-27
392	vespers	0	psalm	Psalm 5:11-12
392	vespers	1	gospel	Matthew 13:53-58
392	matins	0	psalm	Psalm 101:8
392	matins	1	gospel	Matthew 14:1-5
392	liturgy	0	psalm	Psalm 50:23|Psalm 50:14
392	liturgy	1	gospel	Luke 14:16-24
393	vespers	0	psalm	Psalm 33:22|Psalm 33:18
393	vespers	1	gospel	Mk 6:45-56
393	matins	0	psalm	Psalm 33:20-21
393	matins	1	gospel	Mt 28:1-20
393	liturgy	0	psalm	Psalm 80:14-15
393	liturgy	1	gospel	Lk 20:9-19
394	vespers	0	psalm	Psalm 119:145-146
394	vespers	1	gospel	Lk 18:9-17
394	matins	0	psalm	Psalm 89:1-2
394	matins	1	gospel	Mk 16:2-8
394	liturgy	0	psalm	Psalm 89:5|Psalm 89:15
394	liturgy	1	gospel	Lk 5:27-39
395	vespers	0	psalm	Psalm 5:7, 11
395	vespers	1	gospel	Luke 11:27-36
395	matins	0	psalm	Psalm 15:1-2
395	matins	1	gospel	Luke 24:1-12
395	liturgy	0	psalm	Psalm 28:2, 6
395	liturgy	1	gospel	Mark 3:22-35
396	vespers	0	psalm	Psalm 119:169,176
396	vespers	1	gospel	Lk 17:20-36
396	matins	0	psalm	Psalm 90:1-2
396	matins	1	gospel	Jn 20:1-18
396	liturgy	0	psalm	Psalm 89:11-12
396	liturgy	1	gospel	Mk 13:3-37
397	vespers	0	psalm	Psalm 93:3,4
397	vespers	1	gospel	Mt 14:15-21
397	matins	0	psalm	Psalm 97:11-12
397	matins	1	gospel	Mk 6:35-44
397	liturgy	0	psalm	Psalm 143:6-7
397	liturgy	1	gospel	Lk 9:12-17
398	vespers	0	psalm	Psalm 65:4-5
398	vespers	1	gospel	Matt 10:34-42
398	matins	0	psalm	Psalm 37:17-18
398	matins	1	gospel	Jn 1:1-17
398	liturgy	0	psalm	Psalm 37:30-31
398	liturgy	1	gospel	Jn 21:15-25
399	vespers	0	psalm	Psalm 19:3-4
399	vespers	1	gospel	Lk 4:38-41
399	matins	0	psalm	Psalm 110:4|Psalm 110:5|Psalm 110:7
399	matins	1	gospel	Lk 5:18-26
399	liturgy	0	psalm	Psalm 105:1|Psalm 68: 11
399	liturgy	1	gospel	Lk 6:12-23
400	vespers	0	psalm	Psalm 34:7-8
400	vespers	1	gospel	Matt 16:24-28
400	matins	0	psalm	Psalm 97:7-9
400	matins	1	gospel	Matt 18:10-20
400	liturgy	0	psalm	Psalm 138:1-3
400	liturgy	1	gospel	Matt 25:32-46
401	vespers	0	psalm	Psalm 68:65|Psalm 68:3
401	vespers	1	gospel	Matt 24:42-47
401	matins	0	psalm	Psalm 97:11-12
401	matins	1	gospel	Mk 13:33-37
401	liturgy	0	psalm	Psalm 116:15-16
401	liturgy	1	gospel	Lk 16:1-12
402	vespers	0	psalm	Psalm 89:19-21
402	vespers	1	gospel	Matt 10:34-42
402	matins	0	psalm	Psalm 132:9|Psalm 132:10|Psalm 132:17|Psalm 132:18
402	matins	1	gospel	Lk 6:17-23
402	liturgy	0	psalm	Psalm 99:6-7
402	liturgy	1	gospel	Jn 16:20-33
403	vespers	0	psalm	Psalm 112:6,7,9
403	vespers	1	gospel	Matt 24:42-47
403	matins	0	psalm	Psalm 92:10|Psalm 92:14|Psalm 92:15
403	matins	1	gospel	Lk 19:11-19
403	liturgy	0	psalm	Psalm 92:12 - 13
403	liturgy	1	gospel	Lk 12:32 - 44
404	matins	0	psalm	Psalm 102:14-15|Psalm 102:7|Psalm 102:9
404	matins	1	gospel	Luke 13:6-9
404	liturgy	0	psalm	Psalm 84:2-3
404	liturgy	1	gospel	Luke 11:29-36
405	matins	0	psalm	Psalm 102:13|Psalm 102:12
405	matins	1	gospel	Matthew 11:25-30
405	liturgy	0	psalm	Psalm 32:1|Psalm 32:5
405	liturgy	1	gospel	Mt 15:32—|Mt 16:1-4
406	vespers	0	psalm	Psalm 17:1,2
406	vespers	1	gospel	Lk 17:3-6
406	matins	0	psalm	Psalm 119:49|Psalm 119:52
406	matins	1	gospel	Mk 13:33-37
406	liturgy	0	psalm	Psalm 95:1|Psalm 95:2
406	liturgy	1	gospel	Lk 13:1-5
407	vespers	0	psalm	Psalm 46:10
407	vespers	1	gospel	Mk 11:22-26
407	matins	0	psalm	Psalm 100:2|Psalm 100:3
407	matins	1	gospel	Lk 17:3-10
407	liturgy	0	psalm	Psalm 2:11|Psalm 2:10
407	liturgy	1	gospel	Matt 6:1-18
408	vespers	0	psalm	Psalm 19:1,4
408	vespers	1	gospel	Jn 15:7 - 16
408	matins	0	psalm	Psalm 45:1 - 2
408	matins	1	gospel	Jn 1:1 - 17
408	liturgy	0	psalm	Psalm 139:17 - 18
408	liturgy	1	gospel	John 21:15 - 25
409	matins	0	psalm	Psalm 22:1|Psalm 22:3
409	matins	1	gospel	Matthew 9:10-15
409	liturgy	0	psalm	Psalm 25:16-17
409	liturgy	1	gospel	Luke 12:41-50
410	matins	0	psalm	Psalm 25:6-7
410	matins	1	gospel	Luke 6:24-34
410	liturgy	0	psalm	Psalm 24:20|Psalm 24:16
410	liturgy	1	gospel	Luke 6:35-38
411	matins	0	psalm	Psalm 23:1-2
411	matins	1	gospel	Luke 8:23-25
411	liturgy	0	psalm	Psalm 117:14|Psalm 117:18
411	liturgy	1	gospel	Mark 4:21-29
412	matins	0	psalm	Psalm 30:1-2
412	matins	1	gospel	Luke 5:12-16
412	liturgy	0	psalm	Psalm 13:5-6
412	liturgy	1	gospel	Luke 11:1-10
413	matins	0	psalm	Psalm 119:57-58
413	matins	1	gospel	Matthew 5:25-37
413	liturgy	0	psalm	Psalm 5:1|Psalm 5:2
413	liturgy	1	gospel	Matthew 5:38-48
414	vespers	0	psalm	Psalm 16:1-2
414	vespers	1	gospel	Matthew 6:34—|Matthew 7:1-12
414	matins	0	psalm	Psalm 18:1-2
414	matins	1	gospel	Matthew 7:22-29
414	liturgy	0	psalm	Psalm 24:1|Psalm 24:2|Psalm 24:4
414	liturgy	1	gospel	Matthew 6:19-30
415	matins	0	psalm	Psalm 38:11
415	matins	1	gospel	Mark 9:25-29
415	liturgy	0	psalm	Psalm 28:1-2
415	liturgy	1	gospel	Luke 18:1-8
416	matins	0	psalm	Psalm 41:4|Psalm 41:13
416	matins	1	gospel	Luke 12:22-31
416	liturgy	0	psalm	Psalm 41:1
416	liturgy	1	gospel	Mark 10:17-27
417	matins	0	psalm	Psalm 18:17-18
417	matins	1	gospel	Matthew 5:17-24
417	liturgy	0	psalm	Psalm 18:1-2
417	liturgy	1	gospel	Matthew 15:32-38
418	matins	0	psalm	Psalm 28:9
418	matins	1	gospel	Matthew 11:20-30
418	liturgy	0	psalm	Psalm 48:10-11
418	liturgy	1	gospel	Matthew 19:16-30
419	vespers	0	psalm	Psalm 4:6-8
419	vespers	1	gospel	Jn 8:28-42
419	matins	0	psalm	Psalm 60:4-5
419	matins	1	gospel	Jn 12:26-36
419	liturgy	0	psalm	Psalm 65:1-2
419	liturgy	1	gospel	Jn 10:22-38
420	matins	0	psalm	Psalm 25:7|Psalm 25:8|Psalm 25:11
420	matins	1	gospel	Mark 9:43-50
420	liturgy	0	psalm	Psalm 118:19|Psalm 118:20
420	liturgy	1	gospel	Matthew 7:13-21
421	vespers	0	psalm	Psalm 51:1|Psalm 51:9
421	vespers	1	gospel	Mark 1:12-15
421	matins	0	psalm	Psalm 57:1
421	matins	1	gospel	Luke 4:1-13
421	liturgy	0	psalm	Psalm 27:8-10
421	liturgy	1	gospel	Matthew 4:1-11
422	matins	0	psalm	Psalm 32:1-2
422	matins	1	gospel	Luke 19:11-28
422	liturgy	0	psalm	Psalm 32:5
422	liturgy	1	gospel	Luke 11:33-36
423	matins	0	psalm	Psalm 31:10
423	matins	1	gospel	Luke 12:54-59
423	liturgy	0	psalm	Psalm 32:2-3
423	liturgy	1	gospel	John 8:31-39
424	matins	0	psalm	Psalm 26:4
424	matins	1	gospel	Luke 13:18-22
424	liturgy	0	psalm	Psalm 27:7-8
424	liturgy	1	gospel	Luke 4:1-13
425	matins	0	psalm	Psalm 9:11-12
425	matins	1	gospel	Luke 20:20-26
425	liturgy	0	psalm	Psalm 9:7-8
425	liturgy	1	gospel	John 12:44-50
426	matins	0	psalm	Psalm 16:10-11
426	matins	1	gospel	Luke 20:27-38
426	liturgy	0	psalm	Psalm 16:1|Psalm 16:2
426	liturgy	1	gospel	Luke 11:14-26
427	matins	0	psalm	Psalm 130:1-2
427	matins	1	gospel	Mark 10:17-27
427	liturgy	0	psalm	Psalm 27:6-8
427	liturgy	1	gospel	Matthew 18:23-35
428	vespers	0	psalm	Psalm 88:1-2
428	vespers	1	gospel	Matthew 15:1-20
428	matins	0	psalm	Psalm 55:1|Psalm 55:2|Psalm 55:16
428	matins	1	gospel	Matthew 20:1-16
428	liturgy	0	psalm	Psalm 79:8-9
428	liturgy	1	gospel	Luke 15:11-32
429	matins	0	psalm	Psalm 55:1|Psalm 27: 7,8
429	matins	1	gospel	Luke 14:7-15
429	liturgy	0	psalm	Psalm 55:16-17
429	liturgy	1	gospel	Luke 16:1-9
430	matins	0	psalm	Psalm 17:1
430	matins	1	gospel	Matthew 21:28-32
430	liturgy	0	psalm	Psalm 17:6
430	liturgy	1	gospel	Luke 9:57-62
431	matins	0	psalm	Psalm 18:37|Psalm 18:40
431	matins	1	gospel	Luke 14:16-24
431	liturgy	0	psalm	Psalm 18:17-18
431	liturgy	1	gospel	Mark 4:35-41
432	matins	0	psalm	Psalm 12:7
432	matins	1	gospel	Mark 3:7-12
432	liturgy	0	psalm	Psalm 48:10-11
432	liturgy	1	gospel	Luke 18:35-43
433	matins	0	psalm	Psalm 28:6-7
433	matins	1	gospel	Luke 4:31-37
433	liturgy	0	psalm	Psalm 28:2
433	liturgy	1	gospel	Matthew 15:21-31
434	matins	0	psalm	Psalm 142:5|Psalm 142:7
434	matins	1	gospel	Luke 16:19-31
434	liturgy	0	psalm	Psalm 61:1|Psalm 610:5
434	liturgy	1	gospel	Matthew 21:33-45
435	vespers	0	psalm	Psalm 27:14|27:13
435	vespers	1	gospel	Luke 12:22-31
435	matins	0	psalm	Psalm 31:24|Psalm 31:33
435	matins	1	gospel	Matthew 22:1-14
435	liturgy	0	psalm	Psalm 105:3-5
435	liturgy	1	gospel	John 4:1-42
436	matins	0	psalm	Psalm 88:2-4
436	matins	1	gospel	Luke 12:16-21
436	liturgy	0	psalm	Psalm 86:3-4
436	liturgy	1	gospel	Luke 9:12-17
437	matins	0	psalm	Psalm 86:5-6
437	matins	1	gospel	Mark 9:14-24
437	liturgy	0	psalm	Psalm 86:17
437	liturgy	1	gospel	John 8:12-20
438	matins	0	psalm	Psalm 86:14
438	matins	1	gospel	Luke 9:37-43
438	liturgy	0	psalm	Psalm 86:17
438	liturgy	1	gospel	Luke 13:10-17
439	matins	0	psalm	Psalm 86:9 - 10
439	matins	1	gospel	Mark 12:28-34
439	liturgy	0	psalm	Psalm 138:1|Psalm 138:2
439	liturgy	1	gospel	John 8:21-27
440	matins	0	psalm	Psalm 65:2|Psalm 65:3
440	matins	1	gospel	Luke 15:3-10
440	liturgy	0	psalm	Psalm 143:1-2
440	liturgy	1	gospel	Matthew 23:14-39
441	vespers	0	psalm	Psalm 39:12
441	vespers	1	gospel	Luke 18:1-8
441	matins	0	psalm	Psalm 101:1|Psalm 101:2|Psalm 101:12
441	matins	1	gospel	Matthew 21:33-46
441	liturgy	0	psalm	Psalm 33:5-6
441	liturgy	1	gospel	John 5:1-18
442	matins	0	psalm	Psalm 38:9
442	matins	1	gospel	Mark 12:1-12
442	liturgy	0	psalm	Psalm 35:1|Psalm 35:2
442	liturgy	1	gospel	Luke 13:1-5
443	matins	0	psalm	Psalm 35:13
443	matins	1	gospel	Luke 4:22-30
443	liturgy	0	psalm	Psalm 42:1
443	liturgy	1	gospel	Luke 9:18-22
444	matins	0	psalm	Psalm 102:17|Psalm 102:21
444	matins	1	gospel	Mark 7:1-20
444	liturgy	0	psalm	Psalm 9:11|Psalm 9:12
444	liturgy	1	gospel	Luke 11:45-52
445	matins	0	psalm	Psalm 9:13
445	matins	1	gospel	Luke 20:9-19
445	liturgy	0	psalm	Psalm 9:13|Psalm 9:14
445	liturgy	1	gospel	John 6:47-71
446	matins	0	psalm	Psalm 51:7-8
446	matins	1	gospel	John 3:14-21
446	liturgy	0	psalm	Psalm 34:5|Psalm 34:4
446	liturgy	1	gospel	John 3:1-13
447	matins	0	psalm	Psalm 79:8|Psalm 79:9
447	matins	1	gospel	Matthew 9:1-8
447	liturgy	0	psalm	Psalm 32:1|Psalm 32:2
447	liturgy	1	gospel	Mark 10:46-52
448	vespers	0	psalm	Psalm 17:3|17:5
448	vespers	1	gospel	Luke 13:22-35
448	matins	0	psalm	Psalm 26:2|Psalm 26:3
448	matins	1	gospel	Matthew 23:1-39
448	liturgy	0	psalm	Psalm 143:7|Psalm 143:1
448	liturgy	1	gospel	John 9:1-41
449	matins	0	psalm	Psalm 32:10-11
449	matins	1	gospel	Luke 16:19-31
449	liturgy	0	psalm	Psalm 86:12|Psalm 86:13
449	liturgy	1	gospel	John 5:31-47
450	matins	0	psalm	Psalm 38:18|Psalm 38:19
450	matins	1	gospel	Luke 17:1-10
450	liturgy	0	psalm	Psalm 51:2|Psalm 51:3
450	liturgy	1	gospel	John 12:36-43
451	matins	0	psalm	Psalm 57:1
451	matins	1	gospel	Luke 14:28-35
451	liturgy	0	psalm	Psalm 51:2|Psalm 51:3
451	liturgy	1	gospel	John 6:35-45
452	matins	0	psalm	Psalm 63:1
452	matins	1	gospel	Matthew 20:20-28
452	liturgy	0	psalm	Psalm 122:1-2
452	liturgy	1	gospel	Mark 12:18-27
453	matins	0	psalm	Psalm 32:10-11
453	matins	1	gospel	Luke 17:20-37
453	liturgy	0	psalm	Psalm 98:8|Psalm 98:9
453	liturgy	1	gospel	Luke 13:31-35
454	matins	0	psalm	Psalm 88:2-4
454	matins	1	gospel	Luke 18:35-43
454	liturgy	0	psalm	Psalm 129:8|Psalm 129:2
454	liturgy	1	gospel	John 11:1-45
455	vespers	0	psalm	Psalm 118:26-27
455	vespers	1	gospel	Jn 12:1-11
455	matins	0	psalm	Psalm 68:19|Psalm 68:35
455	matins	1	gospel	Lk 19:1-10
455	liturgy	0	psalm	Psalm 80:3|Psalm 80:1|Psalm 80:2
455	liturgy	1	gospel	Matthew 21:1-17|Mark 11:1-11|Luke 19:29-48
455	liturgy	2	psalm	Psalm 64:1,2
455	liturgy	3	gospel	John 12:12-19
462	matins	0	psalm	Psalm 78:65|Psalm 78:69
462	matins	1	gospel	Mk 16:2-11
462	liturgy	0	psalm	Psalm 118:24|Psalm 118:25|Psalm 118:27
462	liturgy	1	gospel	Jn 20:1-18
463	vespers	0	psalm	Psalm 96:10
463	vespers	1	gospel	Jn 20:19-23
463	matins	0	psalm	Psalm 97:1|Psalm 97:2
463	matins	1	gospel	Lk 24:1-12
463	liturgy	0	psalm	Psalm 104:24|Psalm 104:31
463	liturgy	1	gospel	Lk 24:13-35
464	vespers	0	psalm	Psalm 92:4,5
464	vespers	1	gospel	Jn 6:15-22
464	matins	0	psalm	Psalm 105:1-3
464	matins	1	gospel	Matt 28:16-20
464	liturgy	0	psalm	Psalm 105:3-5
464	liturgy	1	gospel	Mk 16:9-20
465	vespers	0	psalm	Psalm 30:5-7
465	vespers	1	gospel	Matt 9:15-17
465	matins	0	psalm	Psalm 105:43|Psalm 105:45
465	matins	1	gospel	Jn 1:9-14
465	liturgy	0	psalm	Psalm 106:1|Psalm 106:2
465	liturgy	1	gospel	Jn 2:12-25
466	vespers	0	psalm	Psalm 97:8,9
466	vespers	1	gospel	Mk 2:3-13
466	matins	0	psalm	Psalm 106:4|Psalm 106:5
466	matins	1	gospel	Lk 9:28-36
466	liturgy	0	psalm	Psalm 106:48
466	liturgy	1	gospel	Lk 7:11-17
467	vespers	0	psalm	Psalm 12:4,5
467	vespers	1	gospel	Lk 4:38-42
467	matins	0	psalm	Psalm 106:47
467	matins	1	gospel	Lk 20:27-39
467	liturgy	0	psalm	Psalm 107:1|Psalm 107:2
467	liturgy	1	gospel	Mk 16:2-8
468	vespers	0	psalm	Psalm 119:10,11
468	vespers	1	gospel	Jn 6:54-58
468	matins	0	psalm	Psalm 77:2
468	matins	1	gospel	Jn 20:19-23
468	liturgy	0	psalm	Psalm 119:73
468	liturgy	1	gospel	Lk 9:28-35
469	vespers	0	psalm	Psalm 33:3,4
469	vespers	1	gospel	Lk 5:1-11
469	matins	0	psalm	Psalm 96:1|Psalm 96:2
469	matins	1	gospel	Jn 21:1-14
469	liturgy	0	psalm	Psalm 98:1|Psalm 98:4
469	liturgy	1	gospel	Jn 20:19-31
470	vespers	0	psalm	Psalm 27:13-14
470	vespers	1	gospel	Matt 14:23-33
470	matins	0	psalm	Psalm 112:4|Psalm 112:6|Psalm 112:7
470	matins	1	gospel	Matt 8:23-27
470	liturgy	0	psalm	Psalm 70:5
470	liturgy	1	gospel	Jn 3:31-36
471	vespers	0	psalm	Psalm 9:19
471	vespers	1	gospel	Matt 17:19-23
471	matins	0	psalm	Psalm 7:6|Psalm 7:8
471	matins	1	gospel	Matt 9:27-31
471	liturgy	0	psalm	Psalm 7:6-8
471	liturgy	1	gospel	Jn 5:22-24
472	vespers	0	psalm	Psalm 41:1,2
472	vespers	1	gospel	Matt 9:36-38
472	matins	0	psalm	Psalm 63:1|Psalm 63:2
472	matins	1	gospel	Matt 9:32-35
472	liturgy	0	psalm	Psalm 9:1|Psalm 9:2
472	liturgy	1	gospel	Jn 5:31-37
473	vespers	0	psalm	Psalm 90:14
473	vespers	1	gospel	Matt 11:11-15
473	matins	0	psalm	Psalm 5:3|Psalm 5:4
473	matins	1	gospel	Matt 11:2-6
473	liturgy	0	psalm	Psalm 8:4|Psalm 8:5
473	liturgy	1	gospel	Jn 5:39-47
474	vespers	0	psalm	Psalm 16:9
474	vespers	1	gospel	Matt 17:14-18
474	matins	0	psalm	Psalm 16:10-11
474	matins	1	gospel	Matt 16:21-23
474	liturgy	0	psalm	Psalm 9:10-11
474	liturgy	1	gospel	Jn 6:54-58
475	vespers	0	psalm	Psalm 42:8,11
475	vespers	1	gospel	Lk 18:35-43
475	matins	0	psalm	Psalm 111:1|Psalm 111:2
475	matins	1	gospel	Jn 5:37-47
475	liturgy	0	psalm	Psalm 107:20|Psalm 107:22
475	liturgy	1	gospel	Jn 6:1-14
476	vespers	0	psalm	Psalm 111:1,2
476	vespers	1	gospel	Jn 6:16-23
476	matins	0	psalm	Psalm 111:3-4
476	matins	1	gospel	Jn 6:24-33
476	liturgy	0	psalm	Psalm 111:9-10
476	liturgy	1	gospel	Jn 6:35-45
477	vespers	0	psalm	Psalm 96:5,6
477	vespers	1	gospel	Matt 18:1-5
477	matins	0	psalm	Psalm 19:1|Psalm 19:2
477	matins	1	gospel	Matt 17:10-13
477	liturgy	0	psalm	Psalm 7:1|Psalm 7:17
477	liturgy	1	gospel	Jn 7:39-42
478	vespers	0	psalm	Psalm 56:6
478	vespers	1	gospel	Matt 18:6-7
478	matins	0	psalm	Psalm 57:1|Psalm 57:5
478	matins	1	gospel	Matt 17:20-23
478	liturgy	0	psalm	Psalm 7:10|Psalm 7:11
478	liturgy	1	gospel	Jn 8:12-16
479	vespers	0	psalm	Psalm 44:23|Psalm 44:26
479	vespers	1	gospel	Matt 20:29-33
479	matins	0	psalm	Psalm 57:8|Psalm 57:9|Psalm 57:10
479	matins	1	gospel	Matt 20:17-19
479	liturgy	0	psalm	Psalm 18:46|Psalm 18:49
479	liturgy	1	gospel	Jn 8:23-26
480	vespers	0	psalm	Psalm 100:1-4
480	vespers	1	gospel	Matt 13:53-58
480	matins	0	psalm	Psalm 101:8
480	matins	1	gospel	Matt 22:34-40
480	liturgy	0	psalm	Psalm 33:20-21
480	liturgy	1	gospel	Jn 8:28-30
481	vespers	0	psalm	Psalm 146:7,8
481	vespers	1	gospel	Matt 11:20-24
481	matins	0	psalm	Psalm 146:1|Psalm 146:2|Psalm 146:5
481	matins	1	gospel	Matt 22:41-46
481	liturgy	0	psalm	Psalm 86:12|Psalm 86:10
481	liturgy	1	gospel	Jn 8:31-39
482	vespers	0	psalm	Psalm 32:8
482	vespers	1	gospel	Matt 15:29-31
482	matins	0	psalm	Psalm 106:1|Psalm 106:2
482	matins	1	gospel	Jn 7:10-13
482	liturgy	0	psalm	Psalm 20:5|Psalm 20:6
482	liturgy	1	gospel	Jn 6:47-56
483	vespers	0	psalm	Psalm 116:1,2
483	vespers	1	gospel	Jn 8:12-20
483	matins	0	psalm	Psalm 116:4-6
483	matins	1	gospel	Jn 8:21-30
483	liturgy	0	psalm	Psalm 115:12-13
483	liturgy	1	gospel	Jn 4:1-42
484	vespers	0	psalm	Psalm 42:5
484	vespers	1	gospel	Mk 16:17-20
484	matins	0	psalm	Psalm 43:3
484	matins	1	gospel	Mk 4:30-34
484	liturgy	0	psalm	Psalm 119:105|Psalm 119:135
484	liturgy	1	gospel	Jn 8:39-42
485	vespers	0	psalm	Psalm 66:1,2
485	vespers	1	gospel	Mk 4:35-41
485	matins	0	psalm	Psalm 67:5|Psalm 67:6
485	matins	1	gospel	Mk 1:40-44
485	liturgy	0	psalm	Psalm 54:1|Psalm 54:2
485	liturgy	1	gospel	Jn 8:51-55
486	vespers	0	psalm	Psalm 119:49,50
486	vespers	1	gospel	Mk 6:47-52
486	matins	0	psalm	Psalm 119:33|Psalm 119:34
486	matins	1	gospel	Mk 3:31-35
486	liturgy	0	psalm	Psalm 74:12|Psalm 74:13|Psalm 74:22|Psalm 74:23
486	liturgy	1	gospel	Jn 7:14-29
487	vespers	0	psalm	Psalm 127:3
487	vespers	1	gospel	Mk 7:1-4
487	matins	0	psalm	Psalm 97:7|Psalm 97:8
487	matins	1	gospel	Mk 4:21-25
487	liturgy	0	psalm	Psalm 66:1|Psalm 66:6
487	liturgy	1	gospel	Jn 8:54-59
488	vespers	0	psalm	Psalm 70:1,2
488	vespers	1	gospel	Mk 8:10-15
488	matins	0	psalm	Psalm 70:1|Psalm 70:5
488	matins	1	gospel	Mk 4:26-29
488	liturgy	0	psalm	Psalm 24:1|Psalm 24:4
488	liturgy	1	gospel	Jn 10:34-38
489	vespers	0	psalm	Psalm 129:1,2
489	vespers	1	gospel	Lk 11:17-23
489	matins	0	psalm	Psalm 146:10
489	matins	1	gospel	Jn 7:31-36
489	liturgy	0	psalm	Psalm 15:4
489	liturgy	1	gospel	Jn 7:14-24
490	vespers	0	psalm	Psalm 117:1-2
490	vespers	1	gospel	Jn 6:57-69
490	matins	0	psalm	Psalm 118:28|Psalm 118:21
490	matins	1	gospel	Jn 8:51-59
490	liturgy	0	psalm	Psalm 118:14-15
490	liturgy	1	gospel	Jn 12:35-50
491	vespers	0	psalm	Psalm 42:5
491	vespers	1	gospel	Mk 5:21-43
491	matins	0	psalm	Psalm 118:16|Psalm 118:17
491	matins	1	gospel	Mk 4:30-34
491	liturgy	0	psalm	Psalm 70:5
491	liturgy	1	gospel	Jn 3:25-30
492	vespers	0	psalm	Psalm 19:2,4
492	vespers	1	gospel	Mk 12:35-40
492	matins	0	psalm	Psalm 118:24-25
492	matins	1	gospel	Mk 12:28-34
492	liturgy	0	psalm	Psalm 118:8-9
492	liturgy	1	gospel	Jn 13:16-20
493	vespers	0	psalm	Psalm 18:46-47
493	vespers	1	gospel	Jn 6:70—|Jn 7:1-1
493	matins	0	psalm	Psalm 118:26-27
493	matins	1	gospel	Mk 7:5-8
493	liturgy	0	psalm	Psalm 39:12
493	liturgy	1	gospel	Jn 17:18-21
494	vespers	0	psalm	Psalm 118:8-9
494	vespers	1	gospel	Lk 14:7-11
494	matins	0	psalm	Psalm 118:28|Psalm 118:21
494	matins	1	gospel	Lk 14:12-15
494	liturgy	0	psalm	Psalm 119:145-146
494	liturgy	1	gospel	Jn 17:22-26
495	vespers	0	psalm	Psalm 135:19-20
495	vespers	1	gospel	Lk 14:1-6
495	matins	0	psalm	Psalm 36:5|Psalm 36:6
495	matins	1	gospel	Jn 7:37-46
495	liturgy	0	psalm	Psalm 135:3|Psalm 135:5
495	liturgy	1	gospel	Jn 14:1-11
496	vespers	0	psalm	Psalm 135:6|Psalm 135:21
496	vespers	1	gospel	Jn 14:21-25
496	matins	0	psalm	Psalm 135:19-20
496	matins	1	gospel	Jn 15:4-8
496	liturgy	0	psalm	Psalm 136:1|Psalm 136:2
496	liturgy	1	gospel	Jn 14:1-11
497	vespers	0	psalm	Psalm 47:1
497	vespers	1	gospel	Mk 6:30-34
497	matins	0	psalm	Psalm 47:6|Psalm 47:7
497	matins	1	gospel	Mk 8:22-26
497	liturgy	0	psalm	Psalm 28:9|Psalm 28:8
497	liturgy	1	gospel	Jn 16:15-23
498	vespers	0	psalm	Psalm 47:4,5
498	vespers	1	gospel	Mk 9:14-29
498	matins	0	psalm	Psalm 47:3|Psalm 47:4
498	matins	1	gospel	Mk 9:30-32
498	liturgy	0	psalm	Psalm 116:1|Psalm 116:2
498	liturgy	1	gospel	Jn 16:23-33
499	vespers	0	psalm	Psalm 23:5
499	vespers	1	gospel	Mk 9:33-37
499	matins	0	psalm	Psalm 23:1-3
499	matins	1	gospel	Mk 9:38-42
499	liturgy	0	psalm	Psalm 40:13|Psalm 40:17
499	liturgy	1	gospel	Jn 17:1-9
500	vespers	0	psalm	Psalm 68:32-34
500	vespers	1	gospel	Lk 9:51-62
500	matins	0	psalm	Psalm 68:18-19
500	matins	1	gospel	Mk 16:12-20
500	liturgy	0	psalm	Psalm 24:9|Psalm 24:10
500	liturgy	1	gospel	Lk 24:36-53
501	vespers	0	psalm	Psalm 98:1,2
501	vespers	1	gospel	Mk 8:34—|Mk 9:1-1
501	matins	0	psalm	Psalm 110:1|Psalm 110:2
501	matins	1	gospel	Mk 9:2-7
501	liturgy	0	psalm	Psalm 69:32|Psalm 69:33|Psalm 69:30
501	liturgy	1	gospel	Jn 14:26-31
502	vespers	0	psalm	Psalm 51:10
502	vespers	1	gospel	Lk 11:53—|Lk 12:1-3
502	matins	0	psalm	Psalm 112:4
502	matins	1	gospel	Lk 10:21-24
502	liturgy	0	psalm	Psalm 136:1|Psalm 136:2
502	liturgy	1	gospel	Jn 16:15-23
503	vespers	0	psalm	Psalm 145:1,2,10
503	vespers	1	gospel	Mk 12:28-37
503	matins	0	psalm	Psalm 147:1|Psalm 147:2
503	matins	1	gospel	Jn 14:8-14
503	liturgy	0	psalm	Psalm 147:12|Psalm 147:18
503	liturgy	1	gospel	Jn 16:23-33
504	vespers	0	psalm	Psalm 22:2
504	vespers	1	gospel	Lk 4:38-41
504	matins	0	psalm	Psalm 119:164|Psalm 119:165
504	matins	1	gospel	Lk 4:42—|Lk 5:1-3
504	liturgy	0	psalm	Psalm 81:8|Psalm 81:6
504	liturgy	1	gospel	Jn 15:1-8
505	vespers	0	psalm	Psalm 48:1
505	vespers	1	gospel	Mk 9:14-29
505	matins	0	psalm	Psalm 138:1
505	matins	1	gospel	Lk 6:12-16
505	liturgy	0	psalm	Psalm 13:6|Psalm 13:5
505	liturgy	1	gospel	Jn 15:9-15
506	vespers	0	psalm	Psalm 119:130
506	vespers	1	gospel	Lk 7:18-23
506	matins	0	psalm	Psalm 12:6
506	matins	1	gospel	Lk 7:24-28
506	liturgy	0	psalm	Psalm 89:52|Psalm 89:49
506	liturgy	1	gospel	Jn 15:12-16
507	vespers	0	psalm	Psalm 132:4-5
507	vespers	1	gospel	Lk 8:22-25
507	matins	0	psalm	Psalm 91:13|Psalm 91:14
507	matins	1	gospel	Lk 8:1-3
507	liturgy	0	psalm	Psalm 31:16-17
507	liturgy	1	gospel	Jn 15:17-25
508	vespers	0	psalm	Psalm 42:8
508	vespers	1	gospel	Lk 11:24-26
508	matins	0	psalm	Psalm 119:96|Psalm 119:87
508	matins	1	gospel	Lk 8:18-21
508	liturgy	0	psalm	Psalm 25:1-3
508	liturgy	1	gospel	Jn 7:37-39
509	vespers	0	psalm	Psalm 107:2,3
509	vespers	1	gospel	Lk 8:40-56
509	matins	0	psalm	Psalm 33:5|Psalm 33:6
509	matins	1	gospel	Jn 17:1-13
509	liturgy	0	psalm	Psalm 108:3|Psalm 108:4
509	liturgy	1	gospel	Jn 17:14-26
510	vespers	0	psalm	Psalm 51:12,14
510	vespers	1	gospel	Jn 7:37-44
510	matins	0	psalm	Psalm 104:30-31
510	matins	1	gospel	Jn 14:26—|Jn 15:1-4
510	liturgy	0	psalm	Psalm 47:5|Psalm 47:7
510	liturgy	1	gospel	Jn 15:26—|Jn 16:1-15
"""


def _parse_occasions(tsv):
    for line in tsv.splitlines():
        idx, season_group, title, category, major = line.split("\t")
        yield int(idx), season_group, title, (category or None), bool(int(major))


def _parse_readings(tsv):
    for line in tsv.splitlines():
        idx, service, seq, kind, refs = line.split("\t")
        yield int(idx), service, int(seq), kind, refs.split("|")


def seed_offline_db(
    output_db_path=DEFAULT_OUTPUT_DB,
    psalm_source="brenton",
    gospel_source="web",
    psalm_bible=None,
    gospel_bible=None,
    log=print,
):
    """Build `output_db_path` (see OFFLINE_SCHEMA) from this script's own
    hardcoded lectionary structure, with each reading's text looked up
    fresh from a real translation: Psalms from `psalm_bible` (built per
    `psalm_source`, one of PSALM_SOURCES, if not given directly), Gospels
    from `gospel_bible` (built per `gospel_source`, one of GOSPEL_SOURCES).
    See this module's docstring for why Psalms default to Brenton rather
    than UKJV. Returns the list of (occasion_id, service, seq, kind,
    reference, error) skipped because their reference didn't resolve."""
    psalm_bible = psalm_bible or _build_bible(psalm_source)
    gospel_bible = gospel_bible or _build_bible(gospel_source)
    # evangelion.psalm_numbering deliberately leaves verse numbers
    # unconverted (only the chapter shifts) -- fine for the vast majority
    # of psalms, but a reference into one of the two chapters Septuagint
    # numbering *splits* one Masoretic psalm across (MT 116 -> LXX 114/115;
    # MT 147 -> LXX 146/147) lands on a verse number that chapter of
    # Brenton was never going to have (the split chapter only carries the
    # verses on its own side of the split). Rather than silently dropping
    # a reading over that known, documented gap, fall back to plain UKJV
    # under the original Masoretic reference for just that reading -- it
    # still renders under the same LXX-converted label at render time
    # (draw_labeled_reading converts the *label* unconditionally), only the
    # body text underneath is UKJV instead of Brenton for these few.
    psalm_fallback_bible = _build_bible("ukjv") if psalm_source == "brenton" else None
    dst = sqlite3.connect(output_db_path)
    dst.executescript(OFFLINE_SCHEMA)
    dst.execute("DELETE FROM occasions")
    dst.execute("DELETE FROM readings")

    occasions = list(_parse_occasions(_OCCASIONS_TSV))
    for idx, season_group, title, category, major in occasions:
        dst.execute(
            "INSERT INTO occasions (id, season_group, title, category, major) VALUES (?,?,?,?,?)",
            (idx, season_group, title, category, int(major)),
        )
    dst.commit()
    log(f"[occasions] seeded {len(occasions)} entries.")

    skipped = []
    seeded_readings = 0
    for idx, service, seq, kind, segments in _parse_readings(_READINGS_TSV):
        reference = " & ".join(segments)
        if kind == "psalm":
            bible = psalm_bible
            # Brenton is LXX-numbered; UKJV is Masoretic, same as the
            # stored `reference` -- only actually convert when looking the
            # text up in a Septuagint-numbered source. See this module's
            # docstring.
            lookup_ref = (
                septuagint_ref(reference) if psalm_source == "brenton" else reference
            )
        else:
            bible = gospel_bible
            lookup_ref = reference
        try:
            text = bible.text_for_ref(lookup_ref)
            if not text:
                # A reference that resolves with no ValueError but also no
                # text: e.g. a single-verse Brenton Psalm reference landing
                # exactly on a title-only verse (see bible_source._parse_usfx
                # -- such a verse is deliberately "", not missing, so a
                # *range* including it elsewhere still reads fine, but a
                # reference naming *only* that one verse has nothing left
                # to join). Treat the same as a lookup failure -- fall
                # back/skip -- rather than silently seeding an empty
                # reading.
                raise ValueError(f"{lookup_ref} resolved to no text")
        except (KeyError, ValueError) as e:
            if kind == "psalm" and psalm_fallback_bible is not None:
                try:
                    text = psalm_fallback_bible.text_for_ref(reference)
                    if not text:
                        raise ValueError(f"{reference} resolved to no text")
                    log(
                        f"[fallback] occasion {idx} {service}#{seq} {kind} "
                        f"{reference!r}: Brenton lookup {lookup_ref!r} failed "
                        f"({e}); used UKJV instead"
                    )
                except KeyError, ValueError:
                    skipped.append((idx, service, seq, kind, reference, str(e)))
                    log(
                        f"[skip] occasion {idx} {service}#{seq} {kind} {reference!r}: {e}"
                    )
                    continue
            else:
                skipped.append((idx, service, seq, kind, reference, str(e)))
                log(f"[skip] occasion {idx} {service}#{seq} {kind} {reference!r}: {e}")
                continue
        dst.execute(
            "INSERT INTO readings (occasion_id, service, seq, kind, reference, text) "
            "VALUES (?,?,?,?,?,?)",
            (idx, service, seq, kind, reference, text),
        )
        seeded_readings += 1
    dst.commit()

    log(
        f"Done. occasions={len(occasions)} readings={seeded_readings} "
        f"skipped={len(skipped)} -> {output_db_path}"
    )
    return skipped


def load_offline_seasons(db_path=DEFAULT_OUTPUT_DB, every_day=False):
    """Build the {season -> occasions} structure evangelion.generate's
    occasion_pages()/season_divider()/toc_page() render, from the seeded
    database -- grouping consecutive occasions by season_group, in
    `occasions.id` order, into one divider per run.

    By default (`every_day` false) only occasions.major=1 rows come back
    (Sundays and Major/Minor Feasts); pass every_day=True for every day.

    Each service's reading rows (ordered by `seq`) are re-assembled into
    the {"psalm": entry, "gospel": entry_or_list} shape occasion_pages()
    expects: a leading psalm-kind row becomes the "psalm" entry, and
    everything after it becomes the "gospel" entry -- a list of dicts if
    a Gospel harmony had a Psalm verse interleaved partway through."""
    conn = sqlite3.connect(db_path)
    query = "SELECT id, season_group, title, category FROM occasions"
    if not every_day:
        query += " WHERE major = 1"
    occasion_rows = conn.execute(query + " ORDER BY id").fetchall()

    seasons = []
    for occasion_id, season_group, title, category in occasion_rows:
        services = {}
        for service in ("vespers", "matins", "liturgy"):
            rows = conn.execute(
                "SELECT kind, reference, text FROM readings "
                "WHERE occasion_id = ? AND service = ? ORDER BY seq",
                (occasion_id, service),
            ).fetchall()
            if not rows:
                continue
            svc = {}
            if rows[0][0] == "psalm":
                svc["psalm"] = {"ref": rows[0][1], "text": rows[0][2]}
                rest = rows[1:]
            else:
                rest = rows
            if rest:
                if len(rest) == 1:
                    svc["gospel"] = {"ref": rest[0][1], "text": rest[0][2]}
                else:
                    svc["gospel"] = [{"ref": r[1], "text": r[2]} for r in rest]
            services[service] = svc
        for service in ("vespers", "matins", "liturgy"):
            services.setdefault(service, {})

        occasion = {"title": title, "services": services}
        if category:
            occasion["category"] = category

        if seasons and seasons[-1]["name"] == season_group:
            seasons[-1]["occasions"].append(occasion)
        else:
            seasons.append({"name": season_group, "occasions": [occasion]})
    return seasons


def main():
    ap = argparse.ArgumentParser(
        description=(
            "Seed evangelion's lectionary database from this script's own "
            "hardcoded lectionary structure, with real translated text for "
            "each reading."
        )
    )
    ap.add_argument(
        "--output-db",
        default=DEFAULT_OUTPUT_DB,
        help="Where to write the seeded database (default: .cache/offline.sqlite3, "
        "the one `evangelion` itself builds from). For a one-off "
        "custom-sourced database, point this at another path under .cache/ "
        "(e.g. .cache/offline_web.sqlite3) -- fully reproducible, not meant "
        "to be committed.",
    )
    ap.add_argument("--psalm-source", choices=PSALM_SOURCES, default="brenton")
    ap.add_argument("--gospel-source", choices=GOSPEL_SOURCES, default="web")
    args = ap.parse_args()
    seed_offline_db(
        args.output_db, psalm_source=args.psalm_source, gospel_source=args.gospel_source
    )


if __name__ == "__main__":
    main()
