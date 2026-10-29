# Phase 6 — Sample User Story & End-to-End Test

## Goal
Validate the entire pipeline works by running it against a concrete, well-defined Python project user story. This phase produces the first real output from all 9 agents and confirms the orchestrator drives them correctly from start to PR.

---

## Prerequisites
- All previous phases complete (Phases 1–5)
- Git repository initialized with a remote on GitHub (needed for `gh pr create` in the PR agent)
- `gh` CLI authenticated: `gh auth status`
- `pytest` available in the environment
- Python 3.11+ and `pip` available (the app installs `streamlit` as its one runtime dependency)

---

## Step 6.1 — Create the Sample User Story

Create `user-stories/user-story-template.md` (template/example) and `user-stories/user-story-1.md` (the file the pipeline processes) with a complete, realistic Python user story that is:
- Simple enough to implement in a single session
- Complex enough to exercise all pipeline stages meaningfully
- Self-contained (no external APIs or services required)

**Recommended story — Streamlit Todo App:**

```markdown
# User Story: Streamlit Todo App

**As a** busy professional,  
**I want** a small web-based todo app built with Python and Streamlit that stores my tasks locally,  
**So that** I can add, view, complete, edit, and delete tasks in my browser without any account or external service.

## Details
- The app is a Python application built with Streamlit, started from the command line: `streamlit run src/todo_app/app.py`
- The page shows:
  - A title and a summary line, e.g. "2 of 5 tasks completed"
  - An "Add task" form: a text input and an "Add" button
  - A filter control with three options: All, Open, Done (default: All)
  - The task list, ordered by ID ascending. Each task row shows a checkbox (checked = done), the title, an "Edit" control, and a "Delete" button
  - A "Clear completed" button that removes all done tasks
- Adding a task:
  - The title is trimmed of leading and trailing whitespace
  - An empty, whitespace-only, or over-200-character title is rejected with a visible error message and no task is created
  - On success the input is cleared and the new task appears as open
- Toggling the checkbox marks a task done (recording a completion time) or open again (clearing it)
- Editing a task changes its title, using the same validation as adding
- Deleting a task removes it; task IDs are positive integers, assigned incrementally and never reused, even after deletion
- If there are no tasks (or none match the current filter), the page shows "No tasks found"
- Tasks are stored in a local JSON file:
  - Default location: `~/.todo_app.json`; overridable with the `TODO_FILE` environment variable
  - The file is created on the first change if it does not exist
  - Format: `{"version": 1, "next_id": <int>, "tasks": [ ... ]}` where each task has `id`, `title`, `done`, `created_at`, `completed_at`
  - Writes are atomic (write to a temp file in the same directory, then replace) so a crash never leaves a half-written file
  - UTF-8 encoding, so non-ASCII titles work
- If the JSON file is corrupted, unreadable, or has an unsupported version, the page shows a clear error message and stops; the file is never overwritten or repaired automatically
- Data persists across browser refreshes and app restarts
- Code structure: business logic (models, validation, storage) lives in modules separate from the Streamlit UI so it can be tested without a browser
- Python 3.11+; `streamlit` is the only runtime dependency and must be pinned to an exact version; `pytest` and `pytest-cov` are dev-only
- Must run on Windows, Linux, and macOS (use `pathlib`, no OS-specific code)
- Not designed for multiple simultaneous users or processes writing the same file (documented limitation, not an error)

## Acceptance Criteria
1. Given a valid title, adding a task creates an open task that appears in the list
2. Given an empty, whitespace-only, or over-200-character title, the app shows an error and creates no task
3. Ticking a task's checkbox marks it done and records a completion time; unticking reopens it and clears the time
4. Editing a task with a valid title updates it; an invalid title shows an error and leaves the task unchanged
5. Deleting a task removes it from the list and the file
6. IDs are never reused after a task is deleted
7. The filter shows only open tasks, only done tasks, or all tasks as selected
8. "Clear completed" removes only done tasks
9. With no tasks (or none matching the filter), the page shows "No tasks found"
10. The summary line shows the correct completed/total counts after every change
11. Tasks persist between app restarts (read from and written to the JSON file)
12. `TODO_FILE` overrides the default storage location
13. A corrupted JSON file shows a clear error, stops the app, and leaves the file unmodified
14. Non-ASCII titles (e.g. "Café ☕") are stored and displayed correctly
15. The app starts without errors using `streamlit run src/todo_app/app.py`
```

