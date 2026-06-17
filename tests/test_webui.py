from __future__ import annotations

from deep_memory import DeepMemory
from deep_memory.webui import delete_memory, list_records, render_index, update_memory


def test_webui_lists_and_searches_memory_records(tmp_path):
    db = tmp_path / "memory.db"
    mem = DeepMemory(db)
    target = mem.add("用户偏好：中文为主，技术术语用英文", kind="semantic", importance=0.9)
    mem.add("本次会话讨论 WebUI", kind="episodic")

    rows = list_records(db, query="中文")

    assert [row.id for row in rows] == [target.id]
    assert rows[0].kind == "semantic"


def test_webui_updates_editable_memory_fields(tmp_path):
    db = tmp_path / "memory.db"
    mem = DeepMemory(db)
    record = mem.add("用户偏好：深色模式", kind="semantic", importance=0.4, confidence=0.6)

    updated = update_memory(
        db,
        record.id,
        content="用户偏好：浅色模式",
        kind="semantic",
        importance=0.8,
        confidence=0.9,
        source="webui:test",
    )

    assert updated.content == "用户偏好：浅色模式"
    assert updated.importance == 0.8
    assert updated.confidence == 0.9
    assert updated.source == "webui:test"
    assert mem.get(record.id).content == "用户偏好：浅色模式"


def test_webui_soft_deletes_records_from_default_list(tmp_path):
    db = tmp_path / "memory.db"
    mem = DeepMemory(db)
    record = mem.add("过期记忆", kind="semantic")

    deleted = delete_memory(db, record.id, reason="manual cleanup")

    assert deleted.conflict_status == "deprecated"
    assert list_records(db) == []
    assert list_records(db, include_deleted=True)[0].id == record.id
    assert "manual cleanup" in (list_records(db, include_deleted=True)[0].source or "")


def test_webui_renders_accessible_local_inspector(tmp_path):
    db = tmp_path / "memory.db"
    mem = DeepMemory(db)
    mem.add("用户偏好：中文为主", kind="semantic", source="test")

    html = render_index(db)

    assert "Memory Inspector" in html
    assert "用户偏好：中文为主" in html
    assert "method=\"post\"" in html
    assert "aria-label=\"Search memories\"" in html
