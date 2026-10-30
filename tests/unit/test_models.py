"""Unit tests for todo.models."""

import dataclasses

import pytest

from todo.models import Task


def test_task_fields() -> None:
    """Fields hold the values given."""
    task = Task(id=1, description="Buy milk", completed=False)
    assert (task.id, task.description, task.completed) == (1, "Buy milk", False)


def test_task_is_immutable() -> None:
    """Assigning to a field raises."""
    task = Task(1, "x", False)
    with pytest.raises(dataclasses.FrozenInstanceError):
        task.completed = True  # type: ignore[misc]


def test_replace_returns_new_instance() -> None:
    """replace yields a new object and leaves the original unchanged."""
    task = Task(1, "x", False)
    updated = dataclasses.replace(task, completed=True)
    assert updated is not task
    assert updated.completed is True
    assert task.completed is False


def test_task_equality() -> None:
    """Tasks with equal fields are equal."""
    assert Task(1, "x", False) == Task(1, "x", False)
    assert Task(1, "x", False) != Task(2, "x", False)
