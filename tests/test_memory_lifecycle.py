from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from typer.testing import CliRunner

from deep_memory import DeepMemory
from deep_memory.cli import app
from deep_memory.core import LifecycleConfig, forgetting_decay


def test_search_marks_retrieved_memories_as_accessed(tmp_path):
    mem = DeepMemory(tmp_path / "memory.db")
    record = mem.add("用户偏好：中文为主，技术术语用英文", kind="semantic", importance=0.9)

    results = mem.search("用户偏好", limit=3)

    assert results[0].record.id == record.id
    accessed = mem.get(record.id)
    assert accessed.access_count == 1
    assert accessed.last_accessed_at is not None


def test_forgetting_decay_uses_kind_specific_half_life():
    created = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    config = LifecycleConfig(half_life_days={"working": 7, "episodic": 30, "semantic": 180, "procedural": 365})

    working = forgetting_decay(created, importance=0.5, kind="working", config=config)
    semantic = forgetting_decay(created, importance=0.5, kind="semantic", config=config)

    assert semantic > working


def test_consolidation_reduces_100_similar_active_memories_to_30_or_less(tmp_path):
    mem = DeepMemory(tmp_path / "memory.db")
    for idx in range(100):
        mem.add(
            f"用户偏好：中文为主 技术术语保留英文 相似记忆样本 {idx}",
            kind="semantic",
            importance=0.6,
            confidence=0.8,
        )

    plan = mem.consolidate(dry_run=False, threshold=0.6, max_group_size=10)

    active = mem.export_records(include_deprecated=False)
    archived = [record for record in mem.export_records(include_deprecated=True) if record.conflict_status == "archived"]
    assert len(active) <= 30
    assert plan.groups
    assert archived
    assert any(record.source and "consolidated from" in record.source for record in active)


def test_consolidation_dry_run_does_not_modify_db(tmp_path):
    mem = DeepMemory(tmp_path / "memory.db")
    for idx in range(5):
        mem.add(f"项目事实：alpha beta gamma delta {idx}", kind="semantic")
    before = [(record.id, record.conflict_status) for record in mem.export_records(include_deprecated=True)]

    plan = mem.consolidate(dry_run=True, threshold=0.6)
    after = [(record.id, record.conflict_status) for record in mem.export_records(include_deprecated=True)]

    assert plan.groups
    assert after == before


def test_consolidate_cli_dry_run_outputs_candidates_without_modifying_db(tmp_path):
    db = tmp_path / "memory.db"
    mem = DeepMemory(db)
    for idx in range(5):
        mem.add(f"项目事实：alpha beta gamma delta {idx}", kind="semantic")
    before = mem.stats()["total"]
    mem.close()

    result = CliRunner().invoke(app, ["consolidate", "--dry-run", str(db)])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["dry_run"] is True
    assert payload["groups"]
    reopened = DeepMemory(db)
    assert reopened.stats()["total"] == before
    assert all(record.conflict_status == "active" for record in reopened.export_records(include_deprecated=True))
