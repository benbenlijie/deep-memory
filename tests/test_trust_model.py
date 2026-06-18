from __future__ import annotations

from datetime import datetime, timedelta, timezone

from typer.testing import CliRunner

from deep_memory import DeepMemory
from deep_memory.cli import app
from deep_memory.core import SourceInfo, parse_source_info


def test_structured_source_can_be_added_and_legacy_string_is_upgraded(tmp_path):
    mem = DeepMemory(tmp_path / "memory.db")

    structured = mem.add(
        "用户明确偏好：中文为主",
        kind="semantic",
        source={"agent": "human", "trust_level": "user", "origin_type": "explicit"},
    )
    legacy = mem.add("Codex 自动提取的项目约定", kind="semantic", source="codex:s_123")

    assert structured.source == {"agent": "human", "trust_level": "user", "origin_type": "explicit"}
    assert structured.source_info.trust_level == "user"
    assert structured.source_info.trust_factor == 1.0
    assert legacy.source == "codex:s_123"
    assert legacy.source_info == SourceInfo(
        agent="codex:s_123", trust_level="agent-auto", origin_type="auto-extracted"
    )
    assert parse_source_info(None) == SourceInfo(
        agent=None, trust_level="agent-auto", origin_type="auto-extracted"
    )


def test_parse_source_info_auto_detects_external_url_source():
    assert parse_source_info("https://example.com/page").trust_level == "external"
    assert parse_source_info("http://example.com/page").trust_level == "external"
    assert parse_source_info("ftp://example.com/archive.tar.gz").trust_level == "external"
    assert parse_source_info("ftps://example.com/archive.tar.gz").trust_level == "external"
    assert parse_source_info("mailto:security@example.com").trust_level == "external"
    assert parse_source_info("192.168.1.1").trust_level == "external"
    assert parse_source_info("10.0.0.1:8080/status").trust_level == "external"
    assert parse_source_info("[::1]").trust_level == "external"
    assert parse_source_info("[fe80::1]:80/status").trust_level == "external"


def test_parse_source_info_does_not_auto_detect_ambiguous_source_names():
    assert parse_source_info("claude-code").trust_level == "agent-auto"
    assert parse_source_info("example.com").trust_level == "agent-auto"
    assert parse_source_info("file:///tmp/memory.json").trust_level == "agent-auto"


def test_parse_source_info_auto_detects_imported_source_without_agent():
    info = parse_source_info({"origin_type": "imported"})

    assert info == SourceInfo(agent=None, trust_level="external", origin_type="imported")


def test_parse_source_info_auto_detects_explicit_human_source_as_user():
    info = parse_source_info({"agent": "human", "origin_type": "explicit"})
    user_info = parse_source_info({"agent": "user", "origin_type": "explicit"})

    assert info == SourceInfo(agent="human", trust_level="user", origin_type="explicit")
    assert user_info == SourceInfo(agent="user", trust_level="user", origin_type="explicit")


def test_parse_source_info_respects_auto_detect_config_off(monkeypatch):
    monkeypatch.setenv("DEEP_MEMORY_TRUST_AUTO_DETECT", "false")

    assert parse_source_info("https://example.com/page").trust_level == "agent-auto"
    assert parse_source_info({"origin_type": "imported"}).trust_level == "agent-auto"
    assert parse_source_info({"agent": "human", "origin_type": "explicit"}).trust_level == "agent-auto"


def test_search_scores_are_weighted_by_source_trust_level(tmp_path):
    mem = DeepMemory(tmp_path / "memory.db")
    low = mem.add(
        "部署命令：uv run deploy",
        kind="procedural",
        importance=1.0,
        confidence=1.0,
        source={"agent": "unknown-web", "trust_level": "external", "origin_type": "imported"},
    )
    high = mem.add(
        "部署命令：uv run deploy",
        kind="procedural",
        importance=0.2,
        confidence=0.2,
        source={"agent": "human", "trust_level": "user", "origin_type": "explicit"},
    )

    results = mem.search("部署命令", limit=2)

    assert [result.record.id for result in results] == [high.id]
    assert results[0].record.source_info.trust_level == "user"
    assert results[0].score > 0
    assert mem.get(low.id).conflict_status == "candidate"


