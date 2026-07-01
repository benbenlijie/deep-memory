from __future__ import annotations

import sqlite3

from typer.testing import CliRunner

from deep_memory import DeepMemory, build_idempotency_key
from deep_memory.cli import app
from deep_memory.core import _infer_workspace_from_cwd


def test_idempotency_key_skip_policy_prevents_unbounded_duplicate_imports(tmp_path):
    db = tmp_path / "memory.db"
    mem = DeepMemory(db)
    key = build_idempotency_key(
        "Project convention: adapter imports explicit facts only",
        kind="procedural",
        source="codex:same-run",
        scope="workspace",
        scope_id="/repo/a",
        agent="codex",
    )

    first = mem.add(
        "Project convention: adapter imports explicit facts only",
        kind="procedural",
        source="codex:same-run",
        scope="workspace",
        scope_id="/repo/a",
        agent="codex",
        idempotency_key=key,
        duplicate_policy="skip",
    )
    second = mem.add(
        "Project convention: adapter imports explicit facts only",
        kind="procedural",
        source="codex:same-run",
        scope="workspace",
        scope_id="/repo/a",
        agent="codex",
        idempotency_key=key,
        duplicate_policy="skip",
    )

    assert second.id == first.id
    assert mem.stats()["total"] == 1


def test_scope_id_scoped_search_does_not_mix_different_scope_ids_by_default(tmp_path):
    db = tmp_path / "memory.db"
    mem = DeepMemory(db)
    mem.add(
        "Build command: uv run pytest -q",
        scope="workspace",
        scope_id="/repo/a",
        idempotency_key=build_idempotency_key(
            "Build command: uv run pytest -q", scope="workspace", scope_id="/repo/a"
        ),
    )
    mem.add(
        "Build command: npm test",
        scope="workspace",
        scope_id="/repo/b",
        idempotency_key=build_idempotency_key(
            "Build command: npm test", scope="workspace", scope_id="/repo/b"
        ),
    )

    results = mem.search("Build command", scope="workspace", scope_id="/repo/a", limit=10)

    assert [row.record.scope_id for row in results] == ["/repo/a"]
    assert [row.record.content for row in results] == ["Build command: uv run pytest -q"]


def test_global_memory_is_visible_inside_scope_id_scope(tmp_path):
    db = tmp_path / "memory.db"
    mem = DeepMemory(db)
    mem.add("User preference: concise answers", scope="global")

    results = mem.search("concise answers", scope="workspace", scope_id="/repo/a", limit=5)

    assert results
    assert results[0].record.scope == "global"
    assert results[0].record.scope_id is None


def test_add_auto_infers_scope_id_from_cwd_when_omitted(tmp_path, monkeypatch):
    project = tmp_path / "my-project"
    project.mkdir()
    monkeypatch.chdir(project)
    mem = DeepMemory(tmp_path / "memory.db")

    record = mem.add("Project convention: pytest is the default verification command")

    assert record.scope == "workspace"
    assert record.scope_id == "my-project"


def test_search_auto_infers_scope_id_when_omitted(tmp_path, monkeypatch):
    my_project = tmp_path / "my-project"
    other_project = tmp_path / "other"
    my_project.mkdir()
    other_project.mkdir()
    mem = DeepMemory(tmp_path / "memory.db")
    monkeypatch.chdir(my_project)
    mem.add("Build command: run pytest from my-project", scope="workspace")

    found_in_project = mem.search("Build command", include_global=False, limit=10)
    monkeypatch.chdir(other_project)
    hidden_elsewhere = mem.search("Build command", include_global=False, limit=10)

    assert [row.record.scope_id for row in found_in_project] == ["my-project"]
    assert hidden_elsewhere == []


def test_cross_scope_true_returns_all_scoped_records(tmp_path):
    mem = DeepMemory(tmp_path / "memory.db")
    mem.add("Build command: run pytest for repo-a", scope="workspace", scope_id="repo-a")
    mem.add("Build command: run npm test for repo-b", scope="workspace", scope_id="repo-b")
    mem.add("Build command: run uv for project", scope="project", scope_id="deep-memory")

    results = mem.search("Build command", include_global=False, cross_scope=True, limit=10)

    assert {(row.record.scope, row.record.scope_id) for row in results} == {
        ("workspace", "repo-a"),
        ("workspace", "repo-b"),
        ("project", "deep-memory"),
    }


def test_include_global_false_strictly_isolates_scope_id(tmp_path):
    mem = DeepMemory(tmp_path / "memory.db")
    mem.add("Searchable command: global default", scope="global")
    mem.add("Searchable command: scope_id default", scope="workspace", scope_id="repo-a")

    results = mem.search("Searchable command", scope="workspace", scope_id="repo-a", include_global=False, limit=10)

    assert [row.record.scope for row in results] == ["workspace"]
    assert [row.record.content for row in results] == ["Searchable command: scope_id default"]


