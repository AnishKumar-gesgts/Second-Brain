---
name: chat-context-compaction
description: Compact a long conversation into a portable canonical checkpoint for Codex, Ollama, and Ultimate Thinker handoffs. Use when the user asks to compact, checkpoint, summarize, or carry forward context; do not claim that the underlying transcript or model context window changed.
---

# Chat Context Compaction

## Purpose and use when

Use this skill when the user asks to compact context, compact a chat, make a checkpoint, summarize working context for continuation, or carry context between model providers.

No provider can erase the original transcript or directly resize the host application's underlying context window. Create a concise checkpoint instead. An Ollama or Ultimate Thinker adapter may apply a provider-specific context budget, such as Ollama `num_ctx`, but must describe that as an adapter setting rather than a changed underlying context window.

## Workflow

Create or update one clearly labeled `Context checkpoint` with exactly these fields:

- **Current goals**
- **Decisions**
- **Constraints**
- **Active tasks**
- **Key technical facts**
- **Unresolved questions**
- **User preferences**
- **Important references**

Preserve commitments, authorization boundaries, file paths, and pending follow-ups. Mark facts as **verified**, **assumption**, **uncertain**, or **stale as of YYYY-MM-DD** when relevant. Separate completed, in-progress, blocked, and superseded work.

## Provider handoff

Keep the checkpoint provider-neutral so Codex, Ollama, and Ultimate Thinker can consume the same artifact.

- Codex may combine it with native skills and tools.
- Ollama may receive it in the system prompt alongside only the relevant skill text and source material.
- Ultimate Thinker should pass it to planning, local-worker, and review stages with explicit stage labels.
- Never include hidden reasoning, credentials, or claims that a provider can use unavailable tools.
- When context budgets differ, preserve goals, constraints, active tasks, unresolved questions, key facts, and references first. Trim narrative and completed detail before dropping commitments.

Use this portable handoff shape when one stage communicates with another:

```text
HANDOFF TYPE: context-checkpoint
SOURCE PROVIDER: Codex | Ollama | Ultimate Thinker
TARGET PROVIDER: Codex | Ollama | Ultimate Thinker
CONTEXT BUDGET: provider-configured value or unknown
CHECKPOINT:
<the eight-field checkpoint>
OPEN QUESTIONS:
<questions for the next stage>
TOOL RESULTS:
<verified results only; omit unavailable tools>
```

## Validation

Before finishing, confirm all eight fields are present, provider-specific context limits are labeled rather than overstated, commitments and authorization boundaries survived compression, and the checkpoint does not claim that transcript history or the underlying model context window was changed.
