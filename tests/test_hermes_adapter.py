from __future__ import annotations

import json

from typer.testing import CliRunner

from deep_memory import DeepMemory
from deep_memory.adapters.hermes import iter_hermes_facts, write_hermes_session_facts
from deep_memory.cli import app


def test_iter_hermes_facts_reads_jsonl_fact_records(tmp_path):
    session = tmp_path / "session.jsonl"
    session.write_text(
        "\n".join(
            [
                json.dumps({"session_id": "s_123", "facts": [
                    {"content": "用户偏好：中文为主，技术术语用英文", "kind": "semantic", "importance": 0.9},
                    {"content": "成功流程应该沉淀为 skill", "kind": "procedural", "confidence": 0.7},
                ]}, ensure_ascii=False),
                json.dumps({"role": "assistant", "content": "ordinary chat, not a durable fact"}, ensure_ascii=False),
            ]
        ),
        encoding="utf-8",
    )

    facts = list(iter_hermes_facts(session))

    assert [fact.content for fact in facts] == [
        "用户偏好：中文为主，技术术语用英文",
        "成功流程应该沉淀为 skill",
    ]
    assert facts[0].kind == "semantic"
    assert facts[0].importance == 0.9
    assert facts[0].source == "hermes:s_123"
    assert facts[0].agent == "hermes"
    assert facts[1].kind == "procedural"
    assert facts[1].confidence == 0.7


def test_write_hermes_session_facts_persists_searchable_memories(tmp_path):
    session = tmp_path / "session.jsonl"
    session.write_text(
        json.dumps(
            {
                "session_id": "s_demo",
                "facts": [
                    {"content": "项目约定：所有 agent 配置输出到独立目录", "kind": "semantic", "importance": 0.85}
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    db = tmp_path / "memory.db"

    records = write_hermes_session_facts(db, session)

    mem = DeepMemory(db)
    results = mem.search("独立目录", limit=3)
    assert len(records) == 1
    assert results
    assert results[0].record.content == "项目约定：所有 agent 配置输出到独立目录"
    assert results[0].record.source == "hermes:s_demo"


def test_hermes_import_cli_imports_facts_and_prints_count(tmp_path):
    session = tmp_path / "session.jsonl"
    session.write_text(
        json.dumps({"session_id": "s_cli", "facts": [{"content": "用户偏好：回答要简洁有深度"}]}, ensure_ascii=False),
        encoding="utf-8",
    )
    db = tmp_path / "memory.db"

    result = CliRunner().invoke(app, ["hermes-import", str(db), str(session)])

    assert result.exit_code == 0
    assert "imported 1 Hermes fact" in result.output
    assert DeepMemory(db).stats()["semantic"] == 1


def test_hermes_import_uses_scope_id_and_dedupes_reimports(tmp_path):
    session = tmp_path / "session.jsonl"
    session.write_text(
        json.dumps(
            {
                "session_id": "s_scope",
                "scope": "workspace",
                "scope_id": "/repo/a",
                "agent": "hermes",
                "facts": [
                    {
                        "content": "项目约定：所有 agent 配置输出到独立目录",
                        "kind": "semantic",
                        "importance": 0.85,
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    db = tmp_path / "memory.db"

    first = write_hermes_session_facts(db, session)
    second = write_hermes_session_facts(db, session)
    mem = DeepMemory(db)

    try:
        results = mem.search("独立目录", scope="workspace", scope_id="/repo/a", limit=3)
        assert len(first) == 1
        assert len(second) == 1
        assert len(results) == 1
        assert results[0].record.scope_id == "/repo/a"
        assert results[0].record.scope == "workspace"
    finally:
        mem.close()


def test_hermes_import_infers_event_time_from_session_timestamp(tmp_path):
    session = tmp_path / "session.jsonl"
    session.write_text(
        json.dumps(
            {
                "session_id": "s_time",
                "timestamp": "2026-05-20T12:34:56Z",
                "facts": [{"content": "项目事实：event_time 来自 session timestamp"}],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    db = tmp_path / "memory.db"

    records = write_hermes_session_facts(db, session)

    assert records[0].event_time == "2026-05-20T12:34:56+00:00"


def test_hermes_import_refuses_obvious_secret_facts(tmp_path):
    session = tmp_path / "session.jsonl"
    session.write_text(
        json.dumps(
            {
                "session_id": "s_secret",
                "facts": [{"content": "API token: ghp_1234567890abcdef1234567890abcdef123456"}],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    db = tmp_path / "memory.db"

    result = CliRunner().invoke(app, ["hermes-import", str(db), str(session)])

    assert result.exit_code != 0
    assert "refusing to store high-risk memory" in result.output
    assert DeepMemory(db).stats()["total"] == 0


def test_scope_id_preserves_explicit_names_and_supports_cross_scope_search(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    session = tmp_path / "session.jsonl"
    session.write_text(
        json.dumps(
            {
                "session_id": "s_scope2",
                "scope": "project",
                "scope_id": str(tmp_path / "repo-a"),
                "agent": "hermes",
                "facts": [
                    {"content": "Project convention: default scope should be workspace", "kind": "semantic"}
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    db = tmp_path / "memory.db"

    write_hermes_session_facts(db, session)
    mem = DeepMemory(db)
    try:
        row = mem.search("default scope", cross_scope=True, include_global=False, limit=3)[0].record
        assert row.scope == "project"
        assert row.scope_id == str(tmp_path / "repo-a")
    finally:
        mem.close()
