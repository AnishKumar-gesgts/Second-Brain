---
name: weekly-update
user-invocable: true
description: "Run a vault-wide weekly update: scan context files, interview for weekly pulse, update root SecondBrainAgent.md, GOALS.md (if changed), and each project's Current Status."
argument-hint: "Optional: target date for the weekly update (default: today). Run to perform a meta-level check-in and update context files."
---

# Skill: Weekly Update

Summary
- Perform a fast, vault-wide weekly check-in: scan root and project context files, conduct a meta-level interview, update Weekly Update sections, and optionally create a dated weekly review note.

When to Use
- User says "weekly update", "weekly review", or similar
 - A week (or more) has passed since the last `Weekly Update` in `SecondBrainAgent.md`

Process
1. Phase 1 — Scan current state: read `SecondBrainAgent.md` (Weekly Update, Goals & Progress, Projects), `GOALS.md` (if present), and each project's `SecondBrainAgent.md` Current Status.
2. Phase 2 — Meta-level interview (Weekly Pulse + Goals check-in). Ask targeted questions based on what you read.
3. Phase 3 — Project updates: quick one-question status check per project and targeted follow-ups only when needed.
4. Phase 4 — Update files: write the new Weekly Update section, update Goals & Progress only when changed, and update each project's Current Status for changed projects.
5. Phase 5 — Optional: create a dated weekly review note using the interview content.

Interview focal points
- What's working?
- What's not working?
- What are you sitting on / need to decide?
- What are you feeling pulled toward?
- Any deadlines or time-sensitive items?

Rules & guardrails
- Read everything first — do not ask the user to repeat information already present.
- Only change status/progress sections (do not rework project processes, rules, or structure during a weekly update).
- Ask the user to confirm the set of file edits before writing them.

Outputs
- Updated `SecondBrainAgent.md` → Weekly Update + any changed Goals/Projects entries
- Updated `GOALS.md` (only if user requested changes)
- Updated `03 Projects/[Project]/SecondBrainAgent.md` → Current Status for changed projects
- Optional dated weekly review note (in the user's reviews folder)

Example prompts
- "Run weekly update" — scan + interview + update files
- "Weekly update: create review note" — do the update and save a dated review note

Done criteria
- User confirms the summary of proposed edits and the files are written
- All updated sections include a `Last updated:` timestamp and the `Status` line for projects changed

Implementation notes
- Keep each project check-in fast: one question plus a quick follow-up if needed.
- If GOALS.md doesn't exist, do not create one here unless the user explicitly asks.
