# Architecture

Source requirements: `docs/requirements.md` (US-001: Simple Python To-Do App).
Design review: `docs/design-review.md` (Required Changes 1, 2, 3 and 5 are resolved in this document and implemented. Required Change 4 is resolved: the csv-summary edits were preserved on branch `csv-summary-sample` (commit 60ffcc2), see "Resolved: pyproject.toml overwrite").

## Architecture Pattern

A two-layer design with a thin entry point, in a single Python package `src/todo/`:

1. **Logic layer (pure, no I/O)**: `models.py`, `errors.py`, `manager.py`. It never calls `input()` or `print()`. It takes plain values and returns values or raises typed exceptions.
2. **CLI layer (all I/O)**: `cli.py`. It parses typed commands, calls the logic layer, and formats output. Input and output functions are injected, so the loop can be tested without a terminal.
3. **Entry point**: `__main__.py` wires the real `input` and `print` into `cli.run` and passes the returned exit code to `sys.exit`, so the app starts with `python -m todo`.

Why this pattern:
- Requirements demand that task-management logic be separate from input parsing and printing (NFR modularity).
- A pure logic layer makes the 90% coverage floor and the invalid-path tests (FR-10) cheap and deterministic.
- Dependencies point one way (CLI depends on logic, never the reverse), so the scope stays small. Heavier patterns (MVC, repositories, services) add nothing at this scale.

## Component Overview

| Component | Responsibility |
|-----------|-----------------|
| `src/todo/models.py` | Defines `Task`, a frozen dataclass with `id: int`, `description: str`, `completed: bool`. Immutable, so state changes produce a new instance (via `dataclasses.replace`). |
| `src/todo/errors.py` | Exception hierarchy: `TaskError` (base), `InvalidDescriptionError`, `InvalidIdError`, `TaskNotFoundError`. Each carries a user-presentable message (see the message table). The classes are bare subclasses with docstrings only; the message is supplied by the raiser. |
| `src/todo/manager.py` | `TaskManager`: in-memory store (`Dict[int, Task]`) and a `_next_id` counter that starts at 1 and is never decremented. Provides `add`, `list_tasks`, `complete`, `delete`, plus a private `_lookup` helper that performs the ID checks shared by `complete` and `delete`. Owns description validation (`MAX_DESCRIPTION_LENGTH = 200`) and ID validation. Also hosts the public module-level function `parse_task_id(raw: str) -> int`, so it falls inside the gated logic layer and its unit tests count toward coverage. |
| `src/todo/cli.py` | Command parser and loop. Provides `run(input_fn, output_fn) -> int` and the public `format_tasks`, plus module constants (`MAIN_PROMPT`, `DESCRIPTION_PROMPT`, `ID_PROMPT`, `QUIT_COMMANDS`, `HELP_TEXT`) and the type aliases `InputFn` and `OutputFn`. Private helpers: `_split` (split once), `_argument` (inline argument or prompt), `_handle_add` / `_handle_complete` / `_handle_delete`, and `_dispatch` (returns the output text for `add`, `list`, `complete`, `delete`, `help`, and the unknown-command error). `quit` and its aliases are handled in `run` itself, before dispatch. Converts `TaskError` to `Error: <message>` output. Handles `KeyboardInterrupt` and `EOFError`. Calls `parse_task_id` for ID text and passes only `int` to the manager. |
| `src/todo/__main__.py` | Entry point. Executes `sys.exit(run(input, print))` under an `if __name__ == "__main__":  # pragma: no cover` guard. |
| `src/todo/__init__.py` | Marks the package (docstring only). Exports nothing else. |
| `tests/unit/` | Unit tests for the logic layer (errors, models, add, list, complete, delete, `parse_task_id`, invalid-ID, invalid-description, ID non-reuse, 200-character boundary) and for the command parser. |
| `tests/integration/` | Tests that drive `cli.run` with scripted input and captured output (full sessions, error continuation, EOF and Ctrl+C exit, returned exit code), and a subprocess smoke test of `python -m todo`. |

### Test module naming

Test module basenames must be unique across all of `tests/` (including `tests/unit/` and `tests/integration/`), because pytest's default import mode raises "import file mismatch" for duplicate basenames in directories without `__init__.py`. Implemented modules (add more only if they are also unique):

