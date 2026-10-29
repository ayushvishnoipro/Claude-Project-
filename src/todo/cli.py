"""Command-line interface: parsing, dispatch and output formatting."""

from typing import Callable, List, Tuple

from todo.errors import TaskError
from todo.manager import TaskManager, parse_task_id
from todo.models import Task

InputFn = Callable[[str], str]
OutputFn = Callable[[str], None]

MAIN_PROMPT = "> "
DESCRIPTION_PROMPT = "Description: "
ID_PROMPT = "Task ID: "
QUIT_COMMANDS = ("quit", "q", "exit")

HELP_TEXT = "\n".join(
    [
        "Commands:",
        "  add [description]   Add a new task",
        "  list                Show all tasks",
        "  complete [id]       Mark a task as completed",
        "  delete [id]         Delete a task",
        "  help                Show this help",
        "  quit                Exit (aliases: q, exit)",
        "On Windows, end-of-input is Ctrl+Z then Enter.",
    ]
)


def format_tasks(tasks: List[Task]) -> str:
    """Format tasks one per line, or 'No tasks.' when empty."""
    if not tasks:
        return "No tasks."
    return "\n".join(
        f"{task.id}. [{'x' if task.completed else ' '}] {task.description}"
        for task in tasks
    )


def _argument(rest: str, prompt: str, input_fn: InputFn) -> str:
    """Return the inline argument, prompting for it when missing."""
    return rest if rest else input_fn(prompt)


def _handle_add(manager: TaskManager, rest: str, input_fn: InputFn) -> str:
    task = manager.add(_argument(rest, DESCRIPTION_PROMPT, input_fn))
    return f"Added task {task.id}: {task.description}"


def _handle_complete(manager: TaskManager, rest: str, input_fn: InputFn) -> str:
    task_id = parse_task_id(_argument(rest, ID_PROMPT, input_fn))
    task, changed = manager.complete(task_id)
    if changed:
        return f"Completed task {task.id}."
    return f"Task {task.id} is already completed."


def _handle_delete(manager: TaskManager, rest: str, input_fn: InputFn) -> str:
    task_id = parse_task_id(_argument(rest, ID_PROMPT, input_fn))
    task = manager.delete(task_id)
    return f"Deleted task {task.id}."


def _dispatch(
    manager: TaskManager, token: str, rest: str, input_fn: InputFn
) -> str:
    """Execute one command and return its output text."""
    command = token.lower()
    if command == "add":
        return _handle_add(manager, rest, input_fn)
    if command == "list":
        return format_tasks(manager.list_tasks())
    if command == "complete":
        return _handle_complete(manager, rest, input_fn)
    if command == "delete":
        return _handle_delete(manager, rest, input_fn)
    if command == "help":
        return HELP_TEXT
    return f"Error: Unknown command {token!r}. Type 'help' for a list of commands."


def _split(line: str) -> Tuple[str, str]:
    """Split a stripped line once at the first whitespace run."""
    parts = line.split(None, 1)
    return parts[0], parts[1] if len(parts) > 1 else ""


def run(input_fn: InputFn, output_fn: OutputFn) -> int:
    """Run the interactive loop; return the process exit code (always 0)."""
    manager = TaskManager()
    try:
        while True:
            line = input_fn(MAIN_PROMPT).strip()
            if not line:
                continue
            token, rest = _split(line)
            if token.lower() in QUIT_COMMANDS:
                output_fn("Goodbye!")
                return 0
            try:
                output_fn(_dispatch(manager, token, rest, input_fn))
            except TaskError as error:
                output_fn(f"Error: {error}")
    except (KeyboardInterrupt, EOFError):
        output_fn("\nGoodbye!")
        return 0
