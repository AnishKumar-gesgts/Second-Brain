# Vault operating guide

This Obsidian vault is the user's source of truth. Codex is integrated through the `Codex Workspace` Obsidian plugin and runs from this vault root.

## Structure

- `Documents/`, `Notes/`, and `Projects/` contain user-owned material.
- `Tasks/` contains task capture and task dashboards.
- `Daily Notes/` contains daily planning and activity notes.
- `Templates/` contains note templates.
- `Machine/` contains reusable AI workflows and generated operational material.
- `System/` contains documentation about how the vault works.
- `Setup/` contains existing setup material.

## Working rules

1. Treat existing user notes as authoritative and preserve their writing style.
2. Do not reorganize or rename existing files unless explicitly asked.
3. Use templates when creating daily notes or standalone task notes.
4. Keep new paths vault-relative and prefer the existing folder structure.
5. In read-only conversations, inspect and answer without changing files.
6. In edit-enabled conversations, make only changes required by the request and summarize them clearly.
7. When a message begins with a supported workflow command, read and follow its file:
   - `/today` -> `Machine/Workflows/today.md`
   - `/new` -> `Machine/Workflows/new.md`
   - `/closeday` -> `Machine/Workflows/closeday.md`
8. Use web research when current information is required. Do not claim the search provider is Google. If the user asks to see Google results inside Obsidian, use the plugin's `[[GOOGLE_SEARCH:query]]` marker.