- `tests/unit/test_errors.py`
- `tests/unit/test_models.py`
- `tests/unit/test_manager.py`
- `tests/unit/test_parse_task_id.py`
- `tests/unit/test_cli_parser.py`
- `tests/integration/test_cli_session.py`
- `tests/integration/test_main_entry.py` (subprocess smoke test: runs `sys.executable -m todo` with `PYTHONPATH` set to `src`; covers a scripted session and EOF-only stdin)

Do not add `__init__.py` files under `tests/` as an alternative.

### Logic layer contract

- `add(description: str) -> Task`: trims the description (`str.strip()`), validates it, assigns `_next_id`, increments the counter, stores and returns the task. Raises `InvalidDescriptionError`. Length is counted in Unicode code points after trimming: 200 is accepted, 201 is rejected. Internal whitespace is preserved verbatim. The counter is incremented only after validation passes, so a rejected add does not consume an ID.
- `list_tasks() -> List[Task]`: returns all tasks sorted by ID. Returns an empty list when there are none.
- `complete(task_id: int) -> Tuple[Task, bool]`: returns the task and a `changed` flag. `changed` is `False` when the task was already completed (a no-op, not an error). Raises `InvalidIdError` or `TaskNotFoundError`.
- `delete(task_id: int) -> Task`: removes and returns the task. Raises `InvalidIdError` or `TaskNotFoundError`. The counter is untouched, so IDs are never reused.
- `parse_task_id(raw: str) -> int`: public, module-level, pure. Converts user-typed ID text to an `int`. See the ID contract.

### ID contract

**Manager methods (`complete`, `delete`)** accept `int` only. They do not accept `str`. Checks, in this order (implemented in `_lookup`):

1. If the argument is not an `int`, or is a `bool` (`bool` is a subclass of `int`, so it is rejected explicitly; the `bool` test must come before any numeric comparison, otherwise `True` would be treated as ID 1), raise `InvalidIdError`.
2. If the value is less than 1, raise `InvalidIdError`.
3. If no task has that ID (never existed or already deleted), raise `TaskNotFoundError`.

**`parse_task_id(raw)` grammar**: trim the input with `str.strip()`; the result must consist of one or more ASCII digits (`0`-`9`) and nothing else; its integer value must be at least 1. Consequences: `"+2"`, `"-2"`, `"2_0"`, `"1.0"`, `"1e3"`, `"2 3"` (extra tokens), and Unicode digits (such as Arabic-Indic, full-width, or superscript digits) are all rejected. Leading zeros are allowed (`"007"` parses to 7). `parse_task_id` never returns a value that the manager would reject for being non-positive.

The ASCII-digit test is `text.isascii() and text.isdigit()`. The `isascii()` guard is what excludes Unicode digits (`"٢".isdigit()` and `"²".isdigit()` are both true).

**Very long digit strings are Python-version dependent.** Python versions that enforce the integer string-conversion length limit (default 4300 digits; present in 3.11+ and backported to 3.10.7 and later 3.10 patch releases) make `int()` raise `ValueError` for such input, which `parse_task_id` maps to the "must be a whole number" message. Older interpreters (and any with the limit disabled) parse the same input successfully. The unit test therefore accepts either outcome (a parsed value of at least 1, or the whole-number `InvalidIdError`). Note that on the error path the message embeds the full `repr` of the input, so it can be very long.

**Exception messages** (all raised as `InvalidIdError` unless noted; `{raw}` is the trimmed text rendered with `repr`, so control characters are shown escaped):

| Where | Failure | Exception | Message |
|-------|---------|-----------|---------|
| `parse_task_id` | Empty or whitespace-only after trim | `InvalidIdError` | `Task ID cannot be empty.` |
| `parse_task_id` | Not purely ASCII digits (letters, signs, underscores, decimal points, Unicode digits, internal whitespace / extra tokens). Any `ValueError` raised during integer conversion (for example an extremely long digit string on a Python with the conversion limit) maps to this same message. | `InvalidIdError` | `Task ID must be a whole number, got {raw}.` |
| `parse_task_id` | ASCII digits but value is 0 (`"0"`, `"00"`) | `InvalidIdError` | `Task ID must be a positive number.` |
| `complete`, `delete` | Argument is not an `int`, or is a `bool` | `InvalidIdError` | `Task ID must be an integer.` |
| `complete`, `delete` | `int` value less than 1 | `InvalidIdError` | `Task ID must be a positive number.` |
| `complete`, `delete` | No task with that ID | `TaskNotFoundError` | `Task {id} not found.` |

