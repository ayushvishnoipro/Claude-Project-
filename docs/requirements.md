# Requirements

Source: `user-stories/user-story-1.md` (US-001: Simple Python To-Do App). All clarifying questions were resolved by the user accepting the proposed defaults.

## Functional Requirements
- FR-1 Add task: The user can add a task with a text description. The system assigns a unique integer ID, sequential from 1 and never reused within a session. New tasks start as pending.
- FR-2 Description validation: Leading and trailing whitespace is trimmed. Empty or whitespace-only descriptions are rejected with an error message. Descriptions longer than 200 characters are rejected. Duplicate descriptions are allowed.
- FR-3 View tasks: The user can list all tasks in ID order. Each line shows the ID, a status marker (`[ ]` pending or `[x]` completed), and the description. There is no filtering. An empty list prints "No tasks."
- FR-4 Complete task: The user can mark a task as completed by ID. Completing an already completed task is a no-op with an informational message. Tasks cannot be marked pending again.
- FR-5 Delete task: The user can delete a task by ID. There is no confirmation prompt. IDs of deleted tasks are not reused.
- FR-6 Invalid ID handling: Non-numeric input, nonexistent IDs, zero or negative numbers, and empty input each produce a clear error message. The app continues running and never crashes or exits.
- FR-7 CLI: The app is an interactive menu or command loop with commands for add, list, complete, delete, and quit.
- FR-8 Clean exit: Ctrl+C and EOF (Ctrl+D or Ctrl+Z) exit cleanly with a goodbye message and no traceback.
- FR-9 Storage: Tasks are held in memory only. All data is lost on exit.
- FR-10 Unit tests: Unit tests cover all core operations (add, list, complete, delete), including the invalid-ID and invalid-description paths.

## Non-Functional Requirements
- Language and runtime: Python 3.10 or later, standard library only at runtime.
- Modularity and simplicity: Task-management logic (pure, no I/O) is separate from the CLI layer (input parsing and printing). Both live under `src/`. The implementation stays simple. Detailed design is deferred to the architecture phase.
- Test framework: pytest, unless `pyproject.toml` already specifies another. In that case, defer to it.
- Performance: Not a concern at this scale.
- Security and compliance: No requirements beyond basic input sanitization. No logging is required.
- Dependencies: No database, no external APIs, and no network access.

## User Roles and Workflows
- Role: A single end user running the app locally from a terminal. There are no accounts or multi-user concerns.
- Workflow: Start the app, then repeatedly choose a command (add, list, complete, delete) until the user quits (quit command, Ctrl+C, or EOF).
- Add: enter a description, then see a confirmation with the new ID.
- List: view all tasks with IDs and status markers.
- Complete or delete: enter an ID, then see a confirmation or an error message. The loop continues either way.

## Constraints and Assumptions
- Use Python with a command-line interface.
- Tasks live in memory only. One interactive session is the lifetime of the data. Subcommand-style one-shot invocation is not used, because it would lose state between runs.
- A task has three fields: integer ID, text description, and completed flag.
- Source goes in `src/` and tests in `tests/`, per the project conventions.

## Acceptance Criteria
1. A task can be added, and it appears in the list as pending with a unique sequential ID.
2. The list shows all tasks with ID, status marker, and description. An empty list prints "No tasks."
3. A task can be marked completed, and the list reflects it.
4. A task can be deleted and no longer appears in the list. Its ID is not reused.
5. Invalid IDs (non-numeric, nonexistent, zero or negative, empty) and invalid descriptions (empty, whitespace-only, over 200 characters) produce clear error messages without crashing.
6. Ctrl+C and EOF exit cleanly with no traceback.
7. Unit tests cover add, list, complete, and delete, including the invalid paths. Line coverage on the logic layer is at least 90%. CLI-layer tests are optional, and a few I/O-mocked tests are welcome.
8. All tests pass.
9. The app has no runtime dependencies beyond the standard library, and it uses no database, files, or network.

## Out of Scope
- Persistence (files or databases) and export or import
- Network or API access
- GUI or web interface
- Multi-user support
- Task editing
- Un-completing a task
- Due dates, priorities, and categories
- Search and filtering
- Undo
- Delete confirmation
- Packaging or distribution
