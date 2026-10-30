"""Unit tests for todo.manager.TaskManager."""

import random
from typing import Any

import pytest

from todo.errors import (
    InvalidDescriptionError,
    InvalidIdError,
    TaskNotFoundError,
)
from todo.manager import TaskManager
from todo.models import Task


@pytest.fixture
def manager() -> TaskManager:
    """A fresh manager."""
    return TaskManager()


def test_add_assigns_sequential_ids_and_pending(manager: TaskManager) -> None:
    """IDs start at 1 and tasks start pending."""
    first = manager.add("a")
    second = manager.add("b")
    assert first == Task(1, "a", False)
    assert second.id == 2


def test_add_trims_and_preserves_internal_whitespace(manager: TaskManager) -> None:
    """Only outer whitespace is trimmed."""
    assert manager.add("  a   b  ").description == "a   b"


def test_add_allows_duplicates(manager: TaskManager) -> None:
    """Duplicate descriptions are accepted."""
    manager.add("x")
    manager.add("x")
    assert len(manager.list_tasks()) == 2


def test_add_accepts_200_characters(manager: TaskManager) -> None:
    """200 code points is the maximum."""
    assert len(manager.add("a" * 200).description) == 200


def test_add_rejects_201_characters(manager: TaskManager) -> None:
    """201 code points is rejected with the exact message."""
    with pytest.raises(InvalidDescriptionError) as info:
        manager.add("a" * 201)
    assert str(info.value) == "Description cannot exceed 200 characters."


def test_add_length_counted_after_trim(manager: TaskManager) -> None:
    """Padding does not count toward the limit."""
    assert len(manager.add("  " + "a" * 200 + "  ").description) == 200


def test_add_counts_code_points(manager: TaskManager) -> None:
    """Astral characters count as one each."""
    assert manager.add("\U0001F600" * 200).id == 1
    with pytest.raises(InvalidDescriptionError):
        manager.add("\U0001F600" * 201)


@pytest.mark.parametrize("text", ["", "   ", "\t\n"])
def test_add_rejects_empty(manager: TaskManager, text: str) -> None:
    """Empty or whitespace-only is rejected with the exact message."""
    with pytest.raises(InvalidDescriptionError) as info:
        manager.add(text)
    assert str(info.value) == "Description cannot be empty."


def test_failed_add_does_not_consume_id(manager: TaskManager) -> None:
    """A rejected add leaves the counter untouched."""
    with pytest.raises(InvalidDescriptionError):
        manager.add("")
    assert manager.add("ok").id == 1


def test_list_empty(manager: TaskManager) -> None:
    """No tasks yields an empty list."""
    assert manager.list_tasks() == []


def test_list_sorted_by_id(manager: TaskManager) -> None:
    """Listing is in ID order even after completion replaces entries."""
    for name in "abc":
        manager.add(name)
    manager.complete(1)
    assert [task.id for task in manager.list_tasks()] == [1, 2, 3]


def test_complete_marks_completed(manager: TaskManager) -> None:
    """Completing returns the updated task and changed=True."""
    manager.add("a")
    task, changed = manager.complete(1)
    assert changed is True
    assert task.completed is True
    assert manager.list_tasks()[0].completed is True


def test_complete_twice_is_noop(manager: TaskManager) -> None:
    """Second completion reports changed=False."""
    manager.add("a")
    manager.complete(1)
    task, changed = manager.complete(1)
    assert changed is False
    assert task.completed is True


def test_delete_removes_and_returns(manager: TaskManager) -> None:
    """Delete returns the removed task."""
    manager.add("a")
    assert manager.delete(1) == Task(1, "a", False)
    assert manager.list_tasks() == []


def test_ids_not_reused_after_delete(manager: TaskManager) -> None:
    """The counter never goes back."""
    manager.add("a")
    manager.delete(1)
    assert manager.add("b").id == 2


@pytest.mark.parametrize("method", ["complete", "delete"])
@pytest.mark.parametrize("bad", [True, False, "1", 1.0, None])
def test_non_int_ids_rejected(manager: TaskManager, method: str, bad: Any) -> None:
    """Non-int and bool IDs raise the integer message."""
    manager.add("a")
    with pytest.raises(InvalidIdError) as info:
        getattr(manager, method)(bad)
    assert str(info.value) == "Task ID must be an integer."


@pytest.mark.parametrize("method", ["complete", "delete"])
@pytest.mark.parametrize("bad", [0, -1])
def test_non_positive_ids_rejected(manager: TaskManager, method: str, bad: int) -> None:
    """IDs below 1 raise the positive-number message."""
    with pytest.raises(InvalidIdError) as info:
        getattr(manager, method)(bad)
    assert str(info.value) == "Task ID must be a positive number."


@pytest.mark.parametrize("method", ["complete", "delete"])
def test_unknown_id_not_found(manager: TaskManager, method: str) -> None:
    """Never-existed ID raises TaskNotFoundError."""
    with pytest.raises(TaskNotFoundError) as info:
        getattr(manager, method)(5)
    assert str(info.value) == "Task 5 not found."


@pytest.mark.parametrize("method", ["complete", "delete"])
def test_deleted_id_not_found(manager: TaskManager, method: str) -> None:
    """Already-deleted ID raises TaskNotFoundError."""
    manager.add("a")
    manager.delete(1)
    with pytest.raises(TaskNotFoundError) as info:
        getattr(manager, method)(1)
    assert str(info.value) == "Task 1 not found."


def test_ids_unique_and_increasing_over_random_ops() -> None:
    """Property-style: IDs strictly increase across random add/delete."""
    rng = random.Random(1234)
    manager = TaskManager()
    issued = []
    for _ in range(300):
        if rng.random() < 0.6 or not manager.list_tasks():
            issued.append(manager.add("t").id)
        else:
            manager.delete(rng.choice(manager.list_tasks()).id)
    assert issued == sorted(set(issued))
