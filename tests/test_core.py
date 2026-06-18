import sqlite3
from datetime import datetime, timedelta, timezone
from time import perf_counter

from typer.testing import CliRunner

from deep_memory import DeepMemory
from deep_memory.cli import app
from deep_memory.core import forgetting_decay, _jaccard_overlap


def test_add_and_search_chinese_memory(tmp_path):
    mem = DeepMemory(tmp_path / "memory.db")
    mem.add("用户偏好：中文为主，技术术语用英文", kind="semantic", importance=0.9)

    results = mem.search("用户偏好", limit=3)

    assert results
    assert "中文" in results[0].record.content
    assert results[0].record.kind == "semantic"


def test_stats_counts_layers(tmp_path):
    mem = DeepMemory(tmp_path / "memory.db")
    mem.add("讨论了 deep-memory 的 GitHub 启动", kind="episodic")
    mem.add("成功流程应该沉淀为 skill", kind="procedural")

    assert mem.stats()["episodic"] == 1
    assert mem.stats()["procedural"] == 1
    assert mem.stats()["total"] == 2


def test_forgetting_decay_respects_importance():
    created = (datetime.now(timezone.utc) - timedelta(days=20)).isoformat()

    low = forgetting_decay(created, importance=0.1)
    high = forgetting_decay(created, importance=0.9)

    assert high > low


def test_conflict_candidates_returns_related_semantic_records(tmp_path):
    mem = DeepMemory(tmp_path / "memory.db")
    mem.add("用户偏好：深色模式", kind="semantic")

    candidates = mem.conflict_candidates("用户偏好改为浅色模式")

    assert candidates
    assert "深色模式" in candidates[0].record.content


def test_conflict_detection_uses_jaccard_overlap_for_short_memory_vs_long_memory(tmp_path):
    mem = DeepMemory(tmp_path / "memory.db")
    old = mem.add(
        "user prefers dark theme across all desktop and mobile interfaces",
        kind="semantic",
        source={"agent": "reviewer", "trust_level": "verified", "origin_type": "explicit"},
    )

    new = mem.add(
        "dark mode",
        kind="semantic",
        source={"agent": "importer", "trust_level": "untrusted", "origin_type": "imported"},
    )

    assert _jaccard_overlap(old.content, new.content) < 0.33
    assert new.conflict_status == "active"
    assert new.supersedes_id is None


def test_conflict_detection_scales_on_thousand_row_smoke(tmp_path):
    mem = DeepMemory(tmp_path / "memory.db")
    for idx in range(1000):
        mem.add(
            f"用户偏好示例 {idx}: keep setting {idx}",
            kind="semantic",
            source={"agent": "reviewer", "trust_level": "verified", "origin_type": "explicit"},
        )

    start = perf_counter()
    mem.add(
        "keep setting 999",
        kind="procedural",
        source={"agent": "importer", "trust_level": "untrusted", "origin_type": "imported"},
    )
    elapsed = perf_counter() - start

    assert elapsed < 1.0


def test_confirmed_preference_change_supersedes_old_semantic_memory_with_source_trail(tmp_path):
    mem = DeepMemory(tmp_path / "memory.db")
    old = mem.add("用户偏好：深色模式", kind="semantic", source="profile:v1")

    conflict = mem.resolve_conflict(
        "用户偏好改为浅色模式",
        supersedes=[old.id],
        source="chat:42",
        confirmed_by_user=True,
    )

    new = mem.get(conflict.record.id)
    superseded = mem.get(old.id)

    assert conflict.status == "resolved"
    assert conflict.confirmed_by_user is True
    assert new.conflict_status == "resolved"
    assert new.supersedes_id == old.id
    assert new.source == "chat:42; supersedes profile:v1"
    assert superseded.conflict_status == "superseded"
    assert superseded.superseded_by_id == new.id
    assert mem.conflicts()[0].record.id == new.id


def test_unconfirmed_preference_change_stays_candidate_without_superseding_old_value(tmp_path):
    mem = DeepMemory(tmp_path / "memory.db")
    old = mem.add("用户偏好：深色模式", kind="semantic", source="profile:v1")

    conflict = mem.resolve_conflict(
        "用户偏好改为浅色模式",
        supersedes=[old.id],
        source="chat:42",
        confirmed_by_user=False,
    )

    candidate = mem.get(conflict.record.id)
    original = mem.get(old.id)

    assert conflict.status == "candidate"
    assert conflict.confirmed_by_user is False
    assert candidate.conflict_status == "candidate"
    assert candidate.supersedes_id == old.id
    assert original.conflict_status == "active"
    assert original.superseded_by_id is None


