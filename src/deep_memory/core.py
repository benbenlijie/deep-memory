from __future__ import annotations

import math
import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
from uuid import uuid4

MemoryKind = Literal["working", "episodic", "semantic", "procedural"]
ConflictStatus = Literal["active", "candidate", "resolved", "superseded", "deprecated"]
RetrievalBackend = Literal["local", "jieba"]


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class MemoryRecord:
    id: str
    content: str
    kind: MemoryKind
    importance: float
    confidence: float
    source: str | None
    created_at: str
    updated_at: str
    expires_at: str | None = None
    conflict_status: ConflictStatus = "active"
    supersedes_id: str | None = None
    superseded_by_id: str | None = None


@dataclass(frozen=True)
class SearchResult:
    record: MemoryRecord
    score: float


@dataclass(frozen=True)
class ConflictResolution:
    record: MemoryRecord
    status: ConflictStatus
    confirmed_by_user: bool
    superseded: tuple[MemoryRecord, ...]


class DeepMemory:
    """Local-first persistent memory store for AI agents."""

    def __init__(self, path: str | Path = "deep-memory.db") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                kind TEXT NOT NULL CHECK (kind IN ('working','episodic','semantic','procedural')),
                importance REAL NOT NULL DEFAULT 0.5,
                confidence REAL NOT NULL DEFAULT 0.8,
                source TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                expires_at TEXT,
                conflict_status TEXT NOT NULL DEFAULT 'active'
                    CHECK (conflict_status IN ('active','candidate','resolved','superseded','deprecated')),
                supersedes_id TEXT,
                superseded_by_id TEXT
            );
            CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(
                content, kind, source, content='memories', content_rowid='rowid'
            );
            CREATE TRIGGER IF NOT EXISTS memories_ai AFTER INSERT ON memories BEGIN
              INSERT INTO memories_fts(rowid, content, kind, source)
              VALUES (new.rowid, new.content, new.kind, COALESCE(new.source, ''));
            END;
            CREATE TRIGGER IF NOT EXISTS memories_ad AFTER DELETE ON memories BEGIN
              INSERT INTO memories_fts(memories_fts, rowid, content, kind, source)
              VALUES('delete', old.rowid, old.content, old.kind, COALESCE(old.source, ''));
            END;
            CREATE TRIGGER IF NOT EXISTS memories_au AFTER UPDATE ON memories BEGIN
              INSERT INTO memories_fts(memories_fts, rowid, content, kind, source)
              VALUES('delete', old.rowid, old.content, old.kind, COALESCE(old.source, ''));
              INSERT INTO memories_fts(rowid, content, kind, source)
              VALUES (new.rowid, new.content, new.kind, COALESCE(new.source, ''));
            END;
            """
        )
        self._migrate_schema()
        self.conn.commit()

    def _migrate_schema(self) -> None:
        columns = {row["name"] for row in self.conn.execute("PRAGMA table_info(memories)")}
        migrations = {
            "conflict_status": "ALTER TABLE memories ADD COLUMN conflict_status TEXT NOT NULL DEFAULT 'active'",
            "supersedes_id": "ALTER TABLE memories ADD COLUMN supersedes_id TEXT",
            "superseded_by_id": "ALTER TABLE memories ADD COLUMN superseded_by_id TEXT",
        }
        for column, statement in migrations.items():
            if column not in columns:
                self.conn.execute(statement)

    def add(
        self,
        content: str,
        *,
        kind: MemoryKind = "semantic",
        importance: float = 0.5,
        confidence: float = 0.8,
        source: str | None = None,
        expires_at: str | None = None,
    ) -> MemoryRecord:
        if not content.strip():
            raise ValueError("memory content cannot be empty")
        importance = _clamp01(importance)
        confidence = _clamp01(confidence)
        now = utcnow()
        record_id = str(uuid4())
        self.conn.execute(
            """
            INSERT INTO memories(id, content, kind, importance, confidence, source, created_at, updated_at, expires_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (record_id, content.strip(), kind, importance, confidence, source, now, now, expires_at),
        )
        self.conn.commit()
        return self.get(record_id)

    def get(self, record_id: str) -> MemoryRecord:
        row = self.conn.execute("SELECT * FROM memories WHERE id = ?", (record_id,)).fetchone()
        if row is None:
            raise KeyError(record_id)
        return _row_to_record(row)

    def search(
        self,
        query: str,
        *,
        limit: int = 5,
        kind: MemoryKind | None = None,
        now: datetime | None = None,
        backend: RetrievalBackend = "local",
    ) -> list[SearchResult]:
        query = query.strip()
        if not query:
            return []
        query_tokens = _query_tokens(query, backend=backend)
        fts_query = " OR ".join(f'"{token}"' for token in query_tokens)
        params: list[object] = [fts_query]
        kind_sql = ""
        if kind:
            kind_sql = "AND m.kind = ?"
            params.append(kind)
        params.append(limit)
        rows = self.conn.execute(
            f"""
            SELECT m.*, bm25(memories_fts) AS lexical_score
            FROM memories_fts
            JOIN memories m ON m.rowid = memories_fts.rowid
            WHERE memories_fts MATCH ? {kind_sql}
            ORDER BY lexical_score ASC
            LIMIT ?
            """,
            params,
        ).fetchall()
        if not rows:
            like_terms = query_tokens[:8]
            like_where = " OR ".join("content LIKE ?" for _ in like_terms)
            like_params: list[object] = [f"%{term}%" for term in like_terms]
            if kind:
                like_where = f"({like_where}) AND kind = ?"
                like_params.append(kind)
            like_params.append(limit)
            rows = self.conn.execute(
                f"SELECT *, -1.0 AS lexical_score FROM memories WHERE {like_where} LIMIT ?",
                like_params,
            ).fetchall()
        results: list[SearchResult] = []
        seen_ids: set[str] = set()
        ref = now or datetime.now(timezone.utc)
        for row in rows:
            record = _row_to_record(row)
            seen_ids.add(record.id)
            decay = forgetting_decay(record.created_at, record.importance, ref)
            lexical = 1.0 / (1.0 + abs(float(row["lexical_score"])))
            score = lexical * 0.55 + record.importance * 0.25 + record.confidence * 0.15 + decay * 0.05
            results.append(SearchResult(record=record, score=round(score, 4)))
        if len(results) < limit:
            supplement_sql = "AND kind = ?" if kind else ""
            supplement_params: list[object] = [kind] if kind else []
            supplement_rows = self.conn.execute(
                f"""
                SELECT *, 0.0 AS lexical_score
                FROM memories
                WHERE conflict_status != 'superseded' {supplement_sql}
                ORDER BY importance DESC, updated_at DESC
                LIMIT 200
                """,
                supplement_params,
            ).fetchall()
            for row in supplement_rows:
                record = _row_to_record(row)
                if record.id in seen_ids:
                    continue
                seen_ids.add(record.id)
                decay = forgetting_decay(record.created_at, record.importance, ref)
                lexical = _token_overlap_score(query, record.content, backend=backend)
                score = lexical * 0.55 + record.importance * 0.25 + record.confidence * 0.15 + decay * 0.05
                results.append(SearchResult(record=record, score=round(score, 4)))
        return sorted(results, key=lambda r: r.score, reverse=True)[:limit]

    def resolve_conflict(
        self,
        content: str,
        *,
        supersedes: list[str] | tuple[str, ...],
        source: str | None = None,
        confirmed_by_user: bool = False,
        importance: float = 0.5,
        confidence: float = 0.8,
    ) -> ConflictResolution:
        if not supersedes:
            raise ValueError("resolve_conflict requires at least one superseded memory id")
        old_records = [self.get(record_id) for record_id in supersedes]
        source_trail = _source_trail(source, old_records)
        status: ConflictStatus = "resolved" if confirmed_by_user else "candidate"
        new = self.add(
            content,
            kind="semantic",
            importance=importance,
            confidence=confidence,
            source=source_trail,
        )
        now = utcnow()
        self.conn.execute(
            """
            UPDATE memories
            SET conflict_status = ?, supersedes_id = ?, updated_at = ?
            WHERE id = ?
            """,
            (status, old_records[0].id, now, new.id),
        )
        if confirmed_by_user:
            for old in old_records:
                self.conn.execute(
                    """
                    UPDATE memories
                    SET conflict_status = 'superseded', superseded_by_id = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (new.id, now, old.id),
                )
        self.conn.commit()
        return ConflictResolution(
            record=self.get(new.id),
            status=status,
            confirmed_by_user=confirmed_by_user,
            superseded=tuple(self.get(old.id) for old in old_records),
        )

    def deprecate(self, record_id: str, *, source: str | None = None) -> MemoryRecord:
        current = self.get(record_id)
        now = utcnow()
        next_source = _source_trail(source, [current])
        self.conn.execute(
            """
            UPDATE memories
            SET conflict_status = 'deprecated', source = ?, updated_at = ?
            WHERE id = ?
            """,
            (next_source, now, record_id),
        )
        self.conn.commit()
        return self.get(record_id)

    def conflict_candidates(self, content: str, *, limit: int = 5) -> list[SearchResult]:
        tokens = [t for t in _query_tokens(content) if len(t) >= 2]
        if not tokens:
            return []
        return self.search(" ".join(tokens[:8]), limit=limit, kind="semantic")

    def conflicts(self, *, include_superseded: bool = False) -> list[SearchResult]:
        statuses: tuple[str, ...] = ("candidate", "resolved", "deprecated")
        if include_superseded:
            statuses = statuses + ("superseded",)
        placeholders = ", ".join("?" for _ in statuses)
        rows = self.conn.execute(
            f"""
            SELECT *, 0.0 AS lexical_score
            FROM memories
            WHERE conflict_status IN ({placeholders})
            ORDER BY updated_at DESC
            """,
            statuses,
        ).fetchall()
        return [SearchResult(record=_row_to_record(row), score=1.0) for row in rows]

    def stats(self) -> dict[str, int]:
        rows = self.conn.execute("SELECT kind, COUNT(*) AS n FROM memories GROUP BY kind").fetchall()
        out = {"working": 0, "episodic": 0, "semantic": 0, "procedural": 0}
        out.update({row["kind"]: row["n"] for row in rows})
        out["total"] = sum(out.values())
        return out

    def close(self) -> None:
        self.conn.close()


def forgetting_decay(created_at: str, importance: float, now: datetime | None = None) -> float:
    created = datetime.fromisoformat(created_at)
    ref = now or datetime.now(timezone.utc)
    age_days = max((ref - created).total_seconds() / 86400, 0)
    half_life = 1 + 30 * _clamp01(importance)
    return math.exp(-age_days / half_life)


def _query_tokens(text: str, backend: RetrievalBackend = "local") -> list[str]:
    """Return query tokens for mixed Chinese/English memory text.

    The default ``local`` backend is the lightweight Chinese baseline: preserve
    ASCII words, extract meaningful Chinese runs, and add character bigrams so
    SQLite FTS5 can recall short Chinese phrases without external installs.

    The optional ``jieba`` backend keeps the same local tokens and adds jieba
    Chinese word segmentation when the ``deep-memory[retrieval]`` extra is
    installed. That gives a tokenizer seam without making the base install
    heavier.
    """
    if backend not in {"local", "jieba"}:
        raise ValueError(f"unknown retrieval backend: {backend}")
    text = text.strip()
    ascii_words = re.findall(r"[A-Za-z0-9][A-Za-z0-9_./+-]*", text)
    zh_runs = re.findall(r"[\u4e00-\u9fff]+", text)
    zh_bigrams = [run[i : i + 2] for run in zh_runs for i in range(max(len(run) - 1, 0))]
    tokens = ascii_words + zh_runs + zh_bigrams
    if backend == "jieba":
        tokens.extend(_jieba_tokens(zh_runs))
    return list(dict.fromkeys(tokens)) or [text]


def _jieba_tokens(zh_runs: list[str]) -> list[str]:
    try:
        import jieba  # type: ignore[import-not-found]
    except ImportError as exc:  # pragma: no cover - exercised only without optional extra
        raise RuntimeError(
            "jieba retrieval backend requires the optional extra: "
            "pip install 'deep-memory[retrieval]'"
        ) from exc
    return [token for run in zh_runs for token in jieba.cut(run) if token.strip()]


def _token_overlap_score(query: str, content: str, backend: RetrievalBackend = "local") -> float:
    query_tokens = set(_query_tokens(query, backend=backend))
    if not query_tokens:
        return 0.0
    content_tokens = set(_query_tokens(content, backend=backend))
    return len(query_tokens & content_tokens) / len(query_tokens)


def _row_to_record(row: sqlite3.Row) -> MemoryRecord:
    return MemoryRecord(
        id=row["id"],
        content=row["content"],
        kind=row["kind"],
        importance=float(row["importance"]),
        confidence=float(row["confidence"]),
        source=row["source"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        expires_at=row["expires_at"],
        conflict_status=row["conflict_status"],
        supersedes_id=row["supersedes_id"],
        superseded_by_id=row["superseded_by_id"],
    )


def _source_trail(source: str | None, superseded: list[MemoryRecord]) -> str | None:
    old_sources = [record.source for record in superseded if record.source]
    if not source and not old_sources:
        return None
    trail_parts = []
    if source:
        trail_parts.append(source)
    if old_sources:
        trail_parts.append("supersedes " + ", ".join(old_sources))
    return "; ".join(trail_parts)


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))
