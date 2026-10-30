"""Data model for the to-do application."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Task:
    """An immutable task."""

    id: int
    description: str
    completed: bool
