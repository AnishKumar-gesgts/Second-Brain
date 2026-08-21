---
name: notion-schedule-control
description: Interpret and update the user's Notion task schedule from Obsidian inline requests. Use when changing a task's working date, work date, completion status, due date, or related schedule metadata.
---

# Notion Schedule Control

Treat the task's working date and due date as separate fields.

Interpret every request containing “move” as a request to change the date the user will work on. Never map “move” to `Due`.

Supported inline edits are limited to task name, description, working date, priority, and completion status.

- “working date,” “work date,” “date I am working on,” and similar wording means the field used to plan when the user will work on the task. Prefer the Notion property `Work Date`, then `Working Date`, then another clearly labeled planning-date property.
- “due,” “deadline,” or “due date” means the deadline property, normally `Due`.
- Never silently substitute `Due` when the user explicitly says working date.
- Resolve relative dates using the current date and preserve the user’s intended timezone.
- Match task names against the current Notion task list before updating.
- If multiple tasks match or the relevant property is missing, ask for clarification rather than changing an unrelated task.
- After an update, report the task name, field changed, and resulting date/status.
