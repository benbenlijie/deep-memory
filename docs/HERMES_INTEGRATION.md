# Hermes integration MVP

如果你退后一步看，Hermes 集成的第一层问题不是“让模型自动记住一切”，而是把已经判定为 durable 的 session facts 写入一个可检查、可搜索、可治理的本地 memory store。

这个 MVP 选择一个保守边界：Hermes 或外部调用方负责抽取事实，`deep-memory` 负责接收显式 facts、持久化、检索和审计。这样避免把不可靠的自动抽取伪装成已经解决的问题。

## Fact JSONL contract

在任意 Hermes session JSONL 行里加入 `facts` 数组：

```json
{"session_id":"s_demo","facts":[{"content":"用户偏好：中文为主，技术术语用英文","kind":"semantic","importance":0.9,"confidence":0.8}]}
```

字段：

- `content`：必填，写入 deep-memory 的事实文本。
- `kind`：可选，`working | episodic | semantic | procedural`，默认 `semantic`。
- `importance`：可选，0-1，默认 `0.7`。
- `confidence`：可选，0-1，默认 `0.8`。
- `source`：可选；未提供时使用 `hermes:<session_id>`。

## Python adapter

```python
from deep_memory.adapters.hermes import write_hermes_session_facts

records = write_hermes_session_facts("agent.db", "hermes-session.jsonl")
print(f"imported {len(records)} facts")
```

## CLI demo

```bash
cat > /tmp/hermes-session.jsonl <<'JSONL'
{"session_id":"s_demo","facts":[{"content":"用户偏好：中文为主，技术术语用英文","kind":"semantic","importance":0.9}]}
{"session_id":"s_demo","facts":[{"content":"成功流程应该沉淀为 skill","kind":"procedural","confidence":0.8}]}
JSONL

uv run deep-memory hermes-import /tmp/hermes-memory.db /tmp/hermes-session.jsonl
uv run deep-memory search /tmp/hermes-memory.db "用户偏好"
uv run deep-memory stats /tmp/hermes-memory.db
```

Expected shape:

```text
imported 2 Hermes facts into /tmp/hermes-memory.db
┏━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┓
┃ score  ┃ kind     ┃ content                              ┃ source         ┃
┡━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━┩
│ ...    │ semantic │ 用户偏好：中文为主，技术术语用英文       │ hermes:s_demo  │
└────────┴──────────┴──────────────────────────────────────┴────────────────┘
{
  "working": 0,
  "episodic": 0,
  "semantic": 1,
  "procedural": 1,
  "total": 2
}
```

## Where this fits in Hermes

A minimal Hermes plugin can call this adapter after a session turn, compression pass, or explicit `/memory` action:

```python
from deep_memory.adapters.hermes import write_hermes_session_facts

# session_jsonl is a Hermes-exported or plugin-produced JSONL stream containing explicit facts.
write_hermes_session_facts("~/.hermes/deep-memory.db", session_jsonl)
```

真正有趣的问题是下一层：哪些事实值得保存、什么时候自动保存、什么时候必须让用户确认，以及如何把 procedural memory 进一步升级成 Hermes skill。这个 MVP 先给出可运行的 writing path，后续再迭代 extraction 和 governance。
