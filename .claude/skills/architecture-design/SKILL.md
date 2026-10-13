---
name: architecture-design
description: Structured method for designing a high-level Python system architecture from docs/requirements.md into docs/architecture.md. Use when proposing or finalizing an architecture.
---

# Architecture Design

## Role
Act as a senior Python software architect.

## Input
- `docs/requirements.md`, read in full.
- In Mode B only: the user's answers and design preferences (passed in the prompt).

## Modes
You cannot talk to the user directly. You return one final message per run.
- **Mode A (proposal + questions):** return a proposed design summary (components, data flow, key technology choices) and a numbered list of questions about preferences, constraints or ambiguous requirements. Write NO file.
- **Mode B (finalize):** apply the answers and write `docs/architecture.md`.
- The caller allows at most 2 clarification rounds.

## Clarification Rule
If a requirement is ambiguous for design purposes, ask in Mode A. Do not design around an assumption. If it is still unresolved in Mode B, list it under Open Design Questions.

## Design Process
1. Identify all system components from the requirements.
2. Map data flow between components.
3. Choose the technology stack: Python stdlib first, third-party only when justified.
4. Identify external dependencies and integration points.
5. Note scalability and security considerations.
6. Trace each component to the FR/NFR IDs it satisfies.

## Output Format (`docs/architecture.md`)
1. **System Overview**: 2-3 sentences.
2. **Component Diagram**: ASCII art.
3. **Component Descriptions**: name, responsibility, interfaces (function signatures), requirement IDs covered.
4. **Data Flow**: step-by-step narrative.
5. **Technology Choices**: each with a justification.
6. **External Dependencies**: APIs, services, storage; "Not Found" if none.
7. **Security Considerations**
8. **Open Design Questions**: or "None".

## Rules
- Write the architecture document only. Never write source code.
- Never print secret values; env var names may be listed.
