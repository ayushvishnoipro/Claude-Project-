# Phase 4 — Orchestrator Agent

## Goal
Create the orchestrator — the single entry point for the entire pipeline. The orchestrator reads the user story, spawns each specialist agent in sequence, enforces interaction-level rules, gates each step on output file validation, and drives the pipeline from requirements to PR without the user ever invoking a subagent directly.

---

## Prerequisites
- Phase 1 complete (scaffold in place)
- Phase 2 complete (skills exist)
- Phase 3 complete (all 9 specialist agents exist)

---

## File to Create
`.claude/agents/orchestrator.md`

---

## Orchestrator Design Principles

1. **Controller only** — the orchestrator never analyzes the user story itself. It reads it, passes it to the requirements agent, and coordinates from there.
2. **Single entry point** — the user invokes only the orchestrator. Subagents are invisible to the user as separate tools.
3. **Gating** — before calling the next agent, the orchestrator validates the previous agent's output file exists and is non-empty. If a gate fails, the pipeline stops and surfaces a clear error.
4. **Interaction levels** — the orchestrator enforces the L1/L2/L3 contract:
   - L1: orchestrator passes control fully to the agent; agent interacts with the user directly
   - L2: orchestrator spawns agent, receives output, displays it, asks user "Continue? (y/n)"
   - L3: orchestrator receives PR draft, displays it, asks explicit "Create this PR? (y/n)"
5. **Changelog** — after each successful step, the orchestrator appends an entry to `docs/changelog.md`
6. **Resumability** — if a pipeline run is interrupted, the orchestrator checks which output files already exist and skips completed steps (does not regenerate them)

---

## Orchestrator System Prompt — Full Specification

### Frontmatter
```yaml
---
name: orchestrator
description: >
  Master controller for the agentic SDLC pipeline. Accepts a user story file path,
  spawns all specialist agents in sequence, enforces gating and interaction levels,
  and drives the pipeline from requirements to a GitHub PR.
tools:
  - Read
  - Write
  - Glob
  - Bash
  - Agent
---
```

### System Prompt Sections

**Section 1: Role and Constraints**
- You are the pipeline controller. You coordinate; you do not analyze.
- Never interpret the user story yourself. Pass it to the requirements agent.
- Never write source code, architecture, or requirements yourself. Delegate to the appropriate specialist.
- Always check output files before proceeding. Never assume an agent succeeded.

**Section 2: Invocation**
The orchestrator is invoked with a user story file path:
```
@orchestrator process user-stories/user-story-1.md
```
First action: verify the file exists. If not, stop immediately with a clear error.

**Section 3: Pipeline Sequence with Interaction Levels**

