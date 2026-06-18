from __future__ import annotations

from deep_memory import DeepMemory
from deep_memory.mcp_server import (
    add_memory,
    list_memory_conflicts,
    memory_stats,
    resolve_memory_conflict,
    search_memory,
)


def test_mcp_add_refuses_policy_denied_memory(tmp_path):
    db = tmp_path / "memory.db"

    try:
        add_memory(db_path=str(db), content="user: hello\nassistant: hi", kind="semantic")
    except ValueError as exc:
        assert "raw transcript" in str(exc)
    else:  # pragma: no cover - assertion clarity
        raise AssertionError("raw transcript should be rejected")

    assert memory_stats(db_path=str(db))["total"] == 0


def test_mcp_add_search_and_stats_tools_share_database(tmp_path):
    db = tmp_path / "memory.db"

    added = add_memory(
        db_path=str(db),
        content="用户偏好：中文为主，技术术语用英文",
        kind="semantic",
        importance=0.9,
        confidence=0.85,
        source="mcp-test",
    )

    assert added["kind"] == "semantic"
    assert added["content"] == "用户偏好：中文为主，技术术语用英文"
    assert added["source"] == "mcp-test"

    results = search_memory(db_path=str(db), query="用户偏好", limit=3)

    assert results
    assert results[0]["record"]["id"] == added["id"]
    assert results[0]["record"]["kind"] == "semantic"
    assert results[0]["score"] > 0

    stats = memory_stats(db_path=str(db))

    assert stats["semantic"] == 1
    assert stats["total"] == 1


def test_mcp_search_accepts_kind_filter(tmp_path):
    db = tmp_path / "memory.db"
    add_memory(db_path=str(db), content="用户偏好：深色模式", kind="semantic")
    add_memory(db_path=str(db), content="用户偏好：本次会话讨论 MCP", kind="episodic")

    semantic_results = search_memory(db_path=str(db), query="用户偏好", kind="semantic")

    assert semantic_results
    assert {result["record"]["kind"] for result in semantic_results} == {"semantic"}


def test_mcp_surfaces_conflict_resolution_status(tmp_path):
    db = tmp_path / "memory.db"
    old = add_memory(db_path=str(db), content="用户偏好：深色模式", source="profile:v1")

    resolution = resolve_memory_conflict(
        db_path=str(db),
        content="用户偏好改为浅色模式",
        supersedes=[old["id"]],
        source="chat:42",
        confirmed_by_user=True,
    )
    conflicts = list_memory_conflicts(db_path=str(db), include_superseded=True)

    assert resolution["status"] == "resolved"
    assert resolution["confirmed_by_user"] is True
    assert resolution["record"]["conflict_status"] == "resolved"
    assert {item["record"]["conflict_status"] for item in conflicts} == {"resolved", "superseded"}


def test_mcp_add_defaults_to_workspace_scope_and_search_supports_scope_flags(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    db = tmp_path / "memory.db"

    added = add_memory(
        db_path=str(db),
        content="Workspace fact: default scope should be isolated",
        kind="semantic",
    )

    assert added["scope"] == "workspace"
    assert added["workspace"] == tmp_path.name

    results = search_memory(
        db_path=str(db),
        query="Workspace fact",
        include_global=False,
        cross_workspace=True,
    )

    assert results
    assert results[0]["record"]["scope"] == "workspace"


def test_mcp_scope_promotion_is_exposed_through_python_api(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    db = tmp_path / "memory.db"
    added = add_memory(db_path=str(db), content="Workspace fact to promote", scope="workspace")
    mem = DeepMemory(db)
    try:
        promoted = mem.promote_scope(added["id"], to="global")
        assert promoted.scope == "global"
        assert promoted.workspace is None
    finally:
        mem.close()
