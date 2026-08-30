---
name: notion-schedule-control
description: Interpret and update the user's Notion task schedule from Obsidian inline requests. Use when the user asks to change a task's working date, due date, priority, description, name, or completion status; keep planning dates separate from deadlines and do not use for unrelated Notion edits.
---

# Notion Schedule Control

## Purpose and use when

Use this skill for schedule-related task edits originating in the Obsidian task interface and mirrored to Notion. Treat Notion as the task source of truth while preserving the interface's field meanings.

Treat the task's working date and due date as separate fields.

Interpret every request containing "move" as a request to change the date the user will work on. Never map "move" to `Due`.

Supported inline edits are limited to task name, description, working date, priority, and completion status.

- "working date," "work date," "date I am working on," and similar wording means the field used to plan when the user will work on the task. Prefer the Notion property `Work Date`, then `Working Date`, then another clearly labeled planning-date property.
- "due," "deadline," or "due date" means the deadline property, normally `Due`.
- Never silently substitute `Due` when the user explicitly says working date.
- Resolve relative dates using the current date and preserve the user's intended timezone.
- Match task names against the current Notion task list before updating.
- If multiple tasks match or the relevant property is missing, ask for clarification rather than changing an unrelated task.
- After an update, report the task name, field changed, and resulting date/status.

## Access and tool behavior

- Read the current task list and property schema before mutating a task. Prefer the existing Obsidian/Notion bridge or connected Notion access used by the workspace.
- Resolve relative dates using the current date and the user's intended timezone.
- Change only the requested supported fields: task name, description, working date, priority, or completion status. Do not silently edit unrelated properties.
- Treat a request to move a task as a working-date change unless the user explicitly says due date or deadline.

## Provider handoff

This skill is provider-neutral. Codex may use the existing Notion bridge directly. Ollama or Ultimate Thinker may interpret the request and propose a structured action, but the plugin or an authorized connector must perform and verify the Notion read/write. Never claim that a local model changed Notion without a confirmed tool result. Pass the current task list, property schema, timezone, and validation result between stages.

## Error recovery

- If the task list cannot be read, the requested task is missing, or the Notion connection is unavailable, do not guess or report a completed update.
- If multiple tasks match, or the relevant property is absent or ambiguously named, ask for clarification before writing.
- If the write fails, report the task and intended field without claiming success, then leave the existing task unchanged if the connector supports atomic failure.

## Validation

After a successful update, reread the task and confirm the exact task identity, changed property, resulting value, and visible status. Confirm that `Due` was not changed when the request was for a working date, and report any sync/display lag explicitly.