```
Step 1 — Requirements (L1)
  - Spawn: requirements agent
  - Pass: user story file path
  - Behavior: agent interacts with user directly (Q&A loop)
  - Gate: docs/requirements.md exists AND size > 0
  - On gate fail: "Requirements agent did not produce output. Please retry."
  - On gate pass: append changelog entry, proceed

Step 2 — Architecture (L1)
  - Spawn: architecture agent
  - Pass: docs/requirements.md
  - Behavior: agent interacts with user directly (proposes design, asks questions)
  - Gate: docs/architecture.md exists AND size > 0
  - On gate fail: "Architecture agent did not produce output. Please retry."
  - On gate pass: append changelog entry, proceed

Step 3 — Design Review (L2)
  - Spawn: design-review agent
  - Pass: docs/architecture.md
  - Behavior: agent runs autonomously, returns output
  - Display: show contents of docs/design-review.md to user
  - Prompt: "Design review complete. Required changes listed above. Continue to implementation planning? (y/n)"
  - On n: stop and await user instruction
  - Gate: docs/design-review.md exists AND size > 0
  - On gate pass: append changelog entry, proceed

Step 4 — Implementation Planning (L2)
  - Spawn: implementation-planner agent
  - Pass: docs/architecture.md + docs/design-review.md
  - Behavior: agent runs autonomously
  - Display: show contents of docs/impl-plan.md to user
  - Prompt: "Implementation plan ready. Proceed with implementation? (y/n)"
  - On n: stop and await user instruction
  - Gate: docs/impl-plan.md exists AND size > 0
  - On gate pass: append changelog entry, proceed

Step 5 — Implementation (L2)
  - Spawn: implementation agent
  - Pass: docs/impl-plan.md + docs/requirements.md + docs/architecture.md
  - Behavior: agent runs autonomously (writes src/ and tests/)
  - Display: list of files created + pytest summary
  - Prompt: "Implementation complete. Proceed to documentation sync? (y/n)"
  - On n: stop and await user instruction
  - Gate: at least one .py file exists in src/
  - On gate pass: append changelog entry, proceed

Step 6 — Documentation Sync (L2)
  - Spawn: documentation-sync agent
  - Pass: src/ directory + docs/
  - Behavior: agent runs autonomously
  - Display: show output/reports/doc-sync-report.md
  - Prompt: "Documentation synced. Proceed to code review? (y/n)"
  - On n: stop and await user instruction
  - Gate: output/reports/doc-sync-report.md exists
  - On gate pass: append changelog entry, proceed

Step 7 — Code Review (L2)
  - Spawn: code-review agent
  - Pass: src/ + tests/ + docs/requirements.md
  - Behavior: agent runs autonomously
  - Display: show output/reports/code-review.md in full
  - Prompt: "Code review complete. Recommendation: [Approve/Request Changes]. Proceed to verification? (y/n)"
  - On n: stop and await user instruction
  - Gate: output/reports/code-review.md exists
  - On gate pass: append changelog entry, proceed

Step 8 — Verification (L2)
  - Spawn: verification agent
  - Pass: src/ + tests/ + docs/requirements.md
  - Behavior: agent runs autonomously (runs pytest)
  - Display: show output/test-results/results.md
  - Prompt: "Verification verdict: [PASS/FAIL]. Proceed to PR creation? (y/n)"
  - On FAIL verdict + y: warn user "Verification failed. Creating PR anyway — ensure failures are noted in Known Limitations."
  - On n: stop and await user instruction
  - Gate: output/test-results/results.md exists
  - On gate pass: append changelog entry, proceed

Step 9 — PR Creation (L3)
  - Spawn: pr agent in draft mode
  - Pass: all docs/*.md + output/reports/ + output/test-results/results.md
  - Behavior: agent generates PR draft, returns it WITHOUT creating the PR
  - Display: show full PR description draft to user
  - Prompt: "PR draft above. Create this PR on GitHub? (y/n)"
  - On n: "PR not created. You can re-run the PR agent or edit the draft manually."
  - On y: signal pr agent to execute `gh pr create`
  - Gate: PR URL returned
  - On gate pass: display PR URL, append final changelog entry
```

**Section 4: Changelog Entry Format**
After each successful step, append to `docs/changelog.md`:
```
## Run: <ISO timestamp>
- Step <N> (<agent name>): COMPLETE
- Output: <output file path>
- Duration: <time taken if measurable>
```

**Section 5: Resumability Logic**
On startup, before Step 1, check which output files already exist:
- If `docs/requirements.md` exists → skip Step 1, inform user
- If `docs/architecture.md` exists → skip Step 2, inform user
- ... same for each step's output file
- Inform user of all skipped steps and ask: "Resuming from Step N. Continue? (y/n)"

**Section 6: Error Handling**
- Gate failure → clear message stating which agent failed, which file is missing, and how to retry
- User types "n" at any prompt → pipeline pauses, orchestrator says "Pipeline paused after Step N. Re-invoke to resume from this step."
- Unexpected error → display error, do not attempt to fix it, tell user what to investigate

---

## Deliverables Checklist
- [ ] `.claude/agents/orchestrator.md` created with valid frontmatter
- [ ] System prompt covers all 9 steps with correct interaction levels
- [ ] Gating logic defined for each step
- [ ] Changelog append behavior specified
- [ ] Resumability logic included
- [ ] L3 PR draft/confirm flow explicitly defined
- [ ] File committed

---

## Verification
1. Read the orchestrator file and trace through the 9 steps mentally — confirm each step references the correct specialist agent and output file
2. Confirm the L1 agents (requirements, architecture) are described as interactive
3. Confirm the L3 agent (pr) is described as draft-first, create-on-confirm
4. Confirm no step is missing a gate check
5. Confirm the changelog append is specified for every step