def test_search_excludes_deprecated_memory_even_when_query_exactly_matches_deleted_content(tmp_path):
    mem = DeepMemory(tmp_path / "memory.db")
    deleted = mem.add("用户偏好：不要再召回这条已删除记忆", kind="semantic", importance=0.9)
    mem.deprecate(deleted.id, source="manual cleanup")

    results = mem.search("已删除记忆", limit=5)

    assert results == []


def test_search_excludes_superseded_memory_by_default(tmp_path):
    mem = DeepMemory(tmp_path / "memory.db")
    old = mem.add("用户偏好：深色模式", kind="semantic", source="profile:v1", importance=0.9)
    mem.resolve_conflict(
        "用户偏好改为浅色模式",
        supersedes=[old.id],
        source="chat:42",
        confirmed_by_user=True,
    )

    results = mem.search("深色模式", limit=5)

    assert all(result.record.id != old.id for result in results)
    assert all(result.record.conflict_status != "superseded" for result in results)


def test_new_memory_records_have_bitemporal_defaults(tmp_path):
    mem = DeepMemory(tmp_path / "memory.db")

    before = datetime.now(timezone.utc)
    record = mem.add("用户偏好：默认 event_time 来自写入时间", kind="semantic")
    after = datetime.now(timezone.utc)

    assert record.learned_at == record.created_at
    assert record.valid_until is None
    assert before <= datetime.fromisoformat(record.event_time) <= after


def test_add_rejects_malformed_event_time(tmp_path):
    mem = DeepMemory(tmp_path / "memory.db")

    try:
        mem.add("用户偏好：非法 event_time 不应写入", event_time="banana")
    except ValueError as exc:
        assert "event_time" in str(exc)
    else:  # pragma: no cover - assertion clarity
        raise AssertionError("malformed event_time should raise ValueError")


def test_add_accepts_date_only_event_time_as_utc_midnight(tmp_path):
    mem = DeepMemory(tmp_path / "memory.db")

    record = mem.add("项目状态：日期格式 event_time", event_time="2026-06-01")

    assert record.event_time == "2026-06-01T00:00:00+00:00"


def test_add_accepts_timezone_aware_event_time(tmp_path):
    mem = DeepMemory(tmp_path / "memory.db")

    record = mem.add("项目状态：带时区 event_time", event_time="2026-06-01T12:00:00+08:00")

    assert record.event_time == "2026-06-01T04:00:00+00:00"


def test_add_rejects_malformed_valid_until(tmp_path):
    mem = DeepMemory(tmp_path / "memory.db")

    try:
        mem.add("用户偏好：非法 valid_until 不应写入", valid_until="2026-13-45")
    except ValueError as exc:
        assert "valid_until" in str(exc)
    else:  # pragma: no cover - assertion clarity
        raise AssertionError("malformed valid_until should raise ValueError")


def test_search_as_of_filters_by_event_time_and_valid_until(tmp_path):
    mem = DeepMemory(tmp_path / "memory.db")
    old = mem.add(
        "项目状态：使用旧架构",
        kind="semantic",
        event_time="2026-05-01T00:00:00+00:00",
        valid_until="2026-06-01T00:00:00+00:00",
    )
    current = mem.add(
        "项目状态：使用新架构",
        kind="semantic",
        event_time="2026-06-01T00:00:00+00:00",
    )

    before_cutover = mem.search("项目状态", as_of="2026-05-15", limit=5)
    after_cutover = mem.search("项目状态", as_of="2026-06-15", limit=5)

    assert [result.record.id for result in before_cutover] == [old.id]
    assert [result.record.id for result in after_cutover] == [current.id]


def test_as_of_accepts_datetime_object_not_just_string(tmp_path):
    mem = DeepMemory(tmp_path / "memory.db")
    old = mem.add(
        "项目状态：使用旧架构",
        event_time="2026-05-01T00:00:00+00:00",
        valid_until="2026-06-01T00:00:00+00:00",
    )

    results = mem.search("项目状态", as_of=datetime(2026, 5, 15, tzinfo=timezone.utc), limit=5)

    assert [result.record.id for result in results] == [old.id]


