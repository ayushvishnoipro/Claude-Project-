"""Unit tests for CLI command parsing and dispatch."""

from typing import Iterator, List, Tuple

import pytest

from todo.cli import HELP_TEXT, run


def drive(lines: List[str]) -> Tuple[List[str], List[str], int]:
    """Run the CLI on scripted lines; return (outputs, prompts, code)."""
    feed: Iterator[str] = iter(lines)
    outputs: List[str] = []
    prompts: List[str] = []

    def fake_input(prompt: str) -> str:
        prompts.append(prompt)
        return next(feed)  # StopIteration is not EOFError, so script quits

    code = run(fake_input, outputs.append)
    return outputs, prompts, code


def test_blank_main_prompt_lines_produce_no_output() -> None:
    """Empty and whitespace-only lines are ignored."""
    outputs, prompts, _ = drive(["", "   ", "\t", "quit"])
    assert outputs == ["Goodbye!"]
    assert prompts == ["> "] * 4


@pytest.mark.parametrize("word", ["quit", "QUIT", "q", "Q", "exit", "Exit"])
def test_quit_aliases_case_insensitive(word: str) -> None:
    """quit, q, exit end the session with Goodbye!."""
    outputs, _, code = drive([word])
    assert outputs == ["Goodbye!"]
    assert code == 0


def test_commands_case_insensitive() -> None:
    """ADD and LiSt work."""
    outputs, _, _ = drive(["ADD Milk", "LiSt", "quit"])
    assert outputs[:2] == ["Added task 1: Milk", "1. [ ] Milk"]


def test_add_inline() -> None:
    """Inline description is used and trimmed."""
    outputs, prompts, _ = drive(["add   Buy milk  ", "quit"])
    assert outputs[0] == "Added task 1: Buy milk"
    assert "Description: " not in prompts


def test_add_without_argument_prompts() -> None:
    """Missing argument triggers the Description prompt."""
    outputs, prompts, _ = drive(["add", "Walk dog", "quit"])
    assert prompts == ["> ", "Description: ", "> "]
    assert outputs[0] == "Added task 1: Walk dog"


def test_add_whitespace_only_inline_prompts() -> None:
    """Whitespace-only inline argument counts as omitted."""
    _, prompts, _ = drive(["add    ", "x", "quit"])
    assert prompts[1] == "Description: "


def test_add_empty_at_argument_prompt_errors_and_returns() -> None:
    """Empty answer yields a validation error, then the main prompt."""
    outputs, prompts, _ = drive(["add", "", "quit"])
    assert outputs == ["Error: Description cannot be empty.", "Goodbye!"]
    assert prompts == ["> ", "Description: ", "> "]


def test_add_preserves_internal_whitespace() -> None:
    """Internal whitespace is kept verbatim."""
    outputs, _, _ = drive(["add a   b\tc", "quit"])
    assert outputs[0] == "Added task 1: a   b\tc"


def test_add_too_long() -> None:
    """Over-length description error message."""
    outputs, _, _ = drive(["add " + "a" * 201, "quit"])
    assert outputs[0] == "Error: Description cannot exceed 200 characters."


def test_complete_prompts_for_id() -> None:
    """Missing ID triggers the Task ID prompt."""
    outputs, prompts, _ = drive(["add x", "complete", "1", "quit"])
    assert prompts[2] == "Task ID: "
    assert outputs[1] == "Completed task 1."


def test_complete_empty_id_at_prompt() -> None:
    """Empty answer at the ID prompt gives the empty-ID error."""
    outputs, _, _ = drive(["delete", "", "quit"])
    assert outputs[0] == "Error: Task ID cannot be empty."


def test_complete_extra_tokens_rejected_and_nothing_completed() -> None:
    """'complete 2 3' fails the ID grammar and completes nothing."""
    outputs, _, _ = drive(["add a", "add b", "complete 2 3", "list", "quit"])
    assert outputs[2] == "Error: Task ID must be a whole number, got '2 3'."
    assert outputs[3] == "1. [ ] a\n2. [ ] b"


def test_complete_already_completed_message() -> None:
    """Second completion is informational."""
    outputs, _, _ = drive(["add a", "complete 1", "complete 1", "quit"])
    assert outputs[1:3] == ["Completed task 1.", "Task 1 is already completed."]


def test_delete_and_not_found() -> None:
    """Delete succeeds once, then reports not found."""
    outputs, _, _ = drive(["add a", "delete 1", "delete 1", "quit"])
    assert outputs[1:3] == ["Deleted task 1.", "Error: Task 1 not found."]


def test_zero_id_message() -> None:
    """Zero ID is rejected."""
    outputs, _, _ = drive(["complete 0", "quit"])
    assert outputs[0] == "Error: Task ID must be a positive number."


def test_list_ignores_rest() -> None:
    """'list foo' behaves as 'list'."""
    outputs, _, _ = drive(["list foo", "quit"])
    assert outputs[0] == "No tasks."


def test_help_ignores_rest_and_is_verbatim() -> None:
    """'help me' prints the exact help text as one output."""
    outputs, _, _ = drive(["help me", "quit"])
    assert outputs[0] == HELP_TEXT
    assert HELP_TEXT.splitlines()[0] == "Commands:"
    assert not HELP_TEXT.endswith("\n")
    assert HELP_TEXT.splitlines()[-1] == (
        "On Windows, end-of-input is Ctrl+Z then Enter."
    )


def test_quit_ignores_rest() -> None:
    """'quit now' still quits."""
    outputs, _, code = drive(["quit now"])
    assert outputs == ["Goodbye!"]
    assert code == 0


def test_unknown_command_uses_repr_of_original_case_token() -> None:
    """Unknown token is shown with repr and original case."""
    outputs, _, _ = drive(["FooBar baz", "quit"])
    assert outputs[0] == (
        "Error: Unknown command 'FooBar'. Type 'help' for a list of commands."
    )
