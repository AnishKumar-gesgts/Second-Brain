# Notion Task Bridge

The Codex Workspace plugin can mirror an explicitly shared Notion task database into separate pages under `Tasks/Notion Tasks/`. The vault's master mirror is `Tasks/Notion Tasks.md`.

## Notion setup

Create an internal Notion integration and give it access to the task database. The database should contain:

- `Name` — title property, or `Task` as an alternative title/rich-text property
- `Status` — select property with `Not started` and `Done`
- `Due` — optional date property
- `Priority` — optional select property
- `Date Working On` — optional planning date, separate from the deadline
- `Type` — optional select property
- `Time` — optional planned-time number

Copy the integration token and database URL or ID into Obsidian under **Settings → Codex Workspace → Notion task bridge**.

## Controls

- **Sync Notion** pulls each open Notion task into its own page under `Tasks/Notion Tasks/`.
- Each task page includes editable `Due`, `Priority`, `Status`, `Notes`, and `Reminders` sections. The master mirror also records `Date Working On`, `Type`, and `Time` when present.
- **Push task status** reads each task page's checkbox state and updates the linked Notion page.
- The command palette includes **Sync Notion tasks** and **Push Notion task status**.
- Automatic sync can be enabled when Home opens.

The generated file contains stable Notion page markers. Do not remove the `notion:` marker from a task that should remain linked.
