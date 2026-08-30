---
name: apush-reading-notes
description: Create compact APUSH textbook reading notes from the latest matching U.S. History AP reading assignment in the local Canvas Checkup sync when no note for that assignment exists. Use for APUSH reading-note requests, not general history summaries or unrelated Canvas work.
---

# APUSH Reading Notes

Use this skill for the user's recurring AP U.S. History textbook readings.

## Purpose and use when

Use this skill to turn the newest synced APUSH reading assignment into a quiz-ready note while preserving the teacher's scope, the established vault location, and the previous note's format. Do not create a note when the assignment is ambiguous or already covered.

## Source of truth

1. Read `Machine/Canvas Checkup/assignments.json` and `Canvas Checkup.md`.
2. Filter for `U.S. History A (AP) - Harrington, J` reading assignments.
3. Use the newest relevant reading assignment and record its Canvas assignment ID, page range, due date, directions, and textbook/PDF link.
4. Read the immediately previous APUSH reading assignment too. Its directions establish any standing reading rules that the newest assignment may omit.
5. Never substitute the textbook chapter number for the APUSH unit number.
   - If Canvas explicitly states an APUSH unit, use that unit.
   - If the synced Canvas data omits the unit, infer the College Board APUSH unit from the assigned historical period/content rather than the book chapter. Do not pretend Canvas supplied a unit that it did not.

## Duplicate check

Before doing any textbook work, inspect `Anish's Second Brain/Notes/APUSH/`.

- Treat a note as associated with the assignment when its filename or contents clearly match the assigned page range or Canvas assignment ID.
- If matching notes already exist, make no duplicate note and stop.
- If no matching note exists, continue.

If the local Canvas sync is stale or missing, report that limitation before using another source. Do not silently substitute a different course, assignment, or page range.

## Reading rules

- Follow the teacher's standing instruction to read and summarize only the normal black text on white background.
- Exclude purple, yellow, brown, or otherwise colored feature pages/boxes.
- Exclude source-analysis features, comparison sidebars, `Thinking Like a Historian`, decorative captions, maps/tables used only as features, and other colored supplemental material unless the normal black-and-white narrative explicitly depends on it.
- Read the entire assigned page range carefully. Do not summarize only bold or italic material; quiz questions may cover ordinary narrative details.
- Prioritize specific people, places, events, causes, effects, chronology, comparisons, and vocabulary.
- Include every bolded/key term from the assigned range that appears in the chapter's terms/key-people material, with a concise definition.

## Note style

Use the immediately previous APUSH reading note as the formatting and density template. The standard pattern is:

> Condensed notes for the assigned black-text-on-white narrative only. Colored feature sections and their source-analysis/comparison material are excluded.

Then include:

- `## Big picture`
- chronological/topical sections with book page ranges in headings
- useful `###` subsections
- concise but information-dense bullets
- `## Essential chronology`
- `## Must-know terms and people` with **bolded terms/names** and one-line definitions
- `## Likely quiz comparisons`
- `## Final review questions`

Preserve the factual, condensed style of the previous note. Do not turn the notes into prose essays.

## Naming

Save the finished note in:

`Anish's Second Brain/Notes/APUSH/`

Filename format:

`APUSH Unit <unit-number> - pp. <start>-<end>.md`

Example: `APUSH Unit 2 - pp. 82-111.md`

The APUSH unit is authoritative; the textbook chapter number is not part of the filename unless the user later changes this convention.

## Completion

After creating the note, verify that:

1. the assigned page range is complete;
2. colored/non-assigned feature content was excluded;
3. key terms and people have definitions;
4. the filename uses APUSH Unit + assigned pages;
5. no duplicate note was created.

## Access and tool behavior

- Use the local Canvas sync and Obsidian vault files named above as the primary inputs. Read the previous APUSH note before writing so formatting and density remain consistent.
- Read the assigned textbook/PDF pages themselves when accessible; use assignment metadata only to identify scope and standing instructions.
- Write only to `Anish's Second Brain/Notes/APUSH/` and preserve existing notes, links, and unrelated files.

## Provider handoff

This skill is provider-neutral. Codex may use its native Canvas, browser, and file tools; Ollama or Ultimate Thinker may use this workflow only when the orchestrator supplies the referenced local files or verified tool results. Do not claim that an Ollama model accessed Canvas, a textbook, or a PDF unless those contents were actually provided to it. Preserve the assignment scope, duplicate check, and validation requirements across every handoff.

## Error recovery

- If Canvas data, the assignment link, the textbook pages, or the previous note cannot be accessed, stop before creating a partial note and report the missing input.
- If the newest assignment is not clearly APUSH, the page range is missing, or the unit cannot be established without a risky inference, ask for clarification.
- If a duplicate is found after work begins, stop and do not overwrite it; report the matching filename or assignment ID.
- If writing or validation fails, do not claim completion and leave no partial or misleading note when safe cleanup is possible.

## Validation

Before finishing, verify the note's assignment ID/page range, APUSH unit filename, complete assigned-page coverage, exclusion of colored feature material, definitions for required terms and people, required review sections, formatting consistency with the previous note, and absence of a duplicate.
