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
