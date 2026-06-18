from __future__ import annotations

import json

from typer.testing import CliRunner

from deep_memory import DeepMemory
from deep_memory.cli import app
from deep_memory.mcp_server import memory_feedback, search_memory
from deep_memory.webui import render_index, telemetry_insights

runner = CliRunner()


def test_search_writes_retrieval_log_with_caller_and_scores(tmp_path):
    db = tmp_path / "memory.db"
    mem = DeepMemory(db)
    record = mem.add("用户偏好：中文为主，技术术语用英文", kind="semantic", importance=0.9)

    results = mem.search("用户偏好", limit=3, caller="wrapper")

    row = mem.conn.execute("SELECT * FROM retrieval_log").fetchone()
    assert results[0].record.id == record.id
    assert row["query"] == "用户偏好"
    assert row["caller"] == "wrapper"
    assert json.loads(row["returned_ids"])[0] == record.id
    assert json.loads(row["scores"])[0] > 0
    assert row["query_hash"]


def test_telemetry_can_be_disabled_by_env(tmp_path, monkeypatch):
    db = tmp_path / "memory.db"
    mem = DeepMemory(db)
    mem.add("用户偏好：中文为主", kind="semantic")
    monkeypatch.setenv("DEEP_MEMORY_TELEMETRY", "off")

    mem.search("用户偏好", caller="cli")

    count = mem.conn.execute("SELECT COUNT(*) AS n FROM retrieval_log").fetchone()["n"]
    assert count == 0


def test_telemetry_hash_only_mode_omits_raw_query(tmp_path, monkeypatch):
    db = tmp_path / "memory.db"
    mem = DeepMemory(db)
    mem.add("用户偏好：中文为主", kind="semantic")
    monkeypatch.setenv("DEEP_MEMORY_TELEMETRY_QUERY", "hash")

    mem.search("用户偏好", caller="cli")

    row = mem.conn.execute("SELECT query, query_hash FROM retrieval_log").fetchone()
    assert row["query"] is None
    assert row["query_hash"]


def test_feedback_round_trip_core_mcp_and_cli(tmp_path):
    db = tmp_path / "memory.db"
    mem = DeepMemory(db)
    record = mem.add("用户偏好：用 pytest 验证变更", kind="procedural")

    core_entry = mem.add_feedback(record.id, helpful=True, note="used in answer")
    mcp_entry = memory_feedback(record.id, False, "misleading", db_path=str(db))
    cli_result = runner.invoke(app, ["feedback", str(db), record.id, "--helpful", "--note", "clear"])

    assert core_entry.helpful is True
    assert mcp_entry["helpful"] is False
    assert cli_result.exit_code == 0
    rows = mem.conn.execute("SELECT helpful, note FROM memory_feedback ORDER BY id").fetchall()
    assert [(bool(row["helpful"]), row["note"]) for row in rows] == [
        (True, "used in answer"),
        (False, "misleading"),
        (True, "clear"),
    ]


def test_mcp_search_logs_caller(tmp_path):
    db = tmp_path / "memory.db"
    mem = DeepMemory(db)
    mem.add("用户偏好：中文为主", kind="semantic")

    assert search_memory("用户偏好", db_path=str(db))

    row = mem.conn.execute("SELECT caller FROM retrieval_log").fetchone()
    assert row["caller"] == "mcp"


def test_wrapper_searches_log_wrapper_caller(tmp_path):
    from deep_memory.adapters.agent_wrapper import run_codex_wrapper

    db = tmp_path / "memory.db"
    mem = DeepMemory(db)
    mem.add("用户偏好：先写测试再改实现", kind="procedural")

    result = run_codex_wrapper(db=db, task="测试", command=["python", "-c", "pass"], limit=1)

    assert result.returncode == 0
    row = mem.conn.execute("SELECT caller FROM retrieval_log").fetchone()
    assert row["caller"] == "wrapper"


def test_report_markdown_snapshot_and_webui_insights(tmp_path):
    db = tmp_path / "memory.db"
    mem = DeepMemory(db)
    first = mem.add("用户偏好：中文为主", kind="semantic", importance=0.9)
    mem.add("本次会话讨论 telemetry", kind="episodic")
    mem.search("用户偏好", caller="cli")
    mem.search("用户偏好", caller="cli")
    mem.add_feedback(first.id, helpful=False, note="stale")

    report = mem.telemetry_report_markdown()
    insights = telemetry_insights(db)
    html = render_index(db, view="insights")
    cli_result = runner.invoke(app, ["report", str(db)])

    assert "# deep-memory telemetry report (7 days)" in report
    assert "- retrievals: 2" in report
    assert "- hit rate: 100.0%" in report
    assert "## Score distribution" in report
    assert "## High usage / low feedback candidates" in report
    assert insights.retrieval_count == 2
    assert "Insights" in html
    assert "High usage / low feedback candidates" in html
    assert cli_result.exit_code == 0
    assert "retrievals: 2" in cli_result.stdout


def test_report_command_default_db_outputs_non_empty(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    db = tmp_path / ".deep-memory" / "deep-memory.db"
    mem = DeepMemory(db)
    mem.add("用户偏好：中文为主", kind="semantic")
    mem.search("用户偏好", caller="cli")

    result = runner.invoke(app, ["report"])

    assert result.exit_code == 0
    assert result.stdout.strip()
    assert "deep-memory telemetry report" in result.stdout
