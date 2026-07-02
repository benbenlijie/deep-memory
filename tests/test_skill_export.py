import json

from typer.testing import CliRunner

from deep_memory import DeepMemory
from deep_memory.cli import app
from deep_memory.skill_export import procedural_memory_to_skill_markdown


runner = CliRunner()


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
    assert "state: `candidate`" in candidate.markdown
    assert "install_boundary: `review_required`" in candidate.markdown
    assert "Human review checklist" in candidate.markdown
    assert "Two previously blocked cards" in candidate.markdown
    assert "Kanban workers can hit protocol violations" in candidate.markdown
    assert "Do not include credentials, tokens, raw PII, or stale task IDs" in candidate.markdown
    assert "## Playbook" in candidate.markdown


def test_cli_export_skill_writes_candidate_file_for_procedural_memory(tmp_path):
    db = tmp_path / "memory.db"
    output = tmp_path / "skill-candidates" / "kanban-recovery" / "SKILL.md"
    mem = DeepMemory(db)
    record = mem.add(
        "Workflow: recover Kanban protocol violations by reading task history and verifying artifacts.",
        kind="procedural",
        importance=0.91,
        confidence=0.87,
        source="test",
    )
    mem.close()

    result = runner.invoke(
        app,
        [
            "export-skill",
            str(db),
            record.id,
            "--output",
            str(output),
            "--name",
            "kanban-protocol-recovery",
            "--evidence",
            "Recovered two blocked cards with tests.",
            "--recurrence-hint",
            "Use when Kanban worker exits are ambiguous.",
        ],
    )

    assert result.exit_code == 0, result.output
    assert output.exists()
    candidate = output.read_text()
    payload = json.loads(result.output)
    assert payload["candidate_path"] == str(output)
    assert payload["source_memory_id"] == record.id
    assert payload["auto_install"] is False
    assert payload["auto_install_label"] == "Auto-install: no"
    assert "name: kanban-protocol-recovery" in candidate
    assert f"memory_id: `{record.id}`" in candidate
    assert "Recovered two blocked cards" in candidate
    assert "Auto-install: no" in candidate


def test_cli_export_skill_rejects_non_procedural_memory_without_writing_candidate(tmp_path):
    for kind in ("semantic", "episodic", "working"):
        db = tmp_path / f"{kind}.db"
        output = tmp_path / kind / "SKILL.md"
        mem = DeepMemory(db)
        record = mem.add(f"This {kind} memory is not a procedure.", kind=kind)
        mem.close()

        result = runner.invoke(
            app,
            [
                "export-skill",
                str(db),
                record.id,
                "--output",
                str(output),
                "--name",
                f"{kind}-candidate",
            ],
        )

        assert result.exit_code != 0
        assert "only procedural memories can be exported" in result.output
        assert not output.exists()


def test_cli_export_skill_rejects_active_hermes_skill_directory_by_default(tmp_path, monkeypatch):
    db = tmp_path / "memory.db"
    hermes_home = tmp_path / ".hermes"
    active_skill = hermes_home / "profiles" / "demis" / "skills" / "unsafe" / "SKILL.md"
    monkeypatch.setenv("HOME", str(tmp_path))
    mem = DeepMemory(db)
    record = mem.add("Workflow: repeatable but must be reviewed first.", kind="procedural")
    mem.close()

    result = runner.invoke(
        app,
        [
            "export-skill",
            str(db),
            record.id,
            "--output",
            str(active_skill),
            "--name",
            "unsafe-direct-install",
        ],
    )

    assert result.exit_code != 0
    assert "review directory" in result.output
    assert not active_skill.exists()
