from deep_memory import DeepMemory
from deep_memory.skill_export import procedural_memory_to_skill_markdown


def test_procedural_memory_exports_reviewable_skill_candidate(tmp_path):
    mem = DeepMemory(tmp_path / "memory.db")
    record = mem.add(
        "When syncing Teambition, use the default profile MCP operator and verify counts.",
        kind="procedural",
        importance=0.9,
        confidence=0.85,
        source="test",
    )

    candidate = procedural_memory_to_skill_markdown(record, name="teambition-sync-operator")

    assert candidate.name == "teambition-sync-operator"
    assert "memory_id" in candidate.markdown
    assert "default profile MCP operator" in candidate.markdown
    assert "Verification" in candidate.markdown


def test_successful_workflow_exports_procedural_candidate_with_evidence_and_safety_gate(tmp_path):
    mem = DeepMemory(tmp_path / "memory.db")
    record = mem.add(
        "Workflow: recover Kanban protocol violations by reading task history, "
        "classifying provider versus worker causes, verifying artifacts, and then "
        "blocking for review or completing with structured metadata.",
        kind="procedural",
        importance=0.92,
        confidence=0.88,
        source="conversation:kanban-recovery#rule-based-v0",
    )

    candidate = procedural_memory_to_skill_markdown(
        record,
        name="kanban-protocol-recovery",
        evidence=[
            "Two previously blocked cards were recovered without repeating the failed path.",
            "Targeted tests and full verification commands passed before handoff.",
        ],
        recurrence_hint="Kanban workers can hit protocol violations whenever provider or worker exits are ambiguous.",
    )

    assert candidate.source_memory_id == record.id
    assert "successful workflow" in candidate.trigger_reasons
    assert "high confidence" in candidate.trigger_reasons
    assert "recurrence likely" in candidate.trigger_reasons
    assert "Auto-install: no" in candidate.markdown
    assert "Two previously blocked cards" in candidate.markdown
    assert "Kanban workers can hit protocol violations" in candidate.markdown
    assert "Do not include credentials, tokens, raw PII, or stale task IDs" in candidate.markdown
    assert "## Playbook" in candidate.markdown