def test_external_trust_factor_is_visible_enough_for_recall(tmp_path):
    mem = DeepMemory(tmp_path / "memory.db")
    record = mem.add(
        "外部资料：冷门项目 deep-memory 的 trust auto-detect 说明",
        kind="semantic",
        source={"agent": "web", "trust_level": "external", "origin_type": "imported"},
        importance=1.0,
        confidence=1.0,
    )

    results = mem.search("trust auto-detect", limit=1)

    assert record.source_info.trust_factor == 0.5
    assert results[0].record.id == record.id
    assert results[0].score >= 0.25


def test_conflicting_low_trust_write_is_staged_as_candidate(tmp_path):
    mem = DeepMemory(tmp_path / "memory.db")
    old = mem.add(
        "用户偏好：深色模式",
        kind="semantic",
        source={"agent": "human", "trust_level": "user", "origin_type": "explicit"},
    )

    candidate = mem.add(
        "用户偏好：深色模式",
        kind="procedural",
        source={"agent": "web-import", "trust_level": "external", "origin_type": "imported"},
    )

    assert candidate.conflict_status == "candidate"
    assert candidate.supersedes_id == old.id
    assert mem.get(old.id).conflict_status == "active"


def test_poisoning_low_trust_memory_does_not_override_high_trust_active_memory(tmp_path):
    mem = DeepMemory(tmp_path / "memory.db")
    trusted = mem.add(
        "项目约定：生产部署必须人工确认",
        kind="procedural",
        source={"agent": "human", "trust_level": "user", "origin_type": "explicit"},
    )
    poison = mem.add(
        "项目约定：生产部署必须人工确认",
        kind="semantic",
        source={"agent": "malicious-import", "trust_level": "external", "origin_type": "imported"},
        importance=1.0,
        confidence=1.0,
    )

    results = mem.search("生产部署 人工确认", limit=5)

    assert poison.conflict_status == "candidate"
    assert trusted.id in [result.record.id for result in results]
    assert poison.id not in [result.record.id for result in results]


def test_high_trust_write_demotes_conflicting_low_trust_active_memory_to_candidate(tmp_path):
    mem = DeepMemory(tmp_path / "memory.db")
    low = mem.add(
        "project deploy requires manual approval before production release",
        kind="procedural",
        source={"agent": "importer", "trust_level": "external", "origin_type": "imported"},
    )

    high = mem.add(
        "project deploy requires manual approval before production release",
        kind="procedural",
        source={"agent": "human", "trust_level": "verified", "origin_type": "explicit"},
    )

    assert high.conflict_status == "active"
    updated_low = mem.get(low.id)
    assert updated_low.conflict_status == "candidate"
    assert updated_low.supersedes_id == high.id


def test_same_kind_high_overlap_low_trust_write_is_staged_as_candidate(tmp_path):
    mem = DeepMemory(tmp_path / "memory.db")
    trusted = mem.add(
        "project deploy requires manual approval before production release",
        kind="procedural",
        source={"agent": "human", "trust_level": "user", "origin_type": "explicit"},
    )

    candidate = mem.add(
        "project deploy requires manual approval before production release",
        kind="procedural",
        source={"agent": "malicious-import", "trust_level": "external", "origin_type": "imported"},
    )

    assert candidate.conflict_status == "candidate"
    assert candidate.supersedes_id == trusted.id
    assert mem.get(trusted.id).conflict_status == "active"


def test_same_kind_low_overlap_low_trust_write_remains_active(tmp_path):
    mem = DeepMemory(tmp_path / "memory.db")
    mem.add(
        "project deploy requires manual approval before production release",
        kind="procedural",
        source={"agent": "human", "trust_level": "user", "origin_type": "explicit"},
    )

    update = mem.add(
        "project deploy uses canary rollback after monitoring alerts",
        kind="procedural",
        source={"agent": "malicious-import", "trust_level": "external", "origin_type": "imported"},
    )

    assert update.conflict_status == "active"
    assert update.supersedes_id is None


