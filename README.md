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

### Run the 2-minute examples

```bash
uv run python examples/quickstart.py
uv run python examples/memory_vs_nomemory.py
```

`examples/quickstart.py` shows the smallest local SQLite memory flow: add records,
inspect stats, and recall a style preference. `examples/memory_vs_nomemory.py`
prints the same toy agent question with and without persistent memory so the
behavioral difference is visible immediately.

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

### Import explicit Hermes session facts

Hermes integration starts with a conservative contract: Hermes or an adapter emits explicit durable `facts`, and `deep-memory` persists them as searchable records.

```bash
cat > /tmp/hermes-session.jsonl <<'JSONL'
{"session_id":"s_demo","facts":[{"content":"用户偏好：中文为主，技术术语用英文","kind":"semantic","importance":0.9}]}
{"session_id":"s_demo","facts":[{"content":"成功流程应该沉淀为 skill","kind":"procedural","confidence":0.8}]}
JSONL

uv run deep-memory hermes-import /tmp/hermes-memory.db /tmp/hermes-session.jsonl
uv run deep-memory search /tmp/hermes-memory.db "用户偏好"
uv run deep-memory stats /tmp/hermes-memory.db
```

See `docs/HERMES_INTEGRATION.md` for the adapter contract, Python API, and end-to-end demo.

### Use the MCP server

`deep-memory` exposes a stdio MCP server with three tools: `add`, `search`, and `stats`.
Install the optional MCP dependency before connecting it to an agent:

```bash
uv sync --extra mcp --extra dev
```

Hermes Agent example (`~/.hermes/config.yaml` or the active profile config):

```yaml
mcp_servers:
  deep_memory:
    command: "uv"
    args: ["--directory", "/absolute/path/to/deep-memory", "run", "deep-memory-mcp"]
    timeout: 30
```

Claude Code example:

```bash
claude mcp add deep-memory -- uv --directory /absolute/path/to/deep-memory run deep-memory-mcp
```

Manual verification without an MCP client:

```bash
uv run python - <<'PY'
from deep_memory.mcp_server import add_memory, search_memory, memory_stats

DB = "/tmp/deep-memory-mcp-smoke.db"
print(add_memory("用户偏好：中文为主，技术术语用英文", db_path=DB, kind="semantic"))
print(search_memory("用户偏好", db_path=DB, limit=1))
print(memory_stats(db_path=DB))
PY
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
- [x] Hermes adapter MVP: explicit session facts JSONL → `deep-memory` records
- [x] MCP server adapter (stdio, optional `mcp` extra)
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

## Memory benchmark

The repository includes a first retrieval-value benchmark at `benchmarks/fixtures/memory_benchmark_v0.json` and `benchmarks/memory_benchmark.py`. It compares a no-memory baseline against a fresh `DeepMemory` database on 20 bilingual tasks where the answer depends on remembered user/project facts.

```bash
uv run python benchmarks/memory_benchmark.py
uv run python benchmarks/memory_benchmark.py --json
```

See `docs/MEMORY_BENCHMARK.md` for the metric, fixture schema, and reproduction notes.

Read `CONTRIBUTING.md` before opening a PR. For contribution lanes, good-first-issue ideas, label conventions, and the path for new backends/adapters, see `docs/COMMUNITY.md`.

## License

MIT
