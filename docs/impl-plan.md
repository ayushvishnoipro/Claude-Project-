# Implementation Plan

Source documents: `docs/architecture.md` and `docs/design-review.md` (verdict: APPROVED WITH CHANGES). Required Changes 1, 2, 3 and 5 are resolved in the architecture. Required Change 4 (preserving the uncommitted csv-summary edits) is resolved by Task 0, which is done: the edits were preserved on branch `csv-summary-sample` (commit 60ffcc2).

## Implementation Status (updated after the original doc sync)

| Tasks | Status | Evidence |
|-------|--------|----------|
| 1-14 | Implemented | `src/todo/{__init__,errors,models,manager,cli,__main__}.py`; `tests/unit/{test_errors,test_models,test_manager,test_parse_task_id,test_cli_parser}.py`; `tests/integration/{test_cli_session,test_main_entry}.py`. |
| 0 | Done | The csv-summary edits to `pyproject.toml`, `README.md` and `user-stories/` were preserved on branch `csv-summary-sample` (commit 60ffcc2). |
| 15, 16 | Done | `pyproject.toml` and `README.md` are updated for the to-do app. `pyproject.toml` also has a `[tool.ruff.lint]` ignore for UP006, UP035 and FLY002, because the code deliberately uses `typing.Dict/List/Tuple/Callable`. |
| 17 | Done | Final verification passed on Python 3.13.16: 106 tests, 100% coverage on the gated modules, ruff and mypy clean. Python 3.10 was not available, so it was not run there. |

Implementation notes that resolved ambiguities (details in `docs/architecture.md`):

- Whitespace-only inline `add` argument counts as omitted. This is a natural consequence of stripping the whole line before `line.split(None, 1)`, so `rest` is never whitespace-only.
- `repr` quote style follows Python rules (single quotes by default, double quotes if the text contains a single quote). Tests build expected strings with `{raw!r}`.
- A very long digit string either parses (no integer-conversion limit) or maps to the whole-number error (limit enforced in 3.11+ and 3.10.7+). The test in Task 9 accepts either.
- In `TaskManager._lookup` the `bool` check comes before the range check, so `True` is rejected as a non-integer rather than treated as ID 1.
- `quit` and its aliases are handled in `run` before dispatch; `_dispatch` returns the unknown-command error as ordinary text rather than raising.

## Gating Rule (resolved)

Task 0 was a precondition: until the csv-summary edits were preserved, no task could modify any of these paths. It is done (branch `csv-summary-sample`, commit 60ffcc2), so the gate is lifted:

- `pyproject.toml`
- `README.md`
- anything under `user-stories/`

Only Tasks 15 and 16 touched `pyproject.toml` or `README.md`, and both depended on Task 0. No task in this plan edits `user-stories/`. Tasks 1-14 touch only `src/todo/` and `tests/`, so they did not depend on Task 0.

## Task Breakdown

