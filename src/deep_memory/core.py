from __future__ import annotations

import math
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Literal
from uuid import uuid4

MemoryKind = Literal["working", "episodic", "semantic", "procedural"]


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


@dataclass(frozen=True)
class SearchResult:
    record: MemoryRecord
    score: float


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
                expires_at TEXT
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
        self.conn.commit()

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
    ) -> list[SearchResult]:
        query = query.strip()
        if not query:
            return []
        fts_query = " OR ".join(f'"{token}"' for token in _query_tokens(query))
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
            like_terms = list(_query_tokens(query))[:8]
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
        ref = now or datetime.now(timezone.utc)
        for row in rows:
            record = _row_to_record(row)
            decay = forgetting_decay(record.created_at, record.importance, ref)
            lexical = 1.0 / (1.0 + abs(float(row["lexical_score"])))
            score = lexical * 0.55 + record.importance * 0.25 + record.confidence * 0.15 + decay * 0.05
            results.append(SearchResult(record=record, score=round(score, 4)))
        return sorted(results, key=lambda r: r.score, reverse=True)

    def conflict_candidates(self, content: str, *, limit: int = 5) -> list[SearchResult]:
        tokens = [t for t in _query_tokens(content) if len(t) >= 2]
        if not tokens:
            return []
        return self.search(" ".join(tokens[:8]), limit=limit, kind="semantic")

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


def _query_tokens(text: str) -> Iterable[str]:
    text = text.strip()
    words = [w for w in text.replace("，", " ").replace("。", " ").split() if w]
    zh_chars = [c for c in text if "一" <= c <= "鿿"]
    bigrams = ["".join(zh_chars[i : i + 2]) for i in range(max(len(zh_chars) - 1, 0))]
    tokens = words + bigrams
    return list(dict.fromkeys(tokens)) or [text]


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
    )


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))