def test_same_kind_high_overlap_equal_trust_write_remains_active(tmp_path):
    mem = DeepMemory(tmp_path / "memory.db")
    mem.add(
        "project deploy requires manual approval before production release",
        kind="procedural",
        source={"agent": "pipeline-a", "trust_level": "verified", "origin_type": "explicit"},
    )

    revision = mem.add(
        "project deploy requires manual approval before production release",
        kind="procedural",
        source={"agent": "pipeline-b", "trust_level": "verified", "origin_type": "explicit"},
    )

    assert revision.conflict_status == "active"
    assert revision.supersedes_id is None


def test_trust_list_orders_records_by_trust_level(tmp_path):
    db = tmp_path / "memory.db"
    mem = DeepMemory(db)
    mem.add(
        "外部导入：低信任",
        source={"agent": "web", "trust_level": "external", "origin_type": "imported"},
    )
    mem.add(
        "用户明确：高信任",
        source={"agent": "human", "trust_level": "user", "origin_type": "explicit"},
    )
    mem.add("旧格式：自动升级", source="codex:s_legacy")
    mem.close()

    result = CliRunner().invoke(app, ["trust", "list", str(db)])

    assert result.exit_code == 0
    output = result.output
    assert output.index("1.0") < output.index("0.50")
    assert "human" in output
    assert "web" in output


def test_trust_list_default_limit_and_count_message(tmp_path):
    db = tmp_path / "memory.db"
    mem = DeepMemory(db)
    for i in range(60):
        mem.add(f"记录 {i}", source={"agent": "human", "trust_level": "user", "origin_type": "explicit"})
    mem.close()

    result = CliRunner().invoke(app, ["trust", "list", str(db)])

    assert result.exit_code == 0
    assert "showing 50 of 60" in result.output
    assert result.output.count("记录") == 50


def test_trust_list_suspicious_agent_filter_and_all(tmp_path):
    db = tmp_path / "memory.db"
    mem = DeepMemory(db)
    suspicious = mem.add(
        "外部来源：可疑",
        source={"agent": "web", "trust_level": "external", "origin_type": "imported"},
    )
    mem.add(
        "用户来源：可信",
        source={"agent": "human", "trust_level": "user", "origin_type": "explicit"},
    )
    mem.add(
        "另一个外部来源：可疑",
        source={"agent": "web", "trust_level": "external", "origin_type": "imported"},
    )
    mem.close()

    suspicious_result = CliRunner().invoke(app, ["trust", "list", str(db), "--suspicious"])
    by_agent_result = CliRunner().invoke(app, ["trust", "list", str(db), "--by-agent", "web"])
    all_result = CliRunner().invoke(app, ["trust", "list", str(db), "--all"])

    assert suspicious_result.exit_code == 0
    assert by_agent_result.exit_code == 0
    assert all_result.exit_code == 0
    assert "外部来源：可疑" in suspicious_result.output
    assert "另一个外部来源：可疑" in suspicious_result.output
    assert suspicious.id in suspicious_result.output
    assert "用户来源：可信" not in suspicious_result.output
    assert by_agent_result.output.count("web") == 2
    assert "showing 2 of 2" in by_agent_result.output
    assert "showing 3 of 3" in all_result.output


def test_trust_list_by_trust_filter(tmp_path):
    db = tmp_path / "memory.db"
    mem = DeepMemory(db)
    mem.add("用户记录", source={"agent": "human", "trust_level": "user", "origin_type": "explicit"})
    mem.add("外部记录", source={"agent": "web", "trust_level": "external", "origin_type": "imported"})
    mem.close()

    result = CliRunner().invoke(app, ["trust", "list", str(db), "--by-trust", "external"])

    assert result.exit_code == 0
    assert "外部记录" in result.output
    assert "用户记录" not in result.output


def test_trust_promote_command_updates_record_trust_level(tmp_path):
    db = tmp_path / "memory.db"
    mem = DeepMemory(db)
    record = mem.add(
        "外部资料：审核后可信",
        source={"origin_type": "imported"},
    )
    mem.close()

    result = CliRunner().invoke(app, ["trust", "promote", str(db), record.id, "--to", "verified"])

    assert result.exit_code == 0
    mem = DeepMemory(db)
    promoted = mem.get(record.id)
    mem.close()
    assert promoted.source_info.trust_level == "verified"
    assert promoted.source_info.origin_type == "explicit"
    assert promoted.source_info.agent is None
    assert promoted.source_info.promoted_by == "reviewer"
    assert promoted.source_info.promoted_at is not None


