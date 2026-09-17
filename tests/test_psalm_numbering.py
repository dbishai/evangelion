"""Unit tests for evangelion.psalm_numbering's Masoretic<->Septuagint Psalm
chapter conversion table -- pure functions, every boundary of the
documented MT<->LXX concordance table exercised directly, independent of
any translation source or rendered book.
"""

from evangelion.psalm_numbering import masoretic_ref, septuagint_ref

# --------------------------------------------------------------------------
# septuagint_ref (MT -> LXX)
# --------------------------------------------------------------------------


def test_septuagint_ref_unchanged_range_low_and_high_bounds():
    assert septuagint_ref("Psalm 1:1") == "Psalm 1:1"
    assert septuagint_ref("Psalm 8:5") == "Psalm 8:5"


def test_septuagint_ref_mt_9_and_10_merge_to_lxx_9():
    assert septuagint_ref("Psalm 9:1") == "Psalm 9:1"
    assert septuagint_ref("Psalm 10:1") == "Psalm 9:1"


def test_septuagint_ref_main_shift_range_bounds():
    assert septuagint_ref("Psalm 11:1") == "Psalm 10:1"
    assert septuagint_ref("Psalm 113:1") == "Psalm 112:1"


def test_septuagint_ref_mt_114_and_115_merge_to_lxx_113():
    assert septuagint_ref("Psalm 114:1") == "Psalm 113:1"
    assert septuagint_ref("Psalm 115:1") == "Psalm 113:1"


def test_septuagint_ref_mt_116_splits_at_verse_nine_ten():
    assert septuagint_ref("Psalm 116:9") == "Psalm 114:9"
    assert septuagint_ref("Psalm 116:10") == "Psalm 115:10"
    assert septuagint_ref("Psalm 116:1-9") == "Psalm 114:1-9"
    assert septuagint_ref("Psalm 116:10-19") == "Psalm 115:10-19"


def test_septuagint_ref_mt_116_with_no_verse_number_defaults_to_115():
    """_lxx_chapter's documented tie-break when a verse number can't be
    found in the citation at all."""
    assert septuagint_ref("Psalm 116:") == "Psalm 115:"


def test_septuagint_ref_second_shift_range_bounds():
    assert septuagint_ref("Psalm 117:1") == "Psalm 116:1"
    assert septuagint_ref("Psalm 146:1") == "Psalm 145:1"


def test_septuagint_ref_mt_147_splits_at_verse_eleven_twelve():
    assert septuagint_ref("Psalm 147:11") == "Psalm 146:11"
    assert septuagint_ref("Psalm 147:12") == "Psalm 147:12"


def test_septuagint_ref_final_unchanged_range():
    assert septuagint_ref("Psalm 148:1") == "Psalm 148:1"
    assert septuagint_ref("Psalm 150:6") == "Psalm 150:6"


def test_septuagint_ref_joins_multiple_segments_independently():
    assert septuagint_ref("Psalm 65:11 & Psalm 81:1") == "Psalm 64:11 & Psalm 80:1"


def test_septuagint_ref_segment_without_psalm_word_still_converts():
    """A bare "17:5" segment (no "Psalm" prefix) must still be recognized
    and converted."""
    assert septuagint_ref("Psalm 17:3 & 17:5") == "Psalm 16:3 & Psalm 16:5"


def test_septuagint_ref_unrecognized_segment_passes_through():
    assert septuagint_ref("not a psalm reference") == "not a psalm reference"


def test_septuagint_ref_empty_string_unchanged():
    assert septuagint_ref("") == ""


def test_septuagint_ref_none_unchanged():
    assert septuagint_ref(None) is None


# --------------------------------------------------------------------------
# masoretic_ref (LXX -> MT)
# --------------------------------------------------------------------------


def test_masoretic_ref_unchanged_range():
    assert masoretic_ref("Psalm 1:1") == "Psalm 1:1"
    assert masoretic_ref("Psalm 8:5") == "Psalm 8:5"


def test_masoretic_ref_lxx_9_picks_lower_of_merged_pair():
    assert masoretic_ref("Psalm 9:1") == "Psalm 9:1"


def test_masoretic_ref_main_shift_range_bounds():
    assert masoretic_ref("Psalm 10:1") == "Psalm 11:1"
    assert masoretic_ref("Psalm 112:1") == "Psalm 113:1"


def test_masoretic_ref_lxx_113_picks_lower_of_merged_pair():
    assert masoretic_ref("Psalm 113:1") == "Psalm 114:1"


def test_masoretic_ref_lxx_114_and_115_both_map_to_mt_116():
    assert masoretic_ref("Psalm 114:9") == "Psalm 116:9"
    assert masoretic_ref("Psalm 115:10") == "Psalm 116:10"


def test_masoretic_ref_second_shift_range_bounds():
    assert masoretic_ref("Psalm 116:1") == "Psalm 117:1"
    assert masoretic_ref("Psalm 145:1") == "Psalm 146:1"


def test_masoretic_ref_lxx_146_and_147_both_map_to_mt_147():
    assert masoretic_ref("Psalm 146:11") == "Psalm 147:11"
    assert masoretic_ref("Psalm 147:12") == "Psalm 147:12"


def test_masoretic_ref_final_unchanged_range():
    assert masoretic_ref("Psalm 148:1") == "Psalm 148:1"
    assert masoretic_ref("Psalm 150:6") == "Psalm 150:6"


def test_masoretic_ref_joins_multiple_segments_independently():
    assert masoretic_ref("Psalm 64:11 & Psalm 80:1") == "Psalm 65:11 & Psalm 81:1"


def test_masoretic_ref_unrecognized_segment_passes_through():
    assert masoretic_ref("not a psalm reference") == "not a psalm reference"


def test_masoretic_ref_empty_string_unchanged():
    assert masoretic_ref("") == ""


# --------------------------------------------------------------------------
# round-tripping
# --------------------------------------------------------------------------


def test_round_trip_is_lossless_outside_the_two_ambiguous_merge_chapters():
    for chapter in (1, 5, 8, 50, 100, 148, 150):
        ref = f"Psalm {chapter}:3"
        assert masoretic_ref(septuagint_ref(ref)) == ref


def test_round_trip_is_lossy_exactly_where_documented():
    """MT 10 and MT 115 both merge into a lower-numbered LXX chapter
    shared with another MT psalm (9 and 114 respectively) -- inverting
    that LXX chapter can only guess, and per _mt_chapter's own docstring
    it picks the lower half every time. This is expected, documented
    behavior, not a bug -- asserting it here so a future change to that
    tie-break is a deliberate, visible one."""
    assert septuagint_ref("Psalm 10:1") == "Psalm 9:1"
    assert masoretic_ref("Psalm 9:1") == "Psalm 9:1"  # not 10

    assert septuagint_ref("Psalm 115:1") == "Psalm 113:1"
    assert masoretic_ref("Psalm 113:1") == "Psalm 114:1"  # not 115


def test_round_trip_split_chapters_recover_the_original_mt_chapter():
    """Unlike the merge chapters, the two MT psalms that *split* across two
    LXX chapters (116 -> 114/115; 147 -> 146/147) invert unambiguously --
    both LXX halves map back to the same one MT chapter."""
    assert masoretic_ref(septuagint_ref("Psalm 116:9")) == "Psalm 116:9"
    assert masoretic_ref(septuagint_ref("Psalm 116:10")) == "Psalm 116:10"
    assert masoretic_ref(septuagint_ref("Psalm 147:11")) == "Psalm 147:11"
    assert masoretic_ref(septuagint_ref("Psalm 147:12")) == "Psalm 147:12"
