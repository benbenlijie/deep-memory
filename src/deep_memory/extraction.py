from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Literal

from .core import DeepMemory, MemoryRecord

MessageRole = Literal["system", "user", "assistant", "tool"]


class MemoryLayer(StrEnum):
    """Extraction-layer names mapped onto the current storage kinds.

    L2 semantic records capture durable facts and preferences.
    L3 episodic records capture time-bound events and decisions.
    L4 procedural records capture reusable workflows and skills.
    """

    SEMANTIC = "semantic"
    EPISODIC = "episodic"
    PROCEDURAL = "procedural"


@dataclass(frozen=True)
class AgentMessage:
    role: MessageRole
    content: str
    created_at: str | None = None
    message_id: str | None = None
    name: str | None = None


@dataclass(frozen=True)
class ConversationExtractionInput:
    conversation_id: str
    messages: list[AgentMessage]
    agent_id: str | None = None
    user_id: str | None = None
    locale: str | None = None
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ExtractedMemory:
    layer: MemoryLayer
    content: str
    source_message_ids: list[str] = field(default_factory=list)
    importance: float = 0.5
    confidence: float = 0.8
    rationale: str | None = None


@dataclass(frozen=True)
class ConversationExtractionOutput:
    conversation_id: str
    memories: list[ExtractedMemory]
    extractor_version: str
    skipped_messages: list[str] = field(default_factory=list)


class MemoryExtractor:
    """Small deterministic baseline extractor for the public API contract.

    Production extraction can later be LLM/model-backed; this implementation is
    intentionally transparent so the contract has executable tests.
    """

    version = "rule-based-v0"

    def extract(self, extraction_input: ConversationExtractionInput) -> ConversationExtractionOutput:
        memories: list[ExtractedMemory] = []
        skipped: list[str] = []
        seen: set[tuple[MemoryLayer, str]] = set()

        for index, message in enumerate(extraction_input.messages):
            content = message.content.strip()
            message_ref = message.message_id or f"#{index}"
            if not content:
                skipped.append(message_ref)
                continue

            for memory in _extract_from_message(content, message_ref):
                key = (memory.layer, memory.content)
                if key not in seen:
                    memories.append(memory)
                    seen.add(key)

        return ConversationExtractionOutput(
            conversation_id=extraction_input.conversation_id,
            memories=memories,
            extractor_version=self.version,
            skipped_messages=skipped,
        )


def persist_extracted_memories(
    store: DeepMemory,
    memories: list[ExtractedMemory],
    *,
    conversation_id: str,
    extractor_version: str,
    event_time: str | None = None,
) -> list[MemoryRecord]:
    """Store extracted L2/L3/L4 records in the current DeepMemory backend."""

    source = f"conversation:{conversation_id}#{extractor_version}"
    return [
        store.add(
            memory.content,
            kind=memory.layer.value,
            importance=memory.importance,
            confidence=memory.confidence,
            source=source,
            event_time=event_time,
        )
        for memory in memories
    ]


def extract_and_persist(
    store: DeepMemory,
    extraction_input: ConversationExtractionInput,
    *,
    extractor: MemoryExtractor | None = None,
) -> tuple[ConversationExtractionOutput, list[MemoryRecord]]:
    extractor = extractor or MemoryExtractor()
    output = extractor.extract(extraction_input)
    records = persist_extracted_memories(
        store,
        output.memories,
        conversation_id=output.conversation_id,
        extractor_version=output.extractor_version,
        event_time=_event_time_from_extraction_input(extraction_input),
    )
    return output, records


def _event_time_from_extraction_input(extraction_input: ConversationExtractionInput) -> str | None:
    for key in ("timestamp", "created_at", "session_timestamp"):
        value = extraction_input.metadata.get(key)
        if value:
            return value
    message_times = [message.created_at for message in extraction_input.messages if message.created_at]
    return min(message_times) if message_times else None


def _extract_from_message(content: str, message_ref: str) -> list[ExtractedMemory]:
    lowered = content.lower()
    memories: list[ExtractedMemory] = []

    if _looks_semantic(content, lowered):
        memories.append(
            ExtractedMemory(
                layer=MemoryLayer.SEMANTIC,
                content=content,
                source_message_ids=[message_ref],
                importance=0.85 if "偏好" in content or "preference" in lowered else 0.7,
                confidence=0.8,
                rationale="durable fact or preference",
            )
        )

    if _looks_procedural(content, lowered):
        memories.append(
            ExtractedMemory(
                layer=MemoryLayer.PROCEDURAL,
                content=content,
                source_message_ids=[message_ref],
                importance=0.75,
                confidence=0.75,
                rationale="reusable workflow or instruction",
            )
        )

    if _looks_episodic(content, lowered) or not memories:
        memories.append(
            ExtractedMemory(
                layer=MemoryLayer.EPISODIC,
                content=content,
                source_message_ids=[message_ref],
                importance=0.55,
                confidence=0.7,
                rationale="conversation event, decision, or fallback episode",
            )
        )

    return memories


def _looks_semantic(content: str, lowered: str) -> bool:
    semantic_markers = (
        "用户偏好",
        "偏好：",
        "事实：",
        "约定：",
        "架构决策",
        "preference",
        "prefers",
        "fact:",
        "convention:",
        "decision:",
    )
    return any(marker in content or marker in lowered for marker in semantic_markers)


def _looks_episodic(content: str, lowered: str) -> bool:
    episodic_markers = (
        "讨论",
        "完成",
        "决定",
        "今天",
        "昨天",
        "202",
        "discussed",
        "completed",
        "decided",
        "meeting",
        "session",
    )
    return any(marker in content or marker in lowered for marker in episodic_markers)


def _looks_procedural(content: str, lowered: str) -> bool:
    procedural_markers = (
        "流程",
        "步骤",
        "方法",
        "沉淀为 skill",
        "reusable",
        "workflow",
        "procedure",
        "steps",
        "skill",
    )
    return any(marker in content or marker in lowered for marker in procedural_markers)
