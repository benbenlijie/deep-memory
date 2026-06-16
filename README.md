# deep-memory

> 给 AI Agent 装上不会轻易遗忘的大脑：跨会话记忆、自动遗忘、矛盾消解、中文优先，让 Agent 从“金鱼”变成长期伙伴。

`deep-memory` is an open-source persistent memory layer for AI agents. The design target is simple: **6-line integration, local-first storage, Chinese-first retrieval quality, and an architecture that can grow from facts into skills.**

This repository starts as a small, working core rather than a slide deck. The long-term ambition is a 100k-star developer infrastructure project. The first milestone is to prove the bottleneck: agents need durable memory that is inspectable, editable, and reliable across sessions.

## Why now

If you step back, the interesting problem is not “can the model remember a longer prompt?” It is: **what should be stored, when should it be recalled, when should it be forgotten, and how do we know the memory is still true?**

Current gaps we target:

- Chinese-first semantic memory: segmentation, entities, time expressions, and retrieval behavior differ from English.
- Beyond vector search: memory needs lifecycle, confidence, source traces, and conflict handling.
- Memory × skills: successful procedures should become reusable playbooks, not just text snippets.
- Cross-agent memory: Hermes, Claude Code, Codex, OpenCode/OpenClaw-style agents should share durable context through a common layer.

## Four-layer memory architecture

```text
L1 Working Memory     recent turns, hot context, exact short-term state
L2 Episodic Memory    timeline of sessions/events: what happened, when
L3 Semantic Memory    durable facts, preferences, project knowledge
L4 Procedural Memory  reusable skills/playbooks extracted from successful work

Memory Engine         forgetting, conflict detection, importance scoring, compression
```

## Install

```bash
pip install deep-memory
```

For local development:

```bash
git clone https://github.com/benbenlijie/deep-memory.git
cd deep-memory
uv sync --extra dev
uv run pytest
```

## 6-line usage

```python
from deep_memory import DeepMemory

mem = DeepMemory("agent.db")
mem.add("user prefers concise Chinese answers", kind="semantic", importance=0.9)
mem.add("2026-06-16: discussed deep-memory GitHub launch", kind="episodic")

print(mem.search("用户喜欢什么风格？", limit=3))
```

## CLI

```bash
deep-memory init agent.db
deep-memory add agent.db "用户偏好：中文为主，技术术语用英文" --kind semantic --importance 0.9
deep-memory search agent.db "用户偏好"
deep-memory stats agent.db
```

## MVP features

- [x] SQLite local-first persistence
- [x] L2/L3/L4 memory records with source, confidence, importance and timestamps
- [x] FTS5 lexical retrieval, good enough for the first local MVP
- [x] Decay score inspired by forgetting curves
- [x] Conflict candidate detection through simple key/entity overlap
- [x] Python API + CLI + tests
- [ ] Chinese tokenization/embedding retrieval
- [ ] Web memory inspector/editor
- [ ] Hermes plugin
- [ ] MCP server
- [ ] Memory → Skill generation

## Roadmap to 100k stars

See [`docs/ROADMAP.md`](docs/ROADMAP.md).

## Design principle

The key bottleneck is not storage. It is **memory governance**: deciding what is worth remembering, how it should be represented, how it decays, how contradictions are resolved, and how users can inspect/control it.

## License

MIT
