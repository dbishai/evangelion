"""Unit tests for evangelion.generate's pure helper functions -- no
rendering, no database, no network.
"""

from evangelion.generate import _capitalize_first


def test_capitalize_first_uppercases_a_lowercase_first_letter():
    assert _capitalize_first("and wine makes glad the heart of man") == (
        "And wine makes glad the heart of man"
    )


def test_capitalize_first_leaves_an_already_uppercase_letter_alone():
    assert _capitalize_first("Blessed is the man") == "Blessed is the man"


def test_capitalize_first_does_not_lowercase_the_rest_of_the_text():
    """Deliberately not str.capitalize() -- that would mangle "LORD" and
    other legitimate all-caps text elsewhere in the verse."""
    assert _capitalize_first("the LORD is my shepherd") == "The LORD is my shepherd"


def test_capitalize_first_skips_leading_punctuation_and_quotes():
    assert _capitalize_first("“and he said”") == "“And he said”"


def test_capitalize_first_skips_a_leading_verse_number():
    assert _capitalize_first("123 not a letter") == "123 Not a letter"


def test_capitalize_first_empty_string_unchanged():
    assert _capitalize_first("") == ""


def test_capitalize_first_no_alphabetic_characters_unchanged():
    assert _capitalize_first("123 456") == "123 456"