def test_trust_promote_preserves_original_agent_and_records_actor(tmp_path):
    db = tmp_path / "memory.db"
    mem = DeepMemory(db)
    record = mem.add(
        "Codex 自动提取：需要审核后提升",
        source={"agent": "codex", "trust_level": "agent-auto", "origin_type": "auto-extracted"},
    )

    promoted = mem.promote_trust(record.id, to="verified", promoted_by="alice", reason="manual review")
    audit = mem.trust_audit(record.id)
    mem.close()

    assert promoted.source_info.agent == "codex"
    assert promoted.source_info.trust_level == "verified"
    assert promoted.source_info.origin_type == "explicit"
    assert promoted.source_info.promoted_by == "alice"
    assert promoted.source_info.promoted_at is not None
    assert audit[0].memory_id == record.id
    assert audit[0].action == "promote"
    assert audit[0].old_trust == "agent-auto"
    assert audit[0].new_trust == "verified"
    assert audit[0].actor == "alice"
    assert audit[0].reason == "manual review"


def test_parse_source_info_legacy_promoted_fields_are_optional():
    old_info = parse_source_info({"agent": "codex", "trust_level": "verified", "origin_type": "explicit"})
    new_info = parse_source_info(
        {
            "agent": "codex",
            "trust_level": "verified",
            "origin_type": "explicit",
            "promoted_by": "reviewer",
            "promoted_at": "2026-06-17T15:30:00+00:00",
        }
    )

    assert old_info.promoted_by is None
    assert old_info.promoted_at is None
    assert new_info.promoted_by == "reviewer"
    assert new_info.promoted_at == "2026-06-17T15:30:00+00:00"


def test_trust_audit_command_supports_memory_id_and_recent(tmp_path):
    db = tmp_path / "memory.db"
    mem = DeepMemory(db)
    record = mem.add("外部资料：CLI audit", source={"agent": "codex", "origin_type": "auto-extracted"})
    mem.promote_trust(record.id, to="verified", promoted_by="cli-reviewer")
    mem.close()

    by_id = CliRunner().invoke(app, ["trust", "audit", str(db), record.id])
    recent = CliRunner().invoke(app, ["trust", "audit", str(db), "--recent", "7"])

    assert by_id.exit_code == 0
    assert recent.exit_code == 0
    assert record.id in by_id.output
    assert "cli-reviewer" in by_id.output
    assert record.id in recent.output


def test_agent_registry_bootstraps_defaults_and_unknown_agent_cold_start(tmp_path):
    mem = DeepMemory(tmp_path / "memory.db")

    defaults = {entry["agent"]: entry for entry in mem.agent_list()}
    assert defaults["codex"]["trusted"] is True
    assert defaults["hermes"]["trusted"] is True

    record = mem.add(
        "新 agent 明确写入的项目事实",
        source={"agent": "new-agent", "origin_type": "explicit"},
    )

    assert record.baseline_trust == 0.7
    assert record.reputation == 1.0
    assert record.source_info.trust_factor == 0.7
    registry = {entry["agent"]: entry for entry in mem.agent_list()}
    assert registry["new-agent"]["trusted"] is False
    assert registry["new-agent"]["memory_count"] == 1


def test_baseline_matrix_for_trusted_known_unknown_imported_and_web(tmp_path):
    mem = DeepMemory(tmp_path / "memory.db")
    mem.set_agent_trust("trusted-bot", to="trusted")
    mem.set_agent_trust("known-bot", to="known")

    cases = [
        ({"agent": "human", "origin_type": "explicit"}, 1.0),
        ({"agent": "trusted-bot", "origin_type": "explicit"}, 0.85),
        ({"agent": "trusted-bot", "origin_type": "auto-extracted"}, 0.65),
        ({"agent": "known-bot", "origin_type": "explicit"}, 0.7),
        ({"agent": "known-bot", "origin_type": "auto-extracted"}, 0.55),
        ({"agent": "unknown-bot", "origin_type": "explicit"}, 0.7),
        ({"agent": "fresh-bot", "origin_type": "auto-extracted"}, 0.45),
        ({"agent": "importer", "origin_type": "imported"}, 0.35),
        ({"origin_type": "imported"}, 0.3),
        ("https://example.com/memory", 0.2),
    ]

    for index, (source, expected) in enumerate(cases):
        record = mem.add(f"baseline case {index}", source=source)
        assert record.baseline_trust == expected
        assert record.source_info.trust_factor == expected