**`repr` quote style.** `{raw}` and the unknown-command `{token}` are produced with `repr` (the `!r` format spec), so the quote character follows Python's rule: single quotes by default (`'x'`), but double quotes when the text contains a single quote and no double quote (`"it's"`), and backslash-escaped single quotes when it contains both. Tests build their expected strings with `{raw!r}` rather than hard-coding quotes for that reason.

## Command grammar

The CLI reads one line per iteration from the main prompt and processes it as follows.

1. **Main-prompt line**: take the line and apply `str.strip()`. If the result is empty (empty line or whitespace-only), do nothing: produce no output and re-prompt.
2. **Split once**: split the stripped line with `line.split(None, 1)` (at the first run of whitespace) into `command` and `rest`. `rest` is everything after that run, verbatim (internal whitespace preserved, and no trailing whitespace because the line was already stripped); it is the empty string if there was no whitespace. Because of `split(None, 1)`, leading whitespace between the command and the argument is discarded.
3. **Command matching** is case-insensitive on `command`: `add`, `list`, `complete`, `delete`, `help`, `quit`, with `q` and `exit` as aliases for `quit`.
4. **`add`**: if `rest` is empty, prompt with `Description: `. A whitespace-only inline argument (for example `add    `) is therefore treated as omitted and prompts: this follows from stripping the whole line in step 1 before the split, so `rest` can never be whitespace-only, and the check is a plain truthiness test on `rest`. The argument, inline or prompted, is passed to `TaskManager.add`.
5. **`complete` and `delete`**: if `rest` is empty, prompt with `Task ID: `. The argument, inline or prompted, is passed to `parse_task_id`, and the resulting `int` to the manager. Extra tokens are not ignored: `complete 2 3` makes `rest` equal `2 3`, which fails the ID grammar and prints the "must be a whole number" error. Nothing is completed.
6. **`list`, `help`, `quit` (and aliases)**: any `rest` is ignored. (`list foo` behaves as `list`.)
7. **Unknown command**: print the unknown-command error (see the message table) and re-prompt.

**Empty input rule (main prompt versus argument prompt)**:
- At the **main prompt**, empty or whitespace-only input is silently ignored and the prompt is shown again.
- At an **argument prompt** (`Description: ` or `Task ID: `), empty or whitespace-only input is NOT ignored. The answer is not stripped by the CLI; it is passed on and produces the relevant validation error (`Error: Description cannot be empty.` or `Error: Task ID cannot be empty.`). The loop then returns to the main prompt; it does not re-ask the argument.

**Prompts** (passed as the argument to `input_fn`): main prompt `> `, then `Description: ` and `Task ID: `.

## Message table

All text is passed to `output_fn` as shown. Placeholders: `{id}` is the integer ID in decimal, `{description}` is the stored (trimmed) description, `{token}` is the first token the user typed, exactly as typed (original case), rendered with `repr`. Each row is exactly one `output_fn` call; multi-line outputs (list, help) are one call with lines joined by `\n` and no trailing newline.

| Situation | Exact output |
|-----------|--------------|
| Add succeeded | `Added task {id}: {description}` |
| Complete succeeded | `Completed task {id}.` |
| Complete on an already completed task (not an error) | `Task {id} is already completed.` |
| Delete succeeded | `Deleted task {id}.` |
| List, no tasks | `No tasks.` |
| List, with tasks (one line per task, ID order; `[ ]` pending, `[x]` completed) | `1. [ ] Buy milk` / `2. [x] Walk dog` |
| Help | See help text below |
| `quit`, `q`, `exit` | `Goodbye!` |
| EOF or Ctrl+C (at any point) | `\nGoodbye!` (a leading newline, then the word) |
| Unknown command | `Error: Unknown command {token}. Type 'help' for a list of commands.` |
| Empty description (after trim) | `Error: Description cannot be empty.` |
| Description over 200 characters | `Error: Description cannot exceed 200 characters.` |
| Empty task ID | `Error: Task ID cannot be empty.` |
| Task ID not purely ASCII digits | `Error: Task ID must be a whole number, got {raw}.` |
| Task ID zero, or non-positive `int` at the manager | `Error: Task ID must be a positive number.` |
| Non-`int` or `bool` ID at the manager (reachable only through direct API misuse, not from the CLI) | `Error: Task ID must be an integer.` |
| Task not found | `Error: Task {id} not found.` |

