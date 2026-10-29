"""Integration tests driving todo.cli.run with scripted input."""

from typing import Iterator, List, Tuple, Union

from todo.cli import run

Step = Union[str, BaseException]


def run_session(steps: List[Step]) -> Tuple[List[str], int]:
    """Run the CLI; BaseException steps are raised by the fake input."""
    feed: Iterator[Step] = iter(steps)
    outputs: List[str] = []

    def fake_input(prompt: str) -> str:
        step = next(feed)
        if isinstance(step, BaseException):
            raise step
        return step

    code = run(fake_input, outputs.append)
    return outputs, code


def test_full_session() -> None:
    """Add, list, complete, delete, list, quit."""
    outputs, code = run_session(
        [
            "add Buy milk",
            "add Walk dog",
            "list",
            "complete 2",
            "list",
            "delete 1",
            "list",
            "quit",
        ]
    )
    assert outputs == [
        "Added task 1: Buy milk",
        "Added task 2: Walk dog",
        "1. [ ] Buy milk\n2. [ ] Walk dog",
        "Completed task 2.",
        "1. [ ] Buy milk\n2. [x] Walk dog",
        "Deleted task 1.",
        "2. [x] Walk dog",
        "Goodbye!",
    ]
    assert code == 0


def test_errors_do_not_end_session() -> None:
    """Loop continues after every kind of error."""
    outputs, code = run_session(
        ["add  ", "", "complete x", "delete 9", "bogus", "add ok", "quit"]
    )
    assert outputs == [
        "Error: Description cannot be empty.",
        "Error: Task ID must be a whole number, got 'x'.",
        "Error: Task 9 not found.",
        "Error: Unknown command 'bogus'. Type 'help' for a list of commands.",
        "Added task 1: ok",
        "Goodbye!",
    ]
    assert code == 0


def test_argument_prompt_empty_path() -> None:
    """Empty answer at the ID prompt errors, then main prompt resumes."""
    outputs, code = run_session(["complete", "  ", "list", "quit"])
    assert outputs == [
        "Error: Task ID cannot be empty.",
        "No tasks.",
        "Goodbye!",
    ]
    assert code == 0


def test_eof_at_main_prompt() -> None:
    """EOF at the main prompt exits 0 with newline-Goodbye."""
    outputs, code = run_session([EOFError()])
    assert outputs == ["\nGoodbye!"]
    assert code == 0


def test_interrupt_at_main_prompt() -> None:
    """Ctrl+C at the main prompt exits 0."""
    outputs, code = run_session([KeyboardInterrupt()])
    assert outputs == ["\nGoodbye!"]
    assert code == 0


def test_eof_and_interrupt_at_argument_prompt() -> None:
    """Exceptions at an argument prompt end cleanly."""
    for command in ("add", "complete", "delete"):
        for exc in (EOFError(), KeyboardInterrupt()):
            outputs, code = run_session([command, exc])
            assert outputs == ["\nGoodbye!"]
            assert code == 0


def test_interrupt_during_dispatch() -> None:
    """Ctrl+C raised while a command executes still exits cleanly."""
    feed: Iterator[str] = iter(["list"])
    calls: List[str] = []

    def fake_output(text: str) -> None:
        calls.append(text)
        if text == "No tasks.":
            raise KeyboardInterrupt

    code = run(lambda prompt: next(feed), fake_output)
    assert calls == ["No tasks.", "\nGoodbye!"]
    assert code == 0


def test_id_not_reused_via_cli() -> None:
    """IDs keep increasing after a delete."""
    outputs, _ = run_session(["add a", "delete 1", "add b", "list", "quit"])
    assert outputs[2] == "Added task 2: b"
    assert outputs[3] == "2. [ ] b"


def test_already_completed_path() -> None:
    """Completing twice reports the informational message."""
    outputs, _ = run_session(["add a", "complete 1", "complete 1", "quit"])
    assert outputs[2] == "Task 1 is already completed."


def test_help_via_session() -> None:
    """Help is a single output call."""
    outputs, code = run_session(["help", "q"])
    assert len(outputs) == 2
    assert outputs[0].startswith("Commands:\n")
    assert code == 0
