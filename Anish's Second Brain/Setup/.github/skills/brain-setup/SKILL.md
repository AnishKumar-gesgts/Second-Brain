---
name: brain-setup
user-invocable: true
description: "Generate a personalized SecondBrainAgent.md by scanning the vault and running a 5-round interview; writes SecondBrainAgent.md after confirmation."
argument-hint: "Vault root path (optional). Run interactively to interview and generate SecondBrainAgent.md."
---

# Skill: Brain Setup

Summary
 - Scan the vault, interview the user in 5 rounds, and generate a fully populated `SecondBrainAgent.md` in the user's voice. Only write the file after explicit confirmation.

When to Use
- Starting a new vault from the template
- `SecondBrainAgent.md` is missing or placeholder-only
- User asks to initialize or re-seed their vault context

How it works (high level)
1. Phase 1: Scan the vault structure silently and record system folders and projects.
2. Phase 2: Conduct a 5-round interview (identity, COPILOT role, rules, strengths/weaknesses, goals/progress).
3. Phase 3: Assemble `SecondBrainAgent.md` using the user's own phrasing and auto-populated folder structure.
4. Phase 4: Show draft for review and accept targeted edits.
5. Phase 5: Save `SecondBrainAgent.md` after confirmation and provide next-step recommendations.

Decision points
- If `SecondBrainAgent.md` already exists with substantive content: ask whether to (a) build on it, (b) replace it, or (c) create a new version with `(C)` prefix.
- If interview answers are thin: capture them verbatim and add `<!-- TODO: expand -->` markers rather than fabricating details.

Interview rounds (use conversational prompts and summarize after each round)
- Round 1 — Who you are & purpose: vault name, one-liner role, mission, energizers, refusals, personal context.
- Round 2 — What you want COPILOT to do: scope, role type (strategic/accountability/brainstorm), prime directive.
- Round 3 — Rules & boundaries: communication style (AskUserQuestion), file-handling rules, absolute no-nos.
- Round 4 — Strengths & weaknesses: strengths list; blind spots and stress-default behaviors.
- Round 5 — Goals & current progress: concrete targets, current state, plan, risks/runway.

Generation rules & quality criteria
- Do not fabricate. When answers are short, write short sections and mark TODOs.
- Use the user's exact phrasing where possible — mirror voice and idioms.
- Auto-populate folder structure from the scan; do not ask the user to name folders you already detected.
- Completion = user confirms the final draft and the file is written to the vault root as `SecondBrainAgent.md`.

Outputs
- Primary output: `SecondBrainAgent.md` at vault root.
- Optional: suggested first tasks, links to `03 Projects/` template, or a recommended `Chess Moves` session.

Example prompts
 - "Run Brain Setup" — run full scan + interview and draft SecondBrainAgent.md.
 - "Refresh SecondBrainAgent.md (keep existing)" — re-run interview but preserve existing sections unless updated.
 - "Start fresh SecondBrainAgent.md" — create a new file and archive previous one as `(C)-archive`.

Notes for implementers
- Use `AskUserQuestion` for fixed-choice items (communication style). Use free text for narrative rounds.
- Keep each interview round brief and summarize after each round to surface misunderstandings quickly.
- Only write the file after explicit user confirmation.
