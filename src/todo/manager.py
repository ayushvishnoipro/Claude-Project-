"""Pure task-management logic (no I/O)."""

import dataclasses
from typing import Dict, List, Tuple

from todo.errors import (
    InvalidDescriptionError,
    InvalidIdError,
    TaskNotFoundError,
)
from todo.models import Task

MAX_DESCRIPTION_LENGTH = 200


def parse_task_id(raw: str) -> int:
    """Convert user-typed ID text to a positive int.

    Raises InvalidIdError if the text is not purely ASCII digits or is zero.
    """
    text = raw.strip()
    if not text:
        raise InvalidIdError("Task ID cannot be empty.")
    message = f"Task ID must be a whole number, got {text!r}."
    if not (text.isascii() and text.isdigit()):
        raise InvalidIdError(message)
    try:
        value = int(text)
    except ValueError:
        raise InvalidIdError(message) from None
    if value < 1:
        raise InvalidIdError("Task ID must be a positive number.")
    return value


class TaskManager:
    """In-memory task store with monotonic, never-reused IDs."""

    def __init__(self) -> None:
        self._tasks: Dict[int, Task] = {}
        self._next_id = 1

    def add(self, description: str) -> Task:
        """Trim, validate and store a new pending task."""
        trimmed = description.strip()
        if not trimmed:
            raise InvalidDescriptionError("Description cannot be empty.")
        if len(trimmed) > MAX_DESCRIPTION_LENGTH:
            raise InvalidDescriptionError(
                f"Description cannot exceed {MAX_DESCRIPTION_LENGTH} characters."
            )
        task = Task(id=self._next_id, description=trimmed, completed=False)
        self._tasks[task.id] = task
        self._next_id += 1
        return task

    def list_tasks(self) -> List[Task]:
        """Return all tasks sorted by ID."""
        return [self._tasks[key] for key in sorted(self._tasks)]

    def complete(self, task_id: int) -> Tuple[Task, bool]:
        """Mark a task completed; return (task, changed)."""
        task = self._lookup(task_id)
        if task.completed:
            return task, False
        updated = dataclasses.replace(task, completed=True)
        self._tasks[task_id] = updated
        return updated, True

    def delete(self, task_id: int) -> Task:
        """Remove and return a task. IDs are never reused."""
        task = self._lookup(task_id)
        del self._tasks[task_id]
        return task

    def _lookup(self, task_id: int) -> Task:
        """Validate an ID and return the matching task."""
        if not isinstance(task_id, int) or isinstance(task_id, bool):
            raise InvalidIdError("Task ID must be an integer.")
        if task_id < 1:
            raise InvalidIdError("Task ID must be a positive number.")
        task = self._tasks.get(task_id)
        if task is None:
            raise TaskNotFoundError(f"Task {task_id} not found.")
        return task
