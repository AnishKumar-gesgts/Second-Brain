---
type: guide
status: active
tags: [system, guide]
---

# Vault Guide

This vault borrows the strongest ideas from the EMAI starter vault without importing its missing dashboard, broken theme reference, encoding problems, or oversized plugin set.

## Main surfaces

- **Home tab:** Google search, recent notes, live open tasks, and quick actions.
- **Codex chat tabs:** each tab is an independent persistent Codex CLI conversation.
- **Task Board:** due, upcoming, and unscheduled task views powered by the Tasks plugin.
- **Daily Notes:** lightweight planning and end-of-day review.

## Codex permissions

Every new conversation starts with **Allow vault edits** so Codex can act on requested changes inside this vault. You can switch a new conversation to **Read only** before sending its first message. The permission is then fixed for that conversation, so the tab remains predictable.

## Workflow commands

- `/today` builds a daily plan from current notes, projects, and tasks.
- `/new` captures and routes a task or note.
- `/closeday` reviews the day and proposes what should carry forward.

## Search

The Google search bars open results in Obsidian's core Web Viewer. Codex may also use its own web-search tools when current information is required, but that internal provider is not represented as Google.