def test_as_of_exactly_equal_to_valid_until_excludes_record(tmp_path):
    mem = DeepMemory(tmp_path / "memory.db")
    old = mem.add(
        "项目状态：使用旧架构",
        event_time="2026-05-01T00:00:00+00:00",
        valid_until="2026-06-01T00:00:00+00:00",
    )

    at_boundary = mem.search("项目状态", as_of="2026-06-01", limit=5)
    before_boundary = mem.search("项目状态", as_of="2026-05-31", limit=5)

    assert [result.record.id for result in at_boundary] == []
    assert [result.record.id for result in before_boundary] == [old.id]


def test_as_of_earlier_than_all_event_times_returns_empty(tmp_path):
    mem = DeepMemory(tmp_path / "memory.db")
    mem.add("项目状态：六月后才存在", event_time="2026-06-01T00:00:00+00:00")
    mem.add("项目状态：七月后才存在", event_time="2026-07-01T00:00:00+00:00")

    results = mem.search("项目状态", as_of="2026-01-01", limit=5)

    assert results == []


def test_search_as_of_cli_filters_temporally(tmp_path):
    db = tmp_path / "memory.db"
    mem = DeepMemory(db)
    mem.add("项目状态：使用旧架构", event_time="2026-05-01T00:00:00+00:00", valid_until="2026-06-01T00:00:00+00:00")
    mem.add("项目状态：使用新架构", event_time="2026-06-01T00:00:00+00:00")
    mem.close()

    result = CliRunner().invoke(app, ["search", str(db), "项目状态", "--as-of", "2026-05-15"])

    assert result.exit_code == 0
    assert "旧架构" in result.output
    assert "新架构" not in result.output


def test_resolve_conflict_sets_valid_until_on_superseded_memory(tmp_path):
    mem = DeepMemory(tmp_path / "memory.db")
    old = mem.add("用户偏好：深色模式", kind="semantic", source="profile:v1", event_time="2026-05-01T00:00:00+00:00")
    before = datetime.now(timezone.utc)

    mem.resolve_conflict(
        "用户偏好改为浅色模式",
        supersedes=[old.id],
        source="chat:42",
        confirmed_by_user=True,
    )
    superseded = mem.get(old.id)

    assert superseded.valid_until is not None
    assert before <= datetime.fromisoformat(superseded.valid_until) <= datetime.now(timezone.utc)


def test_legacy_records_without_provenance_columns_fallback_to_created_at(tmp_path):
    db = tmp_path / "legacy.db"
    conn = sqlite3.connect(db)
    conn.executescript(
        """
        CREATE TABLE memories (
            id TEXT PRIMARY KEY,
            content TEXT NOT NULL,
            kind TEXT NOT NULL CHECK (kind IN ('working','episodic','semantic','procedural')),
            importance REAL NOT NULL DEFAULT 0.5,
            confidence REAL NOT NULL DEFAULT 0.8,
            source TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            expires_at TEXT,
            access_count INTEGER NOT NULL DEFAULT 0,
            last_accessed_at TEXT,
            conflict_status TEXT NOT NULL DEFAULT 'active',
            supersedes_id TEXT,
            superseded_by_id TEXT,
            scope TEXT NOT NULL DEFAULT 'global',
            workspace TEXT,
            tenant TEXT,
            user_id TEXT,
            agent TEXT,
            idempotency_key TEXT,
            embedding_model TEXT,
            embedding_version INTEGER
        );
        CREATE VIRTUAL TABLE memories_fts USING fts5(
            content, kind, source, content='memories', content_rowid='rowid'
        );
        INSERT INTO memories(id, content, kind, importance, confidence, created_at, updated_at, conflict_status, scope)
        VALUES ('legacy-1', '旧记录：兼容 created_at', 'semantic', 0.9, 0.8, '2026-05-01T00:00:00+00:00', '2026-05-01T00:00:00+00:00', 'active', 'global');
        INSERT INTO memories_fts(rowid, content, kind, source)
        SELECT rowid, content, kind, COALESCE(source, '') FROM memories;
        """
    )
    conn.commit()
    conn.close()
    mem = DeepMemory(db)

    record = mem.get("legacy-1")
    results = mem.search("旧记录", as_of="2026-05-15")

    assert record.event_time == "2026-05-01T00:00:00+00:00"
    assert record.learned_at == "2026-05-01T00:00:00+00:00"
    assert record.valid_until is None
    assert results[0].record.id == "legacy-1"


