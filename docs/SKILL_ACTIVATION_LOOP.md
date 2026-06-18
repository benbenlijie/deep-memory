# Skill Activation Loop

## Goal

Memory-to-Skill should not stop at “we can export a candidate”. If you退后一步看，the real capability question is: how does a remembered procedure become a safer, reviewable improvement in future agent behavior?

The activation loop answers that question without silently changing the agent. A memory may propose a skill, but only a reviewed skill can influence future behavior.

```text
procedural memory
  → candidate markdown
  → evidence bundle
  → human/reviewer gate
  → installed skill or rejected candidate
  → agent uses skill in a later task
  → new evidence updates the skill or rolls it back
```

## Non-goal: no automatic installation

This project must keep Memory-to-Skill in candidate/review mode.

The export prototype may generate `SkillCandidate.markdown`, but it must not:

- write into an agent profile’s installed `skills/` directory;
- edit global Hermes skills;
- change tool behavior silently;
- bypass a reviewer because confidence or importance is high;
- treat one successful run as enough for activation.

High-confidence procedural memory is a trigger for review, not a permission to install.

## Activation states

| State | Meaning | Allowed next action |
| --- | --- | --- |
| `memory` | L4 procedural memory exists in the database. | Evaluate trigger conditions. |
| `candidate` | Reviewable markdown was exported from memory. | Attach evidence and checklist. |
| `reviewing` | Human or trusted reviewer inspects candidate. | Accept, request changes, reject, or quarantine. |
| `accepted` | Candidate is safe and useful enough to promote. | Rewrite into canonical skill format and install through normal skill-management path. |
| `installed` | Skill is available to an agent. | Agent may load it when relevant; usage must remain auditable. |
| `rolled_back` | Installed skill was removed or disabled after bad evidence. | Restore previous version or keep candidate rejected. |
| `rejected` | Candidate should not become a skill. | Keep audit record; do not re-export unchanged content. |

## Trigger conditions

A procedural memory becomes eligible for candidate export only when all required triggers are satisfied:

1. Procedural shape
   - The memory describes a workflow, playbook, checklist, debugging method, operational sequence, or reusable decision procedure.
   - It is not merely a preference, status update, project milestone, quote, or fact.

2. Successful use
   - The procedure was used at least once in a real task or controlled smoke test.
   - The outcome is observable, not just asserted by the model.

3. Recurrence likelihood
   - The same situation is likely to recur across sessions, agents, projects, or users.
   - Reuse would reduce future steering or prevent a repeated failure mode.

4. Generalizable scope
   - The procedure can be expressed without stale IDs, one-off paths, private repo details, secrets, raw PII, or temporary task state.
   - Any environment-specific assumptions are explicitly scoped.

5. Safety compatibility
   - The procedure does not bypass approval, access control, privacy policy, security boundaries, or human review.
   - The workflow is bounded, reversible where possible, and has a verification step.

Optional strengthening signals:

- confidence and importance are both high;
- multiple independent memories point to the same procedure;
- failures and fixes are included, not only the happy path;
- a domain expert or maintainer has reviewed the procedure.

## Evidence requirements

A candidate must carry an evidence bundle before review. The minimum bundle is:

- source memory ID;
- memory kind: `procedural`;
- source trail, such as conversation, task, command, or document reference;
- evidence that the procedure worked: tests, command output, review result, artifact path, source link, before/after behavior, or tool return status;
- recurrence reason;
- safety notes and known boundaries;
- explicit `Auto-install: no` marker.

Evidence quality matters. “The agent said it worked” is weak evidence. A passing test, real command output, reviewed diff, or reproduced workflow is stronger.

## Review gate

The review gate is the key bottleneck. It prevents memory from becoming hidden behavioral drift.

A reviewer should answer this checklist before promotion:

- Is this truly a reusable procedure rather than a one-off status note?
- Is the source memory procedural and sufficiently scoped?
- Is there concrete evidence that the procedure worked?
- Are secrets, raw PII, tokens, private credentials, and stale task IDs absent?
- Are project-specific paths or commands either removed or explicitly scoped?
- Does the skill include “when to use” and “when not to use” boundaries?
- Does it include verification steps the future agent can actually run?
- Could the procedure cause unsafe side effects if followed automatically?
- Does it conflict with existing skills or policy documents?
- Is rollback possible if the skill later causes bad behavior?

Promotion should require an explicit human or trusted maintainer action. The export function should only produce review material.

## Installation boundary

Installation is outside the export prototype.

Accepted candidates may be installed only through the normal project or agent skill-management path, for example a maintainer-controlled `skill_manage(action="create")` call or an equivalent reviewed repository change.

