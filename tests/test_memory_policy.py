from __future__ import annotations

import pytest

from deep_memory import DeepMemory
from deep_memory.privacy import MemoryPolicyDecision, evaluate_memory_write_policy


def test_memory_policy_denies_secrets_before_storage(tmp_path):
    mem = DeepMemory(tmp_path / "memory.db")

    with pytest.raises(ValueError, match="secrets/credentials"):
        mem.add("API token: ghp_12...3456")

    assert mem.stats()["total"] == 0


def test_memory_policy_denies_raw_transcript_shape(tmp_path):
    mem = DeepMemory(tmp_path / "memory.db")
    raw_transcript = """
    user: can you debug this?
    assistant: yes, here is the trace
    tool: pytest failed with temporary output
    """

    with pytest.raises(ValueError, match="raw transcript"):
        mem.add(raw_transcript)

    assert mem.stats()["total"] == 0


def test_memory_policy_denies_temporary_task_status(tmp_path):
    mem = DeepMemory(tmp_path / "memory.db")

    with pytest.raises(ValueError, match="temporary task status"):
        mem.add("PR #123 fixed in commit abcdef1234567890; phase 2 done", kind="episodic")

    assert mem.stats()["total"] == 0


def test_memory_policy_third_party_private_data_requires_confirmation():
    decision = evaluate_memory_write_policy("Alice's private phone number is +1 415 555 2671")

    assert decision == MemoryPolicyDecision.REQUIRES_CONFIRMATION


def test_memory_policy_allows_verified_procedural_fact(tmp_path):
    mem = DeepMemory(tmp_path / "memory.db")

    record = mem.add(
        "Workflow: for this repo, run uv run pytest -q and uv run ruff check . before review",
        kind="procedural",
        source="test:verified",
        confidence=0.9,
    )

    assert record.kind == "procedural"
    assert mem.stats()["procedural"] == 1
