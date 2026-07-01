from __future__ import annotations

import json
from datetime import datetime, timezone
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from deep_memory.core import DeepMemory, MemoryKind, MemoryRecord, build_idempotency_key

DEFAULT_HERMES_SOURCE = "hermes"
VALID_KINDS: set[str] = {"working", "episodic", "semantic", "procedural"}


@dataclass(frozen=True)
class HermesFact:
    """A durable fact extracted from a Hermes session export or event stream."""

    content: str
    kind: MemoryKind = "semantic"
    importance: float = 0.7
    confidence: float = 0.8
    source: str = DEFAULT_HERMES_SOURCE
    scope: str = "global"
    scope_id: str | None = None
    agent: str | None = DEFAULT_HERMES_SOURCE
    event_time: str | None = None


def iter_hermes_facts(session_jsonl: str | Path) -> Iterator[HermesFact]:
    """Yield explicit `facts` records from a Hermes JSONL session export.

    The MVP intentionally avoids pretending to solve extraction. Hermes or a
    caller should decide which session facts are durable, then emit records in
    this shape on any JSONL line:

    {"session_id": "...", "facts": [{"content": "...", "kind": "semantic"}]}
    """

    path = Path(session_jsonl)
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid Hermes JSONL at line {line_no}: {exc.msg}") from exc
            yield from _facts_from_event(event)


def write_hermes_session_facts(
    db: str | Path,
    session_jsonl: str | Path,
) -> list[MemoryRecord]:
    """Import explicit Hermes session facts into a deep-memory database."""

    memory = DeepMemory(db)
    records: list[MemoryRecord] = []
    try:
        for fact in iter_hermes_facts(session_jsonl):
            records.append(
                memory.add(
                    fact.content,
                    kind=fact.kind,
                    importance=fact.importance,
                    confidence=fact.confidence,
                    source=fact.source,
                    scope=fact.scope,  # type: ignore[arg-type]
                    scope_id=fact.scope_id,
                    agent=fact.agent,
                    event_time=fact.event_time,
                    idempotency_key=build_idempotency_key(
                        fact.content,
                        kind=fact.kind,
                        source=fact.source,
                        scope=fact.scope,  # type: ignore[arg-type]
                        scope_id=fact.scope_id,
                        agent=fact.agent,
                    ),
                    duplicate_policy="skip",
                )
            )
    finally:
        memory.close()
    return records


def _facts_from_event(event: dict[str, Any]) -> Iterator[HermesFact]:
    session_id = str(event.get("session_id") or event.get("session") or "").strip()
    default_source = f"{DEFAULT_HERMES_SOURCE}:{session_id}" if session_id else DEFAULT_HERMES_SOURCE
    raw_context = event.get("context")
    context = cast(dict[str, Any], raw_context) if isinstance(raw_context, dict) else {}
    default_scope, default_scope_id = _scope_from_payload(event, context)
    default_agent = _optional_str(event.get("agent") or context.get("agent")) or DEFAULT_HERMES_SOURCE
    default_event_time = _event_time_from_event(event, context)
    facts = event.get("facts") or []
    if not isinstance(facts, list):
        return

    for raw in facts:
        if isinstance(raw, str):
            content = raw
            kind = "semantic"
            importance = 0.7
            confidence = 0.8
            source = default_source
            scope = default_scope
            scope_id = default_scope_id
            agent = default_agent
            event_time = default_event_time
        elif isinstance(raw, dict):
            content = str(raw.get("content") or raw.get("text") or "")
            kind = _memory_kind(raw.get("kind", "semantic"))
            importance = float(raw.get("importance", 0.7))
            confidence = float(raw.get("confidence", 0.8))
            source = str(raw.get("source") or default_source)
            scope, scope_id = _scope_from_payload(raw, {"scope": default_scope, "scope_id": default_scope_id})
            agent = _optional_str(raw.get("agent") or default_agent)
            event_time = _optional_str(raw.get("event_time") or raw.get("timestamp") or raw.get("created_at")) or default_event_time
        else:
            continue

        content = content.strip()
        if not content:
            continue
        yield HermesFact(
            content=content,
            kind=kind,
            importance=importance,
            confidence=confidence,
            source=source,
            scope=scope,
            scope_id=scope_id,
            agent=agent,
            event_time=event_time,
        )


def _scope_from_payload(payload: dict[str, Any], fallback: dict[str, Any]) -> tuple[str, str | None]:
    scope = _optional_str(payload.get("scope") or fallback.get("scope"))
    scope_id = _optional_str(payload.get("scope_id") or fallback.get("scope_id"))
    if scope is not None:
        return scope, scope_id

    legacy_workspace = _optional_str(payload.get("workspace") or fallback.get("workspace"))
    if legacy_workspace is not None:
        return "workspace", legacy_workspace
    legacy_tenant = _optional_str(payload.get("tenant") or fallback.get("tenant"))
    if legacy_tenant is not None:
        return "tenant", legacy_tenant
    legacy_user_id = _optional_str(payload.get("user_id") or fallback.get("user_id"))
    if legacy_user_id is not None:
        return "user", legacy_user_id
    return "global", None


def _event_time_from_event(event: dict[str, Any], context: dict[str, Any]) -> str | None:
    raw = event.get("timestamp") or event.get("created_at") or event.get("session_timestamp")
    raw = raw or context.get("timestamp") or context.get("created_at") or context.get("session_timestamp")
    text = _optional_str(raw)
    if text is None:
        return None
    try:
        if text.isdigit():
            return datetime.fromtimestamp(int(text), tz=timezone.utc).isoformat()
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return text
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).isoformat()


def _optional_str(value: object) -> str | None:
    text = str(value).strip() if value is not None else ""
    return text or None


def _memory_kind(value: object) -> MemoryKind:
    kind = str(value).strip().lower()
    if kind not in VALID_KINDS:
        raise ValueError(f"unsupported Hermes fact kind: {kind}")
    return kind  # type: ignore[return-value]
