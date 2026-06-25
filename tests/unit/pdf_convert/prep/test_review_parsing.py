from __future__ import annotations

import pytest

from gm_kit.pdf_convert.prep.handlers import parse_skip_ranges_input


def test_parse_skip_ranges_input__should_return_empty_list__when_input_is_empty() -> None:
    assert parse_skip_ranges_input("", page_count=12) == []


def test_parse_skip_ranges_input__should_return_empty_list__when_input_contains_only_whitespace() -> None:
    assert parse_skip_ranges_input("   ", page_count=12) == []


def test_parse_skip_ranges_input__should_return_sorted_unique_pages__when_input_contains_numbers_and_ranges() -> None:
    assert parse_skip_ranges_input(" 5, 2, 7-9, 8, 2 ", page_count=12) == [2, 5, 7, 8, 9]


def test_parse_skip_ranges_input__should_trim_whitespace_around_ranges__when_input_is_spaced() -> None:
    assert parse_skip_ranges_input("1 - 3, 5", page_count=12) == [1, 2, 3, 5]


@pytest.mark.parametrize(
    ("raw_input", "expected_message"),
    [
        (",", "Invalid skip range token: ''"),
        ("1,,2", "Invalid skip range token: ''"),
        ("1,  ,2", "Invalid skip range token: ''"),
        ("3-", "Invalid skip range token: '3-'"),
        ("a", "Invalid skip range token: 'a'"),
        ("9-4", "Skip range start must be less than or equal to end: '9-4'"),
        ("13", "Skip page 13 is outside document bounds 1-12"),
        ("10-13", "Skip page 13 is outside document bounds 1-12"),
        ("0", "Skip page 0 is outside document bounds 1-12"),
    ],
)
def test_parse_skip_ranges_input__should_raise_value_error__when_input_is_invalid(
    raw_input: str,
    expected_message: str,
) -> None:
    with pytest.raises(ValueError) as error:
        parse_skip_ranges_input(raw_input, page_count=12)

    assert str(error.value) == expected_message
