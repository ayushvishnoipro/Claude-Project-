---
name: code-review
description: Structured 8-area code review checklist producing output/reports/code-review.md. Use when reviewing src/ and tests/ against docs/requirements.md.
---

# Code Review

## Role
Act as a senior reviewer. Review against the spec, not against assumptions.

## Input
- `src/**/*.py` and `tests/**/*.py`, every file read
- `docs/requirements.md`

## Review Areas
Cover all 8 areas.

| Area | Question |
|---|---|
| Correctness | Does each component behave as specified in `docs/requirements.md`? |
| Security | Are secrets excluded from output? Is user input validated at all boundaries? |
| Error Handling | Are API failures, missing files, and edge cases handled gracefully? |
| Test Coverage | Do tests cover the happy path AND the key edge cases (Not Found, empty input, invalid format)? |
| Code Clarity | Are function names self-explanatory? Is logic followable without comments? |
| DRY Principle | Is there duplicated logic that should be refactored into a shared function? |
| Dependency Safety | Are all third-party packages pinned? Are there known-vulnerable versions? |
| Python Conventions | PEP8, type hints, no bare `except:`, no mutable default arguments |

## Output Format (`output/reports/code-review.md`)
1. **Summary**: pass / fail / needs-changes.
2. **Findings**, grouped by area, as a table: Severity (Critical / Major / Minor) | File | Line | Description | Suggestion. An area with no findings says "No findings".
3. **Overall Recommendation**: `Approve` or `Request Changes`.

## Rules
- Only report actual findings, not hypothetical issues.
- Severity is Critical if it would break functionality or expose a security risk.
- Any Critical finding forces the recommendation to `Request Changes`.
- Quote requirement IDs (FR-n, NFR-n) for spec deviations.
- Never print secret values found in code; name the file and line only.
- Do not modify source or test files.
