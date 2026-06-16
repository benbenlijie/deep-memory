"""deep-memory: persistent memory for AI agents."""

from .core import ConflictResolution, DeepMemory, MemoryRecord, SearchResult
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

__all__ = [
    "AgentMessage",
    "ConversationExtractionInput",
    "ConversationExtractionOutput",
    "DeepMemory",
    "ConflictResolution",
    "ExtractedMemory",
    "MemoryExtractor",
    "MemoryLayer",
    "MemoryRecord",
    "SearchResult",
    "extract_and_persist",
    "persist_extracted_memories",
]
