from __future__ import annotations

import json
import math
import os
import re
import shutil
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import sqlite3
from pathlib import Path
from typing import Literal, Mapping
from uuid import uuid4

from .embeddings import EmbeddingBackend, _pack_embedding, get_default_embedding_backend
from .privacy import ensure_memory_content_allowed

MemoryKind = Literal["working", "episodic", "semantic", "procedural"]
ConflictStatus = Literal["active", "candidate", "resolved", "superseded", "deprecated", "archived"]
RetrievalBackend = Literal["local", "jieba"]
MemoryScope = Literal["global", "user", "tenant", "workspace", "project"]
DuplicatePolicy = Literal["create", "skip", "update"]

DEFAULT_HALF_LIFE_DAYS = {
    "working": 7.0,
    "episodic": 30.0,
    "semantic": 180.0,
    "procedural": 365.0,
}


TrustLevel = Literal["user", "verified", "agent-high", "agent-auto", "external", "untrusted"]
OriginType = Literal["explicit", "auto-extracted", "imported"]
SourceInput = str | Mapping[str, object] | None
AgentTrustLevel = Literal["trusted", "known", "untrusted"]

TRUST_LEVEL_FACTORS: dict[TrustLevel, float] = {
    "user": 1.0,
    "verified": 0.9,
    "agent-high": 0.8,
    "agent-auto": 0.5,
    "external": 0.5,
    "untrusted": 0.2,
}
HIGH_TRUST_LEVELS: set[TrustLevel] = {"user", "verified", "agent-high"}
DEFAULT_TRUSTED_AGENTS = ("claude-code", "codex", "hermes", "opencode", "openclaw")
REPUTATION_MIN = 0.3
REPUTATION_MAX = 1.5
REPUTATION_DECAY_PER_DAY = 0.001


@dataclass(frozen=True)
class SourceInfo:
    agent: str | None = None
    trust_level: TrustLevel = "agent-auto"
    origin_type: OriginType = "auto-extracted"
    promoted_by: str | None = None
    promoted_at: str | None = None
    baseline_trust: float | None = field(default=None, compare=False)
    reputation: float = field(default=1.0, compare=False)

    @property
    def trust_factor(self) -> float:
        baseline = self.baseline_trust if self.baseline_trust is not None else TRUST_LEVEL_FACTORS[self.trust_level]
        return round(baseline * self.reputation, 4)


DEFAULT_SOURCE_INFO = SourceInfo()


@dataclass(frozen=True)
class LifecycleConfig:
    half_life_days: dict[MemoryKind, float] | None = None
    consolidation_threshold: float = 0.6
    auto_consolidate_after: int = 1_000

    def half_life_for(self, kind: MemoryKind) -> float:
        values = self.half_life_days or DEFAULT_HALF_LIFE_DAYS
        return float(values.get(kind, DEFAULT_HALF_LIFE_DAYS[kind]))


@dataclass(frozen=True)
class ConsolidationGroup:
    record_ids: tuple[str, ...]
    summary: str
    score: float
    kind: MemoryKind


@dataclass(frozen=True)
class ConsolidationPlan:
    dry_run: bool
    groups: tuple[ConsolidationGroup, ...]
    archived_count: int = 0
    created_count: int = 0


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class MemoryRecord:
    id: str
    content: str
    kind: MemoryKind
    importance: float
    confidence: float
    source: str | dict[str, str] | None
    source_info: SourceInfo
    created_at: str
    updated_at: str
    learned_at: str
    event_time: str
    valid_until: str | None = None
    expires_at: str | None = None
    access_count: int = 0
    last_accessed_at: str | None = None
    conflict_status: ConflictStatus = "active"
    supersedes_id: str | None = None
    superseded_by_id: str | None = None
    scope: MemoryScope = "global"
    workspace: str | None = None
    tenant: str | None = None
    user_id: str | None = None
    agent: str | None = None
    idempotency_key: str | None = None
    embedding_model: str | None = None
    embedding_version: int | None = None
    baseline_trust: float = 0.5
    reputation: float = 1.0
    reputation_updated_at: str | None = None


@dataclass(frozen=True)
class SearchResult:
    record: MemoryRecord
    score: float


@dataclass(frozen=True)
class RetrievalLogEntry:
    id: int
    query: str | None
    query_hash: str
    returned_ids: tuple[str, ...]
    scores: tuple[float, ...]
    caller: str
    created_at: str


@dataclass(frozen=True)
class MemoryFeedbackEntry:
    id: int
    memory_id: str
    helpful: bool
    note: str | None
    created_at: str


@dataclass(frozen=True)
class TrustAuditEntry:
    id: int
    memory_id: str
    action: str
    old_trust: str | None
    new_trust: str | None
    old_reputation: float | None
    new_reputation: float | None
    actor: str | None
    reason: str | None
    at: str


@dataclass(frozen=True)
class InsightCandidate:
    memory_id: str
    content: str
    usage_count: int
    helpful_count: int
    not_helpful_count: int
    helpful_rate: float | None


@dataclass(frozen=True)
class TelemetryReport:
    days: int
    retrieval_count: int
    hit_rate: float
    feedback: dict[str, int]
    weekly_growth_rate: float | None
    score_distribution: dict[str, int]
    high_usage_low_feedback: tuple[InsightCandidate, ...]


@dataclass(frozen=True)
class ConflictResolution:
    record: MemoryRecord
    status: ConflictStatus
    confirmed_by_user: bool
    superseded: tuple[MemoryRecord, ...]


DEFAULT_BACKUP_RETENTION_DAYS = 7
BACKUP_TTL_ENV = "DEEP_MEMORY_BACKUP_TTL_DAYS"


class BackupError(RuntimeError):
    """Raised when a required pre-destructive-operation database backup fails."""


