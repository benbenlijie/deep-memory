from __future__ import annotations

import json
import os
import subprocess
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from deep_memory.core import DeepMemory, MemoryKind, MemoryRecord, SearchResult, build_idempotency_key

PROTOCOL_VERSION = "deep-memory.adapter.v1"
VALID_KINDS: set[str] = {"working", "episodic", "semantic", "procedural"}


@dataclass(frozen=True)
class AdapterRunResult:
    returncode: int
    imported: tuple[MemoryRecord, ...]


def run_codex_wrapper(
    *,
    db: str | Path,
    task: str,
    command: Sequence[str],
    facts_out: str | Path | None = None,
    limit: int = 5,
    agent_name: str = "codex",
    cwd: str | Path | None = None,
) -> AdapterRunResult:
    """Run a coding-agent command with bounded pre-task recall and explicit fact import.

    The wrapper never reads `.env`, token files, or transcripts. It only reads the
    configured deep-memory database for recall and an explicit JSONL facts file
    after a successful child command.
    """

    if not command:
        raise ValueError("command cannot be empty")

    db_path = Path(db)
    workspace = str(Path(cwd).resolve()) if cwd else None
    memory = DeepMemory(db_path)
    try:
        recalled = memory.search(task, limit=limit, workspace=workspace, caller="wrapper")
    finally:
        memory.close()

    context_block = format_recalled_context(recalled)
    env = sanitized_child_env(os.environ)
    env["DEEP_MEMORY_CONTEXT"] = context_block

    completed = subprocess.run(list(command), cwd=str(cwd) if cwd else None, env=env, check=False)
    if completed.returncode != 0:
        return AdapterRunResult(returncode=completed.returncode, imported=())

    if facts_out is None or not Path(facts_out).exists():
        return AdapterRunResult(returncode=0, imported=())

    imported = tuple(import_agent_facts(db_path, facts_out, agent_name=agent_name, workspace=workspace))
    return AdapterRunResult(returncode=0, imported=imported)


def format_recalled_context(results: Sequence[SearchResult]) -> str:
    if not results:
        return "Relevant durable memories: none."

    lines = ["Relevant durable memories (bounded; use only if relevant):"]
    for idx, result in enumerate(results, start=1):
        record = result.record
        source = f" source={record.source}" if record.source else ""
        lines.append(f"{idx}. [{record.kind} score={result.score}{source}] {record.content}")
    return "\n".join(lines)


def sanitized_child_env(source: os._Environ[str]) -> dict[str, str]:
    """Return an environment with obvious credential-bearing names removed."""

    blocked_fragments = ("TOKEN", "SECRET", "PASSWORD", "PASSWD", "API_KEY", "AUTH", "COOKIE")
    return {key: value for key, value in source.items() if not any(fragment in key.upper() for fragment in blocked_fragments)}


def import_agent_facts(
    db: str | Path,
    facts_jsonl: str | Path,
    *,
    agent_name: str,
    workspace: str | None = None,
) -> list[MemoryRecord]:
    memory = DeepMemory(db)
    records: list[MemoryRecord] = []
    try:
        for fact in iter_agent_facts(facts_jsonl, agent_name=agent_name):
            records.append(
                memory.add(
                    fact["content"],
                    kind=fact["kind"],
                    importance=fact["importance"],
                    confidence=fact["confidence"],
                    source=fact["source"],
                    scope="workspace" if workspace else "global",
                    workspace=workspace,
                    agent=agent_name,
                    idempotency_key=build_idempotency_key(
                        fact["content"],
                        kind=fact["kind"],
                        source=fact["source"],
                        workspace=workspace,
                        agent=agent_name,
                    ),
                    duplicate_policy="skip",
                )
            )
    finally:
        memory.close()
    return records


def iter_agent_facts(facts_jsonl: str | Path, *, agent_name: str):
    path = Path(facts_jsonl)
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid {agent_name} facts JSONL at line {line_no}: {exc.msg}") from exc
            facts = event.get("facts") or []
            if not isinstance(facts, list):
                continue
            session_id = str(event.get("session_id") or event.get("session") or "").strip()
            default_source = f"{agent_name}:{session_id}" if session_id else f"{agent_name}:local"
            for raw in facts:
                if isinstance(raw, str):
                    content = raw
                    kind = "semantic"
                    importance = 0.7
                    confidence = 0.8
                    source = default_source
                elif isinstance(raw, dict):
                    content = str(raw.get("content") or raw.get("text") or "").strip()
                    kind = _memory_kind(raw.get("kind", "semantic"), agent_name=agent_name)
                    importance = float(raw.get("importance", 0.7))
                    confidence = float(raw.get("confidence", 0.8))
                    source = str(raw.get("source") or default_source)
                else:
                    continue
                if content:
                    yield {
                        "content": content,
                        "kind": kind,
                        "importance": importance,
                        "confidence": confidence,
                        "source": source,
                    }


def _memory_kind(value: object, *, agent_name: str) -> MemoryKind:
    kind = str(value).strip().lower()
    if kind not in VALID_KINDS:
        raise ValueError(f"unsupported {agent_name} fact kind: {kind}")
    return kind  # type: ignore[return-value]
