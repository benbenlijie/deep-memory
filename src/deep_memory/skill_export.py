from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

from .core import MemoryRecord


@dataclass(frozen=True)
class SkillCandidate:
    name: str
    markdown: str
    source_memory_id: str
    trigger_reasons: tuple[str, ...]
    auto_install: bool = False


def slugify_skill_name(text: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", text.lower()).strip("-")
    return slug[:64] or "procedural-memory-skill"


def procedural_memory_to_skill_markdown(
    record: MemoryRecord,
    *,
    name: str | None = None,
    evidence: Iterable[str] = (),
    recurrence_hint: str | None = None,
) -> SkillCandidate:
    if record.kind != "procedural":
        raise ValueError("only procedural memories can be exported as skill candidates")

    skill_name = name or slugify_skill_name(record.content[:80])
    evidence_items = tuple(item.strip() for item in evidence if item.strip())
    trigger_reasons = _trigger_reasons(record, evidence_items, recurrence_hint)

    markdown = f"""---
name: {skill_name}
description: Skill candidate extracted from verified procedural memory.
---

# {skill_name}

## Source

- memory_id: `{record.id}`
- source: `{record.source or "unknown"}`
- confidence: `{record.confidence}`
- importance: `{record.importance}`
- Auto-install: no

## Activation status

- state: `candidate`
- install_boundary: `review_required`
- rollback_boundary: `remove_or_disable_installed_skill_if_later_activated`

## Trigger reasons

{_markdown_bullets(trigger_reasons)}

## When to use

Use this when a similar situation recurs and the original procedure has been verified.
{_optional_recurrence(recurrence_hint)}

## Playbook

{record.content}

## Evidence

{_markdown_bullets(evidence_items) if evidence_items else "- Evidence must be attached before promotion to an installed skill."}

## Human review checklist

- Confirm this is a reusable procedure, not a one-off fact, status update, or preference.
- Confirm evidence is concrete enough to justify activation.
- Confirm secrets, tokens, raw PII, stale task IDs, and temporary project status are absent.
- Confirm the candidate has clear when-to-use, verification, and rollback boundaries.
- Confirm installation will happen only through the normal reviewed skill-management path.

## Safety boundaries

- Candidate only: require human/reviewer approval before installing as an executable skill.
- Do not include credentials, tokens, raw PII, or stale task IDs.
- Remove one-off paths, PR numbers, transient status, and environment-specific assumptions unless explicitly scoped.
- Prefer bounded, reversible procedures with clear verification steps.

## Verification

Before installing as a real skill, confirm that the procedure is repeatable, safe, and free of stale task-specific state.
"""
    return SkillCandidate(
        name=skill_name,
        markdown=markdown,
        source_memory_id=record.id,
        trigger_reasons=trigger_reasons,
    )


def _trigger_reasons(
    record: MemoryRecord,
    evidence: tuple[str, ...],
    recurrence_hint: str | None,
) -> tuple[str, ...]:
    reasons: list[str] = []
    lowered = record.content.lower()
    if any(marker in lowered for marker in ("workflow", "procedure", "steps", "playbook")) or any(
        marker in record.content for marker in ("流程", "步骤", "方法")
    ):
        reasons.append("successful workflow")
    if record.confidence >= 0.8:
        reasons.append("high confidence")
    if record.importance >= 0.8:
        reasons.append("high importance")
    if evidence:
        reasons.append("verified with evidence")
    if recurrence_hint:
        reasons.append("recurrence likely")
    return tuple(reasons or ["procedural memory candidate"])


def _markdown_bullets(items: Iterable[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def _optional_recurrence(recurrence_hint: str | None) -> str:
    if not recurrence_hint:
        return ""
    return f"\nRecurrence hint: {recurrence_hint}"
