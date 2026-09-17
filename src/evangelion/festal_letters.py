"""Excerpts from public letters that Patriarchs of Alexandria addressed to their
whole congregation, shown on each Coptic-month divider page in place of a
generic caption.

The "festal letter" was an annual custom of the Alexandrian Patriarchate:
each year the Patriarch of Alexandria wrote to the churches of Egypt announcing
the date of Easter and exhorting the fast and feast -- St. Athanasius's are
the best-preserved set, and make up most of the quotes here. St. Peter I's
Canonical Epistle is included too: framed as his own "Sermon on Penitence"
to the whole church on how to receive back those who had lapsed under the
Diocletian persecution, so it's public/congregational in the same way,
even though it isn't a Paschal announcement.

Not limited to Paschal announcements specifically -- any public letter a
Patriarch of Alexandria addressed to his whole congregation qualifies, festal
or not. St. Dionysius the Great's Easter Letters, for instance, are
included here for their eyewitness testimony of the Alexandrian church
enduring persecution and plague, not for any date they announce.

Deliberately excludes letters between bishops on points of doctrine (e.g.
St. Cyril's letters to Nestorius, however historically central) -- real and
well documented, but private correspondence addressed to a fellow
bishop, not to a congregation.

Text is the public-domain R. Payne-Smith translation of Athanasius's
Festal Letters (Nicene and Post-Nicene Fathers, Second Series, Vol. 4;
newadvent.org's own "About this page" credit on each individual letter --
not the volume's general editor, Archibald Robertson, who translated
other works in the same volume but not these) and the James Hawkins
translation of Peter (Ante-Nicene Fathers, Vol. 6), verified verbatim
against newadvent.org before use here -- every quote below is a single
continuous, unedited run of the source text (only bracketed words are the
translator's own, as printed); nothing here is paraphrased, invented, or
spliced together from non-adjacent sentences.

St. Alexander I's encyclical to all bishops is included too, in G.
Thompson's translation (fourthcentury.com, CC BY-NC-SA 4.0, itself adapted
from A.C. Zenos's public-domain NPNF2 rendering) -- used and attributed
here per that license. Checked and explicitly NOT used: fourthcentury.com's
Cyril of Alexandria Festal Letters, which -- unlike Alexander's page --
carry no open license and are adapted from Philip Amidon's 2009 Catholic
University of America Press translation, still under copyright.

St. Dionysius the Great's letters are Charles Lett Feltoe's 1904
translation, "St. Dionysius of Alexandria: Letters and Treatises"
(public domain; Project Gutenberg #36539), verified verbatim against the
Gutenberg HTML edition directly.

Letter 19's FORTY_DAYS quote even names the Coptic month itself -- "the
sixth day of Phamenoth" -- Phamenoth being the Greek-letter transliteration
of the same month this project calls by its Coptic-native name, Paremhotep.
"""

ATHANASIUS = "St. Athanasius, Patriarch of Alexandria"
PETER = "St. Peter I, Patriarch of Alexandria"
ALEXANDER = "St. Alexander I, Patriarch of Alexandria"
DIONYSIUS = "St. Dionysius the Great, Patriarch of Alexandria"