def test_feedback_updates_per_memory_reputation_and_clamps(tmp_path):
    mem = DeepMemory(tmp_path / "memory.db")
    good = mem.add("反馈会提升这条 memory", source={"agent": "human", "origin_type": "explicit"})
    bad = mem.add("反馈会降低这条 memory", source={"agent": "human", "origin_type": "explicit"})

    mem.add_feedback(good.id, helpful=True)
    mem.add_feedback(bad.id, helpful=False)

    assert mem.get(good.id).reputation == 1.02
    assert mem.get(bad.id).reputation == 0.95
    for _ in range(100):
        mem.add_feedback(good.id, helpful=True)
        mem.add_feedback(bad.id, helpful=False)
    assert mem.get(good.id).reputation == 1.5
    assert mem.get(bad.id).reputation == 0.3


def test_lazy_reputation_decay_on_search_updates_returned_record(tmp_path):
    db = tmp_path / "memory.db"
    mem = DeepMemory(db)
    record = mem.add("lazy decay searchable marker", source={"agent": "human", "origin_type": "explicit"})
    old = datetime.now(timezone.utc) - timedelta(days=20)
    mem.conn.execute(
        "UPDATE memories SET reputation = ?, reputation_updated_at = ? WHERE id = ?",
        (1.0, old.isoformat(), record.id),
    )
    mem.conn.commit()

    results = mem.search("lazy decay searchable marker", limit=1, now=datetime.now(timezone.utc))

    assert results[0].record.id == record.id
    decayed = mem.get(record.id)
    assert decayed.reputation == 0.98
    assert decayed.source_info.trust_factor == 0.98


def test_search_uses_baseline_times_reputation_for_scoring(tmp_path):
    mem = DeepMemory(tmp_path / "memory.db")
    low_rep = mem.add(
        "排序测试：相同内容",
        source={"agent": "human", "origin_type": "explicit"},
        importance=1.0,
        confidence=1.0,
    )
    high_rep = mem.add(
        "排序测试：相同内容",
        source={"agent": "human", "origin_type": "explicit"},
        importance=1.0,
        confidence=1.0,
    )
    mem.conn.execute("UPDATE memories SET reputation = 0.4 WHERE id = ?", (low_rep.id,))
    mem.conn.execute("UPDATE memories SET reputation = 1.3 WHERE id = ?", (high_rep.id,))
    mem.conn.commit()

    results = mem.search("排序测试", limit=2)

    assert [result.record.id for result in results] == [high_rep.id, low_rep.id]
    assert results[0].record.source_info.trust_factor == 1.3
    assert results[1].record.source_info.trust_factor == 0.4


def test_helpful_feedback_reputation_boost_changes_search_ranking(tmp_path):
    mem = DeepMemory(tmp_path / "memory.db")
    plain = mem.add(
        "feedback ranking same base query",
        source={"agent": "human", "origin_type": "explicit"},
        importance=1.0,
        confidence=1.0,
    )
    helpful = mem.add(
        "feedback ranking same base query",
        source={"agent": "human", "origin_type": "explicit"},
        importance=1.0,
        confidence=1.0,
    )
    mem.add_feedback(helpful.id, helpful=True)

    results = mem.search("feedback ranking same base query", limit=2)

    assert mem.get(helpful.id).reputation > mem.get(plain.id).reputation
    assert [result.record.id for result in results] == [helpful.id, plain.id]


