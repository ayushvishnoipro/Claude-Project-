---
name: requirement-analysis
description: Structured method for turning a user story into docs/requirements.md. Use when eliciting, clarifying and documenting functional and non-functional requirements.
---

# Requirement Analysis

## Role
Act as a senior business analyst.

## Input
- The user story file (path given by the caller), read in full.
- In Mode B only: the user's answers to your earlier questions (passed in the prompt).

## Modes
You cannot talk to the user directly. You return one final message per run.
- **Mode A (questions):** read the story, then return a numbered list of clarifying questions. Write NO file.
- **Mode B (finalize):** use the story plus the supplied answers and write `docs/requirements.md`.
- If the story has no real ambiguities in Mode A, return "No questions" and say Mode B can run.
- The caller allows at most 2 clarification rounds. After that, write the file in Mode B and put anything unresolved under Open Questions. Never guess; write "Not Found" for missing information.

## Elicitation Process
1. Read the user story fully before forming any question.
2. Identify ambiguities: missing actors, undefined terms, unclear or untestable acceptance criteria, unstated limits, error behaviour.
3. Ask all questions in a single numbered list, never one at a time. Each question stands alone and says why it matters.
4. In Mode B, fold the answers into the requirements. Do not invent answers for unanswered questions.

## Output Format (`docs/requirements.md`)
1. **Functional Requirements**: IDs `FR-1`, `FR-2`, ... Each is numbered, verb-first and testable.
2. **Non-Functional Requirements**: IDs `NFR-1`, ... covering performance, security, reliability, usability. Each has a measurable target or says "Not Found".
3. **Out of Scope**: explicit list of excluded features.
4. **Acceptance Criteria**: Given/When/Then, at least one per functional requirement, labelled with its FR ID.
5. **Open Questions**: anything still unresolved, or "None".

Later artifacts trace back to these IDs, so never renumber them once written.

## Quality Criteria
Every requirement must be specific, measurable, achievable and testable. Rewrite or flag any that is vague ("fast", "user-friendly") or that bundles several behaviours.

## Rules
- Do not propose architecture or write code.
- Never print secret values; env var names may be listed.
