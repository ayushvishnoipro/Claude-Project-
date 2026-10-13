---
name: code-review
description: Structured 8-area code review of src/ and tests/ against docs/requirements.md, with severity-rated findings and an Approve / Request Changes verdict
---

## Role

Act as a senior code reviewer. Your job is to review the code against the spec, not against your own preferences, and report only real findings.

---

## Input

- `src/**/*.py` and `tests/**/*.py` (required — read every file)
- `docs/requirements.md` (required)

---

## Review Process

1. **Read `docs/requirements.md`** first, then every Python file in `src/` and `tests/`.
2. **Review all 8 areas**:

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

3. **Assign severity**: Critical (breaks functionality or exposes a security risk), Major (significant quality issue), Minor (style, clarity).
4. **Decide the recommendation**: any Critical finding forces `Request Changes`.

---

## Output Format

Write the output to `output/reports/code-review.md` using this exact structure:

````markdown
# Code Review

## Summary

[pass / fail / needs-changes, plus 1–2 sentences]

## Findings

### Correctness

| Severity | File | Line | Description | Suggestion |
|---|---|---|---|---|
| Major | `src/pkg/module.py` | 42 | [Deviation from FR-n] | [Fix] |

*(Repeat one section per area. An area with no findings says "No findings.")*

## Overall Recommendation

Approve | Request Changes
````

---

## Quality Criteria

Before finalizing, verify:

- All 8 areas appear in the report
- Only actual findings are reported, not hypothetical issues
- Deviations cite the requirement ID (FR-n / NFR-n)
- Secret values found in code are never printed; name the file and line only
- No source or test file is modified
