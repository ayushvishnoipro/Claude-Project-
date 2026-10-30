"""Unit tests for todo.manager.parse_task_id."""

import pytest

from todo.errors import InvalidIdError
from todo.manager import parse_task_id


@pytest.mark.parametrize(
    ("raw", "expected"), [("2", 2), (" 2 ", 2), ("007", 7), ("10", 10), ("\t3\n", 3)]
)
def test_parse_valid(raw: str, expected: int) -> None:
    """Valid ASCII digit strings parse, with trimming and leading zeros."""
    assert parse_task_id(raw) == expected


@pytest.mark.parametrize("raw", ["", "   ", "\t"])
def test_parse_empty(raw: str) -> None:
    """Empty or whitespace-only gives the empty message."""
    with pytest.raises(InvalidIdError) as info:
        parse_task_id(raw)
    assert str(info.value) == "Task ID cannot be empty."


@pytest.mark.parametrize("raw", ["0", "00", " 0 "])
def test_parse_zero(raw: str) -> None:
    """Zero gives the positive-number message."""
    with pytest.raises(InvalidIdError) as info:
        parse_task_id(raw)
    assert str(info.value) == "Task ID must be a positive number."


@pytest.mark.parametrize(
    "raw",
    [
        "+2",
        "-2",
        "2_0",
        "1.0",
        "1e3",
        "2 3",
        "abc",
        "٢",  # Arabic-Indic digit two
        "２",  # full-width digit two
        "²",  # superscript two
    ],
)
def test_parse_rejects_non_ascii_digit_text(raw: str) -> None:
    """Anything beyond ASCII digits gives the whole-number message with repr."""
    with pytest.raises(InvalidIdError) as info:
        parse_task_id(raw)
    assert str(info.value) == f"Task ID must be a whole number, got {raw!r}."


def test_parse_message_uses_trimmed_text() -> None:
    """The message shows the trimmed text."""
    with pytest.raises(InvalidIdError) as info:
        parse_task_id("  x  ")
    assert str(info.value) == "Task ID must be a whole number, got 'x'."


def test_parse_control_characters_escaped() -> None:
    """Control characters are shown escaped through repr."""
    with pytest.raises(InvalidIdError) as info:
        parse_task_id("a\x00b")
    assert str(info.value) == "Task ID must be a whole number, got 'a\\x00b'."


def test_parse_very_long_digit_string() -> None:
    """A huge digit string either parses or maps to the whole-number error."""
    raw = "1" * 10000
    try:
        result = parse_task_id(raw)
    except InvalidIdError as error:
        assert str(error) == f"Task ID must be a whole number, got {raw!r}."
    else:
        assert result >= 1