Rules: every `TaskError` is printed as `Error: ` followed by the exception message, so the exception messages in the ID contract table are the source of truth and the `Error: ` prefix is added only in the CLI. The unknown-command error is produced by the CLI itself (it is not a `TaskError`; `_dispatch` returns it as ordinary output text) and carries the same `Error: ` prefix. No success message and no list line carries an `Error: ` prefix.

**Help text** (a single output):

```
Commands:
  add [description]   Add a new task
  list                Show all tasks
  complete [id]       Mark a task as completed
  delete [id]         Delete a task
  help                Show this help
  quit                Exit (aliases: q, exit)
On Windows, end-of-input is Ctrl+Z then Enter.
```

## Exit contract

- `run(input_fn: InputFn, output_fn: OutputFn) -> int` returns the process exit code, where `InputFn = Callable[[str], str]` and `OutputFn = Callable[[str], None]` are module-level aliases in `cli.py` (mypy strict clean).
- `quit` (and its aliases), `EOFError`, and `KeyboardInterrupt` all make `run` return `0`. There is no non-zero return path for expected conditions.
- `__main__.py` does `sys.exit(run(input, print))`. The exit code is therefore asserted directly from the return value of `run` in tests.
- **Interrupt handling wraps the whole loop body**, not only the `input_fn` calls: the single `try`/`except (KeyboardInterrupt, EOFError)` encloses reading the main prompt, reading any argument prompt, command dispatch, and output. A Ctrl+C that arrives while a command is executing therefore also ends the session cleanly with exit code 0 and no traceback.
- On EOF or interrupt, `run` outputs `\nGoodbye!` (leading newline, so the message does not land on the prompt line). On `quit`, it outputs `Goodbye!` without the leading newline.
- Unexpected (non-`TaskError`, non-interrupt) exceptions are intentionally not caught. They propagate as a traceback, since they indicate programming errors. FR-6 ("never crashes") applies to expected failures only.

## Implementation Notes

Short excerpts from `src/todo/` that pin down the behaviour described above.

Split-once and inline-argument handling (`cli.py`):

```python
def _split(line: str) -> Tuple[str, str]:
    parts = line.split(None, 1)
    return parts[0], parts[1] if len(parts) > 1 else ""

def _argument(rest: str, prompt: str, input_fn: InputFn) -> str:
    return rest if rest else input_fn(prompt)
```

Loop and error handling (`cli.py`):

```python
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
```

ID checks (`manager.py`): the `bool` rejection precedes the range check.

```python
def _lookup(self, task_id: int) -> Task:
    if not isinstance(task_id, int) or isinstance(task_id, bool):
        raise InvalidIdError("Task ID must be an integer.")
    if task_id < 1:
        raise InvalidIdError("Task ID must be a positive number.")
    task = self._tasks.get(task_id)
    if task is None:
        raise TaskNotFoundError(f"Task {task_id} not found.")
    return task
```

`parse_task_id` conversion (`manager.py`): `ValueError` from `int()` (long digit strings on limit-enforcing interpreters) is re-raised as `InvalidIdError` with the whole-number message.

```python
if not (text.isascii() and text.isdigit()):
    raise InvalidIdError(message)
try:
    value = int(text)
except ValueError:
    raise InvalidIdError(message) from None
```

Typing style: the source uses `typing.Dict`, `List`, `Tuple`, `Callable` rather than builtin generics. Both are valid on 3.10; this is a stylistic choice only.

## Data Flow

```
 user (terminal)
      |  typed line, e.g. "complete 2"
      v
 __main__.py  --- sys.exit(run(input, print)) --->  cli.run(input_fn, output_fn) -> int
                                                    |
                                  strip, split once, match command
                                  (prompt for argument if missing)
                                                    |
                                                    v
                                     parse_task_id("2") -> 2   (raises InvalidIdError)
                                                    |
                                                    v
                                        TaskManager.complete(2)   (int only)
                                                    |
                              +---------------------+----------------------+
                              |                                            |
                     returns (Task, changed)                     raises TaskError subclass
                              |                                            |
                              v                                            v
              "Completed task 2." or                          "Error: <message>"
              "Task 2 is already completed."                  (loop continues)
                              |                                            |
                              +--------------------+-----------------------+
                                                   v
                                          output_fn(...) -> terminal

 quit                       -> "Goodbye!"        -> run returns 0
 KeyboardInterrupt / EOF    -> "\nGoodbye!"      -> run returns 0
 (anywhere in the loop body, including argument prompts and dispatch)
```

