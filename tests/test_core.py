from datetime import datetime, timedelta, timezone

from deep_memory import DeepMemory
from deep_memory.core import forgetting_decay


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
