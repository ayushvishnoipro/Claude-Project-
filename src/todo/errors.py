"""Exception hierarchy for the to-do application."""


class TaskError(Exception):
    """Base class for expected, user-presentable task errors."""


class InvalidDescriptionError(TaskError):
    """Raised when a task description is empty or too long."""


class InvalidIdError(TaskError):
    """Raised when a task ID is malformed or out of range."""


class TaskNotFoundError(TaskError):
    """Raised when no task exists with the requested ID."""