Installation must preserve:

- candidate source memory ID or source trail;
- reviewer identity or review note where the hosting system supports it;
- skill version or diff;
- activation date;
- rollback path.

Candidates should not install themselves. A CLI command such as `deep-memory export-skill` may write a candidate file, but the safe default target is a review directory such as `skill-candidates/`, not an active `skills/` directory.

## Rollback

Rollback is required because activated skills change future agent behavior.

Rollback should happen when:

- the skill causes repeated wrong tool use or unsafe behavior;
- reviewers find stale context, hidden credentials, or private data;
- the underlying tool/API changed and the playbook is no longer valid;
- a better umbrella skill absorbs the procedure;
- usage evidence shows the trigger is too broad.

Rollback actions:

1. Remove or disable the installed skill through the normal skill-management path.
2. Keep the candidate and review record for audit, but mark it `rolled_back` or `rejected`.
3. Record the reason in the candidate review notes.
4. If useful, create a narrower revised candidate instead of reinstalling unchanged content.
5. Add a regression test, checklist item, or documentation note that prevents the same unsafe activation path.

## End-to-end example

### 1. Procedural memory

An agent repeatedly recovered from ambiguous Kanban worker failures. A procedural memory was saved:

```text
Workflow: recover Kanban protocol violations by reading task history, classifying provider versus worker causes, verifying artifacts, and then blocking for review or completing with structured metadata.
```

Metadata:

```text
kind: procedural
importance: 0.92
confidence: 0.88
source: conversation:kanban-recovery#rule-based-v0
```

### 2. Skill candidate markdown

The export prototype converts that memory into candidate markdown:

```python
from deep_memory import DeepMemory
from deep_memory.skill_export import procedural_memory_to_skill_markdown

mem = DeepMemory("agent.db")
record = mem.add(
    "Workflow: recover Kanban protocol violations by reading task history, "
    "classifying provider versus worker causes, verifying artifacts, and then "
    "blocking for review or completing with structured metadata.",
    kind="procedural",
    importance=0.92,
    confidence=0.88,
    source="conversation:kanban-recovery#rule-based-v0",
)

candidate = procedural_memory_to_skill_markdown(
    record,
    name="kanban-protocol-recovery",
    evidence=[
        "Two blocked cards were recovered without repeating the failed path.",
        "Targeted tests and full verification commands passed before handoff.",
    ],
    recurrence_hint="Kanban workers can hit protocol violations whenever provider or worker exits are ambiguous.",
)

print(candidate.markdown)
```

The candidate must include:

```text
Auto-install: no
Trigger reasons: successful workflow, high confidence, high importance, verified with evidence, recurrence likely
Safety boundaries: no credentials, no raw PII, no stale task IDs
Verification: confirm repeatability before installation
```

### 3. Human review checklist

A reviewer inspects the candidate:

```text
[ ] Procedure is reusable and not a one-off task update.
[ ] Evidence references real recovered cards or tests, without leaking stale IDs into the skill body.
[ ] No secrets, raw PII, or private credentials appear.
[ ] The playbook says when to block for human review instead of completing automatically.
[ ] The future agent can verify artifacts before claiming success.
[ ] Rollback is possible by deleting or disabling the installed skill.
```

If any item fails, the candidate remains uninstalled and is revised or rejected.

### 4. Agent usage after approved installation

Only after approval, the candidate may be rewritten into a canonical installed skill. A future Kanban worker can then load it when the current task resembles ambiguous protocol recovery.

Expected usage pattern:

```text
1. Agent scans available skills.
2. It loads `kanban-protocol-recovery` because the task involves a blocked or failed Kanban run.
3. It follows the playbook: inspect task history, classify cause, verify artifacts, then block for review or complete with metadata.
4. It reports evidence: files checked, tests run, and final Kanban action.
5. If the skill misfires, reviewer rolls it back or narrows the trigger.
```

That is the actual activation loop: memory improves future behavior only after evidence, review, installation, later use, and rollback capability.

## Example verification command

A maintainer can verify the current export prototype and this activation-loop documentation with:

```bash
uv run pytest -q tests/test_skill_export.py tests/test_skill_activation_loop_docs.py
uv run pytest -q
uv run ruff check .
```

## Relationship to `docs/internal/MEMORY_TO_SKILL.md`

`docs/internal/MEMORY_TO_SKILL.md` defines the export boundary: procedural memory can become reviewable candidate markdown.

This document defines the next layer: the candidate can become active agent capability only through an explicit activation loop with trigger conditions, evidence, review, installation boundaries, and rollback.
