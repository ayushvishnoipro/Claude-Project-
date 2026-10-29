# To-Do App

A simple command-line to-do app. Tasks live in memory for the length of one session and are lost when the app exits. It uses only the Python standard library and needs Python 3.10 or higher.

## Running

From the repository root, run it without installing:

```bash
PYTHONPATH=src python -m todo
```

On Windows PowerShell:

```powershell
$env:PYTHONPATH = "src"; python -m todo
```

Or install it in editable mode and run it from anywhere:

```bash
pip install -e .
python -m todo
```

## Commands

Commands are case-insensitive. `add`, `complete` and `delete` take an inline argument, or prompt for it if you leave it out.

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

Example session:

```
> add Buy milk
Added task 1: Buy milk
> complete 1
Completed task 1.
> list
1. [x] Buy milk
> quit
Goodbye!
```

Notes:

- Descriptions are trimmed and limited to 200 characters.
- Task IDs are positive whole numbers and are never reused after a delete.
- Errors are printed as `Error: <message>` and the app keeps running.
- Press Ctrl+C or send end-of-input to exit cleanly. On Linux and macOS, end-of-input is Ctrl+D. On Windows it is Ctrl+Z then Enter.

## Development

```bash
pip install -e ".[dev]"
python -m pytest
ruff check src
mypy --strict src
```

The coverage gate covers the logic layer (90% minimum):

```bash
python -m pytest --cov=todo.manager --cov=todo.models --cov=todo.errors --cov-report=term-missing --cov-fail-under=90
```

## Layout

```
src/todo/
  models.py    Task dataclass
  errors.py    Exception hierarchy
  manager.py   TaskManager and parse_task_id
  cli.py       Command loop and output formatting
  __main__.py  Entry point (python -m todo)
tests/
  unit/        Logic and parser tests
  integration/ Scripted sessions and entry-point smoke test
```
