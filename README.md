# deep-memory

> 给 AI Agent 装上不会轻易遗忘的大脑：跨会话记忆、自动遗忘、矛盾消解、中文优先，让 Agent 从“金鱼”变成长期伙伴。
>
> A local-first persistent memory layer for AI agents: cross-session recall, forgetting-aware ranking, conflict candidates, Chinese-first retrieval, and a path from facts to reusable skills.

[![CI](https://github.com/benbenlijie/deep-memory/actions/workflows/ci.yml/badge.svg)](https://github.com/benbenlijie/deep-memory/actions/workflows/ci.yml)

`deep-memory` is for developers building agents that need durable, inspectable memory instead of stuffing everything into a longer prompt. The MVP is deliberately small: a Python SDK + CLI backed by SQLite/FTS5, designed so you can add memories, recall them across sessions, inspect the database, and evolve toward richer memory governance.

真正有趣的问题不是“模型上下文能不能更长”，而是：

- 什么信息值得被长期保存？
- 什么时候应该 recall，什么时候应该 forget？
- 当记忆互相矛盾时，系统如何发现并让人修正？
- 中文场景下，分词、实体、时间表达和检索质量如何做到可靠？
- 成功的流程如何从 memory 进一步沉淀成 reusable skills？

## Why developers care

Most agents are still “goldfish”: they can reason within one session, but they lose project conventions, user preferences, prior decisions, and successful procedures between runs. `deep-memory` focuses on the missing infrastructure layer:

| Bottleneck | deep-memory direction |
| --- | --- |
| Cross-session context disappears | Local persistent records with source, confidence, importance and timestamps |
| Vector search alone is not enough | Lifecycle, decay, conflict candidates and inspectability first |
| Chinese memory quality is under-served | Chinese-first retrieval behavior and future tokenizer/embedding path |
| Agent learnings stay as chat logs | Procedural memory layer for skills/playbooks |
| Closed SaaS memory is hard to trust | Local-first SQLite baseline that developers can inspect and edit |

## Quickstart

### Install from source today

```bash
git clone https://github.com/benbenlijie/deep-memory.git
cd deep-memory
uv sync --extra dev
uv run pytest
```

### Use the Python API

```python
from deep_memory import DeepMemory

mem = DeepMemory("agent.db")
mem.add("用户偏好：中文为主，技术术语用英文", kind="semantic", importance=0.9)
mem.add("2026-06-16: discussed deep-memory GitHub launch", kind="episodic")

for result in mem.search("用户喜欢什么风格？", limit=3):
    print(result.score, result.record.kind, result.record.content)
```

### Use the CLI

```bash
uv run deep-memory init agent.db
uv run deep-memory add agent.db "用户偏好：中文为主，技术术语用英文" --kind semantic --importance 0.9
uv run deep-memory search agent.db "用户偏好"
uv run deep-memory stats agent.db
```

Expected shape:

```text
initialized agent.db
{
  "working": 0,
  "episodic": 0,
  "semantic": 1,
  "procedural": 0,
  "total": 1
}
```

Note: package publishing is on the roadmap. Until the first PyPI release, use the source install above rather than `pip install deep-memory`.

## 6-line integration

```python
from deep_memory import DeepMemory

mem = DeepMemory("agent.db")
mem.add("user prefers concise Chinese answers", kind="semantic", importance=0.9)
mem.add("2026-06-16: discussed deep-memory GitHub launch", kind="episodic")

print(mem.search("用户喜欢什么风格？", limit=3))
```

## Current MVP features

- [x] SQLite local-first persistence
- [x] L2/L3/L4 memory records with source, confidence, importance and timestamps
- [x] FTS5 lexical retrieval plus Chinese bigram fallback for the first local MVP
- [x] Forgetting-curve-inspired decay score
- [x] Conflict candidate detection through simple key/entity overlap
- [x] Python API + CLI + tests + GitHub Actions CI
- [ ] Chinese tokenizer + embedding retrieval
- [ ] Web memory inspector/editor
- [ ] Hermes plugin
- [ ] MCP server
- [ ] Memory → Skill generation

## Architecture

```text
agent event stream
  -> memory extractor
  -> memory engine
  -> SQLite / vector / graph stores
  -> retrieval planner
  -> agent context injector
```

The first implementation is intentionally boring at the storage layer. The key bottleneck is not distributed storage; it is memory governance: deciding what to remember, how to represent it, how it decays, how contradictions are detected, and how users stay in control.

See `docs/ARCHITECTURE.md` for the system model and `docs/ROADMAP.md` for the 100k-star wedge.

## Project direction

The long-term target is to become the default open-source persistent memory layer for AI agents:

1. Foundation memory: local SDK, CLI, tests, transparent records.
2. Memory governance: Chinese retrieval, importance scoring, forgetting, conflict resolution.
3. Agent ecosystem: Hermes plugin, Claude Code/Codex/OpenCode adapters, MCP server.
4. Memory × skills: successful procedures become reusable playbooks, not just snippets.

## Contributing

This project is early. Good first contributions are especially valuable around:

- Chinese tokenization and retrieval evaluation;
- memory schemas and conflict-resolution examples;
- CLI ergonomics and test coverage;
- Hermes/MCP/agent integrations;
- small reproducible benchmarks comparing agents with and without memory.

Read `CONTRIBUTING.md` before opening a PR.

## License

MIT