FASTING_OF_THE_SOUL = {
    "text": (
        "Behold, my brethren, how much a fast can do, and in what manner the "
        "law commands us to fast. It is required that not only with the body "
        "should we fast, but with the soul. Now the soul is humbled when it "
        "does not follow wicked opinions, but feeds on becoming virtues. For "
        "virtues and vices are the food of the soul, and it can eat either of "
        "these two meats, and incline to either of the two, according to its "
        "own will. If it is bent toward virtue, it will be nourished by "
        "virtues, by righteousness, by temperance, by meekness, by fortitude, "
        "as Paul says; ‘Being nourished by the word of truth.’ Such was the "
        "case with our Lord, who said, ‘My meat is to do the will of My "
        "Father which is in heaven.’"
    ),
    "author": ATHANASIUS,
    "source": "Festal Letter 1",
}
PASCHAL_NEW_FRUITS = {
    "text": (
        "Let us keep the Feast, not with old leaven, neither with the leaven "
        "of malice and wickedness; but with the unleavened bread of sincerity "
        "and truth. Putting off the old man and his deeds, let us put on the "
        "new man, which is created in God, in humbleness of mind, and a pure "
        "conscience; in meditation of the law by night and by day. And "
        "casting away all hypocrisy and fraud, putting far from us all pride "
        "and deceit, let us take upon us love towards God and towards our "
        "neighbour, that being new [creatures], and receiving the new wine, "
        "even the Holy Spirit, we may properly keep the feast, even the "
        "month of these new [fruits]."
    ),
    "author": ATHANASIUS,
    "source": "Festal Letter 1",
}
FEAST_TO_FEAST = {
    "text": (
        "It is well, my beloved, to proceed from feast to feast; again "
        "festal meetings, again holy vigils arouse our minds, and compel our "
        "intellect to keep vigil unto contemplation of good things. Let us "
        "not fulfil these days like those that mourn, but, by enjoying "
        "spiritual food, let us seek to silence our fleshly lusts. For by "
        "these means we shall have strength to overcome our adversaries, "
        "like blessed Judith, when having first exercised herself in "
        "fastings and prayers, she overcame the enemies, and killed "
        "Olophernes. And blessed Esther, when destruction was about to come "
        "on all her race, and the nation of Israel was ready to perish, "
        "defeated the fury of the tyrant by no other means than by fasting "
        "and prayer to God, and changed the ruin of her people into safety."
    ),
    "author": ATHANASIUS,
    "source": "Festal Letter 4",
}
HIMSELF_THE_FEAST = {
    "text": (
        "Let us hasten as to the Lord, Who is Himself the feast, not looking "
        "upon it as an indulgence and delight of the belly, but as a "
        "manifestation of virtue. For the feasts of the heathen are full of "
        "greediness, and utter indolence, since they consider they celebrate "
        "a feast when they are idle; and they work the works of perdition "
        "when they feast. But our feasts consist in the exercise of virtue "
        "and the practice of temperance; as the prophetic word testifies in "
        "a certain place, saying, ‘The fast of the fourth, and the fast of "
        "the fifth, and the fast of the seventh, and the fast of the tenth "
        "[month], shall be to the house of Judah for gladness, and "
        "rejoicing, and for pleasant feasts.’ Since therefore this occasion "
        "for exercise is set before us, and such a day as this has come, and "
        "the prophetic voice has gone forth that the feast shall be "
        "celebrated, let us give all diligence to this good proclamation, "
        "and like those who contend on the race course, let us vie with "
        "each other in observing the purity of the fast."
    ),
    "author": ATHANASIUS,
    "source": "Festal Letter 14",
}
FORTY_DAYS = {
    "text": (
        "We begin the fast of forty days on the sixth day of Phamenoth; and "
        "having passed through that properly, with fasting and prayers, we "
        "may be able to attain to the holy day. For he who neglects to "
        "observe the fast of forty days, as one who rashly and impurely "
        "treads on holy things, cannot celebrate the Easter festival. "
        "Further, let us put one another in remembrance, and stimulate one "
        "another not to be negligent, and especially that we should fast "
        "those days, so that fasts may receive us in succession, and we may "
        "rightly bring the feast to a close."
    ),
    "author": ATHANASIUS,
    "source": "Festal Letter 19",
}
PETER_FORTY_DAYS = {
    "text": (
        "But since the fourth passover of the persecution has arrived, it is "
        "sufficient, in the case of those who have been apprehended and "
        "thrown into prison, and who have sustained torments not to be "
        "borne, and stripes intolerable, and many other dreadful "
        "afflictions, and afterwards have been betrayed by the frailty of "
        "the flesh, even though they were not at the first received on "
        "account of their grievous fall that followed, yet because they "
        "contended sorely and resisted long; for they did not come to this "
        "of their own will, but were betrayed by the frailty of the flesh, "
        "for they show in their bodies the marks of Jesus, and some are "
        "now, for the third year, bewailing their fault: it is sufficient, "
        "I say, that from the time of their submissive approach, other "
        "forty days should be enjoined upon them, to keep them in "
        "remembrance of these things; those forty days during which, "
        "though our Lord and Saviour Jesus Christ had fasted, He was yet, "
        "after He had been baptized, tempted of the devil."
    ),
    "author": PETER,
    "source": "Canonical Epistle, Canon 1",
}
ONE_BODY = {
    "text": (
        "Since the catholic church is one body, and we are commanded in the "
        "divine Scriptures to maintain “the bond of unity and peace,” it "
        "follows that we should write, and mutually acquaint one another "
        "with the things that have happened among each of us, so that if "
        "one member suffers or rejoices, we may either sympathize or "
        "rejoice with one other."
    ),
    "author": ALEXANDER,
    "source": "Encyclical Letter to All Bishops",
}
HEAVENLY_JOY = {
    "text": (
        "Again, my brethren, is Easter come and gladness; again the Lord "
        "has brought us to this season; so that when, according to custom, "
        "we have been nourished with His words, we may duly keep the "
        "feast. Let us celebrate it then, even heavenly joy, with those "
        "saints who formerly proclaimed a like feast, and were ensamples "
        "to us of conversation in Christ."
    ),
    "author": ATHANASIUS,
    "source": "Festal Letter 2",
}
SAME_FEAST = {
    "text": (
        "I do not send word to you as though you were ignorant; but I "
        "publish it to those who know it, that you may perceive that "
        "although men have separated us, yet God having made us "
        "companions, we approach the same feast, and worship the same "
        "Lord continually."
    ),
    "author": ATHANASIUS,
    "source": "Festal Letter 3",
}
KEPT_THE_FEAST_IN_EXILE = {
    "text": (
        "First of all they drove us into exile and we kept the feast then "
        "too by ourselves, persecuted and harried to death by all, and "
        "every place where each particular affliction befel us became the "
        "scene of our festal assembly, open country, desert, ship, inn or "
        "prison, and our perfect martyrs spent the brightest of all "
        "feasts, being entertained in heaven above."
    ),
    "author": DIONYSIUS,
    "source": "Easter Letter to the Alexandrians",
}

