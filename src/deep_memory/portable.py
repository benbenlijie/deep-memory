from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any, cast

from .core import DeepMemory, MemoryRecord, TRUST_LEVEL_FACTORS, TrustLevel, build_idempotency_key, utcnow

PORTABLE_SCHEMA_VERSION = 1
PORTABLE_RECORDS_FILE = "memories.jsonl"
PORTABLE_MANIFEST_FILE = "manifest.json"


def record_to_portable(record: MemoryRecord) -> dict[str, Any]:
    payload = asdict(record)
    payload["source_info"] = asdict(record.source_info)
    payload["portable_schema_version"] = PORTABLE_SCHEMA_VERSION
    payload["idempotency_key"] = portable_idempotency_key(payload)
    payload.pop("workspace", None)
    payload.pop("tenant", None)
    payload.pop("user_id", None)
    return payload


def export_portable(
    db: str | Path,
    output: str | Path,
    *,
    include_deprecated: bool = False,
    as_of: str | None = None,
) -> dict[str, Any]:
    out_dir = Path(output)
    out_dir.mkdir(parents=True, exist_ok=True)
    mem = DeepMemory(db)
    try:
        records = [record_to_portable(record) for record in mem.export_records(include_deprecated=include_deprecated, as_of=as_of)]
    finally:
        mem.close()
    records_path = out_dir / PORTABLE_RECORDS_FILE
    content = "".join(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n" for record in records)
    records_path.write_text(content, encoding="utf-8")
    manifest = {
        "schema_version": PORTABLE_SCHEMA_VERSION,
        "record_count": len(records),
        "checksum": sha256(content.encode("utf-8")).hexdigest(),
        "exported_at": utcnow(),
        "records_file": PORTABLE_RECORDS_FILE,
    }
    (out_dir / PORTABLE_MANIFEST_FILE).write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def import_portable(db: str | Path, portable_path: str | Path, *, merge: bool = False) -> dict[str, int]:
    if not merge:
        raise ValueError("portable import currently requires --merge")
    records, _manifest = load_portable_records(portable_path)
    mem = DeepMemory(db)
    imported = 0
    skipped = 0
    updated = 0
    try:
        for raw in records:
            record = upgrade_portable_record(raw)
            key = portable_idempotency_key(record)
            existing_row = mem.conn.execute(
                "SELECT * FROM memories WHERE idempotency_key = ?", (key,)
            ).fetchone()
            if existing_row is None:
                existing_row = _find_merge_conflict(mem, record)
            if existing_row is None:
                mem.add(
                    str(record["content"]),
                    kind=str(record.get("kind", "semantic")),  # type: ignore[arg-type]
                    importance=float(record.get("importance", 0.5)),
                    confidence=float(record.get("confidence", 0.8)),
                    source=record.get("source"),
                    expires_at=record.get("expires_at"),
                    event_time=record.get("event_time"),
                    valid_until=record.get("valid_until"),
                    scope=str(record.get("scope", "global")),  # type: ignore[arg-type]
                    scope_id=record.get("scope_id"),
                    agent=record.get("agent"),
                    idempotency_key=key,
                    duplicate_policy="skip",
                )
                imported += 1
                continue
            existing = _row_to_dict(existing_row)
            if should_replace(existing, record):
                _update_existing(mem, existing["id"], record, key)
                updated += 1
            else:
                skipped += 1
        return {"imported": imported, "updated": updated, "skipped": skipped}
    finally:
        mem.close()


def load_portable_records(portable_path: str | Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    path = Path(portable_path)
    if path.is_dir():
        manifest_path = path / PORTABLE_MANIFEST_FILE
        records_path = path / PORTABLE_RECORDS_FILE
    else:
        manifest_path = path.with_name(PORTABLE_MANIFEST_FILE)
        records_path = path
    manifest: dict[str, Any] = {}
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    records = [json.loads(line) for line in records_path.read_text(encoding="utf-8").splitlines() if line]
    schema_version = int(manifest.get("schema_version", records[0].get("portable_schema_version", 0) if records else PORTABLE_SCHEMA_VERSION))
    if schema_version > PORTABLE_SCHEMA_VERSION:
        raise ValueError(f"unsupported portable schema_version: {schema_version}")
    return records, manifest


def upgrade_portable_record(record: dict[str, Any]) -> dict[str, Any]:
    upgraded = dict(record)
    if "source" not in upgraded and "source_info" in upgraded:
        info = upgraded["source_info"]
        if isinstance(info, dict):
            upgraded["source"] = {
                "agent": info.get("agent") or "",
                "trust_level": info.get("trust_level", "agent-auto"),
                "origin_type": info.get("origin_type", "imported"),
            }
    upgraded.setdefault("kind", "semantic")
    upgraded.setdefault("importance", 0.5)
    upgraded.setdefault("confidence", 0.8)
    upgraded.setdefault("scope", "global")
    if "scope_id" not in upgraded:
        if upgraded["scope"] in {"workspace", "project"}:
            upgraded["scope_id"] = upgraded.get("workspace")
        elif upgraded["scope"] == "tenant":
            upgraded["scope_id"] = upgraded.get("tenant")
        elif upgraded["scope"] == "user":
            upgraded["scope_id"] = upgraded.get("user_id")
        else:
            upgraded["scope_id"] = None
    for legacy_key in ("workspace", "tenant", "user_id"):
        upgraded.pop(legacy_key, None)
    upgraded.setdefault("event_time", upgraded.get("created_at") or utcnow())
    upgraded.setdefault("created_at", upgraded["event_time"])
    upgraded.setdefault("updated_at", upgraded["created_at"])
    return upgraded


def diff_databases(db_a: str | Path, db_b: str | Path) -> dict[str, list[dict[str, Any]]]:
    a_records = _records_by_portable_key(db_a)
    b_records = _records_by_portable_key(db_b)
    only_in_a: list[dict[str, Any]] = []
    only_in_b: list[dict[str, Any]] = []
    conflicts: list[dict[str, Any]] = []
    matched_b: set[str] = set()
    for key in sorted(a_records):
        left = a_records[key]
        if key in b_records:
            right = b_records[key]
            matched_b.add(key)
        else:
            conflict_key = portable_conflict_family(left)
            match_key = next(
                (
                    b_key
                    for b_key, candidate in b_records.items()
                    if b_key not in matched_b and portable_conflict_family(candidate) == conflict_key
                ),
                None,
            )
            if match_key is None:
                only_in_a.append(_diff_payload(left))
                continue
            right = b_records[match_key]
            matched_b.add(match_key)
        if _content_signature(left) != _content_signature(right):
            winner = "a" if should_replace(right, left) else "b"
            conflicts.append(
                {
                    "key": portable_conflict_family(left),
                    "a": _diff_payload(left),
                    "b": _diff_payload(right),
                    "winner": winner,
                }
            )
    for key in sorted(b_records.keys() - matched_b):
        only_in_b.append(_diff_payload(b_records[key]))
    return {"only_in_a": only_in_a, "only_in_b": only_in_b, "conflicts": conflicts}


def _find_merge_conflict(mem: DeepMemory, incoming: dict[str, Any]) -> Any | None:
    incoming_family = portable_conflict_family(incoming)
    rows = mem.conn.execute(
        """
        SELECT *
        FROM memories
        WHERE kind = ? AND scope = ?
          AND COALESCE(scope_id, '') = ?
          AND COALESCE(agent, '') = ?
          AND conflict_status NOT IN ('deprecated', 'superseded', 'archived')
        ORDER BY updated_at DESC
        """,
        (
            str(incoming.get("kind", "semantic")),
            str(incoming.get("scope", "global")),
            str(incoming.get("scope_id") or ""),
            str(incoming.get("agent") or ""),
        ),
    ).fetchall()
    for row in rows:
        if portable_conflict_family(_row_to_dict(row)) == incoming_family:
            return row
    return None


def portable_idempotency_key(record: dict[str, Any]) -> str:
    return build_idempotency_key(
        str(record.get("content", "")),
        kind=str(record.get("kind", "semantic")),  # type: ignore[arg-type]
        source=None,
        scope=str(record.get("scope", "global")),  # type: ignore[arg-type]
        scope_id=record.get("scope_id"),
        agent=record.get("agent"),
    )


def portable_conflict_family(record: dict[str, Any]) -> str:
    """Return a coarse semantic family for cross-machine conflict detection."""
    content = str(record.get("content", "")).strip()
    head = content
    for marker in ("：", ":", " - ", " — "):
        if marker in head:
            head = head.split(marker, 1)[0]
            break
    if head == content:
        words = head.split()
        if len(words) > 1 and len(words[0]) >= 4:
            head = words[0]
    head = " ".join(head.split()).lower()
    parts = [
        "v1",
        str(record.get("kind", "semantic")),
        str(record.get("scope", "global")),
        str(record.get("scope_id") or ""),
        str(record.get("agent") or ""),
        head,
    ]
    return sha256("\x1f".join(parts).encode("utf-8")).hexdigest()


def should_replace(existing: dict[str, Any], incoming: dict[str, Any]) -> bool:
    existing_trust = _trust_factor(existing)
    incoming_trust = _trust_factor(incoming)
    if incoming_trust != existing_trust:
        return incoming_trust > existing_trust
    return _event_time(incoming) > _event_time(existing)


def _update_existing(mem: DeepMemory, record_id: str, record: dict[str, Any], key: str) -> None:
    now = utcnow()
    mem.conn.execute(
        """
        UPDATE memories
        SET content = ?, kind = ?, importance = ?, confidence = ?, source = ?, updated_at = ?,
            event_time = ?, valid_until = ?, expires_at = ?, scope = ?, scope_id = ?,
            agent = ?, idempotency_key = ?
        WHERE id = ?
        """,
        (
            str(record["content"]),
            str(record.get("kind", "semantic")),
            float(record.get("importance", 0.5)),
            float(record.get("confidence", 0.8)),
            _serialize_source_for_sql(record.get("source")),
            now,
            record.get("event_time"),
            record.get("valid_until"),
            record.get("expires_at"),
            str(record.get("scope", "global")),
            record.get("scope_id"),
            record.get("agent"),
            key,
            record_id,
        ),
    )
    mem.conn.commit()


def _records_by_portable_key(db: str | Path) -> dict[str, dict[str, Any]]:
    mem = DeepMemory(db)
    try:
        records = [record_to_portable(record) for record in mem.export_records()]
    finally:
        mem.close()
    return {portable_idempotency_key(record): record for record in records}


def _diff_payload(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": record.get("id"),
        "content": record.get("content"),
        "kind": record.get("kind"),
        "scope": record.get("scope"),
        "trust_level": _trust_level(record),
        "event_time": record.get("event_time"),
    }


def _content_signature(record: dict[str, Any]) -> tuple[Any, ...]:
    return (
        record.get("content"),
        record.get("kind"),
        record.get("importance"),
        record.get("confidence"),
        _trust_level(record),
        record.get("event_time"),
    )


def _row_to_dict(row: Any) -> dict[str, Any]:
    return {key: row[key] for key in row.keys()}


def _serialize_source_for_sql(source: Any) -> str | None:
    if source is None:
        return None
    if isinstance(source, str):
        return source
    return json.dumps(source, ensure_ascii=False, sort_keys=True)


def _trust_level(record: dict[str, Any]) -> str:
    source_info = record.get("source_info")
    if isinstance(source_info, dict):
        return str(source_info.get("trust_level", "agent-auto"))
    source = record.get("source")
    if isinstance(source, dict):
        return str(source.get("trust_level", "agent-auto"))
    if isinstance(source, str):
        try:
            parsed = json.loads(source)
        except json.JSONDecodeError:
            return "agent-auto"
        if isinstance(parsed, dict):
            return str(parsed.get("trust_level", "agent-auto"))
    return "agent-auto"


def _trust_factor(record: dict[str, Any]) -> float:
    level = _trust_level(record)
    if level not in TRUST_LEVEL_FACTORS:
        level = "agent-auto"
    return TRUST_LEVEL_FACTORS[cast(TrustLevel, level)]


def _event_time(record: dict[str, Any]) -> datetime:
    value = str(record.get("event_time") or record.get("created_at") or "1970-01-01T00:00:00+00:00")
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