class DeepMemory:
    """Local-first persistent memory store for AI agents."""

    def __init__(
        self,
        path: str | Path = "deep-memory.db",
        *,
        backup_retention_days: int | None = None,
        lazy_prune: bool = True,
        embedding_backend: EmbeddingBackend | None = None,
    ) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.backup_retention_days = self._resolve_backup_retention_days(backup_retention_days)
        self._embedding_backend = embedding_backend
        self._embedding_backend_resolved = embedding_backend is not None
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()
        if lazy_prune:
            self.prune_backups()

    @staticmethod
    def _resolve_backup_retention_days(override: int | None) -> int:
        if override is not None:
            return max(int(override), 0)
        env_value = os.getenv(BACKUP_TTL_ENV)
        if env_value is None:
            return DEFAULT_BACKUP_RETENTION_DAYS
        try:
            return max(int(env_value), 0)
        except ValueError as exc:
            raise ValueError(f"{BACKUP_TTL_ENV} must be an integer number of days") from exc

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
                learned_at TEXT NOT NULL,
                event_time TEXT NOT NULL,
                valid_until TEXT,
                expires_at TEXT,
                access_count INTEGER NOT NULL DEFAULT 0,
                last_accessed_at TEXT,
                conflict_status TEXT NOT NULL DEFAULT 'active'
                    CHECK (conflict_status IN ('active','candidate','resolved','superseded','deprecated','archived')),
                supersedes_id TEXT,
                superseded_by_id TEXT,
                scope TEXT NOT NULL DEFAULT 'global'
                    CHECK (scope IN ('global','user','tenant','workspace','project')),
                workspace TEXT,
                tenant TEXT,
                user_id TEXT,
                agent TEXT,
                idempotency_key TEXT,
                embedding_model TEXT,
                embedding_version INTEGER,
                baseline_trust REAL NOT NULL DEFAULT 0.5,
                reputation REAL NOT NULL DEFAULT 1.0,
                reputation_updated_at TEXT
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
        self.conn.executescript(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS memories_idempotency_key_uq
              ON memories(idempotency_key)
              WHERE idempotency_key IS NOT NULL;
            CREATE TABLE IF NOT EXISTS retrieval_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT,
                query_hash TEXT NOT NULL,
                returned_ids TEXT NOT NULL,
                scores TEXT NOT NULL,
                caller TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS memory_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                memory_id TEXT NOT NULL,
                helpful INTEGER NOT NULL CHECK (helpful IN (0, 1)),
                note TEXT,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS trust_audit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                memory_id TEXT NOT NULL,
                action TEXT NOT NULL,
                old_trust TEXT,
                new_trust TEXT,
                old_reputation REAL,
                new_reputation REAL,
                actor TEXT,
                reason TEXT,
                at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS memory_embeddings (
                memory_id TEXT PRIMARY KEY,
                embedding BLOB NOT NULL,
                model_name TEXT NOT NULL,
                model_version INTEGER NOT NULL,
                dim INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(memory_id) REFERENCES memories(id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS memories_scope_workspace_idx ON memories(scope, workspace);
            CREATE INDEX IF NOT EXISTS memories_tenant_user_idx ON memories(tenant, user_id);
            CREATE INDEX IF NOT EXISTS memories_agent_idx ON memories(agent);
            CREATE INDEX IF NOT EXISTS retrieval_log_created_at_idx ON retrieval_log(created_at);
            CREATE INDEX IF NOT EXISTS memory_feedback_memory_id_idx ON memory_feedback(memory_id);
            CREATE INDEX IF NOT EXISTS memory_feedback_created_at_idx ON memory_feedback(created_at);
            CREATE INDEX IF NOT EXISTS trust_audit_memory_id_idx ON trust_audit(memory_id, at DESC);
            CREATE INDEX IF NOT EXISTS trust_audit_at_idx ON trust_audit(at DESC);
            """
        )
        self.conn.commit()

    def _migrate_schema(self) -> None:
        columns = {row["name"] for row in self.conn.execute("PRAGMA table_info(memories)")}
        migrations = {
            "access_count": "ALTER TABLE memories ADD COLUMN access_count INTEGER NOT NULL DEFAULT 0",
            "last_accessed_at": "ALTER TABLE memories ADD COLUMN last_accessed_at TEXT",
            "conflict_status": "ALTER TABLE memories ADD COLUMN conflict_status TEXT NOT NULL DEFAULT 'active'",
            "supersedes_id": "ALTER TABLE memories ADD COLUMN supersedes_id TEXT",
            "superseded_by_id": "ALTER TABLE memories ADD COLUMN superseded_by_id TEXT",
            "scope": "ALTER TABLE memories ADD COLUMN scope TEXT NOT NULL DEFAULT 'global'",
            "workspace": "ALTER TABLE memories ADD COLUMN workspace TEXT",
            "tenant": "ALTER TABLE memories ADD COLUMN tenant TEXT",
            "user_id": "ALTER TABLE memories ADD COLUMN user_id TEXT",
            "agent": "ALTER TABLE memories ADD COLUMN agent TEXT",
            "idempotency_key": "ALTER TABLE memories ADD COLUMN idempotency_key TEXT",
            "learned_at": "ALTER TABLE memories ADD COLUMN learned_at TEXT",
            "event_time": "ALTER TABLE memories ADD COLUMN event_time TEXT",
            "valid_until": "ALTER TABLE memories ADD COLUMN valid_until TEXT",
            "embedding_model": "ALTER TABLE memories ADD COLUMN embedding_model TEXT",
            "embedding_version": "ALTER TABLE memories ADD COLUMN embedding_version INTEGER",
            "baseline_trust": "ALTER TABLE memories ADD COLUMN baseline_trust REAL NOT NULL DEFAULT 0.5",
            "reputation": "ALTER TABLE memories ADD COLUMN reputation REAL NOT NULL DEFAULT 1.0",
            "reputation_updated_at": "ALTER TABLE memories ADD COLUMN reputation_updated_at TEXT",
        }
        for column, statement in migrations.items():
            if column not in columns:
                self.conn.execute(statement)
        self.conn.execute("UPDATE memories SET learned_at = created_at WHERE learned_at IS NULL")
        self.conn.execute("UPDATE memories SET event_time = created_at WHERE event_time IS NULL")
        self.conn.execute("UPDATE memories SET reputation = 1.0 WHERE reputation IS NULL")
        self._init_agent_registry()
        self._backfill_agent_registry()
        self._backfill_baseline_trust()
        table_sql = self.conn.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'memories'"
        ).fetchone()["sql"]
        if "conflict_status IN ('active','candidate','resolved','superseded','deprecated')" in table_sql:
            self._rebuild_memories_table()

    def _rebuild_memories_table(self) -> None:
        """Rebuild legacy tables whose CHECK constraints cannot be altered in place."""
        old_columns = [row["name"] for row in self.conn.execute("PRAGMA table_info(memories)")]
        new_columns = [
            "id",
            "content",
            "kind",
            "importance",
            "confidence",
            "source",
            "created_at",
            "updated_at",
            "learned_at",
            "event_time",
            "valid_until",
            "expires_at",
            "access_count",
            "last_accessed_at",
            "conflict_status",
            "supersedes_id",
            "superseded_by_id",
            "scope",
            "workspace",
            "tenant",
            "user_id",
            "agent",
            "idempotency_key",
            "embedding_model",
            "embedding_version",
            "baseline_trust",
            "reputation",
            "reputation_updated_at",
        ]
        self._backup_before_destructive_operation("rebuild_memories_table")
        copy_columns = [column for column in new_columns if column in old_columns]
        column_sql = ", ".join(copy_columns)
        self.conn.executescript(
            """
            DROP TRIGGER IF EXISTS memories_ai;
            DROP TRIGGER IF EXISTS memories_ad;
            DROP TRIGGER IF EXISTS memories_au;
            DROP TABLE IF EXISTS memories_fts;
            ALTER TABLE memories RENAME TO memories_old;
            CREATE TABLE memories (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                kind TEXT NOT NULL CHECK (kind IN ('working','episodic','semantic','procedural')),
                importance REAL NOT NULL DEFAULT 0.5,
                confidence REAL NOT NULL DEFAULT 0.8,
                source TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                learned_at TEXT,
                event_time TEXT,
                valid_until TEXT,
                expires_at TEXT,
                access_count INTEGER NOT NULL DEFAULT 0,
                last_accessed_at TEXT,
                conflict_status TEXT NOT NULL DEFAULT 'active'
                    CHECK (conflict_status IN ('active','candidate','resolved','superseded','deprecated','archived')),
                supersedes_id TEXT,
                superseded_by_id TEXT,
                scope TEXT NOT NULL DEFAULT 'global'
                    CHECK (scope IN ('global','user','tenant','workspace','project')),
                workspace TEXT,
                tenant TEXT,
                user_id TEXT,
                agent TEXT,
                idempotency_key TEXT,
                embedding_model TEXT,
                embedding_version INTEGER,
                baseline_trust REAL NOT NULL DEFAULT 0.5,
                reputation REAL NOT NULL DEFAULT 1.0,
                reputation_updated_at TEXT
            );
            """
        )
        self.conn.execute(
            f"INSERT INTO memories({column_sql}) SELECT {column_sql} FROM memories_old"
        )
        self.conn.execute("DROP TABLE memories_old")
        self.conn.executescript(
            """
            CREATE VIRTUAL TABLE memories_fts USING fts5(
                content, kind, source, content='memories', content_rowid='rowid'
            );
            CREATE TRIGGER memories_ai AFTER INSERT ON memories BEGIN
              INSERT INTO memories_fts(rowid, content, kind, source)
              VALUES (new.rowid, new.content, new.kind, COALESCE(new.source, ''));
            END;
            CREATE TRIGGER memories_ad AFTER DELETE ON memories BEGIN
              INSERT INTO memories_fts(memories_fts, rowid, content, kind, source)
              VALUES('delete', old.rowid, old.content, old.kind, COALESCE(old.source, ''));
            END;
            CREATE TRIGGER memories_au AFTER UPDATE ON memories BEGIN
              INSERT INTO memories_fts(memories_fts, rowid, content, kind, source)
              VALUES('delete', old.rowid, old.content, old.kind, COALESCE(old.source, ''));
              INSERT INTO memories_fts(rowid, content, kind, source)
              VALUES (new.rowid, new.content, new.kind, COALESCE(new.source, ''));
            END;
            INSERT INTO memories_fts(rowid, content, kind, source)
            SELECT rowid, content, kind, COALESCE(source, '') FROM memories;
            """
        )

    def _init_agent_registry(self) -> None:
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS agent_registry (
                agent TEXT PRIMARY KEY,
                trusted INTEGER NOT NULL DEFAULT 0,
                first_seen_at TEXT NOT NULL,
                last_seen_at TEXT NOT NULL,
                note TEXT
            )
            """
        )
        now = utcnow()
        for agent in DEFAULT_TRUSTED_AGENTS:
            self.conn.execute(
                """
                INSERT OR IGNORE INTO agent_registry(agent, trusted, first_seen_at, last_seen_at, note)
                VALUES (?, 1, ?, ?, ?)
                """,
                (agent, now, now, "default trusted agent"),
            )

    def _register_agent(self, agent: str | None, *, trusted: int = 0, note: str | None = None) -> None:
        if not agent or agent.lower() in {"human", "user"}:
            return
        now = utcnow()
        self.conn.execute(
            """
            INSERT INTO agent_registry(agent, trusted, first_seen_at, last_seen_at, note)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(agent) DO UPDATE SET last_seen_at = excluded.last_seen_at
            """,
            (agent, trusted, now, now, note),
        )

    def _agent_trusted_value(self, agent: str | None) -> int | None:
        if not agent or agent.lower() in {"human", "user"}:
            return None
        row = self.conn.execute("SELECT trusted FROM agent_registry WHERE agent = ?", (agent,)).fetchone()
        if row is None:
            return None
        return int(row["trusted"])

    def _backfill_agent_registry(self) -> None:
        rows = self.conn.execute("SELECT source, agent FROM memories").fetchall()
        for row in rows:
            source_info = parse_source_info(deserialize_source(row["source"]))
            agent = row["agent"] or source_info.agent
            self._register_agent(agent)

    def _backfill_baseline_trust(self) -> None:
        rows = self.conn.execute("SELECT id, source FROM memories").fetchall()
        for row in rows:
            source = deserialize_source(row["source"])
            baseline = self._baseline_for_source(source, register_unknown=False)
            self.conn.execute("UPDATE memories SET baseline_trust = ? WHERE id = ?", (baseline, row["id"]))

    def _baseline_for_source(self, source: SourceInput, *, register_unknown: bool = True) -> float:
        info = parse_source_info(source)
        if info.trust_level == "user" or (info.origin_type == "explicit" and (info.agent or "").lower() in {"human", "user"}):
            return 1.0
        if info.trust_level == "untrusted":
            return 0.2
        if isinstance(source, str) and _is_external_url(source):
            return 0.2
        if info.origin_type == "imported" and not info.agent:
            return 0.3
        if info.trust_level == "external":
            return 0.5
        trusted_value = self._agent_trusted_value(info.agent)
        known_agent = trusted_value is not None
        if register_unknown:
            self._register_agent(info.agent)
        if info.origin_type == "explicit":
            if trusted_value == 1:
                return 0.85
            return 0.7
        if info.origin_type == "auto-extracted":
            if trusted_value == 1:
                return 0.65
            if known_agent:
                return 0.55
            return 0.45
        if info.origin_type == "imported" and info.agent:
            return 0.35
        return TRUST_LEVEL_FACTORS.get(info.trust_level, 0.5)

    def add(
        self,
        content: str,
        *,
        kind: MemoryKind = "semantic",
        importance: float = 0.5,
        confidence: float = 0.8,
        source: SourceInput = None,
        expires_at: str | None = None,
        event_time: str | None = None,
        valid_until: str | None = None,
        scope: MemoryScope = "workspace",
        workspace: str | None = None,
        tenant: str | None = None,
        user_id: str | None = None,
        agent: str | None = None,
        idempotency_key: str | None = None,
        duplicate_policy: DuplicatePolicy = "create",
    ) -> MemoryRecord:
        if not content.strip():
            raise ValueError("memory content cannot be empty")
        ensure_memory_content_allowed(content)
        importance = _clamp01(importance)
        confidence = _clamp01(confidence)
        if scope not in {"global", "user", "tenant", "workspace", "project"}:
            raise ValueError(f"unsupported memory scope: {scope}")
        if duplicate_policy not in {"create", "skip", "update"}:
            raise ValueError(f"unsupported duplicate policy: {duplicate_policy}")
        if scope in {"workspace", "project"} and workspace is None:
            workspace = _infer_workspace_from_cwd()
        normalized_event_time = _validate_iso_datetime(event_time, "event_time") or utcnow()
        normalized_valid_until = _validate_iso_datetime(valid_until, "valid_until")
        normalized_content = content.strip()
        stored_source = serialize_source(source)
        source_info = parse_source_info(deserialize_source(stored_source))
        baseline_trust = self._baseline_for_source(deserialize_source(stored_source))
        conflict_target = self._find_trust_conflict(normalized_content, kind, source_info)
        initial_status: ConflictStatus = "candidate" if conflict_target else "active"
        supersedes_id = conflict_target.id if conflict_target else None
        record_id: str | None = None
        if idempotency_key and duplicate_policy != "create":
            existing = self.conn.execute(
                "SELECT * FROM memories WHERE idempotency_key = ?", (idempotency_key,)
            ).fetchone()
            if existing is not None:
                if duplicate_policy == "skip":
                    return _row_to_record(existing)
                now = utcnow()
                self.conn.execute(
                    """
                    UPDATE memories
                    SET content = ?, kind = ?, importance = ?, confidence = ?, source = ?,
                        updated_at = ?, expires_at = ?, event_time = ?, valid_until = ?, scope = ?, workspace = ?, tenant = ?,
                        user_id = ?, agent = ?, conflict_status = ?, supersedes_id = ?, baseline_trust = ?, reputation = ?, reputation_updated_at = ?
                    WHERE idempotency_key = ?
                    """,
                    (
                        normalized_content,
                        kind,
                        importance,
                        confidence,
                        stored_source,
                        now,
                        expires_at,
                        normalized_event_time if event_time is not None else existing["event_time"] or existing["created_at"],
                        normalized_valid_until,
                        scope,
                        workspace,
                        tenant,
                        user_id,
                        agent,
                        initial_status,
                        supersedes_id,
                        baseline_trust,
                        1.0,
                        now,
                        idempotency_key,
                    ),
                )
                self._reverse_trust_conflicts(normalized_content, source_info, conflict_with_id=existing["id"], exclude_ids={existing["id"]})
                self._store_embedding_if_available(existing["id"], normalized_content)
                self.conn.commit()
                return self.get(existing["id"])
        now = utcnow()
        record_id = str(uuid4())
        self.conn.execute(
            """
            INSERT INTO memories(
                id, content, kind, importance, confidence, source, created_at, updated_at, learned_at,
                event_time, valid_until, expires_at, conflict_status, supersedes_id, scope, workspace, tenant, user_id, agent, idempotency_key,
                baseline_trust, reputation, reputation_updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record_id,
                normalized_content,
                kind,
                importance,
                confidence,
                stored_source,
                now,
                now,
                now,
                normalized_event_time,
                normalized_valid_until,
                expires_at,
                initial_status,
                supersedes_id,
                scope,
                workspace,
                tenant,
                user_id,
                agent,
                idempotency_key,
                baseline_trust,
                1.0,
                now,
            ),
        )
        self._reverse_trust_conflicts(normalized_content, source_info, conflict_with_id=record_id, exclude_ids={record_id})
        self._store_embedding_if_available(record_id, normalized_content)
        self.conn.commit()
        return self.get(record_id)

    def _resolve_embedding_backend(self) -> EmbeddingBackend | None:
        if not self._embedding_backend_resolved:
            if os.environ.get("DEEP_MEMORY_EMBEDDING", "off").lower() not in {"1", "true", "yes", "on"}:
                self._embedding_backend = None
            else:
                self._embedding_backend = get_default_embedding_backend()
            self._embedding_backend_resolved = True
        return self._embedding_backend

    def _store_embedding_if_available(self, memory_id: str, content: str) -> None:
        backend = self._resolve_embedding_backend()
        if backend is None:
            return
        vector = backend.embed(content)
        now = utcnow()
        self.conn.execute(
            """
            INSERT INTO memory_embeddings(memory_id, embedding, model_name, model_version, dim, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(memory_id) DO UPDATE SET
                embedding = excluded.embedding,
                model_name = excluded.model_name,
                model_version = excluded.model_version,
                dim = excluded.dim,
                created_at = excluded.created_at
            """,
            (memory_id, _pack_embedding(vector), backend.model_name, backend.model_version, len(vector), now),
        )
        self.conn.execute(
            """
            UPDATE memories
            SET embedding_model = ?, embedding_version = ?, updated_at = ?
            WHERE id = ?
            """,
            (backend.model_name, backend.model_version, now, memory_id),
        )

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
        as_of: str | datetime | None = None,
        backend: RetrievalBackend = "local",
        workspace: str | None = None,
        tenant: str | None = None,
        user_id: str | None = None,
        agent: str | None = None,
        include_global: bool = True,
        cross_workspace: bool = False,
        caller: str = "python",
        high_trust_threshold: float = 0.7,
        allow_fallback: bool = True,
    ) -> list[SearchResult]:
        query = query.strip()
        if not query:
            return []
        if not cross_workspace and workspace is None:
            workspace = _infer_workspace_from_cwd()
        query_tokens = _query_tokens(query, backend=backend)
        fts_query = " OR ".join(f'"{token}"' for token in query_tokens)
        params: list[object] = [fts_query]
        kind_sql = ""
        if kind:
            kind_sql = "AND m.kind = ?"
            params.append(kind)
        temporal_sql, temporal_params = _temporal_filter_sql("m", as_of)
        params.extend(temporal_params)
        scope_sql, scope_params = _scope_filter_sql(
            "m",
            workspace=workspace,
            tenant=tenant,
            user_id=user_id,
            agent=agent,
            include_global=include_global,
            cross_workspace=cross_workspace,
        )
        params.extend(scope_params)
        candidate_limit = max(limit * 10, 50)
        params.append(candidate_limit)
        active_status_sql = "m.conflict_status NOT IN ('candidate', 'deprecated', 'superseded', 'archived')"
        rows = self.conn.execute(
            f"""
            SELECT m.*, bm25(memories_fts) AS lexical_score
            FROM memories_fts
            JOIN memories m ON m.rowid = memories_fts.rowid
            WHERE memories_fts MATCH ? AND {active_status_sql} {kind_sql} {temporal_sql} {scope_sql}
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
            like_temporal_sql, like_temporal_params = _temporal_filter_sql("", as_of)
            like_params.extend(like_temporal_params)
            like_scope_sql, like_scope_params = _scope_filter_sql(
                "",
                workspace=workspace,
                tenant=tenant,
                user_id=user_id,
                agent=agent,
                include_global=include_global,
                cross_workspace=cross_workspace,
            )
            like_where = f"({like_where}) AND conflict_status NOT IN ('candidate', 'deprecated', 'superseded', 'archived') {like_temporal_sql} {like_scope_sql}"
            like_params.extend(like_scope_params)
            like_params.append(candidate_limit)
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
            decay = forgetting_decay(record.created_at, record.importance, ref, kind=record.kind)
            lexical = 1.0 / (1.0 + abs(float(row["lexical_score"])))
            score = (lexical * 0.55 + record.importance * 0.25 + record.confidence * 0.15 + decay * 0.05) * record.baseline_trust * record.reputation
            results.append(SearchResult(record=record, score=round(score, 4)))
        if len(results) < limit:
            supplement_sql = "AND kind = ?" if kind else ""
            supplement_params: list[object] = [kind] if kind else []
            supplement_temporal_sql, supplement_temporal_params = _temporal_filter_sql("", as_of)
            supplement_params.extend(supplement_temporal_params)
            supplement_scope_sql, supplement_scope_params = _scope_filter_sql(
                "",
                workspace=workspace,
                tenant=tenant,
                user_id=user_id,
                agent=agent,
                include_global=include_global,
                cross_workspace=cross_workspace,
            )
            supplement_params.extend(supplement_scope_params)
            supplement_rows = self.conn.execute(
                f"""
                SELECT *, 0.0 AS lexical_score
                FROM memories
                WHERE conflict_status NOT IN ('candidate', 'deprecated', 'superseded', 'archived') {supplement_sql} {supplement_temporal_sql} {supplement_scope_sql}
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
                decay = forgetting_decay(record.created_at, record.importance, ref, kind=record.kind)
                lexical = _token_overlap_score(query, record.content, backend=backend)
                score = (lexical * 0.55 + record.importance * 0.25 + record.confidence * 0.15 + decay * 0.05) * record.baseline_trust * record.reputation
                results.append(SearchResult(record=record, score=round(score, 4)))
        final_results = sorted(results, key=lambda r: r.score, reverse=True)
        high_trust_results = [
            result for result in final_results if result.record.baseline_trust * result.record.reputation >= high_trust_threshold
        ]
        if high_trust_results:
            if len(high_trust_results) >= limit:
                final_results = high_trust_results[:limit]
            elif allow_fallback:
                fallback_results = [
                    result for result in final_results if result.record.baseline_trust * result.record.reputation < high_trust_threshold
                ]
                final_results = (high_trust_results + fallback_results)[:limit]
            else:
                final_results = high_trust_results
        else:
            final_results = final_results[:limit] if allow_fallback else []
        self._apply_lazy_reputation_decay(final_results, ref)
        final_results = [
            SearchResult(record=self.get(result.record.id), score=result.score) for result in final_results
        ]
        self._mark_accessed([result.record.id for result in final_results])
        self.log_retrieval(query=query, results=final_results, caller=caller)
        return final_results

    def _apply_lazy_reputation_decay(self, results: list[SearchResult], ref: datetime) -> None:
        for result in results:
            record = result.record
            updated_at = record.reputation_updated_at or record.created_at
            try:
                last_update = datetime.fromisoformat(updated_at)
            except ValueError:
                continue
            if last_update.tzinfo is None:
                last_update = last_update.replace(tzinfo=timezone.utc)
            days = max((ref - last_update).total_seconds() / 86400, 0)
            if days <= 0:
                continue
            decayed = max(REPUTATION_MIN, min(REPUTATION_MAX, record.reputation - REPUTATION_DECAY_PER_DAY * days))
            decayed = round(decayed, 4)
            if abs(record.reputation - decayed) <= 0.01:
                continue
            now = utcnow()
            self.conn.execute(
                "UPDATE memories SET reputation = ?, reputation_updated_at = ? WHERE id = ?",
                (decayed, now, record.id),
            )
            self._insert_trust_audit(
                memory_id=record.id,
                action="decay",
                old_reputation=record.reputation,
                new_reputation=decayed,
                at=now,
            )
        self.conn.commit()

    def log_retrieval(
        self,
        *,
        query: str,
        results: list[SearchResult] | tuple[SearchResult, ...],
        caller: str,
    ) -> RetrievalLogEntry | None:
        if os.environ.get("DEEP_MEMORY_TELEMETRY", "on").lower() in {"0", "false", "no", "off"}:
            return None
        query_hash = sha256(query.encode("utf-8")).hexdigest()
        store_query = os.environ.get("DEEP_MEMORY_TELEMETRY_QUERY", "raw").lower() != "hash"
        returned_ids = [result.record.id for result in results]
        scores = [result.score for result in results]
        now = utcnow()
        cursor = self.conn.execute(
            """
            INSERT INTO retrieval_log(query, query_hash, returned_ids, scores, caller, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                query if store_query else None,
                query_hash,
                json.dumps(returned_ids, ensure_ascii=False),
                json.dumps(scores, ensure_ascii=False),
                caller,
                now,
            ),
        )
        self.conn.commit()
        return RetrievalLogEntry(
            id=int(cursor.lastrowid),
            query=query if store_query else None,
            query_hash=query_hash,
            returned_ids=tuple(returned_ids),
            scores=tuple(scores),
            caller=caller,
            created_at=now,
        )

    def add_feedback(
        self, memory_id: str, *, helpful: bool, note: str | None = None
    ) -> MemoryFeedbackEntry:
        current = self.get(memory_id)
        now = utcnow()
        old_reputation = current.reputation
        delta = 0.02 if helpful else -0.05
        new_reputation = round(max(REPUTATION_MIN, min(REPUTATION_MAX, old_reputation + delta)), 4)
        cursor = self.conn.execute(
            """
            INSERT INTO memory_feedback(memory_id, helpful, note, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (memory_id, 1 if helpful else 0, note, now),
        )
        self.conn.execute(
            """
            UPDATE memories
            SET reputation = ?, reputation_updated_at = ?, updated_at = ?
            WHERE id = ?
            """,
            (new_reputation, now, now, memory_id),
        )
        self._insert_trust_audit(
            memory_id=memory_id,
            action="feedback",
            old_reputation=old_reputation,
            new_reputation=new_reputation,
            at=now,
        )
        self.conn.commit()
        return MemoryFeedbackEntry(
            id=int(cursor.lastrowid),
            memory_id=memory_id,
            helpful=helpful,
            note=note,
            created_at=now,
        )

    def telemetry_report(self, *, days: int = 7) -> TelemetryReport:
        since = datetime.now(timezone.utc) - timedelta(days=days)
        previous_since = since - timedelta(days=days)
        rows = self.conn.execute(
            """
            SELECT returned_ids, scores, created_at
            FROM retrieval_log
            WHERE created_at >= ?
            ORDER BY created_at DESC
            """,
            (since.isoformat(),),
        ).fetchall()
        previous_count = self.conn.execute(
            """
            SELECT COUNT(*) AS n
            FROM retrieval_log
            WHERE created_at >= ? AND created_at < ?
            """,
            (previous_since.isoformat(), since.isoformat()),
        ).fetchone()["n"]
        usage: Counter[str] = Counter()
        score_buckets: Counter[str] = Counter({"0.00-0.25": 0, "0.25-0.50": 0, "0.50-0.75": 0, "0.75-1.00": 0})
        hit_count = 0
        for row in rows:
            ids = _json_list(row["returned_ids"])
            scores = _json_list(row["scores"])
            if ids:
                hit_count += 1
            usage.update(str(memory_id) for memory_id in ids)
            for score in scores:
                bucket = _score_bucket(float(score))
                score_buckets[bucket] += 1
        feedback_rows = self.conn.execute(
            """
            SELECT memory_id, helpful, COUNT(*) AS n
            FROM memory_feedback
            WHERE created_at >= ?
            GROUP BY memory_id, helpful
            """,
            (since.isoformat(),),
        ).fetchall()
        helpful_by_id: Counter[str] = Counter()
        not_helpful_by_id: Counter[str] = Counter()
        helpful_total = 0
        not_helpful_total = 0
        for row in feedback_rows:
            if int(row["helpful"]):
                helpful_by_id[row["memory_id"]] += int(row["n"])
                helpful_total += int(row["n"])
            else:
                not_helpful_by_id[row["memory_id"]] += int(row["n"])
                not_helpful_total += int(row["n"])
        candidates: list[InsightCandidate] = []
        for memory_id, count in usage.most_common(20):
            helpful_count = helpful_by_id[memory_id]
            not_helpful_count = not_helpful_by_id[memory_id]
            feedback_count = helpful_count + not_helpful_count
            helpful_rate = helpful_count / feedback_count if feedback_count else None
            if count >= 2 and (feedback_count == 0 or (helpful_rate is not None and helpful_rate < 0.5)):
                try:
                    content = self.get(memory_id).content
                except KeyError:
                    content = "<deleted memory>"
                candidates.append(
                    InsightCandidate(
                        memory_id=memory_id,
                        content=content,
                        usage_count=count,
                        helpful_count=helpful_count,
                        not_helpful_count=not_helpful_count,
                        helpful_rate=helpful_rate,
                    )
                )
        weekly_growth_rate = None
        if previous_count:
            weekly_growth_rate = (len(rows) - int(previous_count)) / int(previous_count)
        return TelemetryReport(
            days=days,
            retrieval_count=len(rows),
            hit_rate=(hit_count / len(rows)) if rows else 0.0,
            feedback={"helpful": helpful_total, "not_helpful": not_helpful_total},
            weekly_growth_rate=weekly_growth_rate,
            score_distribution=dict(score_buckets),
            high_usage_low_feedback=tuple(candidates),
        )

    def telemetry_report_markdown(self, *, days: int = 7) -> str:
        report = self.telemetry_report(days=days)
        growth = "n/a" if report.weekly_growth_rate is None else f"{report.weekly_growth_rate:.1%}"
        lines = [
            f"# deep-memory telemetry report ({report.days} days)",
            "",
            f"- retrievals: {report.retrieval_count}",
            f"- hit rate: {report.hit_rate:.1%}",
            f"- feedback: {report.feedback['helpful']} helpful / {report.feedback['not_helpful']} not helpful",
            f"- retrieval growth vs previous window: {growth}",
            "",
            "## Score distribution",
        ]
        for bucket, count in report.score_distribution.items():
            lines.append(f"- {bucket}: {count}")
        lines.extend(["", "## High usage / low feedback candidates"])
        if report.high_usage_low_feedback:
            for candidate in report.high_usage_low_feedback:
                rate = "n/a" if candidate.helpful_rate is None else f"{candidate.helpful_rate:.1%}"
                lines.append(
                    f"- `{candidate.memory_id}` usage={candidate.usage_count} "
                    f"helpful_rate={rate}: {candidate.content}"
                )
        else:
            lines.append("- none")
        return "\n".join(lines) + "\n"

    def _mark_accessed(self, record_ids: list[str]) -> None:
        if not record_ids:
            return
        now = utcnow()
        self.conn.executemany(
            """
            UPDATE memories
            SET access_count = access_count + 1, last_accessed_at = ?, updated_at = ?
            WHERE id = ?
            """,
            [(now, now, record_id) for record_id in record_ids],
        )
        self.conn.commit()

    def resolve_conflict(
        self,
        content: str,
        *,
        supersedes: list[str] | tuple[str, ...],
        source: SourceInput = None,
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
                    SET conflict_status = 'superseded', superseded_by_id = ?, valid_until = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (new.id, now, now, old.id),
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

    @property
    def backup_dir(self) -> Path:
        return self.path.with_name(f"{self.path.name}.backups")

    def create_backup(self, trigger_reason: str) -> Path:
        """Create a required pre-destructive-operation SQLite backup plus manifest."""
        if self.backup_retention_days <= 0:
            return self.path
        try:
            self.conn.commit()
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
            backup_path = self.backup_dir / f"{self.path.name}.bak-{timestamp}"
            suffix = 1
            while backup_path.exists():
                backup_path = self.backup_dir / f"{self.path.name}.bak-{timestamp}-{suffix}"
                suffix += 1
            shutil.copy2(self.path, backup_path)
            manifest = {
                "created_at": utcnow(),
                "trigger_reason": trigger_reason,
                "source_db_size": self.path.stat().st_size,
                "record_count": int(self.conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]),
            }
            backup_path.with_suffix(backup_path.suffix + ".manifest.json").write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            return backup_path
        except OSError as exc:
            raise BackupError(f"unable to create DB backup before {trigger_reason}: {exc}") from exc

    def prune_backups(
        self,
        *,
        retention_days: int | None = None,
        dry_run: bool = False,
    ) -> dict[str, object]:
        """Prune expired database backups using mtime-based TTL."""
        days = self.backup_retention_days if retention_days is None else max(int(retention_days), 0)
        result: dict[str, object] = {"backup_dir": str(self.backup_dir), "retention_days": days, "dry_run": dry_run, "expired": [], "deleted": []}
        if days <= 0 or not self.backup_dir.exists():
            return result
        cutoff = datetime.now(timezone.utc).timestamp() - days * 86400
        expired: list[Path] = []
        for backup_path in sorted(self.backup_dir.glob(f"{self.path.name}.bak-*")):
            if backup_path.suffix == ".json" or not backup_path.is_file():
                continue
            if backup_path.stat().st_mtime < cutoff:
                expired.append(backup_path)
        result["expired"] = [str(path) for path in expired]
        if dry_run:
            return result
        deleted: list[str] = []
        for backup_path in expired:
            manifest_path = backup_path.with_suffix(backup_path.suffix + ".manifest.json")
            backup_path.unlink(missing_ok=True)
            manifest_path.unlink(missing_ok=True)
            deleted.append(str(backup_path))
        result["deleted"] = deleted
        return result

    def _backup_before_destructive_operation(self, trigger_reason: str) -> None:
        if self.backup_retention_days <= 0:
            return
        self.create_backup(trigger_reason)

    def hard_delete(self, record_id: str) -> int:
        """Physically remove one memory record from the local database."""
        self.get(record_id)
        self._backup_before_destructive_operation("hard_delete")
        cursor = self.conn.execute("DELETE FROM memories WHERE id = ?", (record_id,))
        self.conn.commit()
        return int(cursor.rowcount)

    def export_records(
        self,
        *,
        include_deprecated: bool = False,
        as_of: str | datetime | None = None,
    ) -> list[MemoryRecord]:
        """Return records for explicit user-controlled export."""
        clauses: list[str] = []
        params: list[object] = []
        if not include_deprecated:
            clauses.append("conflict_status NOT IN ('deprecated', 'superseded', 'archived')")
        temporal_sql, temporal_params = _temporal_filter_sql("", as_of)
        if temporal_sql:
            clauses.append(temporal_sql.removeprefix("AND "))
            params.extend(temporal_params)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        rows = self.conn.execute(
            f"""
            SELECT *
            FROM memories
            {where}
            ORDER BY updated_at DESC
            """,
            params,
        ).fetchall()
        return [_row_to_record(row) for row in rows]

    def conflict_candidates(self, content: str, *, limit: int = 5) -> list[SearchResult]:
        tokens = [t for t in _query_tokens(content) if len(t) >= 2]
        if not tokens:
            return []
        return self.search(" ".join(tokens[:8]), limit=limit, kind="semantic")

    def conflicts(self, *, include_superseded: bool = False) -> list[SearchResult]:
        statuses: tuple[str, ...] = ("candidate", "resolved", "deprecated", "archived")
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

    def consolidation_candidates(
        self, *, threshold: float = 0.6, max_group_size: int = 10
    ) -> tuple[ConsolidationGroup, ...]:
        rows = self.conn.execute(
            """
            SELECT *
            FROM memories
            WHERE conflict_status = 'active'
            ORDER BY kind ASC, updated_at DESC
            """
        ).fetchall()
        records = [_row_to_record(row) for row in rows]
        used: set[str] = set()
        groups: list[ConsolidationGroup] = []
        for record in records:
            if record.id in used:
                continue
            tokens = set(_query_tokens(record.content))
            if not tokens:
                continue
            group = [record]
            best_score = 0.0
            for candidate in records:
                if candidate.id == record.id or candidate.id in used or candidate.kind != record.kind:
                    continue
                score = _jaccard(tokens, set(_query_tokens(candidate.content)))
                if score > threshold:
                    group.append(candidate)
                    best_score = max(best_score, score)
                if len(group) >= max_group_size:
                    break
            if len(group) > 1:
                for item in group:
                    used.add(item.id)
                groups.append(
                    ConsolidationGroup(
                        record_ids=tuple(item.id for item in group),
                        summary=_summary_for_group(group),
                        score=round(best_score, 4),
                        kind=record.kind,
                    )
                )
        return tuple(groups)

    def consolidate(
        self, *, dry_run: bool = True, threshold: float | None = None, max_group_size: int = 10
    ) -> ConsolidationPlan:
        config = LifecycleConfig()
        groups = self.consolidation_candidates(
            threshold=threshold if threshold is not None else config.consolidation_threshold,
            max_group_size=max_group_size,
        )
        if dry_run or not groups:
            return ConsolidationPlan(dry_run=dry_run, groups=groups)
        self._backup_before_destructive_operation("consolidate")
        now = utcnow()
        created_count = 0
        archived_count = 0
        for group in groups:
            old_records = [self.get(record_id) for record_id in group.record_ids]
            summary = self.add(
                group.summary,
                kind=group.kind,
                importance=max(record.importance for record in old_records),
                confidence=round(sum(record.confidence for record in old_records) / len(old_records), 4),
                source=f"consolidated from {', '.join(group.record_ids)}",
            )
            created_count += 1
            self.conn.executemany(
                """
                UPDATE memories
                SET conflict_status = 'archived', superseded_by_id = ?, valid_until = ?, updated_at = ?
                WHERE id = ?
                """,
                [(summary.id, now, now, record_id) for record_id in group.record_ids],
            )
            archived_count += len(group.record_ids)
        self.conn.commit()
        return ConsolidationPlan(
            dry_run=False,
            groups=groups,
            archived_count=archived_count,
            created_count=created_count,
        )

    def stats(self) -> dict[str, int]:
        rows = self.conn.execute("SELECT kind, COUNT(*) AS n FROM memories GROUP BY kind").fetchall()
        out = {"working": 0, "episodic": 0, "semantic": 0, "procedural": 0}
        out.update({row["kind"]: row["n"] for row in rows})
        out["total"] = sum(out.values())
        return out

    def agent_list(self) -> list[dict[str, object]]:
        rows = self.conn.execute(
            """
            SELECT
                r.agent,
                r.trusted,
                r.first_seen_at,
                r.last_seen_at,
                r.note,
                COUNT(m.id) AS memory_count
            FROM agent_registry r
            LEFT JOIN memories m ON m.source LIKE '%' || '"agent": "' || r.agent || '"' || '%'
            GROUP BY r.agent, r.trusted, r.first_seen_at, r.last_seen_at, r.note
            ORDER BY r.trusted DESC, r.agent ASC
            """
        ).fetchall()
        return [
            {
                "agent": row["agent"],
                "trusted": bool(row["trusted"]),
                "first_seen_at": row["first_seen_at"],
                "last_seen_at": row["last_seen_at"],
                "note": row["note"],
                "memory_count": int(row["memory_count"]),
            }
            for row in rows
        ]

    def set_agent_trust(self, agent: str, *, to: AgentTrustLevel, note: str | None = None) -> dict[str, object]:
        if to not in {"trusted", "known", "untrusted"}:
            raise ValueError("agent trust target must be trusted, known, or untrusted")
        trusted = 1 if to == "trusted" else 0
        now = utcnow()
        self.conn.execute(
            """
            INSERT INTO agent_registry(agent, trusted, first_seen_at, last_seen_at, note)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(agent) DO UPDATE SET trusted = excluded.trusted, last_seen_at = excluded.last_seen_at, note = excluded.note
            """,
            (agent, trusted, now, now, note),
        )
        rows = self.conn.execute("SELECT id, source FROM memories WHERE source LIKE ?", (_like_pattern(f'"agent": "{agent}"'),)).fetchall()
        updated = 0
        for row in rows:
            baseline = self._baseline_for_source(deserialize_source(row["source"]), register_unknown=False)
            if to == "untrusted":
                baseline = 0.2
            self.conn.execute("UPDATE memories SET baseline_trust = ?, updated_at = ? WHERE id = ?", (baseline, now, row["id"]))
            updated += 1
        self.conn.commit()
        return {"agent": agent, "trust": to, "updated_memories": updated}

    def trust_records(
        self,
        *,
        limit: int | None = 50,
        suspicious: bool = False,
        agent: str | None = None,
        trust_level: TrustLevel | None = None,
    ) -> list[MemoryRecord]:
        if trust_level is not None and trust_level not in TRUST_LEVEL_FACTORS:
            raise ValueError(f"unsupported trust level: {trust_level}")
        where_sql, params = _trust_records_filter_sql(
            suspicious=suspicious,
            agent=agent,
            trust_level=trust_level,
        )
        limit_sql = "LIMIT ?" if limit is not None else ""
        if limit is not None:
            params.append(limit)
        rows = self.conn.execute(
            f"""
            WITH ranked AS (
                SELECT
                    m.*,
                    {_trust_factor_case_sql("m")} AS trust_factor,
                    {_trust_level_case_sql("m")} AS parsed_trust_level
                FROM memories m
                WHERE m.conflict_status NOT IN ('candidate', 'deprecated', 'superseded', 'archived') {where_sql}
            )
            SELECT *
            FROM ranked
            ORDER BY trust_factor DESC, updated_at DESC
            {limit_sql}
            """,
            params,
        ).fetchall()
        return [_row_to_record(row) for row in rows]

    def trust_records_count(
        self,
        *,
        suspicious: bool = False,
        agent: str | None = None,
        trust_level: TrustLevel | None = None,
    ) -> int:
        if trust_level is not None and trust_level not in TRUST_LEVEL_FACTORS:
            raise ValueError(f"unsupported trust level: {trust_level}")
        where_sql, params = _trust_records_filter_sql(
            suspicious=suspicious,
            agent=agent,
            trust_level=trust_level,
        )
        row = self.conn.execute(
            f"""
            SELECT COUNT(*) AS n
            FROM memories m
            WHERE m.conflict_status NOT IN ('candidate', 'deprecated', 'superseded', 'archived') {where_sql}
            """,
            params,
        ).fetchone()
        return int(row["n"] if row is not None else 0)

    def promote_trust(
        self,
        record_id: str,
        *,
        to: Literal["verified", "user"],
        promoted_by: str = "reviewer",
        reason: str | None = None,
    ) -> MemoryRecord:
        """Promote one memory record after explicit human/reviewer confirmation."""

        if to not in {"verified", "user"}:
            raise ValueError("trust promotion target must be verified or user")
        current = self.get(record_id)
        now = utcnow()
        promoted_source = serialize_source(
            {
                "agent": current.source_info.agent,
                "trust_level": to,
                "origin_type": "explicit",
                "promoted_by": promoted_by,
                "promoted_at": now,
            }
        )
        self.conn.execute(
            """
            UPDATE memories
            SET source = ?, updated_at = ?
            WHERE id = ?
            """,
            (promoted_source, now, current.id),
        )
        self._insert_trust_audit(
            memory_id=current.id,
            action="promote",
            old_trust=current.source_info.trust_level,
            new_trust=to,
            actor=promoted_by,
            reason=reason,
            at=now,
        )
        self.conn.commit()
        return self.get(current.id)

    def promote_scope(
        self,
        record_id: str,
        *,
        to: Literal["global", "tenant", "user", "workspace", "project"],
        workspace: str | None = None,
        tenant: str | None = None,
        user_id: str | None = None,
    ) -> MemoryRecord:
        """Promote or move one memory into an explicit retrieval scope."""

        if to not in {"global", "tenant", "user", "workspace", "project"}:
            raise ValueError("scope promotion target must be global, tenant, user, workspace, or project")
        current = self.get(record_id)
        next_workspace = None
        next_tenant = None
        next_user_id = None
        if to in {"workspace", "project"}:
            next_workspace = workspace or current.workspace or _infer_workspace_from_cwd()
        elif to == "tenant":
            next_tenant = tenant or current.tenant
        elif to == "user":
            next_user_id = user_id or current.user_id
        now = utcnow()
        self.conn.execute(
            """
            UPDATE memories
            SET scope = ?, workspace = ?, tenant = ?, user_id = ?, updated_at = ?
            WHERE id = ?
            """,
            (to, next_workspace, next_tenant, next_user_id, now, current.id),
        )
        self.conn.commit()
        return self.get(current.id)

    def scope_distribution(self) -> list[dict[str, object]]:
        """Return counts grouped by scope/workspace/tenant/user for audit and migration."""

        rows = self.conn.execute(
            """
            SELECT scope, workspace, tenant, user_id, COUNT(*) AS count
            FROM memories
            GROUP BY scope, workspace, tenant, user_id
            ORDER BY scope, workspace, tenant, user_id
            """
        ).fetchall()
        return [
            {
                "scope": row["scope"],
                "workspace": row["workspace"],
                "tenant": row["tenant"],
                "user_id": row["user_id"],
                "count": row["count"],
            }
            for row in rows
        ]

    def trust_audit(self, record_id: str | None = None, *, recent_days: int | None = None) -> list[TrustAuditEntry]:
        """Return trust change audit entries for one memory or a recent admin window."""

        clauses: list[str] = []
        params: list[object] = []
        if record_id is not None:
            clauses.append("memory_id = ?")
            params.append(record_id)
        if recent_days is not None:
            if recent_days < 0:
                raise ValueError("recent_days must be non-negative")
            since = datetime.now(timezone.utc) - timedelta(days=recent_days)
            clauses.append("at >= ?")
            params.append(since.isoformat())
        where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        rows = self.conn.execute(
            f"""
            SELECT *
            FROM trust_audit
            {where_sql}
            ORDER BY at DESC, id DESC
            """,
            params,
        ).fetchall()
        return [_row_to_trust_audit_entry(row) for row in rows]

    def _insert_trust_audit(
        self,
        *,
        memory_id: str,
        action: str,
        old_trust: str | None = None,
        new_trust: str | None = None,
        old_reputation: float | None = None,
        new_reputation: float | None = None,
        actor: str | None = None,
        reason: str | None = None,
        at: str | None = None,
    ) -> None:
        self.conn.execute(
            """
            INSERT INTO trust_audit(
                memory_id, action, old_trust, new_trust, old_reputation, new_reputation, actor, reason, at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                memory_id,
                action,
                old_trust,
                new_trust,
                old_reputation,
                new_reputation,
                actor,
                reason,
                at or utcnow(),
            ),
        )

    def _find_trust_conflict(
        self, content: str, kind: MemoryKind, source_info: SourceInfo
    ) -> MemoryRecord | None:
        query_tokens = [token for token in _query_tokens(content) if len(token) >= 2]
        if not query_tokens:
            return None
        fts_query = " OR ".join(f'"{token}"' for token in query_tokens)
        rows = self.conn.execute(
            """
            SELECT m.*, bm25(memories_fts) AS lexical_score
            FROM memories_fts
            JOIN memories m ON m.rowid = memories_fts.rowid
            WHERE memories_fts MATCH ?
              AND m.conflict_status = 'active'
            ORDER BY lexical_score ASC
            LIMIT 100
            """,
            (fts_query,),
        ).fetchall()
        for row in rows:
            record = _row_to_record(row)
            if record.kind == kind:
                overlap = _jaccard_overlap(content, record.content)
                if overlap <= 0.7:
                    continue
                if source_info.trust_factor >= record.source_info.trust_factor:
                    continue
                if record.source_info.trust_level not in HIGH_TRUST_LEVELS:
                    continue
                return record
            if record.kind == kind:
                continue
            if record.source_info.trust_level not in HIGH_TRUST_LEVELS:
                continue
            if source_info.trust_factor >= record.source_info.trust_factor:
                continue
            overlap = _jaccard_overlap(content, record.content)
            if overlap > 0.33:
                return record
        return None

    def _reverse_trust_conflicts(
        self,
        content: str,
        source_info: SourceInfo,
        *,
        conflict_with_id: str,
        exclude_ids: set[str] | None = None,
    ) -> None:
        if source_info.trust_level not in HIGH_TRUST_LEVELS:
            return
        exclude_ids = exclude_ids or set()
        rows = self.conn.execute(
            """
            SELECT *
            FROM memories
            WHERE conflict_status = 'active'
            """
        ).fetchall()
        now = utcnow()
        for row in rows:
            record = _row_to_record(row)
            if record.id in exclude_ids:
                continue
            if record.source_info.trust_factor >= source_info.trust_factor:
                continue
            overlap = _jaccard_overlap(content, record.content)
            if overlap <= 0.5:
                continue
            self.conn.execute(
                """
                UPDATE memories
                SET conflict_status = 'candidate', supersedes_id = ?, updated_at = ?
                WHERE id = ?
                """,
                (conflict_with_id, now, record.id),
            )

    def close(self) -> None:
        self.conn.close()


def forgetting_decay(
    created_at: str,
    importance: float,
    now: datetime | None = None,
    *,
    kind: MemoryKind = "semantic",
    config: LifecycleConfig | None = None,
) -> float:
    created = datetime.fromisoformat(created_at)
    ref = now or datetime.now(timezone.utc)
    age_days = max((ref - created).total_seconds() / 86400, 0)
    base_half_life = (config or LifecycleConfig()).half_life_for(kind)
    half_life = base_half_life * (0.5 + _clamp01(importance))
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


def _symmetric_token_overlap(left: str, right: str, backend: RetrievalBackend = "local") -> float:
    left_tokens = set(_query_tokens(left, backend=backend))
    right_tokens = set(_query_tokens(right, backend=backend))
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / min(len(left_tokens), len(right_tokens))


def _jaccard_overlap(left: str, right: str, backend: RetrievalBackend = "local") -> float:
    left_tokens = set(_query_tokens(left, backend=backend))
    right_tokens = set(_query_tokens(right, backend=backend))
    return _jaccard(left_tokens, right_tokens)


def _json_list(value: str) -> list[object]:
    parsed = json.loads(value or "[]")
    if isinstance(parsed, list):
        return parsed
    return []


def _score_bucket(score: float) -> str:
    if score < 0.25:
        return "0.00-0.25"
    if score < 0.50:
        return "0.25-0.50"
    if score < 0.75:
        return "0.50-0.75"
    return "0.75-1.00"


def _jaccard(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def _summary_for_group(records: list[MemoryRecord]) -> str:
    common_tokens = set(_query_tokens(records[0].content))
    for record in records[1:]:
        common_tokens &= set(_query_tokens(record.content))
    signal = " ".join(token for token in records[0].content.split() if token in common_tokens)
    if not signal:
        signal = records[0].content
    return f"Consolidated summary ({len(records)} memories): {signal}"


def _row_to_record(row: sqlite3.Row) -> MemoryRecord:
    raw_source = row["source"]
    source = deserialize_source(raw_source)
    source_info = parse_source_info(source)
    source_info = SourceInfo(
        agent=source_info.agent,
        trust_level=source_info.trust_level,
        origin_type=source_info.origin_type,
        promoted_by=source_info.promoted_by,
        promoted_at=source_info.promoted_at,
        baseline_trust=float(row["baseline_trust"]),
        reputation=float(row["reputation"]),
    )
    return MemoryRecord(
        id=row["id"],
        content=row["content"],
        kind=row["kind"],
        importance=float(row["importance"]),
        confidence=float(row["confidence"]),
        source=source,
        source_info=source_info,
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        learned_at=row["learned_at"] or row["created_at"],
        event_time=row["event_time"] or row["created_at"],
        valid_until=row["valid_until"],
        expires_at=row["expires_at"],
        access_count=int(row["access_count"]),
        last_accessed_at=row["last_accessed_at"],
        conflict_status=row["conflict_status"],
        supersedes_id=row["supersedes_id"],
        superseded_by_id=row["superseded_by_id"],
        scope=row["scope"],
        workspace=row["workspace"],
        tenant=row["tenant"],
        user_id=row["user_id"],
        agent=row["agent"],
        idempotency_key=row["idempotency_key"],
        embedding_model=row["embedding_model"],
        embedding_version=row["embedding_version"],
        baseline_trust=float(row["baseline_trust"]),
        reputation=float(row["reputation"]),
        reputation_updated_at=row["reputation_updated_at"],
    )


def _row_to_trust_audit_entry(row: sqlite3.Row) -> TrustAuditEntry:
    return TrustAuditEntry(
        id=int(row["id"]),
        memory_id=row["memory_id"],
        action=row["action"],
        old_trust=row["old_trust"],
        new_trust=row["new_trust"],
        old_reputation=row["old_reputation"],
        new_reputation=row["new_reputation"],
        actor=row["actor"],
        reason=row["reason"],
        at=row["at"],
    )


def serialize_source(source: SourceInput) -> str | None:
    if source is None:
        return None
    if isinstance(source, str):
        return source
    source_info = parse_source_info(source)
    return json.dumps(
        {
            "agent": source_info.agent,
            "trust_level": source_info.trust_level,
            "origin_type": source_info.origin_type,
            "promoted_by": source_info.promoted_by,
            "promoted_at": source_info.promoted_at,
        },
        ensure_ascii=False,
        sort_keys=True,
    )


def deserialize_source(raw_source: str | None) -> str | dict[str, str] | None:
    if raw_source is None:
        return None
    try:
        parsed = json.loads(raw_source)
    except json.JSONDecodeError:
        return raw_source
    if isinstance(parsed, dict) and "trust_level" in parsed and "origin_type" in parsed:
        source_info = parse_source_info(parsed)
        upgraded = {
            "agent": source_info.agent or "",
            "trust_level": source_info.trust_level,
            "origin_type": source_info.origin_type,
        }
        if source_info.promoted_by is not None:
            upgraded["promoted_by"] = source_info.promoted_by
        if source_info.promoted_at is not None:
            upgraded["promoted_at"] = source_info.promoted_at
        return upgraded
    return raw_source


def parse_source_info(source: SourceInput | dict[str, str]) -> SourceInfo:
    if source is None:
        return DEFAULT_SOURCE_INFO
    if isinstance(source, str):
        trust_level = (
            "external" if _trust_auto_detect_enabled() and _is_external_url(source) else "agent-auto"
        )
        return SourceInfo(agent=source or None, trust_level=trust_level)
    trust_level = str(source.get("trust_level", "agent-auto")).strip()
    if trust_level not in TRUST_LEVEL_FACTORS:
        trust_level = "agent-auto"
    origin_type = str(source.get("origin_type", "auto-extracted")).strip()
    if origin_type not in {"explicit", "auto-extracted", "imported"}:
        origin_type = "auto-extracted"
    raw_agent = source.get("agent")
    agent = str(raw_agent).strip() if raw_agent is not None else ""
    if "trust_level" not in source and _trust_auto_detect_enabled():
        if origin_type == "imported" and not agent:
            trust_level = "external"
        elif origin_type == "explicit" and agent.lower() in {"human", "user"}:
            trust_level = "user"
    promoted_by_raw = source.get("promoted_by")
    promoted_by = str(promoted_by_raw).strip() if promoted_by_raw is not None else ""
    promoted_at_raw = source.get("promoted_at")
    promoted_at = str(promoted_at_raw).strip() if promoted_at_raw is not None else ""
    return SourceInfo(
        agent=agent or None,
        trust_level=trust_level,  # type: ignore[arg-type]
        origin_type=origin_type,  # type: ignore[arg-type]
        promoted_by=promoted_by or None,
        promoted_at=promoted_at or None,
    )


def _is_external_url(source: str) -> bool:
    return any(pattern.match(source) for pattern in EXTERNAL_PATTERNS)


EXTERNAL_PATTERNS = [
    re.compile(r"^https?://", re.IGNORECASE),
    re.compile(r"^ftps?://", re.IGNORECASE),
    re.compile(r"^mailto:", re.IGNORECASE),
    re.compile(r"^\d{1,3}(\.\d{1,3}){3}(:\d+)?(/|$)"),
    re.compile(r"^\[([0-9a-fA-F:]+)\](:\d+)?(/|$)"),
]


def _trust_auto_detect_enabled() -> bool:
    env_value = os.getenv("DEEP_MEMORY_TRUST_AUTO_DETECT")
    if env_value is not None:
        return env_value.strip().lower() not in {"0", "false", "no", "off"}
    config_value = _read_trust_auto_detect_from_pyproject()
    return True if config_value is None else config_value


def _read_trust_auto_detect_from_pyproject() -> bool | None:
    for directory in (Path.cwd(), *Path.cwd().parents):
        pyproject = directory / "pyproject.toml"
        if not pyproject.exists():
            continue
        try:
            text = pyproject.read_text(encoding="utf-8")
        except OSError:
            return None
        in_trust_section = False
        for raw_line in text.splitlines():
            line = raw_line.split("#", 1)[0].strip()
            if not line:
                continue
            if line.startswith("[") and line.endswith("]"):
                in_trust_section = line == "[tool.deep-memory.trust]"
                continue
            if in_trust_section and line.startswith("auto_detect") and "=" in line:
                value = line.split("=", 1)[1].strip().strip('"').strip("'").lower()
                if value in {"true", "1", "yes", "on"}:
                    return True
                if value in {"false", "0", "no", "off"}:
                    return False
        return None
    return None


def _infer_workspace_from_cwd(cwd: str | Path | None = None) -> str:
    """Infer a privacy-preserving workspace name from cwd.

    The value intentionally avoids storing the full absolute path. Prefer a
    human-readable basename; fall back to a short hash for filesystem roots or
    empty names.
    """

    path = Path(cwd).expanduser() if cwd is not None else Path.cwd()
    name = path.name.strip()
    if name and name not in {"/", str(Path.home())}:
        return name
    return sha256(str(path.resolve()).encode("utf-8")).hexdigest()[:8]


def build_idempotency_key(
    content: str,
    *,
    kind: MemoryKind = "semantic",
    source: str | None = None,
    workspace: str | None = None,
    tenant: str | None = None,
    user_id: str | None = None,
    agent: str | None = None,
) -> str:
    """Return a stable key for one adapter-emitted fact in one boundary."""

    normalized_content = re.sub(r"\s+", " ", content.strip())
    parts = [kind, normalized_content, source or "", workspace or "", tenant or "", user_id or "", agent or ""]
    return "v1:" + sha256("\x1f".join(parts).encode("utf-8")).hexdigest()



def _normalize_temporal_value(value: str | datetime) -> str:
    if isinstance(value, datetime):
        dt = value
    else:
        text = value.strip()
        if not text:
            raise ValueError("as_of cannot be empty")
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
            dt = datetime.fromisoformat(text).replace(tzinfo=timezone.utc)
        else:
            dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat()


def _validate_iso_datetime(value: str | datetime | None, field_name: str) -> str | None:
    if value is None:
        return None
    try:
        return _normalize_temporal_value(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be an ISO 8601 datetime or YYYY-MM-DD date") from exc


def _temporal_filter_sql(alias: str, as_of: str | datetime | None) -> tuple[str, list[object]]:
    if as_of is None:
        return "", []
    prefix = f"{alias}." if alias else ""
    value = _normalize_temporal_value(as_of)
    return f"AND {prefix}event_time <= ? AND ({prefix}valid_until IS NULL OR {prefix}valid_until > ?)", [value, value]

def _scope_filter_sql(
    alias: str,
    *,
    workspace: str | None,
    tenant: str | None,
    user_id: str | None,
    agent: str | None,
    include_global: bool,
    cross_workspace: bool,
) -> tuple[str, list[object]]:
    prefix = f"{alias}." if alias else ""
    params: list[object] = []
    visible: list[str] = []
    if include_global:
        visible.append(f"{prefix}scope = 'global'")
    if cross_workspace:
        visible.append(f"{prefix}scope IN ('workspace', 'project')")
    elif workspace is not None:
        visible.append(f"({prefix}scope IN ('workspace', 'project') AND {prefix}workspace = ?)")
        params.append(workspace)
    if tenant is not None:
        visible.append(f"({prefix}scope = 'tenant' AND {prefix}tenant = ?)")
        params.append(tenant)
    if user_id is not None:
        visible.append(f"({prefix}scope = 'user' AND {prefix}user_id = ?)")
        params.append(user_id)
    if not visible:
        return "AND 0", []
    clauses = ["(" + " OR ".join(visible) + ")"]
    if agent is not None:
        clauses.append(f"({prefix}agent IS NULL OR {prefix}agent = ?)")
        params.append(agent)
    return "AND " + " AND ".join(clauses), params


def _source_to_trail_text(source: str | dict[str, str] | None) -> str | None:
    if source is None:
        return None
    if isinstance(source, str):
        return source
    return json.dumps(source, ensure_ascii=False, sort_keys=True)


def _trust_records_filter_sql(
    *,
    suspicious: bool,
    agent: str | None,
    trust_level: TrustLevel | None,
) -> tuple[str, list[object]]:
    clauses: list[str] = []
    params: list[object] = []
    if suspicious:
        clauses.append(f"({_trust_level_case_sql('m')}) NOT IN ('user', 'verified', 'agent-high')")
    if agent:
        agent_pattern = _like_pattern(f'"agent": {json.dumps(agent, ensure_ascii=False)}')
        clauses.append("(m.agent = ? OR m.source LIKE ? ESCAPE '\\')")
        params.extend([agent, agent_pattern])
    if trust_level is not None:
        clauses.append(f"({_trust_level_case_sql('m')}) = ?")
        params.append(trust_level)
    return ("AND " + " AND ".join(clauses)) if clauses else "", params


def _trust_level_case_sql(alias: str) -> str:
    prefix = f"{alias}." if alias else ""
    source = f"COALESCE({prefix}source, '')"
    return (
        f"CASE WHEN {source} LIKE '%\"trust_level\": \"user\"%' THEN 'user' "
        f"WHEN {source} LIKE '%\"trust_level\": \"verified\"%' THEN 'verified' "
        f"WHEN {source} LIKE '%\"trust_level\": \"agent-high\"%' THEN 'agent-high' "
        f"WHEN {source} LIKE '%\"trust_level\": \"external\"%' THEN 'external' "
        f"WHEN {source} LIKE '%\"trust_level\": \"untrusted\"%' THEN 'untrusted' "
        f"ELSE 'agent-auto' END"
    )


def _trust_factor_case_sql(alias: str) -> str:
    trust_level_sql = _trust_level_case_sql(alias)
    return (
        f"CASE {trust_level_sql} "
        "WHEN 'user' THEN 1.0 "
        "WHEN 'verified' THEN 0.9 "
        "WHEN 'agent-high' THEN 0.8 "
        "WHEN 'agent-auto' THEN 0.5 "
        "WHEN 'external' THEN 0.5 "
        "WHEN 'untrusted' THEN 0.2 "
        "ELSE 0.5 END"
    )


def _like_pattern(value: str) -> str:
    escaped = value.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')
    return f"%{escaped}%"


def _source_trail(source: SourceInput, superseded: list[MemoryRecord]) -> str | None:
    source_text = serialize_source(source)
    old_sources = [_source_to_trail_text(record.source) for record in superseded if record.source]
    if not source_text and not old_sources:
        return None
    trail_parts = []
    if source_text:
        trail_parts.append(source_text)
    if old_sources:
        trail_parts.append("supersedes " + ", ".join(source for source in old_sources if source))
    return "; ".join(trail_parts)


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))