# One quote per Coptic month, each matched to what actually falls in that
# month rather than rotated arbitrarily. The Fast of Nineveh, Great Lent,
# Holy Pascha, and the Pascha-to-Pentecost fifty days are dated by the
# Paschalion rather than the fixed Coptic calendar, so they carry their own
# Moveable Cycle season_group in the seeded data (see seed_offline_db.py)
# rather than sitting under whichever Coptic month they happen to fall in
# that year -- hence the four extra keys at the end, none of which need to
# dodge the Coptic-month quotes since the two kinds of divider never
# actually collide on the page:
#   Thout       -- Nayrouz, the Coptic New Year: Alexander's letter on the
#                  Church's unity as one body opens the year's cycle.
#   Paopi       -- an ordinary month; a general "keep the feast" exhortation.
#   Hathor      -- the Fast of the Nativity begins.
#   Koiak       -- the Nativity itself: Christ born is Himself the feast.
#   Tobi        -- three feasts in one month (Circumcision, Theophany, Cana).
#   Meshir      -- the Fast of Nineveh: Peter's own forty-day exhortation.
#   Paremhotep  -- an ordinary month now that Great Lent's own Sundays sit in
#                  the Moveable Cycle instead; usually just the Annunciation.
#   Parmouti    -- likewise, now that Holy Pascha does too.
#   Pashons     -- likewise, now that the Holy Fifty Days' Sundays do too:
#                  another "keep the feast" exhortation, distinct from
#                  Paopi's.
#   Paoni       -- Ascension and Pentecost itself now live in the Moveable
#                  Cycle too, but this month's own ordinary Sundays remain.
#   Apip        -- the Apostles' Fast concludes at the Feast of the
#                  Apostles: Dionysius's own eyewitness account of the
#                  Alexandrian church's endurance under persecution.
#   Mesori      -- the Fast of the Holy Theotokos.
#   Pi Kogi Enavot -- the year's last days: "we may rightly bring the feast to a close."
#   Fast of Nineveh -- the first Moveable Cycle divider of the year:
#                  Athanasius on Christians separated by persecution still
#                  keeping one and the same feast.
#   The Great Fast -- the Athanasian letter that names this fast's own
#                  traditional forty days.
#   Holy Pascha -- Palm Sunday through the Resurrection as one continuous
#                  observance: the Paschal "unleavened bread" letter.
#   Pentecost   -- "from feast to feast": the fifty days from the
#                  Resurrection to Pentecost itself, Ascension included.
MONTH_QUOTES = {
    "Thout": ONE_BODY,
    "Paopi": HIMSELF_THE_FEAST,
    "Hathor": FASTING_OF_THE_SOUL,
    "Koiak": HIMSELF_THE_FEAST,
    "Tobi": FEAST_TO_FEAST,
    "Meshir": PETER_FORTY_DAYS,
    "Paremhotep": FORTY_DAYS,
    "Parmouti": PASCHAL_NEW_FRUITS,
    "Pashons": HEAVENLY_JOY,
    "Paoni": FEAST_TO_FEAST,
    "Apip": KEPT_THE_FEAST_IN_EXILE,
    "Mesori": FASTING_OF_THE_SOUL,
    "Pi Kogi Enavot": FORTY_DAYS,
    "Fast of Nineveh": SAME_FEAST,
    "The Great Fast": FORTY_DAYS,
    "Holy Pascha": PASCHAL_NEW_FRUITS,
    "Pentecost": FEAST_TO_FEAST,
}


def festal_quote_for(season_name):
    """Return {"text", "author", "source"} for the given season-divider name
    -- a Coptic month, or one of the Moveable Cycle's own section/season
    names -- or None."""
    return MONTH_QUOTES.get(season_name)
