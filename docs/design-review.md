# Design Review

Reviewed: `docs/architecture.md` against `docs/requirements.md` (US-001, Simple Python To-Do App).

## Review Summary

The design is sound and proportionate. A pure logic layer, a thin injectable-I/O CLI, an in-memory dict with a monotonic ID counter, and a typed exception hierarchy fit the requirements. It covers FR-1 through FR-10 and all acceptance criteria. There are no critical architectural flaws.

The weaknesses are contract ambiguities that the document explicitly defers to "implementation detail". These would let the implementation, the tests, and the quality gates drift apart. The main ones are:
- who parses ID text, and what type `complete` and `delete` accept;
- how the coverage gate is defined;
- the return value and exit-code contract of `run`;
- the exact user-facing message strings and command-parsing edge cases.

These are cheap to fix at design time and expensive to discover during code review or verification. The `pyproject.toml` overwrite also needs the user's confirmation, because it discards uncommitted work.

## Risk Assessment

| Risk Category | Risk | Severity | Recommendation |
|---------------|------|----------|-----------------|
| Scalability | Unbounded task count and description storage in memory. Listing is O(n log n) on each call. | Minor | Acceptable for a session-scoped local tool. No action needed. Note the assumption in the docs. |
| Security | ANSI or control characters in descriptions are echoed to the terminal. The doc acknowledges this. Python's `int()` also accepts `"+2"`, `" 2 "`, `"2_0"`, and non-ASCII digits, so "strict integer parsing" is not strict unless specified. | Minor | Define the ID grammar explicitly (see Required Change 1). Optionally reject control characters in descriptions (a one-line check) so list output cannot be corrupted. |
| Error Handling | `run` and `__main__` contract is unspecified: whether `run` returns an int exit code or `__main__` calls `sys.exit`. The architecture says `__main__` "returns exit code 0", which is not how Python entry points work. | Major | Specify `run(input_fn, output_fn) -> int` and `__main__` does `sys.exit(run(input, print))`. Tests can then assert the exit code. |
| Error Handling | Behavior on `KeyboardInterrupt` is defined only around `input_fn` calls. On Windows, Ctrl+Z needs Enter before EOF is delivered, and Ctrl+C leaves the cursor on the prompt line. | Minor | Wrap the whole loop body, not only reads. Print a leading newline before `Goodbye!` on interrupt or EOF. Document the Windows Ctrl+Z behavior in help or the README. |
| Error Handling | Unexpected (non-`TaskError`) exceptions propagate as a traceback. | Minor | This is a defensible choice for programming errors. Confirm it is intentional and that FR-6 ("never crashes") applies only to expected failures. |
| Engineering Fit | Five small modules and the two-layer split are appropriate. The `errors.py` hierarchy of 3 subclasses is slightly generous but justified by test assertions. No over-engineering found. | Minor | None. |
| Engineering Fit | Under-specified: command grammar edge cases such as `add` followed only by whitespace, `complete 2 3` (extra args), internal whitespace preservation in descriptions, and which empty-input rule applies at an argument prompt versus the main prompt. | Major | Add a short grammar: split once on the first whitespace run, so the rest is the argument verbatim. Whitespace-only inline argument is treated as omitted and prompts. Extra tokens for `complete` and `delete` produce an invalid-ID error, or are ignored (pick one). |
| Non-Functional | The coverage gate is ambiguous. `fail_under = 90` is described as global, but the requirement is 90% on the logic layer only. The doc then lets the Verification Agent choose either. A gate that varies per run is not a gate. | Major | Pick one: a measured command `pytest --cov=todo.manager --cov=todo.models --cov=todo.errors --cov-fail-under=90`, and set global `fail_under` to a looser value or keep it advisory. Write the chosen command in the doc. |
| Non-Functional | The requirement says Python 3.10+, but only "tested on 3.10 if available". Nothing prevents 3.11-only features (e.g. `tomllib`, `typing.Self`, `StrEnum`) from slipping in. | Minor | Set ruff `target-version = "py310"` and mypy `python_version = "3.10"`, as already planned. Add a note to the Verification Agent to report the interpreter version used. |
| Component Interfaces | `TaskManager.complete(task_id)` and `delete(task_id)` have no stated parameter type. The data flow shows `complete("2" -> 2)`, which implies conversion happens at the boundary but leaves it open whether the manager accepts `str` or `int`. The doc says the helper location "is an implementation detail". With mypy strict, this must be decided. Also `bool` is a subclass of `int`, so `complete(True)` would silently work. | Major | Fix the contract: the manager accepts `int` only. A public helper `parse_task_id(raw: str) -> int` raises `InvalidIdError` for empty, non-numeric, and `<= 0` values. The manager rejects non-positive ints and non-int types (including `bool`). Put the helper in the logic layer (e.g. `manager.py` or a `validation.py`) so FR-10 unit tests cover it. |
| Component Interfaces | User-facing message strings are not specified (only examples like "Completed task 2."). Unit and integration tests will assert on text, and the exact wording, punctuation, and `Error: ` prefix will otherwise be invented separately by the Implementation and test authors. | Major | Add a message table to the architecture: each exception's message, add, complete, delete, already-completed, empty list, unknown command, and goodbye. |
| Component Interfaces | `pyproject.toml` has many conflicting settings (name, python version, coverage source, `addopts`, `markers`). The architecture lists them accurately but also notes the working tree has uncommitted edits from a prior sample story. | Major | Obtain explicit user confirmation before the Implementation phase overwrites them (see Required Change 4). |
| Component Interfaces | Tests live in both `tests/unit/` and `tests/integration/`. Without `__init__.py` files or unique test filenames, pytest's default import mode raises "import file mismatch" for duplicate basenames. | Minor | Require unique test module names (e.g. `test_manager.py`, `test_cli_session.py`) or add `__init__.py` files. |

