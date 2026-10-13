# Agentic SDLC Pipeline — Claude Code Instructions

## Project Overview

This project is an automated, agent-driven Software Development Lifecycle (SDLC) pipeline built natively on Claude Code. It accepts a Python project user story and drives it end-to-end — from requirements elicitation through architecture, implementation, code review, testing, and a GitHub PR — entirely via Claude specialist agents orchestrated by a single controller. You interact only with the orchestrator; it manages all subagents internally.

---

## How to Run the Pipeline

Invoke the orchestrator with a user story file:

```
@orchestrator process user-stories/<filename>.md
```

Example:
```
@orchestrator process user-stories/user-story-1.md
```

You never invoke subagents directly. The orchestrator handles sequencing, gating, and interaction with you at each step.

---

## Pipeline Phases (Agent Order)

1. **Requirements Agent** (L1 — Interactive) — Reads the user story, asks clarifying questions, and produces `docs/requirements.md`
2. **Architecture Agent** (L1 — Interactive) — Proposes system design based on requirements; produces `docs/architecture.md`
3. **Design Review Agent** (L2 — Run + Approve) — Reviews architecture for risks and gaps; produces `docs/design-review.md`
4. **Implementation Planner Agent** (L2 — Run + Approve) — Breaks down work into a dependency-ordered task list; produces `docs/impl-plan.md`
5. **Implementation Agent** (L2 — Run + Approve) — Writes Python source code and tests; populates `src/` and `tests/`
6. **Documentation Sync Agent** (L2 — Run + Approve) — Updates all `docs/` files to reflect the actual implementation
7. **Code Review Agent** (L2 — Run + Approve) — Reviews code for correctness, security, and quality; produces `output/reports/code-review.md`
8. **Verification Agent** (L2 — Run + Approve) — Runs tests and quality gates; produces `output/test-results/results.md`
9. **PR Agent** (L3 — Explicit Approve) — Drafts and creates a GitHub Pull Request after your explicit confirmation

---

## Interaction Levels

| Level | Applies To | Behavior |
|---|---|---|
| L1 — Deep Interactive | Requirements, Architecture | Agent asks clarifying questions; you answer; it iterates until you approve the output |
| L2 — Run + Approve | Design Review, Impl Planner, Implementation, Doc Sync, Code Review, Verification | Agent runs autonomously, shows output, orchestrator waits for your "y/n" before proceeding to the next step |
| L3 — Explicit Approve | PR | Orchestrator shows full PR draft; only creates the PR after your explicit confirmation |

---

## File Conventions

| Artifact | Location | Created By |
|---|---|---|
| User stories | `user-stories/user-story-N.md` | You (human) |
| Requirements | `docs/requirements.md` | Requirements Agent |
| Architecture | `docs/architecture.md` | Architecture Agent |
| Design review | `docs/design-review.md` | Design Review Agent |
| Implementation plan | `docs/impl-plan.md` | Implementation Planner Agent |
| Source code | `src/**/*.py` | Implementation Agent |
| Tests | `tests/**/*.py` | Implementation Agent |
| Code review report | `output/reports/code-review.md` | Code Review Agent |
| Test results | `output/test-results/results.md` | Verification Agent |
| Run log | `docs/changelog.md` | Orchestrator (appended each run) |

User story files must be named `user-story-N.md` where N is an integer (e.g., `user-story-1.md`).

---

## Do Not

- **Never invoke subagents directly** — always go through the orchestrator
- **Never skip gating checks** — each agent's output file must exist and be non-empty before the next agent runs
- **Never create the GitHub PR without explicit user confirmation** — the PR agent is L3 only
- **Never overwrite `docs/changelog.md`** — only append new entries; never truncate
- **Never proceed past a failed verification gate** — surface the error and stop; do not auto-fix silently
