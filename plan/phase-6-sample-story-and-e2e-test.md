# Phase 6 — Sample User Story & End-to-End Test

## Goal
Validate the entire pipeline works by running it against a concrete, well-defined Python project user story. This phase produces the first real output from all 9 agents and confirms the orchestrator drives them correctly from start to PR.

---

## Prerequisites
- All previous phases complete (Phases 1–5)
- Git repository initialized with a remote on GitHub (needed for `gh pr create` in the PR agent)
- `gh` CLI authenticated: `gh auth status`
- `pytest` available in the environment

---

## Step 6.1 — Create the Sample User Story

Create `user-stories/user-story-template.md` with a complete, realistic Python user story that is:
- Simple enough to implement in a single session
- Complex enough to exercise all pipeline stages meaningfully
- Self-contained (no external APIs or services required)

**Recommended story — CSV Summary CLI Tool:**

```markdown
# User Story: CSV Summary Report Generator

**As a** data analyst,  
**I want** a CLI tool that reads a CSV file and outputs a summary report,  
**So that** I can quickly understand the shape and content of any dataset without writing custom scripts.

## Details
- The tool is invoked from the command line: `python -m csv_summary <path-to-csv>`
- It reads the CSV file and produces a summary report printed to stdout
- The report must include:
  - Total row count (excluding header)
  - Column names and their inferred data types (numeric, text, date)
  - For numeric columns: min, max, mean, and count of null values
  - For text columns: count of unique values and count of null values
  - For date columns: earliest and latest date and count of null values
- If the file does not exist, print a clear error and exit with code 1
- If the file is empty or has only a header row, print a message and exit with code 0
- The tool must handle CSV files up to 100MB without running out of memory

## Acceptance Criteria
1. Given a valid CSV, the tool prints a summary report to stdout
2. Given a non-existent file path, the tool prints an error and exits with code 1
3. Given a CSV with only a header row, the tool prints "No data rows found" and exits with code 0
4. Numeric columns show min, max, mean, and null count
5. Text columns show unique count and null count
6. Date columns (ISO 8601 format) show earliest, latest, and null count
7. The tool processes a 100MB CSV file without exceeding 512MB memory usage
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

---

## Step 6.3 — Run the Pipeline

Open Claude Code in the project directory and invoke the orchestrator:

```
@orchestrator process user-stories/user-story-template.md
```

### Expected interaction flow:

**Step 1 — Requirements (L1)**
- Orchestrator spawns requirements agent
- Agent reads the user story, identifies any ambiguities, asks clarifying questions
- You answer (e.g., "use pandas for CSV reading", "output format is plain text, not JSON")
- Agent writes `docs/requirements.md`
- Orchestrator gates on the file and proceeds

**Step 2 — Architecture (L1)**
- Orchestrator spawns architecture agent
- Agent reads requirements, proposes a Python module structure
- You may approve or ask for adjustments (e.g., "use argparse not click")
- Agent writes `docs/architecture.md`
- Orchestrator gates and proceeds

**Step 3 — Design Review (L2)**
- Agent runs, writes `docs/design-review.md`
- Orchestrator shows the review (risks, decisions, required changes)
- You type `y` to continue

**Step 4 — Implementation Planning (L2)**
- Agent runs, writes `docs/impl-plan.md`
- Orchestrator shows the task table
- You type `y` to continue

**Step 5 — Implementation (L2)**
- Agent runs, writes `src/csv_summary/__init__.py`, `src/csv_summary/cli.py`, `src/csv_summary/analyzer.py`, etc.
- Agent writes `tests/unit/test_analyzer.py`, `tests/integration/test_cli.py`
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
- Agent generates full PR description draft
- Orchestrator shows the draft
- You type `y` to confirm
- Agent runs `gh pr create`
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
- [ ] `python -m csv_summary --help` works

### tests/ artifacts
- [ ] Unit tests in `tests/unit/`
- [ ] Integration tests in `tests/integration/`
- [ ] `pytest tests/ -v` passes with 0 failures

### output/ artifacts
- [ ] `output/reports/doc-sync-report.md` exists
- [ ] `output/reports/code-review.md` has an Overall Recommendation
- [ ] `output/test-results/results.md` has Final Verdict: PASS

### GitHub
- [ ] PR exists with all 5 required sections (Summary, Changes Made, Test Evidence, Known Limitations, Reviewer Checklist)
- [ ] PR description ends with the attribution line

---

## Step 6.5 — Final Commit

If any pipeline run outputs were not auto-committed by the agents, commit them:

```bash
git add docs/ src/ tests/ output/
git commit -m "feat: run agentic pipeline on CSV summary user story"
```

---

## Deliverables Checklist
- [ ] `user-stories/user-story-template.md` created with the CSV Summary story
- [ ] Full pipeline run completed without manual intervention beyond L1/L2/L3 interaction points
- [ ] All 9 artifact files validated
- [ ] `pytest tests/ -v` passes
- [ ] GitHub PR created with correct description
- [ ] All artifacts committed

---

## Troubleshooting

| Problem | Likely cause | Fix |
|---|---|---|
| Gate fails on `docs/requirements.md` | Requirements agent returned early | Re-invoke: `@orchestrator resume step 1` |
| `gh pr create` fails | No GitHub remote or not authenticated | Run `gh auth login`, set remote |
| pytest fails | Implementation agent missed a case | Run `@implementation` with the failing test as context |
| Hook script permission denied | Scripts not executable | `chmod +x .claude/hooks/*.sh` |
| Coverage < 80% | Tests incomplete | Add tests manually or re-run verification agent |

---

## Success Definition
The pipeline is considered complete when:
1. A user story dropped into `user-stories/` can be processed to a merged (or mergeable) PR by invoking `@orchestrator` once
2. All 9 specialist agents run without being invoked directly by the user
3. Human interaction is limited to: answering L1 questions, approving L2 steps, and confirming the L3 PR
