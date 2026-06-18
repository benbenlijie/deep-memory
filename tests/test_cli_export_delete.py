from __future__ import annotations

import json

from typer.testing import CliRunner

from deep_memory import DeepMemory
from deep_memory.cli import app


def test_export_cli_outputs_active_memories_by_default(tmp_path):
    db = tmp_path / "memory.db"
    mem = DeepMemory(db)
    active = mem.add("用户偏好：中文为主", kind="semantic", importance=0.9)
    deleted = mem.add("已删除的旧偏好", kind="semantic", importance=0.8)
    mem.deprecate(deleted.id, source="test cleanup")

    result = CliRunner().invoke(app, ["export", str(db)])

    assert result.exit_code == 0
    rows = [json.loads(line) for line in result.output.splitlines() if line.strip()]
    assert [row["id"] for row in rows] == [active.id]
    assert rows[0]["content"] == "用户偏好：中文为主"
    assert rows[0]["conflict_status"] == "active"


def test_export_cli_can_explicitly_include_deprecated_memories(tmp_path):
    db = tmp_path / "memory.db"
    mem = DeepMemory(db)
    active = mem.add("当前偏好", kind="semantic")
    deleted = mem.add("已删除偏好", kind="semantic")
    mem.deprecate(deleted.id, source="test cleanup")

    result = CliRunner().invoke(app, ["export", str(db), "--include-deprecated"])

    assert result.exit_code == 0
    rows = [json.loads(line) for line in result.output.splitlines() if line.strip()]
    assert {row["id"] for row in rows} == {active.id, deleted.id}
    assert any(row["conflict_status"] == "deprecated" for row in rows)


def test_hard_delete_cli_physically_removes_memory(tmp_path):
    db = tmp_path / "memory.db"
    mem = DeepMemory(db)
    record = mem.add("误存的敏感记录", kind="semantic")
    mem.close()

    result = CliRunner().invoke(app, ["hard-delete", str(db), record.id])

    assert result.exit_code == 0
    assert "hard-deleted 1 memory" in result.output
    reopened = DeepMemory(db)
    assert reopened.search("敏感记录") == []
    try:
        reopened.get(record.id)
    except KeyError:
        pass
    else:  # pragma: no cover - assertion clarity
        raise AssertionError("hard-deleted record should not exist")


def test_export_cli_excludes_superseded_memories_by_default(tmp_path):
    db = tmp_path / "memory.db"
    mem = DeepMemory(db)
    old = mem.add("用户偏好：深色模式", kind="semantic", source="profile:v1")
    resolved = mem.resolve_conflict(
        "用户偏好改为浅色模式",
        supersedes=[old.id],
        source="chat:42",
        confirmed_by_user=True,
    )

    result = CliRunner().invoke(app, ["export", str(db)])

    assert result.exit_code == 0
    rows = [json.loads(line) for line in result.output.splitlines() if line.strip()]
    assert [row["id"] for row in rows] == [resolved.record.id]
    assert rows[0]["conflict_status"] == "resolved"


def test_export_cli_as_of_filters_temporally(tmp_path):
    db = tmp_path / "memory.db"
    mem = DeepMemory(db)
    old = mem.add(
        "项目状态：使用旧架构",
        event_time="2026-05-01T00:00:00+00:00",
        valid_until="2026-06-01T00:00:00+00:00",
    )
    current = mem.add("项目状态：使用新架构", event_time="2026-06-01T00:00:00+00:00")
    mem.close()

    result = CliRunner().invoke(app, ["export", str(db), "--as-of", "2026-05-15"])

    assert result.exit_code == 0
    rows = [json.loads(line) for line in result.output.splitlines() if line.strip()]
    assert [row["id"] for row in rows] == [old.id]
    assert current.id not in {row["id"] for row in rows}


def test_add_cli_refuses_obvious_secret_values(tmp_path):
    db = tmp_path / "memory.db"

    result = CliRunner().invoke(
        app,
        ["add", str(db), "API key: sk-1234567890abcdef1234567890abcdef"],
    )

    assert result.exit_code != 0
    assert "refusing to store high-risk memory" in result.output
    assert DeepMemory(db).stats()["total"] == 0
