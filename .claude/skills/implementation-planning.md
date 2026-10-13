---
name: implementation-planning
description: Break an approved architecture into an ordered, dependency-aware task list with paired test tasks and a definition of done
---

## Role

Act as a senior engineering lead doing sprint planning. Your job is to turn an approved architecture into an ordered task list that a developer can execute top to bottom without further questions.

---

## Input

- `docs/architecture.md` (required)
- `docs/design-review.md` (required — apply every item under Required Changes)
- `docs/requirements.md` for requirement IDs, if present

---

## Planning Process

1. **Read both input files fully** before planning.
2. **List all implementation tasks** — one task is one cohesive unit of work.
3. **Identify dependencies** — Task B cannot start until Task A is done.
4. **Order tasks by dependency** (topological sort).
5. **Estimate complexity** per task: S / M / L.
6. **Flag blocked tasks** — anything waiting on an external factor.
7. **Pair tests**: every implementation task has a matching test task.
8. **Trace requirements**: map each task to the FR/NFR IDs it satisfies.

---

## Output Format

Write the output to `docs/impl-plan.md` using this exact structure:

````markdown
# Implementation Plan

## Task Table

| ID | Task Name | Description | Depends On | Complexity | File(s) Affected | Requirements |
|---|---|---|---|---|---|---|
| T-01 | [Name] | [What is built] | None | S | `src/pkg/module.py` | FR-1 |
| T-02 | Test [Name] | [What is tested] | T-01 | S | `tests/unit/test_module.py` | FR-1 |

## Dependency Graph

```
[ASCII graph, e.g. T-01 ──► T-02 ──► T-03]
```

## Blocked Tasks

[Task ID, the blocker, and what unblocks it. If none: "None."]

## Definition of Done

- [Checklist for the full implementation, e.g. all tests pass, coverage ≥ 80%, no secrets in code]
````

---

## Quality Criteria

Before finalizing, verify:

- Each task results in runnable, testable code and has a clear definition of done
- Every implementation task is paired with a test task
- No task is larger than one day of focused work
- Task order respects every dependency; every FR appears in at least one task
- No source code is written
