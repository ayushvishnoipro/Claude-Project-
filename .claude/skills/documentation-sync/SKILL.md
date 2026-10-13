---
name: documentation-sync
description: Method for keeping docs/ files in sync with the implemented source code and writing a sync report. Use after implementation to update docs that diverged from src/.
---

# Documentation Sync

## Role
Act as a technical writer reviewing code changes.

## Input
- `src/` directory contents
- Existing `docs/*.md` files

## Sync Process
1. Diff the current code against what the docs describe.
2. Identify: new functions or classes not documented, removed ones still referenced, changed signatures, new dependencies.
3. Update the affected sections in the relevant docs file in place.
4. Leave sections that are still accurate untouched.
5. If the implementation deviates from `docs/architecture.md`, flag it clearly in the report.

## Output
- In-place updates to the affected `docs/*.md` files.
- A sync report at `output/reports/doc-sync-report.md` listing every change: file, section, what changed and why. If nothing changed, say so.

## Rules
- Never delete documented design decisions, only update them.
- Mark deprecated items as `[DEPRECATED]` rather than deleting them.
- Keep docs concise. Do not pad with obvious information.
- Do not edit `docs/changelog.md`; only the orchestrator writes it.
- Never print secret values.