def test_agent_trust_bulk_update_changes_search_ranking(tmp_path):
    mem = DeepMemory(tmp_path / "memory.db")
    promoted_agent_record = mem.add(
        "agent trust ranking shared query",
        source={"agent": "helper", "origin_type": "explicit"},
        importance=0.95,
        confidence=1.0,
    )
    known_agent_record = mem.add(
        "agent trust ranking shared query",
        source={"agent": "other-helper", "origin_type": "explicit"},
        importance=1.0,
        confidence=1.0,
    )

    before = mem.search("agent trust ranking shared query", limit=2)
    mem.set_agent_trust("helper", to="trusted")
    after = mem.search("agent trust ranking shared query", limit=2)

    assert [result.record.id for result in before] == [known_agent_record.id, promoted_agent_record.id]
    assert [result.record.id for result in after] == [promoted_agent_record.id, known_agent_record.id]


def test_agent_trust_cli_bulk_updates_existing_and_future_baseline(tmp_path):
    db = tmp_path / "memory.db"
    mem = DeepMemory(db)
    before = mem.add("agent trust before", source={"agent": "helper", "origin_type": "explicit"})
    mem.close()

    result = CliRunner().invoke(app, ["agent", "trust", str(db), "helper", "--to", "trusted"])

    assert result.exit_code == 0
    mem = DeepMemory(db)
    after = mem.add("agent trust after", source={"agent": "helper", "origin_type": "explicit"})
    updated = mem.get(before.id)
    mem.close()
    assert updated.baseline_trust == 0.85
    assert after.baseline_trust == 0.85
    assert "helper" in result.output


def test_agent_list_cli_outputs_registry_with_counts(tmp_path):
    db = tmp_path / "memory.db"
    mem = DeepMemory(db)
    mem.add("agent list sample", source={"agent": "list-bot", "origin_type": "explicit"})
    mem.close()

    result = CliRunner().invoke(app, ["agent", "list", str(db)])

    assert result.exit_code == 0
    assert "list-bot" in result.output
    assert "known" in result.output


def test_agent_list_cli_uses_default_project_db_when_db_is_omitted(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    db = tmp_path / ".deep-memory" / "deep-memory.db"
    mem = DeepMemory(db)
    mem.add("default agent list sample", source={"agent": "bot-a", "origin_type": "explicit"})
    mem.close()

    result = CliRunner().invoke(app, ["agent", "list"])

    assert result.exit_code == 0
    assert "bot-a" in result.output


def test_search_cli_can_disable_fallback_bucket(tmp_path):
    db = tmp_path / "memory.db"
    mem = DeepMemory(db)
    mem.add(
        "cli bucket query high",
        source={"agent": "human", "origin_type": "explicit"},
        importance=1.0,
        confidence=1.0,
    )
    mem.add(
        "cli bucket query external",
        source={"agent": "web", "trust_level": "external", "origin_type": "imported"},
        importance=1.0,
        confidence=1.0,
    )
    mem.close()

    result = CliRunner().invoke(app, ["search", str(db), "cli bucket query", "--limit", "2", "--no-fallback"])

    assert result.exit_code == 0
    assert "cli bucket query high" in result.output
    assert "cli bucket query external" not in result.output


def test_bucket_retrieval_prefers_high_trust_pool_and_fallback_is_optional(tmp_path):
    mem = DeepMemory(tmp_path / "memory.db")
    mem.add(
        "bucket retrieval shared query high one",
        source={"agent": "human", "origin_type": "explicit"},
        importance=1.0,
        confidence=1.0,
    )
    mem.add(
        "bucket retrieval shared query high two",
        source={"agent": "human", "origin_type": "explicit"},
        importance=1.0,
        confidence=1.0,
    )
    external = mem.add(
        "bucket retrieval shared query external",
        source={"agent": "web", "trust_level": "external", "origin_type": "imported"},
        importance=1.0,
        confidence=1.0,
    )

    filled = mem.search("bucket retrieval shared query", limit=2)
    with_fallback = mem.search("bucket retrieval shared query", limit=3)
    no_fallback = mem.search("bucket retrieval shared query", limit=3, allow_fallback=False)

    assert all(result.record.source_info.trust_factor >= 0.7 for result in filled)
    assert external.id not in [result.record.id for result in filled]
    assert external.id in [result.record.id for result in with_fallback]
    assert external.id not in [result.record.id for result in no_fallback]