def test_tenant_boundary_enforced(tmp_path):
    mem = DeepMemory(tmp_path / "memory.db")
    mem.add("Tenant boundary fact: acme scope_id settings", scope="workspace", scope_id="acme")
    mem.add("Tenant boundary fact: other scope_id settings", scope="workspace", scope_id="other")

    acme_results = mem.search("Tenant boundary fact", scope="workspace", scope_id="acme", include_global=False, limit=10)
    default_results = mem.search("Tenant boundary fact", include_global=False, limit=10)

    assert [row.record.scope_id for row in acme_results] == ["acme"]
    assert [row.record.content for row in acme_results] == ["Tenant boundary fact: acme scope_id settings"]
    assert default_results == []


def test_user_id_boundary_enforced(tmp_path):
    mem = DeepMemory(tmp_path / "memory.db")
    mem.add("User boundary fact: ben likes concise answers", scope="user", scope_id="ben")
    mem.add("User boundary fact: ada likes detailed answers", scope="user", scope_id="ada")

    ben_results = mem.search("User boundary fact", scope="user", scope_id="ben", include_global=False, limit=10)
    default_results = mem.search("User boundary fact", include_global=False, limit=10)

    assert [row.record.scope_id for row in ben_results] == ["ben"]
    assert [row.record.content for row in ben_results] == ["User boundary fact: ben likes concise answers"]
    assert default_results == []


def test_legacy_global_records_remain_visible_after_migration(tmp_path):
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
            expires_at TEXT
        );
        CREATE VIRTUAL TABLE memories_fts USING fts5(
            content, kind, source, content='memories', content_rowid='rowid'
        );
        INSERT INTO memories(id, content, kind, importance, confidence, created_at, updated_at)
        VALUES ('legacy-1', 'Legacy memory: global scope after migration', 'semantic', 0.9, 0.8,
                '2026-05-01T00:00:00+00:00', '2026-05-01T00:00:00+00:00');
        INSERT INTO memories_fts(rowid, content, kind, source)
        SELECT rowid, content, kind, COALESCE(source, '') FROM memories;
        """
    )
    conn.commit()
    conn.close()

    mem = DeepMemory(db)
    record = mem.get("legacy-1")
    results = mem.search("Legacy memory", limit=10)

    assert record.scope == "global"
    assert record.scope_id is None
    assert results[0].record.id == "legacy-1"


def test_basename_collision_two_different_paths_share_scope_id(tmp_path):
    left = tmp_path / "a" / "test"
    right = tmp_path / "b" / "test"
    left.mkdir(parents=True)
    right.mkdir(parents=True)

    assert _infer_workspace_from_cwd(left) == "test"
    assert _infer_workspace_from_cwd(right) == "test"


def test_scope_demote_cli_moves_global_memory_to_scope_id(tmp_path):
    db = tmp_path / "memory.db"
    mem = DeepMemory(db)
    record = mem.add("Workspace fact: demote me back", scope="workspace", scope_id="repo-a")
    promoted = mem.promote_scope(record.id, to="global")
    assert promoted.scope == "global"

    result = CliRunner().invoke(
        app,
        ["scope", "demote", str(db), record.id, "--to", "workspace", "--scope-id", "repo-a"],
    )

    assert result.exit_code == 0, result.output
    demoted = DeepMemory(db).get(record.id)
    assert demoted.scope == "workspace"
    assert demoted.scope_id == "repo-a"


def test_cli_add_and_search_support_project_scope_id_without_namespace_leakage(tmp_path):
    db = tmp_path / "memory.db"
    runner = CliRunner()

    add_project = runner.invoke(
        app,
        [
            "add",
            str(db),
            "Project fact: CLI exposes scope_id",
            "--scope",
            "project",
            "--scope-id",
            "deep-memory",
        ],
    )
    add_other = runner.invoke(
        app,
        [
            "add",
            str(db),
            "Project fact: other namespace",
            "--scope",
            "project",
            "--scope-id",
            "other-project",
        ],
    )
    search_project = runner.invoke(
        app,
        [
            "search",
            str(db),
            "Project fact",
            "--scope",
            "project",
            "--scope-id",
            "deep-memory",
            "--no-include-global",
            "--limit",
            "10",
        ],
    )

    assert add_project.exit_code == 0, add_project.output
    assert add_other.exit_code == 0, add_other.output
    assert '"scope": "project"' in add_project.output
    assert '"scope_id": "deep-memory"' in add_project.output
    assert search_project.exit_code == 0, search_project.output
    assert "deep-memory" in search_project.output
    assert "exposes scope_id" in search_project.output
    assert "other-project" not in search_project.output
    assert "Project fact: other namespace" not in search_project.output


def test_search_scope_id_without_scope_explains_fixed_scope_model(tmp_path):
    mem = DeepMemory(tmp_path / "memory.db")

    try:
        mem.search("anything", scope_id="deep-memory")
    except ValueError as exc:
        message = str(exc)
    else:  # pragma: no cover - assertion clarity
        raise AssertionError("scope_id without scope should be rejected")

    assert "scope is a fixed layer" in message
    assert "scope_id" in message
    assert "custom names" in message
