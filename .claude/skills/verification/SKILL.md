---
name: verification
description: QA method that runs the test suite, checks coverage and acceptance-criteria mapping, and writes output/test-results/results.md with a PASS/FAIL verdict. Use for final verification before a PR.
---

# Verification

## Role
Act as a QA engineer running final acceptance testing.

## Input
- `src/` and `tests/`
- `docs/requirements.md`
- `output/reports/code-review.md` (to check for open Critical findings)

## Verification Steps
1. Run unit tests: `pytest tests/unit/ -v`
2. Run integration tests: `pytest tests/integration/ -v`
3. Check coverage: `pytest --cov=src --cov-report=term-missing`
4. Validate that each acceptance criterion in `docs/requirements.md` is covered by at least one test.
5. Flag any requirement (FR-n) with zero test coverage as a gap.

If a command cannot run (missing pytest, missing pytest-cov, no tests), record the exact error and set the verdict to FAIL. Do not fix anything.

## Output Format (`output/test-results/results.md`)
1. **Test Run Summary**: total / passed / failed / skipped.
2. **Coverage Report**: overall % and per-module breakdown.
3. **Acceptance Criteria Coverage**: table mapping each criterion (with FR ID) to its test(s).
4. **Gaps**: any requirement with no test coverage, or "None".
5. **Final Verdict**: a line exactly `Final Verdict: PASS` or `Final Verdict: FAIL`.
6. If FAIL, a list of exactly what must be fixed before a PR can be created.

## Pass Criteria
All unit tests pass, all integration tests pass, coverage is 80% or more, and no Critical code-review finding is open. If any is not met, the verdict is FAIL. There is no override.

## Rules
- Report real command output only. Never estimate numbers.
- Do not modify source or test files.