| ID | Task | Module | Dependencies | Effort | Definition of Done | Files |
|----|------|--------|--------------|--------|-------------------|-------|
| 0 | **PRECONDITION. DONE (branch `csv-summary-sample`, commit 60ffcc2).** Preserve the uncommitted csv-summary edits to `pyproject.toml`, `README.md` and `user-stories/` (including the tracked deletion of `user-stories/user-story-template.md`). The user first chose the method: (a) a separate branch holding a commit of those edits, or (b) a commit of those edits. Then perform it, limited to those three paths. | Repo hygiene | None | S | The user has stated the method. The csv-summary edits to the three paths are recoverable from git history (branch or commit). The commit is scoped to those paths only. The user has confirmed it is done. `git status` shows no uncommitted changes to those paths, or only changes the user expects. Nothing was discarded, reset or force-checked-out. | No files edited. Git operation on `pyproject.toml`, `README.md`, `user-stories/`. |
| 1 | Scaffold the package: create `src/todo/__init__.py` (marks the package, exports nothing) and the `tests/unit/` and `tests/integration/` directories. No `__init__.py` under `tests/`. | Package | None | S | `import todo` works with `pythonpath=src`. Test directories exist. No `__init__.py` under `tests/`. | `src/todo/__init__.py`, `tests/unit/`, `tests/integration/` |
| 2 | Implement `errors.py`: `TaskError` base, `InvalidDescriptionError`, `InvalidIdError`, `TaskNotFoundError`. Each carries a user-presentable message. | Logic | 1 | S | Hierarchy matches the architecture. mypy strict clean. Python 3.10 compatible. | `src/todo/errors.py` |
| 3 | Tests for `errors.py`: hierarchy (all subclasses derive from `TaskError`) and message carrying. | Logic | 2 | S | Tests pass. Module name is unique across `tests/`. | `tests/unit/test_errors.py` |
| 4 | Implement `models.py`: frozen dataclass `Task(id: int, description: str, completed: bool)`. | Logic | 1 | S | Instance is immutable. `dataclasses.replace` works. mypy strict clean. | `src/todo/models.py` |
| 5 | Tests for `models.py`: field values, immutability (assignment raises), `replace` yields a new instance, equality. | Logic | 4 | S | Tests pass. | `tests/unit/test_models.py` |
| 6 | Implement `TaskManager` in `manager.py`: `Dict[int, Task]` store, monotonic `_next_id` starting at 1, `add` (strip, validate, 200 accepted and 201 rejected in code points, internal whitespace preserved), `list_tasks` (sorted by ID, empty list when none), `complete` returning `(Task, changed)`, `delete`. ID checks (shared private `_lookup`) in order: non-`int` or `bool` gives `InvalidIdError("Task ID must be an integer.")`; less than 1 gives `"Task ID must be a positive number."`; unknown ID gives `TaskNotFoundError("Task {id} not found.")`. | Logic | 2, 4 | M | Behaviour matches the Logic layer contract and ID contract exactly, with the exact messages from the architecture. No `input()` or `print()`. mypy strict clean. | `src/todo/manager.py` |
| 7 | Tests for `TaskManager`: add, trim, 200/201 boundary, empty and whitespace-only description, list ordering and empty list, complete (including the `changed=False` no-op), delete, ID non-reuse after delete, `bool` and `str` and `0` and negative IDs, not-found for never-existed and already-deleted IDs, exact exception messages. | Logic | 6 | M | All tests pass. Covers every message in the ID contract that the manager produces. | `tests/unit/test_manager.py` |
| 8 | Implement `parse_task_id(raw: str) -> int` as a public module-level function in `manager.py`. It trims, then requires ASCII digits `0-9` only (`text.isascii() and text.isdigit()`). Value must be at least 1. Leading zeros allowed. Rejects signs, underscores, decimals, exponents, Unicode digits and extra tokens. Maps any `ValueError` during conversion to the "must be a whole number" message (this is what very long digit strings hit on interpreters that enforce the int-conversion limit). Messages: `Task ID cannot be empty.`, `Task ID must be a whole number, got {raw}.` (`{raw}` is the trimmed text via `repr`), `Task ID must be a positive number.` | Logic | 2, 6 (same file, so sequential) | M | Grammar and the three messages match the architecture. Never returns a value below 1. mypy strict clean. | `src/todo/manager.py` |
| 9 | Tests for `parse_task_id`: valid (`"2"`, `" 2 "`, `"007"`), empty and whitespace-only, `"0"` and `"00"`, `"+2"`, `"-2"`, `"2_0"`, `"1.0"`, `"1e3"`, `"2 3"`, Unicode digits (Arabic-Indic, full-width and superscript), very long digit string (accepts either a parsed value or the whole-number error, because the outcome depends on the Python version), control characters shown via `repr`, exact messages. | Logic | 8 | M | All tests pass. | `tests/unit/test_parse_task_id.py` |
| 10 | Implement `cli.py`: type aliases for `input_fn` and `output_fn` (`InputFn`, `OutputFn`); `run(input_fn, output_fn) -> int`; command grammar (strip, split once with `line.split(None, 1)`, case-insensitive matching, aliases `q` and `exit`); argument prompts `Description: ` and `Task ID: ` when `rest` is empty; empty-input rule (ignored at main prompt, validation error at argument prompt, then return to main prompt); `list`, `help` and `quit` ignore any `rest`; unknown-command error using `repr` of the original-case token; list formatting (`format_tasks`); every message from the message table; help text verbatim; `TaskError` becomes `Error: <message>`. A single `try/except (KeyboardInterrupt, EOFError)` wraps the whole loop body and outputs `\nGoodbye!`. `quit` outputs `Goodbye!`. All expected paths return 0. One `output_fn` call per message, with no trailing newline on multi-line outputs. | CLI | 8 | L | Output strings match the message table character for character. Exit contract met. Unexpected exceptions are not caught. mypy strict clean. Python 3.10 compatible. | `src/todo/cli.py` |
| 11 | Unit tests for the command parser and dispatch: case-insensitivity, aliases, `add` with inline, whitespace-only and missing argument, `complete 2 3` is rejected and completes nothing, `list foo` behaves as `list`, unknown command message and token `repr`, blank main-prompt lines produce no output, internal whitespace preserved in descriptions. | CLI | 10 | M | All tests pass. Asserts exact strings. | `tests/unit/test_cli_parser.py` |
| 12 | Integration tests that drive `run` with scripted input and captured output: full add, list, complete, delete session; error continuation (loop keeps going after errors); argument-prompt empty-input path; EOF and `KeyboardInterrupt` raised by fake input at the main prompt, at an argument prompt, and during dispatch (raised from the output function); exit code 0 asserted from the return value; "already completed" path; ID non-reuse seen through the CLI. | CLI | 10 | M | All tests pass. Exit code asserted on each exit path. | `tests/integration/test_cli_session.py` |
| 13 | Implement `__main__.py`: `sys.exit(run(input, print))`. Excluded from coverage with `# pragma: no cover` (does not rely on `pyproject.toml`). | Entry point | 10 | S | `python -m todo` starts the app from the repo root with `src` on the path. | `src/todo/__main__.py` |
| 14 | Smoke test of the entry point: subprocess `python -m todo` with `PYTHONPATH=src`, stdin `add Buy milk` then `list` then `quit`. Asserts the output and exit code 0. Also checks that EOF-only stdin exits 0 with no traceback. | Entry point | 13 | S | Test passes on Windows. Unique module name. | `tests/integration/test_main_entry.py` |
| 15 | **Update `pyproject.toml`** (DONE) per the architecture's adjustments table: name and description to the to-do app; `requires-python` to `>=3.10`; ruff `target-version` to `py310`; mypy `python_version` to `3.10`; coverage `source` to `["todo"]`; remove `fail_under` (or set it to 0); remove the pytest `addopts` and the `slow` marker; keep `pythonpath=["src"]`, `testpaths`, pytest-cov, ruff and mypy settings. Verify the `readme` field. Also added a `[tool.ruff.lint]` ignore for UP006, UP035 and FLY002 (the code deliberately uses `typing.Dict/List/Tuple/Callable`). | Config | **0** (done) | M | Only the listed settings change. `python -m pytest` still collects `tests/`. The coverage gate command is the only enforced threshold. | `pyproject.toml` |
| 16 | **Update `README.md`** (DONE) for the to-do app: how to run (`PYTHONPATH=src python -m todo` or `pip install -e .`), command list, and the Windows end-of-input note (Ctrl+Z then Enter). Replace the csv-summary content. | Docs | **0** (done), 13 | S | README describes the to-do app accurately and matches the help text. No csv-summary content remains. | `README.md` |
| 17 | Pre-verification self-check (DONE: passed on Python 3.13.16, 106 tests, 100% on the gated modules, ruff and mypy clean; Python 3.10 was not available), run only after the config is updated: `ruff check src`, `mypy --strict src` (or the configured equivalent), the full `python -m pytest`, and then the exact coverage gate command: `python -m pytest --cov=todo.manager --cov=todo.models --cov=todo.errors --cov-report=term-missing --cov-fail-under=90`. Record the Python version used. Also run on 3.10 if it is available. Do not change the command, modules or threshold. | QA | 3, 5, 7, 9, 11, 12, 14, 15 | M | ruff and mypy clean on `src/`. All tests pass. The gate command exits 0. Interpreter version noted, with a flag if it was not 3.10 while 3.10 is available. A failure is surfaced, not worked around. | No new files. Results are reported to the orchestrator. |

