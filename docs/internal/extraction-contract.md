# Extraction contract

This document defines the first executable contract for turning raw agent conversations into durable `deep-memory` records.

真正有趣的问题不是“把整段聊天塞进数据库”，而是把会话流压缩成可以被检索、审计、遗忘和升级的 memory representation。Phase 1 keeps the interface deliberately small so extraction quality can improve without breaking storage users.

## Scope

Input: ordered agent conversation messages.

Output: candidate L2/L3/L4 memory records with provenance and confidence.

Storage: the current SQLite-backed `DeepMemory` store persists these layers as existing `MemoryKind` values:

| Contract layer | Meaning | Stored kind |
| --- | --- | --- |
| L2 semantic | Durable facts, user preferences, stable project conventions, decisions | `semantic` |
| L3 episodic | Time-bound events, sessions, meetings, completed work, decision episodes | `episodic` |
| L4 procedural | Reusable workflows, skills, playbooks, repeatable methods | `procedural` |

L1 working memory remains prompt/session-local and is not part of this persistence contract.

## Python interface

The public interface lives in `deep_memory.extraction`:

```python
from deep_memory import DeepMemory
from deep_memory.extraction import (
    AgentMessage,
    ConversationExtractionInput,
    MemoryExtractor,
    extract_and_persist,
)

store = DeepMemory("memory.db")
extraction_input = ConversationExtractionInput(
    conversation_id="conv-001",
    agent_id="hermes-agent",
    locale="zh-CN",
    messages=[
        AgentMessage(
            role="user",
            message_id="m1",
            content="用户偏好：中文为主，技术术语用英文",
            created_at="2026-06-16T10:00:00+00:00",
        ),
        AgentMessage(
            role="assistant",
            message_id="m2",
            content="我们讨论了 deep-memory 的 Phase 1 extraction contract。",
            created_at="2026-06-16T10:01:00+00:00",
        ),
    ],
)

output, records = extract_and_persist(store, extraction_input, extractor=MemoryExtractor())
```

### Input schema

`ConversationExtractionInput`

```json
{
  "conversation_id": "conv-001",
  "agent_id": "hermes-agent",
  "user_id": "user-123",
  "locale": "zh-CN",
  "metadata": {"source": "cli"},
  "messages": [
    {
      "message_id": "m1",
      "role": "user",
      "content": "用户偏好：中文为主，技术术语用英文",
      "created_at": "2026-06-16T10:00:00+00:00",
      "name": null
    }
  ]
}
```

Required fields:

- `conversation_id`: stable id for the raw conversation/session.
- `messages`: ordered list of messages.
- each message requires `role` and `content`.

Optional fields:

- `message_id`: used for provenance. If missing, extractor uses the message index.
- `created_at`: ISO-8601 timestamp from the source system.
- `agent_id`, `user_id`, `locale`, `metadata`: context for future model-backed extraction and policy decisions.

### Output schema

`ConversationExtractionOutput`

```json
{
  "conversation_id": "conv-001",
  "extractor_version": "rule-based-v0",
  "skipped_messages": [],
  "memories": [
    {
      "layer": "semantic",
      "content": "用户偏好：中文为主，技术术语用英文",
      "source_message_ids": ["m1"],
      "importance": 0.85,
      "confidence": 0.8,
      "rationale": "durable fact or preference"
    },
    {
      "layer": "episodic",
      "content": "我们讨论了 deep-memory 的 Phase 1 extraction contract。",
      "source_message_ids": ["m2"],
      "importance": 0.55,
      "confidence": 0.7,
      "rationale": "conversation event, decision, or fallback episode"
    }
  ]
}
```

Persistence uses source provenance in this format:

```text
conversation:{conversation_id}#{extractor_version}
```

Example:

```text
conversation:conv-001#rule-based-v0
```

## English example

Raw conversation:

```text
User: Preference: answer primarily in Chinese, but keep technical terms in English.
Assistant: We discussed the Phase 1 extraction contract for deep-memory today.
```

Expected candidates:

```json
[
  {
    "layer": "semantic",
    "content": "Preference: answer primarily in Chinese, but keep technical terms in English.",
    "source_message_ids": ["m1"],
    "importance": 0.85,
    "confidence": 0.8
  },
  {
    "layer": "episodic",
    "content": "We discussed the Phase 1 extraction contract for deep-memory today.",
    "source_message_ids": ["m2"],
    "importance": 0.55,
    "confidence": 0.7
  }
]
```

## 中文示例

原始会话：

```text
用户：用户偏好：中文为主，技术术语用英文。
助手：今天我们完成了 deep-memory 的 extraction contract 第一版。
```

期望候选记忆：

```json
[
  {
    "layer": "semantic",
    "content": "用户偏好：中文为主，技术术语用英文。",
    "source_message_ids": ["m1"],
    "importance": 0.85,
    "confidence": 0.8
  },
  {
    "layer": "episodic",
    "content": "今天我们完成了 deep-memory 的 extraction contract 第一版。",
    "source_message_ids": ["m2"],
    "importance": 0.55,
    "confidence": 0.7
  }
]
```

## Contract invariants

1. Extraction is provenance-preserving: every candidate should point back to source message ids when available.
2. Extraction is layer-explicit: callers should not infer L2/L3/L4 from free text after the fact.
3. Storage is append-only in Phase 1: conflict resolution, deduplication, merge/update policy and human review are later phases.
4. Confidence is extractor confidence, not truth. It should be used for review/ranking, not as a factual guarantee.
5. Importance is lifecycle/ranking metadata. It influences decay and recall, but should stay editable by higher-level memory governance.
6. Empty messages are skipped and reported in `skipped_messages`.

## Current baseline and future extension

`MemoryExtractor` is a deterministic rule-based baseline. It is intentionally conservative and inspectable; the API is the important artifact in Phase 1. A later model-backed extractor can implement the same input/output contract and improve recall, compression, deduplication, contradiction detection, and L4 skill synthesis.