## Design Decisions Confirmed

- Two-layer split with injectable I/O (`run(input_fn, output_fn)`): Confirmed. It makes Ctrl+C, EOF, and full-session tests deterministic.
- Frozen `Task` dataclass with `dataclasses.replace`: Confirmed. It is safe to return from `list_tasks` without defensive copies.
- `dict[int, Task]` plus monotonic `_next_id`: Confirmed. IDs are never reused, and the counter is independent of dict contents.
- Validation in the logic layer (trim, 200-character limit with 200 accepted and 201 rejected): Confirmed. Note that length is counted in code points after trimming. State this in the docs.
- `complete` returns `(Task, bool)`: Confirmed. It keeps presentation out of the logic layer. Consider a small named result type only if mypy or readability suffers.
- Typed exception hierarchy under `TaskError`: Confirmed.
- Typed command loop with aliases and `help`: Confirmed. The extras (`q`, `exit`, `help`) are small and testable, and they are consistent with the requirements.
- In-memory, session-scoped storage: Confirmed (FR-9).
- ID parsing ownership: Needs Clarification (Required Change 1).
- Coverage gate definition: Needs Clarification (Required Change 2).
- `run` return value and exit code: Needs Clarification (Required Change 3).
- Overwriting `pyproject.toml`, `README.md`, and `user-stories/` changes: Risky until the user confirms (Required Change 4).

## Required Changes Before Implementation

1. Define the ID contract. The manager's `complete` and `delete` accept `int` only (reject `bool`). Add a public `parse_task_id(raw: str) -> int` in the logic layer with a precise grammar, for example ASCII digits only after trimming, value at least 1, which rejects `+2`, `2_0`, `1.0`, and Unicode digits. State which exception message each failure produces. Update the data-flow text accordingly.
2. Make the coverage gate unambiguous. Specify the single command or `pyproject.toml` configuration that enforces 90% on `models.py`, `errors.py`, and `manager.py`, and remove the "Verification Agent may choose" latitude.
3. Specify the `run` and `__main__` exit contract. Use `run(...) -> int` and `sys.exit(run(input, print))`, and state that `quit`, EOF, and Ctrl+C all return 0.
4. Obtain the user's explicit confirmation before overwriting the uncommitted `pyproject.toml`, `README.md`, and `user-stories/` changes, which belong to the earlier csv-summary sample. The Orchestrator should surface this to the user. Consider preserving the old sample on a branch or in a commit.
5. Add a message table and a command-grammar section to the architecture, covering exact strings for every success and error output, the handling of whitespace-only and extra arguments, and the rule for empty input at the main prompt versus an argument prompt.

## Recommendations for Later

- Add a `[project.scripts]` entry (e.g. `todo = "todo.cli:main"`) if packaging ever enters scope.
- Reject or escape control characters in descriptions so the list output cannot be corrupted.
- Add a CI matrix (3.10 and the latest version) if the project is hosted on GitHub.
- Add a property-style test that, over random add and delete sequences, IDs stay strictly increasing and unique.
- Document the Windows Ctrl+Z, Enter behavior in the README.
- Define type aliases for `input_fn` and `output_fn` (`Callable[[str], str]` and `Callable[[str], None]`) to keep mypy strict clean.

## Approval Status
- **Design Review Verdict**: APPROVED WITH CHANGES