Task state exists only inside the `TaskManager` instance created by `run`. It is lost when the process exits (FR-9).

## Technology Stack

- Language: Python 3.10+ (source must not use features newer than 3.10, for example no `tomllib`, `typing.Self`, or `StrEnum`).
- Runtime dependencies: none (standard library only: `dataclasses`, `typing`, `sys`).
- Framework: none. A plain `input()` command loop meets FR-7 without extra tooling.
- Storage: in-memory `Dict[int, Task]`. No database, files, or network.
- Testing: pytest. pytest-cov for coverage, with a 90% line-coverage gate on the logic layer defined by one exact command (see Non-Functional Considerations).
- Dev tooling already configured in `pyproject.toml`: ruff, mypy (strict).

### Required `pyproject.toml` adjustments

`pyproject.toml` previously described a different sample project (`csv-summary`). The adjustments below have been applied (Task 15). Settings that were reusable as-is: pytest as the test framework, `pythonpath = ["src"]`, `testpaths = ["tests"]`, pytest-cov in the `dev` extras, and the ruff and mypy configuration. The table lists the settings that conflicted with this design and their applied state:

| Setting | Previous (csv-summary) | Applied |
|---------|------------------------|---------|
| `[project] name`, `description` | `csv-summary` and a CSV description | To-do app name and description (`todo-app`) |
| `[project] requires-python` | `>=3.11` | `>=3.10` (matches the requirements) |
| `[tool.ruff] target-version`, `[tool.mypy] python_version` | `py311`, `3.11` | `py310`, `3.10` |
| `[tool.coverage.run] source` | `["csv_summary"]` | `["todo"]` |
| `[tool.coverage.report] fail_under` | `80` | Removed. The only enforced coverage gate is the exact command in Non-Functional Considerations, so there is no second, global threshold that could disagree with it. |
| `[tool.pytest.ini_options] addopts`, `markers` | `-m 'not slow'` and a `slow` marker for a 100 MB fixture | Removed (no slow tests exist here) |
| `[tool.ruff.lint] ignore` | (not set) | `["UP006", "UP035", "FLY002"]`, because the code deliberately uses `typing.Dict`/`List`/`Tuple`/`Callable` and a joined `HELP_TEXT` |
| `readme` | `README.md` | Kept; `README.md` was rewritten for the to-do app (Task 16) |

The pytest `pythonpath = ["src"]` setting is present, so tests import `todo` without installation.

### Resolved: pyproject.toml overwrite

Overwriting `pyproject.toml` was blocked until the user's uncommitted csv-summary edits had been preserved. That is done: the csv-summary edits to `pyproject.toml`, `README.md` and `user-stories/` were preserved on branch `csv-summary-sample` (commit 60ffcc2), which resolves Required Change 4 in `docs/design-review.md` (Task 0). `pyproject.toml` and `README.md` have since been updated for the to-do app (Tasks 15 and 16). The final verification (Task 17) passed on Python 3.13.16: 106 tests, 100% coverage on the gated modules, ruff and mypy clean. Python 3.10 was not available, so the run was not on the minimum supported version.

## Deployment Strategy

- Local, single-user terminal application. There is no server, container, or scaling concern.
- Run with `python -m todo` from the repository root with `src` on the path (for example `PYTHONPATH=src python -m todo`, or after `pip install -e .`).
- Packaging and distribution are out of scope.
- Maintenance: tests run with `pytest`; the coverage gate is the exact command given below. No migrations, no configuration files, no environment variables.

## Key Design Decisions

