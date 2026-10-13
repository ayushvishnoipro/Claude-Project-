---
name: implementation-planning
description: Method for breaking an approved architecture into an ordered, dependency-aware task list in docs/impl-plan.md. Use when planning implementation work.
---

# Implementation Planning

## Role
Act as a senior engineering lead doing sprint planning.

## Input
- `docs/architecture.md`
- `docs/design-review.md` (apply every item under Required Changes)

## Planning Process
1. List all implementation tasks. One task is one cohesive unit of work.
2. Identify dependencies between tasks (Task B cannot start until Task A is done).
3. Order tasks by dependency (topological sort).
4. Estimate complexity per task: S / M / L.
5. Flag tasks blocked on external factors.
6. Map each task to the FR/NFR IDs it satisfies.

## Output Format (`docs/impl-plan.md`)
1. **Task table**: ID | Task Name | Description | Depends On | Complexity | File(s) Affected | Requirement IDs
2. **Dependency graph**: ASCII.
3. **Blocked tasks**: section listing the blocker, or "None".
4. **Definition of Done** for the full implementation.

## Rules
- Each task results in runnable, testable code.
- Every implementation task is paired with a test task.
- No task is larger than one day of focused work.
- Never write source code.
