from __future__ import annotations

from deep_memory import DeepMemory
from deep_memory.extraction import (
    AgentMessage,
    ConversationExtractionInput,
    ExtractedMemory,
    MemoryExtractor,
    MemoryLayer,
    persist_extracted_memories,
)


def test_rule_based_extractor_returns_semantic_and_episodic_memories():
    extraction_input = ConversationExtractionInput(
        conversation_id="conv-001",
        agent_id="agent-alpha",
        messages=[
            AgentMessage(
                role="user",
                content="用户偏好：中文为主，技术术语用英文",
                created_at="2026-06-16T10:00:00+00:00",
            ),
            AgentMessage(
                role="assistant",
                content="我们讨论了 deep-memory 的 Phase 1 extraction contract。",
                created_at="2026-06-16T10:01:00+00:00",
            ),
        ],
    )

    output = MemoryExtractor().extract(extraction_input)

    assert output.conversation_id == "conv-001"
    assert {memory.layer for memory in output.memories} >= {
        MemoryLayer.SEMANTIC,
        MemoryLayer.EPISODIC,
    }
    assert any("中文为主" in memory.content for memory in output.memories)
    assert any("Phase 1 extraction contract" in memory.content for memory in output.memories)


def test_persist_extracted_memories_stores_semantic_and_episodic_records(tmp_path):
    mem = DeepMemory(tmp_path / "memory.db")
    extracted = [
        ExtractedMemory(
            layer=MemoryLayer.SEMANTIC,
            content="用户偏好：中文为主，技术术语用英文",
            source_message_ids=["m1"],
            importance=0.9,
            confidence=0.85,
        ),
        ExtractedMemory(
            layer=MemoryLayer.EPISODIC,
            content="2026-06-16 讨论了 extraction contract。",
            source_message_ids=["m2"],
            importance=0.6,
            confidence=0.75,
        ),
    ]

    stored = persist_extracted_memories(
        mem,
        extracted,
        conversation_id="conv-001",
        extractor_version="rule-based-v0",
    )

    assert [record.kind for record in stored] == ["semantic", "episodic"]
    assert mem.stats()["semantic"] == 1
    assert mem.stats()["episodic"] == 1
    assert mem.search("中文为主", kind="semantic")
    assert mem.search("extraction contract", kind="episodic")
    assert all(record.source == "conversation:conv-001#rule-based-v0" for record in stored)
