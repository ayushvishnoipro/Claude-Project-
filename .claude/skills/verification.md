---
name: verification
description: Run the test suite and coverage, map acceptance criteria to tests, and issue a PASS/FAIL verdict in output/test-results/results.md
---

## Role

Act as a QA engineer running final acceptance testing. Your job is to report what the tests actually show and give a verdict the PR gate can trust.

---

## Input

- `src/` and `tests/` (required)
- `docs/requirements.md` (required)
- `output/reports/code-review.md` (to check for open Critical findings)

---

## Verification Steps

1. **Run unit tests**: `pytest tests/unit/ -v`
2. **Run integration tests**: `pytest tests/integration/ -v`
3. **Check coverage**: `pytest --cov=src --cov-report=term-missing`
4. **Map criteria**: confirm each acceptance criterion in `docs/requirements.md` is covered by at least one test.
5. **Find gaps**: flag any requirement (FR-n) with zero test coverage.
6. **Check code review**: confirm no Critical finding is still open.

If a command cannot run (missing pytest or pytest-cov, no tests), record the exact error and set the verdict to FAIL. Do not fix anything.

**Pass criteria**: all unit tests pass, all integration tests pass, coverage ≥ 80%, no open Critical code-review finding. If any is unmet the verdict is FAIL. There is no override.

---

## Output Format

Write the output to `output/test-results/results.md` using this exact structure:

````markdown
# Verification Results

## Test Run Summary

| Suite | Total | Passed | Failed | Skipped |
|---|---|---|---|---|
| Unit | 0 | 0 | 0 | 0 |
| Integration | 0 | 0 | 0 | 0 |

## Coverage Report

Overall: [N]%

| Module | Coverage | Missing Lines |
|---|---|---|
| `src/pkg/module.py` | [N]% | [lines] |

## Acceptance Criteria Coverage

| Requirement | Criterion | Test(s) |
|---|---|---|
| FR-1 | [Given/When/Then summary] | `tests/unit/test_x.py::test_y` |

## Gaps

[Requirements with no test coverage, or "None."]

## Final Verdict

Final Verdict: PASS | FAIL

[If FAIL: exact list of what must be fixed before a PR can be created.]
````

---

## Quality Criteria

Before finalizing, verify:

- Every number comes from real command output; nothing is estimated
- The verdict line is exactly `Final Verdict: PASS` or `Final Verdict: FAIL`
- Every FR appears in the criteria table or in Gaps
- No source or test file is modified