- **Two-layer split with injectable I/O**: `run(input_fn, output_fn) -> int` allows full-session tests with scripted input, so Ctrl+C and EOF paths can be tested by having the fake input raise the exception, and the exit code is asserted from the return value.
- **Frozen `Task` dataclass**: immutability prevents accidental mutation from the CLI layer. Completing a task replaces the stored instance.
- **`Dict[int, Task]` plus a monotonic `_next_id`**: lookup and delete are O(1), and IDs are never reused after deletion because the counter is independent of the dict contents. `list_tasks` sorts by ID.
- **Validation lives in the logic layer**: trimming, the 200-character limit (200 accepted, 201 rejected, counted in code points after trimming), ID text parsing (`parse_task_id`), and ID checks are enforced in `manager.py`, so any front end gets the same rules and the unit tests cover them.
- **Manager takes `int` IDs only; text parsing is a separate public function**: this keeps the manager's type contract simple under mypy strict, and the strict grammar (ASCII digits, at least 1) is defined once and tested in isolation. `bool` is rejected explicitly, and before the range check.
- **`complete` returns `(task, changed)`**: an already-completed task is a no-op, not an error. The CLI decides the message, which keeps the logic layer free of presentation text.
- **Typed exception hierarchy under `TaskError`**: the CLI catches one base class and prints `Error: <message>`. Specific subclasses let tests assert exact failure causes. Unexpected exceptions (programming errors) are not swallowed.
- **Typed command loop instead of numbered menu**: supports inline arguments (`complete 2`) and a fallback prompt, and is easy to script in tests. Commands are case-insensitive; `q` and `exit` alias `quit`; `help` is included.
- **Exact message strings are part of the design**: the message table is the contract that both the implementation and the tests assert against.
- **In-memory only, session-scoped**: one `TaskManager` per `run` call; one-shot subcommands are not used because state would be lost between invocations.
- **Tests split by layer, with unique module names**: `tests/unit/` for logic and parser, `tests/integration/` for the CLI loop and entry-point smoke test. Requirements make CLI tests optional, but the injectable design makes them cheap.

## Non-Functional Considerations

- **Performance**: not a concern. Operations are O(1) except listing, which is O(n log n) for a session-sized list. Storage is unbounded in memory, which is acceptable for a session-scoped local tool.
- **Security**: no network, files, or subprocesses in the application. Input sanitization consists of trimming, length limits, and the strict ID grammar. Descriptions are stored and printed as plain text only (never evaluated or used in format strings). Control characters in descriptions are not specially handled, which is acceptable for a local single-user tool (a possible later improvement). In error messages, user-supplied ID text is shown via `repr`, so control characters are escaped. (Only the test suite spawns a subprocess, in `test_main_entry.py`.)
- **Monitoring and observability**: none required. No logging is implemented, per the requirements.
- **Error handling**:
  - All expected failures are `TaskError` subclasses, caught in the CLI loop, printed as `Error: <message>`, and the loop continues (FR-6).
  - `KeyboardInterrupt` and `EOFError` anywhere in the loop body produce `\nGoodbye!` and exit code 0, with no traceback (FR-8).
  - Messages are exactly those in the message table.
  - Non-`TaskError`, non-interrupt exceptions propagate (intentional, see Exit contract).
- **Testing and quality gates**:
  - All tests must pass.
  - **The one coverage gate** is this exact command, run from the repository root, which must exit with code 0:

    ```
    python -m pytest --cov=todo.manager --cov=todo.models --cov=todo.errors --cov-report=term-missing --cov-fail-under=90
    ```

    It enforces at least 90% line coverage across `todo.manager`, `todo.models`, and `todo.errors` combined. The Verification Agent runs exactly this command. It has no latitude to substitute another command, change the modules, change the threshold, or measure the CLI instead. CLI coverage (`todo.cli`) is not gated; it may be reported separately for information only. A non-zero exit from this command is a failed gate, to be surfaced and not worked around.
  - `__main__.py` is excluded from coverage via `# pragma: no cover` on its `if __name__ == "__main__":` guard (implemented). It is not among the measured modules above in any case.
  - ruff and mypy (strict) must pass on `src/`.
  - The Verification Agent must report the Python interpreter version used for the run, and must flag if the run was not on 3.10 (the minimum supported version) when 3.10 is available. Because very-long-digit-string handling differs by interpreter version (see ID contract), results on 3.10 and 3.11+ may legitimately differ for that one input; the test accepts both.
- **Maintainability**: the package has five small modules with one-way dependencies (`cli` -> `manager` -> `models`/`errors`). Adding persistence or another front end later requires no change to the logic layer's public contract.