def test_embedding_schema_fields_are_nullable_and_do_not_break_add_search(tmp_path):
    mem = DeepMemory(tmp_path / "memory.db")

    record = mem.add("用户偏好：用 pytest 验证变更", kind="procedural")
    results = mem.search("pytest", limit=3)

    columns = {
        row["name"]: row
        for row in mem.conn.execute("PRAGMA table_info(memories)").fetchall()
    }
    assert columns["embedding_model"]["type"] == "TEXT"
    assert columns["embedding_model"]["notnull"] == 0
    assert columns["embedding_version"]["type"] == "INTEGER"
    assert columns["embedding_version"]["notnull"] == 0
    assert record.embedding_model is None
    assert record.embedding_version is None
    assert results[0].record.embedding_model is None
    assert results[0].record.embedding_version is None


def test_schema_migration_adds_embedding_fields_idempotently_to_legacy_database(tmp_path):
    db = tmp_path / "legacy.db"
    mem = DeepMemory(db)
    mem.conn.execute("ALTER TABLE memories RENAME TO memories_with_embedding")
    mem.conn.executescript(
        """
        CREATE TABLE memories (
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
        DROP TABLE memories_with_embedding;
        """
    )
    mem.conn.commit()
    mem._init_schema()
    mem._init_schema()

    columns = {row["name"] for row in mem.conn.execute("PRAGMA table_info(memories)")}
    assert "embedding_model" in columns
    assert "embedding_version" in columns

    record = mem.add("schema migration remains re-entrant", kind="semantic")
    assert mem.search("schema migration")
    assert record.embedding_model is None
    assert record.embedding_version is None


def test_add_without_scope_defaults_to_workspace_and_infers_cwd(tmp_path, monkeypatch):
    mem = DeepMemory(tmp_path / "memory.db")
    monkeypatch.chdir(tmp_path)

    record = mem.add("Project convention: isolate memory by workspace")

    assert record.scope == "workspace"
    assert record.workspace == tmp_path.name


def test_search_defaults_to_current_workspace_and_keeps_global_visible(tmp_path, monkeypatch):
    mem = DeepMemory(tmp_path / "memory.db")
    monkeypatch.chdir(tmp_path)
    mem.add("Workspace fact: use uv run pytest -q", scope="workspace")
    mem.add("Global fact: user prefers concise answers", scope="global")

    results = mem.search("fact", limit=10)

    assert any(row.record.scope == "workspace" for row in results)
    assert any(row.record.scope == "global" for row in results)


def test_search_can_exclude_global_and_search_cross_workspace_explicitly(tmp_path, monkeypatch):
    mem = DeepMemory(tmp_path / "memory.db")
    monkeypatch.chdir(tmp_path)
    mem.add("Workspace current fact", scope="workspace")
    mem.add("Workspace A fact", scope="workspace", workspace="repo-a")
    mem.add("Workspace B fact", scope="workspace", workspace="repo-b")
    mem.add("Global fact", scope="global")

    local_only = mem.search("fact", include_global=False, limit=10)
    cross = mem.search("fact", include_global=False, cross_workspace=True, limit=10)

    assert all(row.record.scope != "global" for row in local_only)
    assert {row.record.workspace for row in local_only} == {tmp_path.name}
    assert {row.record.workspace for row in cross} == {tmp_path.name, "repo-a", "repo-b"}


def test_promote_scope_moves_workspace_memory_to_global(tmp_path, monkeypatch):
    mem = DeepMemory(tmp_path / "memory.db")
    monkeypatch.chdir(tmp_path)
    record = mem.add("Workspace fact: promote me", scope="workspace")

    promoted = mem.promote_scope(record.id, to="global")

    assert promoted.scope == "global"
    assert promoted.workspace is None


def test_scope_distribution_reports_scope_counts(tmp_path, monkeypatch):
    mem = DeepMemory(tmp_path / "memory.db")
    monkeypatch.chdir(tmp_path)
    mem.add("Workspace fact", scope="workspace")
    mem.add("Global fact", scope="global")

    dist = mem.scope_distribution()

    assert any(row["scope"] == "workspace" and row["count"] == 1 for row in dist)
    assert any(row["scope"] == "global" and row["count"] == 1 for row in dist)