---

## Step 6.2 — Prepare the Environment

Before running the pipeline:

```bash
# Confirm gh CLI is authenticated
gh auth status

# Confirm pytest is available
pytest --version

# Confirm the repo has a remote set
git remote -v

# If no remote, add one:
git remote add origin https://github.com/<your-username>/automated-documentation-sync.git
git push -u origin main
```

If you ran an earlier story, clear its artifacts first. The orchestrator skips any step whose output file already exists:

```bash
rm -f docs/requirements.md docs/architecture.md docs/design-review.md docs/impl-plan.md
rm -rf src/* tests/unit/* tests/integration/* output/reports/* output/test-results/*
# Keep docs/changelog.md and all .gitkeep files
```

---

## Step 6.3 — Run the Pipeline

Start the orchestrator as the main-session agent (subagents cannot spawn subagents), then give it the story:

```
claude --agent orchestrator
process user-stories/user-story-1.md
```

### Expected interaction flow:

**Step 1 — Requirements (L1)**
- Orchestrator spawns requirements agent (Mode A: returns questions, writes nothing)
- Agent reads the user story, identifies any ambiguities, returns clarifying questions via the orchestrator
- You answer (e.g., "Streamlit 1.x pinned, no other runtime deps", "use `st.session_state` for UI state", "JSON storage only")
- Orchestrator re-spawns the agent with your answers (Mode B); agent writes `docs/requirements.md`
- Orchestrator gates on the file and proceeds

**Step 2 — Architecture (L1)**
- Orchestrator spawns architecture agent (Mode A: proposal + questions)
- Agent reads requirements, proposes a Python module structure (e.g., `models.py`, `storage.py`, `app.py`) and how the Streamlit UI calls the logic layer
- You may approve or ask for adjustments (e.g., "use `st.form` for the add task input", "keep `app.py` under 150 lines")
- Agent writes `docs/architecture.md` (Mode B)
- Orchestrator gates and proceeds

**Step 3 — Design Review (L2)**
- Agent runs, writes `docs/design-review.md`
- Orchestrator shows the review (risks, decisions, required changes), such as Streamlit's rerun-on-every-interaction model and session state handling
- You type `y` to continue

**Step 4 — Implementation Planning (L2)**
- Agent runs, writes `docs/impl-plan.md`
- Orchestrator shows the task table
- You type `y` to continue

