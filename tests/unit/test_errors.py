"""Unit tests for todo.errors."""

import pytest

from todo.errors import (
    InvalidDescriptionError,
    InvalidIdError,
    TaskError,
    TaskNotFoundError,
)


@pytest.mark.parametrize(
    "error_class", [InvalidDescriptionError, InvalidIdError, TaskNotFoundError]
)
def test_subclasses_derive_from_task_error(error_class: type) -> None:
    """Every specific error is a TaskError."""
    assert issubclass(error_class, TaskError)


def test_task_error_derives_from_exception() -> None:
    """TaskError is a normal Exception."""
    assert issubclass(TaskError, Exception)


def test_error_carries_message() -> None:
    """The message is available via str()."""
    assert str(InvalidIdError("boom")) == "boom"


def test_specific_error_caught_as_base() -> None:
    """Catching TaskError catches subclasses."""
    with pytest.raises(TaskError):
        raise TaskNotFoundError("Task 1 not found.")
