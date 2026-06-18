"""deep-memory: persistent memory for AI agents."""

from . import core as _core
from .extraction import (
    AgentMessage,
    ConversationExtractionInput,
    ConversationExtractionOutput,
    ExtractedMemory,
    MemoryExtractor,
    MemoryLayer,
    extract_and_persist,
    persist_extracted_memories,
)
from .skill_export import SkillCandidate, procedural_memory_to_skill_markdown

ConflictResolution = _core.ConflictResolution
DeepMemory = _core.DeepMemory
InsightCandidate = _core.InsightCandidate
MemoryFeedbackEntry = _core.MemoryFeedbackEntry
MemoryRecord = _core.MemoryRecord
RetrievalLogEntry = _core.RetrievalLogEntry
SearchResult = _core.SearchResult
SourceInfo = _core.SourceInfo
TelemetryReport = _core.TelemetryReport
TrustAuditEntry = _core.TrustAuditEntry
build_idempotency_key = _core.build_idempotency_key
parse_source_info = _core.parse_source_info

__all__ = [
    "AgentMessage",
    "ConversationExtractionInput",
    "ConversationExtractionOutput",
    "DeepMemory",
    "ConflictResolution",
    "ExtractedMemory",
    "MemoryExtractor",
    "MemoryLayer",
    "InsightCandidate",
    "MemoryFeedbackEntry",
    "MemoryRecord",
    "RetrievalLogEntry",
    "SearchResult",
    "SourceInfo",
    "TelemetryReport",
    "TrustAuditEntry",
    "build_idempotency_key",
    "parse_source_info",
    "extract_and_persist",
    "persist_extracted_memories",
]

__all__ += ["SkillCandidate", "procedural_memory_to_skill_markdown"]