**Step 5 — Implementation (L2)**
- Agent runs, writes `src/todo_app/__init__.py`, `src/todo_app/models.py`, `src/todo_app/storage.py`, `src/todo_app/app.py`, etc.
- Agent writes `tests/unit/test_models.py`, `tests/unit/test_storage.py`, `tests/integration/test_app.py` (UI tests using Streamlit's `AppTest`)
- Agent runs pytest, reports results
- Orchestrator shows file list and test summary
- You type `y` to continue

**Step 6 — Documentation Sync (L2)**
- Agent scans `src/`, updates any docs that diverged
- Orchestrator shows sync report
- You type `y` to continue

**Step 7 — Code Review (L2)**
- Agent reviews all Python files against requirements
- Orchestrator shows the review report with findings and recommendation
- You type `y` to continue (or `n` to pause and fix issues)

**Step 8 — Verification (L2)**
- Agent runs full test suite + coverage
- Orchestrator shows the results.md with PASS/FAIL verdict
- You type `y` to continue to PR

**Step 9 — PR (L3)**
- Agent generates full PR description draft (draft mode, nothing created)
- Orchestrator shows the draft
- You type `y` to confirm
- Agent runs `gh pr create` (create mode)
- Orchestrator displays the PR URL

---

## Step 6.4 — Validate Artifacts

After the pipeline completes, check each artifact:

### docs/ artifacts
- [ ] `docs/requirements.md` — has Functional Requirements, Non-Functional Requirements, Acceptance Criteria sections
- [ ] `docs/architecture.md` — has Component Diagram, Technology Choices, Data Flow
- [ ] `docs/design-review.md` — has Risk Table, Design Decisions, Required Changes
- [ ] `docs/impl-plan.md` — has ordered task table with dependencies
- [ ] `docs/changelog.md` — has one entry per completed step with timestamps

### src/ artifacts
- [ ] At least 3 Python source files in `src/`
- [ ] All files have type hints
- [ ] No hardcoded secrets or credentials
- [ ] Business logic (`models.py`, `storage.py`) does not import Streamlit
- [ ] `streamlit` is pinned to an exact version in `pyproject.toml`
- [ ] `pip install -e .` then `streamlit run src/todo_app/app.py` opens the app in the browser
- [ ] Manual check: add a task, tick it, edit it, filter it, delete it, restart the app, confirm data persisted

### tests/ artifacts
- [ ] Unit tests in `tests/unit/`
- [ ] Integration tests in `tests/integration/` (Streamlit `AppTest`)
- [ ] `pytest tests/ -v` passes with 0 failures

### output/ artifacts
- [ ] `output/reports/doc-sync-report.md` exists
- [ ] `output/reports/code-review.md` has an Overall Recommendation
- [ ] `output/test-results/results.md` has Final Verdict: PASS and maps all 15 acceptance criteria to tests

### GitHub
- [ ] PR exists with all 5 required sections (Summary, Changes Made, Test Evidence, Known Limitations, Reviewer Checklist)
- [ ] PR description ends with the attribution line: `Generated by the agentic SDLC pipeline (Claude Code)`

---

## Step 6.5 — Final Commit

If any pipeline run outputs were not auto-committed by the agents, commit them:

```bash
git add docs/ src/ tests/ pyproject.toml user-stories/
git commit -m "feat: run agentic pipeline on Streamlit todo app user story"
```

`output/` is gitignored by design, so reports and test results are not committed.

---

## Deliverables Checklist
- [ ] `user-stories/user-story-1.md` created with the Streamlit todo story (and `user-story-template.md` kept as the template)
- [ ] Full pipeline run completed without manual intervention beyond L1/L2/L3 interaction points
- [ ] All 9 artifact files validated
- [ ] `pytest tests/ -v` passes
- [ ] The app runs with `streamlit run src/todo_app/app.py`
- [ ] GitHub PR created with correct description
- [ ] All artifacts committed

---

## Troubleshooting

| Problem | Likely cause | Fix |
|---|---|---|
| Gate fails on `docs/requirements.md` | Requirements agent returned early | Ask the orchestrator to retry Step 1 |
| Orchestrator skips Steps 1–2 | Old `docs/requirements.md` / `architecture.md` still present | Delete stale artifacts (Step 6.2) or confirm the skip was intended |
| Orchestrator cannot spawn agents | Started with plain `claude` or run as a subagent | Start with `claude --agent orchestrator` |
| `gh pr create` fails | No GitHub remote or not authenticated | Run `gh auth login`, set remote, push the branch |
| `ModuleNotFoundError: streamlit` | Dependencies not installed | `pip install -e .[dev]` |
| `ModuleNotFoundError: todo_app` when running tests | Package not installed or `src/` not on path | `pip install -e .` or set `pythonpath = ["src"]` in pytest config |
| `AppTest` tests fail on import | Streamlit version too old for `streamlit.testing.v1` | Pin Streamlit 1.28 or newer |
| pytest fails | Implementation agent missed a case | Re-run the implementation step with the failing test as context |
| Hook script permission denied | Scripts not executable | `chmod +x .claude/hooks/*.sh` |
| Coverage < 80% | Tests incomplete | Add tests manually or re-run verification agent |

---

## Success Definition
The pipeline is considered complete when:
1. A user story dropped into `user-stories/` can be processed to a merged (or mergeable) PR by running the orchestrator once
2. All 9 specialist agents run without being invoked directly by the user
3. Human interaction is limited to: answering L1 questions, approving L2 steps, and confirming the L3 PR
4. The generated Streamlit todo app launches and satisfies all 15 acceptance criteria