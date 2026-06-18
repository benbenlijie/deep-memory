from __future__ import annotations

import json

from typer.testing import CliRunner

from deep_memory import DeepMemory
from deep_memory.cli import app
from deep_memory.portable import diff_databases


def _jsonl_rows(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def test_portable_export_writes_jsonl_and_manifest(tmp_path):
    db = tmp_path / "memory.db"
    out_dir = tmp_path / "portable"
    mem = DeepMemory(db)
    active = mem.add("用户偏好：中文为主", kind="semantic", importance=0.9)
    deleted = mem.add("已删除的旧偏好", kind="semantic", importance=0.8)
    mem.deprecate(deleted.id, source="test cleanup")
    mem.close()

    result = CliRunner().invoke(app, ["export", str(db), "--portable", "--output", str(out_dir)])

    assert result.exit_code == 0, result.output
    records_path = out_dir / "memories.jsonl"
    manifest_path = out_dir / "manifest.json"
    assert records_path.exists()
    assert manifest_path.exists()
    rows = _jsonl_rows(records_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert [row["id"] for row in rows] == [active.id]
    assert rows[0]["portable_schema_version"] == 1
    assert manifest["schema_version"] == 1
    assert manifest["record_count"] == 1
    assert manifest["checksum"]
    assert manifest["exported_at"]


def test_portable_export_as_of_filters_temporally(tmp_path):
    db = tmp_path / "memory.db"
    out_dir = tmp_path / "portable"
    mem = DeepMemory(db)
    old = mem.add(
        "项目状态：使用旧架构",
        event_time="2026-05-01T00:00:00+00:00",
        valid_until="2026-06-01T00:00:00+00:00",
    )
    current = mem.add("项目状态：使用新架构", event_time="2026-06-01T00:00:00+00:00")
    mem.close()

    result = CliRunner().invoke(
        app,
        ["export", str(db), "--portable", "--output", str(out_dir), "--as-of", "2026-05-15"],
    )

    assert result.exit_code == 0, result.output
    rows = _jsonl_rows(out_dir / "memories.jsonl")
    assert [row["id"] for row in rows] == [old.id]
    assert current.id not in {row["id"] for row in rows}


def test_portable_import_merge_round_trip_without_duplicates(tmp_path):
    source_db = tmp_path / "source.db"
    export_dir = tmp_path / "portable"
    target_db = tmp_path / "target.db"
    source = DeepMemory(source_db)
    first = source.add(
        "项目偏好：使用 local-first memory",
        kind="semantic",
        source={"agent": "human", "trust_level": "user", "origin_type": "explicit"},
        scope="project",
    )
    source.close()
    export_result = CliRunner().invoke(app, ["export", str(source_db), "--portable", "--output", str(export_dir)])
    assert export_result.exit_code == 0, export_result.output

    first_import = CliRunner().invoke(app, ["import", str(target_db), str(export_dir), "--merge"])
    second_import = CliRunner().invoke(app, ["import", str(target_db), str(export_dir), "--merge"])

    assert first_import.exit_code == 0, first_import.output
    assert second_import.exit_code == 0, second_import.output
    imported = DeepMemory(target_db)
    rows = imported.export_records()
    assert len(rows) == 1
    assert rows[0].content == first.content
    assert rows[0].scope == "project"
    assert rows[0].idempotency_key
    imported.close()


def test_portable_import_merge_prefers_higher_trust_then_newer_event_time(tmp_path):
    target_db = tmp_path / "target.db"
    low_trust_dir = tmp_path / "low"
    high_trust_dir = tmp_path / "high"
    newer_dir = tmp_path / "newer"

    low = DeepMemory(tmp_path / "low.db")
    low.add(
        "事实：模型优先级低可信",
        kind="semantic",
        source={"agent": "auto", "trust_level": "external", "origin_type": "imported"},
        scope="project",
        event_time="2026-01-01T00:00:00+00:00",
    )
    low.close()
    high = DeepMemory(tmp_path / "high.db")
    high.add(
        "事实：模型优先级高可信",
        kind="semantic",
        source={"agent": "human", "trust_level": "user", "origin_type": "explicit"},
        scope="project",
        event_time="2025-01-01T00:00:00+00:00",
    )
    high.close()
    newer = DeepMemory(tmp_path / "newer.db")
    newer.add(
        "事实：模型优先级更新事件",
        kind="semantic",
        source={"agent": "human", "trust_level": "user", "origin_type": "explicit"},
        scope="project",
        event_time="2027-01-01T00:00:00+00:00",
    )
    newer.close()
    for db, out_dir in [
        (tmp_path / "low.db", low_trust_dir),
        (tmp_path / "high.db", high_trust_dir),
        (tmp_path / "newer.db", newer_dir),
    ]:
        result = CliRunner().invoke(app, ["export", str(db), "--portable", "--output", str(out_dir)])
        assert result.exit_code == 0, result.output

    assert CliRunner().invoke(app, ["import", str(target_db), str(low_trust_dir), "--merge"]).exit_code == 0
    assert CliRunner().invoke(app, ["import", str(target_db), str(high_trust_dir), "--merge"]).exit_code == 0
    assert CliRunner().invoke(app, ["import", str(target_db), str(newer_dir), "--merge"]).exit_code == 0

    rows = DeepMemory(target_db).export_records()
    assert len(rows) == 1
    assert rows[0].content == "事实：模型优先级更新事件"
    assert rows[0].source_info.trust_level == "user"
    assert rows[0].event_time == "2027-01-01T00:00:00+00:00"


def test_portable_import_accepts_legacy_schema_version_zero(tmp_path):
    db = tmp_path / "target.db"
    portable = tmp_path / "legacy"
    portable.mkdir()
    record = {
        "content": "旧版 portable 记录",
        "kind": "semantic",
        "importance": 0.7,
        "confidence": 0.8,
        "source": "legacy-agent",
        "created_at": "2026-01-01T00:00:00+00:00",
        "updated_at": "2026-01-01T00:00:00+00:00",
        "event_time": "2026-01-01T00:00:00+00:00",
        "scope": "global",
    }
    (portable / "memories.jsonl").write_text(json.dumps(record, ensure_ascii=False) + "\n", encoding="utf-8")
    (portable / "manifest.json").write_text(
        json.dumps({"schema_version": 0, "record_count": 1, "checksum": "legacy", "exported_at": "2026-01-01T00:00:00+00:00"}),
        encoding="utf-8",
    )

    result = CliRunner().invoke(app, ["import", str(db), str(portable), "--merge"])

    assert result.exit_code == 0, result.output
    rows = DeepMemory(db).export_records()
    assert len(rows) == 1
    assert rows[0].content == "旧版 portable 记录"
    assert rows[0].source_info.agent == "legacy-agent"


def test_diff_databases_reports_only_in_a_only_in_b_and_conflicts(tmp_path):
    db_a = tmp_path / "a.db"
    db_b = tmp_path / "b.db"
    a = DeepMemory(db_a)
    a.add("仅在 A", kind="semantic", scope="project")
    a.add(
        "共同事实 A 版本",
        kind="semantic",
        scope="project",
        source={"agent": "a", "trust_level": "external", "origin_type": "imported"},
        event_time="2026-01-01T00:00:00+00:00",
    )
    a.close()
    b = DeepMemory(db_b)
    b.add("仅在 B", kind="semantic", scope="project")
    b.add(
        "共同事实 B 版本",
        kind="semantic",
        scope="project",
        source={"agent": "b", "trust_level": "user", "origin_type": "explicit"},
        event_time="2027-01-01T00:00:00+00:00",
    )
    b.close()

    diff = diff_databases(db_a, db_b)

    assert [item["content"] for item in diff["only_in_a"]] == ["仅在 A"]
    assert [item["content"] for item in diff["only_in_b"]] == ["仅在 B"]
    assert len(diff["conflicts"]) == 1
    assert diff["conflicts"][0]["winner"] == "b"


def test_diff_cli_outputs_json_shape(tmp_path):
    db_a = tmp_path / "a.db"
    db_b = tmp_path / "b.db"
    DeepMemory(db_a).add("仅在 A", kind="semantic")
    DeepMemory(db_b).add("仅在 B", kind="semantic")

    result = CliRunner().invoke(app, ["diff", str(db_a), str(db_b)])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert set(payload) == {"only_in_a", "only_in_b", "conflicts"}
    assert payload["only_in_a"][0]["content"] == "仅在 A"
    assert payload["only_in_b"][0]["content"] == "仅在 B"
