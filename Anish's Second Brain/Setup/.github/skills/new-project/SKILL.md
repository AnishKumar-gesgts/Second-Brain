---
name: new-project
user-invocable: true
description: "Create a new project under 03 Projects/ by interviewing the user, scaffolding folders, and writing SecondBrainAgent.md and COMMANDS.md."
argument-hint: "Project name (optional). Run interactively to scaffold a project from the template."
---

# Skill: New Project

Summary
- Interview the user to collect project metadata, duplicate the project template, scaffold numbered folders, create `SecondBrainAgent.md` and `COMMANDS.md`, and update the root `SecondBrainAgent.md` with the new project entry.

When to Use
- User wants to create a new project inside `03 Projects/`
- Starting a new initiative and wants standard scaffolding and contextual COPILOT support

Process (step-by-step)
1. Ask the interview questions (one at a time, up to 6): name, short description, "shipped" definition, people involved, process from idea→done, rules/conventions.
2. Duplicate `03 Projects/(PROJECT TEMPLATE)` into `03 Projects/[Project Name]`.
3. Remove template artifacts and create properly numbered folders based on the process answer (input → process → output), then add system folders (System, Skills, Attachments, Iteration Logs) at the next available numbers.
4. Write a project `SecondBrainAgent.md` populated from interview answers. Add `<!-- TODO -->` placeholders for unknowns.
5. Write `COMMANDS.md` with an index of skills and commands for the project.
6. Update root `SecondBrainAgent.md` (Folder Structure + My Current Projects & Overviews) to include the new project entry.
7. Show the folder tree and draft files to the user and ask for confirmation; implement requested edits.

Interview questions (ask one at a time)
1. Project name (used as folder name)
2. What is this project? (one paragraph)
3. What does "shipped" look like? (prime directive)
4. Who else is involved? (names/roles)
5. What is the process from start to finish? (creates numbered folders)
6. Any project-specific rules or conventions?

Decision points
- If no `(PROJECT TEMPLATE)` folder exists: offer to create a minimal default structure (00 Ideas, 01 In Progress, 02 Done) and then continue.
- If the user is unsure about the process: scaffold a simple default and add TODOs where clarification is needed.

Outputs
- Folder: `03 Projects/[Project Name]/` with numbered process folders and utility folders
- `03 Projects/[Project Name]/SecondBrainAgent.md` (project-level context)
- `03 Projects/[Project Name]/COMMANDS.md` (skills & commands index)
- Updated root `SecondBrainAgent.md` entry under My Current Projects & Overviews

Done criteria
- Project folder exists with numbered structure
- SecondBrainAgent.md and COMMANDS.md drafted and reviewed by user
- Root SecondBrainAgent.md updated with project overview

Example prompts
- "New Project: [Project Name]" — starts the interactive scaffold
- "Scaffold project without template" — use default minimal structure
 - "Create project and open SecondBrainAgent.md for editing" — scaffold and open the draft for immediate edits

Implementation notes
- Use `AskUserQuestion` for controlled responses and confirm each critical step before destructive actions (like deleting template placeholders).
- Prefix AI-generated files with `(C)` when appropriate and add TODO markers for missing user inputs.
