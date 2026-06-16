from __future__ import annotations

import json
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from deep_memory.core import DeepMemory, MemoryKind, MemoryRecord

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
                )
            )
    finally:
        memory.close()
    return records


def _facts_from_event(event: dict[str, Any]) -> Iterator[HermesFact]:
    session_id = str(event.get("session_id") or event.get("session") or "").strip()
    default_source = f"{DEFAULT_HERMES_SOURCE}:{session_id}" if session_id else DEFAULT_HERMES_SOURCE
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
        elif isinstance(raw, dict):
            content = str(raw.get("content") or raw.get("text") or "")
            kind = _memory_kind(raw.get("kind", "semantic"))
            importance = float(raw.get("importance", 0.7))
            confidence = float(raw.get("confidence", 0.8))
            source = str(raw.get("source") or default_source)
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
        )


def _memory_kind(value: object) -> MemoryKind:
    kind = str(value).strip().lower()
    if kind not in VALID_KINDS:
        raise ValueError(f"unsupported Hermes fact kind: {kind}")
    return kind  # type: ignore[return-value]