## Execution Order

1. Task 0 (user decision and preservation) and Task 1 (scaffold) could start at once. They are independent. Both are done.
2. Tasks 2 and 4 (parallel) depend on Task 1.
3. Tasks 3 and 5 (parallel) depend on Tasks 2 and 4 respectively. Task 6 depends on Tasks 2 and 4.
4. Task 7 depends on Task 6. Task 8 depends on Task 6. They can proceed in parallel only if the test author works from the contract; both edit different files.
5. Task 9 depends on Task 8. Task 10 depends on Task 8.
6. Tasks 11, 12 and 13 (parallel) depend on Task 10.
7. Task 14 depends on Task 13.
8. Task 15 depends on Task 0 only. Task 16 needs Tasks 0 and 13. Both are done.
9. Task 17 depends on Tasks 3, 5, 7, 9, 11, 12, 14 and 15. It is done.

Source and test work (Tasks 1-14) did not wait for Task 0. All tasks, 0 through 17, are now complete.

## Dependencies Graph

```
0 (user decision + preserve csv-summary edits) ---+--------------------> 15 (pyproject.toml) --------+
                                                  |                                                  |
                                                  +--> 16 (README.md) <------ 13                     |
                                                                                                     v
1 -> 2 -> 3                                                                                          |
1 -> 4 -> 5                                                                                          |
2,4 -> 6 -> 7                                                                                        |
2,6 -> 8 -> 9                                                                                        |
8 -> 10 -> 11                                                                                        |
10 -> 12                                                                                             |
10 -> 13 -> 14                                                                                       |
3,5,7,9,11,12,14,15 ---------------------------------------------------------------------------> 17 (self-check)
```

