# Memory → Skill

## Goal

Cross the gap from remembering facts to improving future agent capability.

If you退后一步看，ordinary memory answers “what should the agent recall?” Skill generation answers a different question: “what did the agent learn to do better next time?” The boundary matters. A memory can be recalled automatically; a skill changes future behavior and therefore needs stronger evidence, safety checks, and review.

## Layer model

`deep-memory` currently stores L2/L3/L4 records:

- L2 semantic: durable facts, preferences, conventions, architecture decisions.
- L3 episodic: time-bound events, decisions, attempts, outcomes.
- L4 procedural: reusable workflows, playbooks, troubleshooting patterns, tool sequences.

Only L4 procedural memories are eligible for Memory → Skill export. L2/L3 records may support the evidence trail, but they should not become skills directly.

## Trigger criteria

A procedural memory can become a skill candidate when all required criteria are true:

1. Repeatable procedure
   - It describes a workflow, steps, playbook, checklist, debugging method, or reusable operating pattern.
   - It is not just a fact, opinion, status update, or one-off note.

2. Successful outcome with evidence
   - The workflow produced a concrete result.
   - Evidence exists: tests, command output, tool return status, source links, artifact paths, review result, or before/after behavior.

3. Recurrence likely
   - The same situation is expected to recur across sessions, projects, tools, or agents.
   - Reuse would reduce future steering, prevent repeated mistakes, or improve agent capability.

4. Generalizable scope
   - The procedure can be expressed without stale task IDs, private paths, one-off PR numbers, temporary status, or context that will expire quickly.
   - Environment-specific details are either removed or explicitly scoped.

5. Reviewable safety boundary
   - The candidate can be inspected before installation.
   - The generated artifact is “candidate markdown”, not an auto-installed skill.

Strong candidates usually have high confidence/importance, an explicit source trail, and at least one successful run with verification.

## Non-triggers

Do not export a memory to a skill when it is:

- a user preference (“用户偏好：中文为主” belongs in semantic memory, not a skill);
- a temporary status (“Phase N done”, PR numbers, issue IDs, commit SHAs);
- a private credential, token, cookie, API key, or authentication workaround;
- raw PII or sensitive personal data;
- unverified speculation from the model;
- a one-off workaround that should be fixed at the source;
- a procedure that bypasses human approval, review gates, safety policy, or access controls.

## Safety boundaries

Memory → Skill generation is deliberately conservative:

- Generate candidates, not installed skills.
- Require human/reviewer approval before promotion.
- Preserve source memory ID and source trail for auditability.
- Include evidence and trigger reasons in the candidate.
- Strip or rewrite stale state before installation.
- Prefer reversible, bounded procedures with explicit verification.
- Never smuggle secrets or private data into skill markdown.

A useful rule: if putting the content into a public repository or shared agent profile would be unsafe, it should not be exported as a skill candidate without redaction and scope narrowing.

## Candidate format

The prototype exports L4 procedural memory into reviewable markdown:

```markdown
---
name: kanban-protocol-recovery
description: Skill candidate extracted from verified procedural memory.
---

# kanban-protocol-recovery

## Source

- memory_id: `...`
- source: `conversation:kanban-recovery#rule-based-v0`
- confidence: `0.88`
- importance: `0.92`
- Auto-install: no

## Trigger reasons

- successful workflow
- high confidence
- high importance
- verified with evidence
- recurrence likely

## When to use

Use this when a similar situation recurs and the original procedure has been verified.
Recurrence hint: Kanban workers can hit protocol violations whenever provider or worker exits are ambiguous.

## Playbook

Workflow: recover Kanban protocol violations by reading task history, classifying provider versus worker causes, verifying artifacts, and then blocking for review or completing with structured metadata.

## Evidence

- Two previously blocked cards were recovered without repeating the failed path.
- Targeted tests and full verification commands passed before handoff.

## Safety boundaries

- Candidate only: require human/reviewer approval before installing as an executable skill.
- Do not include credentials, tokens, raw PII, or stale task IDs.
- Remove one-off paths, PR numbers, transient status, and environment-specific assumptions unless explicitly scoped.
- Prefer bounded, reversible procedures with clear verification steps.

## Verification

Before installing as a real skill, confirm that the procedure is repeatable, safe, and free of stale task-specific state.
```

## Prototype API

`deep_memory.skill_export.procedural_memory_to_skill_markdown()` converts one L4 procedural `MemoryRecord` into a `SkillCandidate`:

```python
from deep_memory import DeepMemory
from deep_memory.skill_export import procedural_memory_to_skill_markdown

mem = DeepMemory("agent.db")
record = mem.add(
    "Workflow: run failing test, implement minimal fix, then run full verification.",
    kind="procedural",
    importance=0.9,
    confidence=0.85,
    source="conversation:tdd-example#rule-based-v0",
)

candidate = procedural_memory_to_skill_markdown(
    record,
    name="tdd-fix-loop",
    evidence=["Targeted regression test failed before fix and passed after fix."],
    recurrence_hint="Bug fixes frequently need the same red-green-verification loop.",
)

print(candidate.markdown)
```

The returned `SkillCandidate` includes:

- `name`: proposed skill name;
- `markdown`: reviewable candidate markdown;
- `source_memory_id`: source L4 memory ID;
- `trigger_reasons`: why this was considered promotable;
- `auto_install=False`: explicit guard against silent behavior changes.

## Promotion workflow

1. Extract or identify L4 procedural memory.
2. Attach evidence from successful execution.
3. Export a candidate markdown artifact.
4. Review for recurrence, generality, safety, and stale state.
5. Rewrite into the project/profile’s canonical skill format if accepted.
6. Install with the normal skill-management path.
7. Keep tests/docs/examples that prove the trigger behavior.

## Example decisions

| Memory | Decision | Why |
| --- | --- | --- |
| “用户偏好：中文为主，技术术语用英文” | Keep as L2 semantic memory | Durable preference, not a procedure |
| “2026-06-16: completed MCP smoke test” | Keep as L3 episodic memory | Time-bound event, likely stale |
| “Workflow: use MCP smoke test to verify add/search/stats before claiming interop works” | Export candidate | Repeatable workflow with verification path |
| “Token for service X is abc…” | Reject and redact | Secret; never skill material |
| “When provider 503 causes Kanban protocol violations, inspect logs, verify artifacts, then block/complete honestly” | Export candidate after evidence | Recurring operational playbook |

## Current implementation boundary

This phase prototypes export only. It does not yet:

- auto-detect candidates across the whole database;
- install generated skills;
- run a reviewer model;
- redact secrets automatically;
- merge multiple memories into one polished skill.

Those are future layers. The current root problem is to make the transition from L4 procedural memory to reviewable playbook explicit, testable, and safe.