Critical path: 1 -> 2 -> 6 -> 8 -> 10 -> 13 -> 14 -> 17. Task 0 is done, so it no longer gates 15 and 17.

## Testing Strategy

- Unit tests are paired with each logic module: `test_errors.py`, `test_models.py`, `test_manager.py`, `test_parse_task_id.py`, `test_cli_parser.py`.
- Integration tests drive `cli.run` with scripted input and captured output (`test_cli_session.py`). They assert on exit codes returned by `run`, not on `sys.exit`.
- An entry-point smoke test (`test_main_entry.py`) runs `python -m todo` in a subprocess.
- All test module basenames are unique across `tests/`. No `__init__.py` is added under `tests/`.
- Assertions use the exact strings from the message table. Strings that embed user text via `repr` are built with `{raw!r}` in the test so they stay correct regardless of quote style.
- The one coverage gate is the exact command in Task 17: at least 90% on `todo.manager`, `todo.models` and `todo.errors` combined. CLI coverage is informational only.
- Optional, from the design review's later recommendations: a property-style test that IDs stay unique and strictly increasing across random add and delete sequences. It would go in `tests/unit/test_manager.py` and needs no new dependency unless hypothesis is used (do not add it without approval).

## Risk Mitigation

- **Loss of csv-summary edits (highest risk). Resolved.** Task 0 was a hard precondition for Tasks 15 and 16. The edits were preserved on branch `csv-summary-sample` (commit 60ffcc2), scoped to the three paths only. The approach to follow for any similar case: do not use `git checkout`, `git restore`, `git reset --hard` or `git stash drop` on them, and check afterwards that the edits are recoverable. The commit method also includes the tracked deletion of `user-stories/user-story-template.md`. The unrelated uncommitted items (`docs/changelog.md`, `plan/`, `.mcp.json`, new `docs/` files) are outside this constraint and should not be swept into that commit unless the user wants them to be.
- **Method not yet chosen. Resolved.** The plan did not pick between branch and commit; the user chose, and the preservation was done on a separate branch (`csv-summary-sample`).
- **Interim config mismatch. Resolved.** Before Task 15, `pyproject.toml` had a `csv_summary` coverage source, `fail_under = 80`, `-m 'not slow'` addopts and py311 targets, so any earlier test or lint run was provisional. Task 15 is done and the Task 17 run, done after it, is the gate result. Explicit `--cov=` flags in the gate command mean coverage measurement does not depend on the old `source`, and Task 15 removed the `fail_under = 80` that would have added a second threshold.
- **`__main__.py` coverage exclusion** uses `# pragma: no cover` so it does not depend on `pyproject.toml`. It is also outside the measured modules.
- **Python 3.10 compatibility.** Avoid `tomllib`, `typing.Self`, `StrEnum` and `match` statements are allowed in 3.10 but not needed. Task 17 reports the interpreter version, and runs on 3.10 if available (it was not available; the run used 3.13.16). Long-digit-string behaviour differs by interpreter version (see Implementation Status); the test accepts both outcomes.
- **Pytest basename collisions** are avoided by the required unique module names.
- **Windows specifics.** The Ctrl+Z note is in the help text (Task 10) and the README (Task 16). The subprocess smoke test (Task 14) uses `sys.executable` and an explicit `PYTHONPATH`.
- **Message-string drift.** Tests assert the exact strings from the architecture. If an implementation task finds an ambiguity, it should be raised with the orchestrator and not resolved silently.
- No external services or third-party dependencies are needed. Nothing is blocked.

## Estimated Timeline

- Totals: 9 small tasks (0, 1, 2, 3, 4, 5, 13, 14, 16), 7 medium tasks (6, 7, 8, 9, 11, 12, 15, 17 counted below), and 1 large task (10).
  - Exact count: 9 S (0, 1, 2, 3, 4, 5, 13, 14, 16), 8 M (6, 7, 8, 9, 11, 12, 15, 17), 1 L (10). Total 18 tasks.
- The critical path is 8 tasks (1, 2, 6, 8, 10, 13, 14, 17), roughly one L, three M and four S tasks. Several branches (3, 5, 7, 9, 11, 12) can run in parallel with it.
- All 18 tasks are complete.
