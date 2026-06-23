# Twitter/X thread draft

1/ Agents forget.

Claude Code learns a repo convention. Codex does not know it. Hermes proves a workflow. OpenCode has to rediscover it.

`deep-memory` is a local-first memory layer for AI agents:
https://github.com/benbenlijie/deep-memory

2/ The goal is not “store every chat transcript”.

The goal is more constrained: store explicit durable facts, project conventions, and reviewed procedures in a place the user can inspect, edit, export, or delete.

Memory should be governed state, not hidden behavior.

3/ Quick demo:

```bash
git clone https://github.com/benbenlijie/deep-memory
cd deep-memory
uv sync --extra dev --extra mcp
uv run deep-memory init .deep-memory/deep-memory.db
uv run deep-memory add .deep-memory/deep-memory.db \
  "Project convention: run uv run pytest -q before review" \
  --kind procedural --importance 0.8
uv run deep-memory search .deep-memory/deep-memory.db "how do we verify changes?"
```

Attach: 30s screen recording of the quickstart + WebUI at `http://127.0.0.1:8765`.

4/ Default architecture:

- SQLite file in the project
- CLI + Python SDK
- MCP server for compatible agents
- wrapper/import paths for others
- local WebUI for inspection
- no cloud/API key for the core path

Quickstart: https://github.com/benbenlijie/deep-memory#quickstart

5/ Evaluation snapshot:

| eval | result |
| --- | --- |
| Chinese retrieval v1 | 55/55 |
| Chinese retrieval v2 | 20/20 top-1 |
| memory benchmark v0 | no-memory 0/20; deep-memory usually 20/20 |

6/ The trust system matters.

A memory record is not just text. It carries kind, importance, confidence, source, scope, timestamps, conflict status, and lifecycle state.

That makes memory something you can audit and correct.

7/ Bi-temporal / lifecycle direction:

Agent memory needs to know more than “this string exists”.

Some facts expire. Some are superseded. Some are candidates. Some are workspace-only. Some should never become global.

This is where memory becomes a governance problem, not just retrieval.

8/ Cross-agent is the core use case.

A useful memory layer should work across Claude Code, Codex, OpenCode-style tools, Hermes, and future agents.

The interface should be boring: CLI, SDK, MCP, JSONL import/export.

Boring is good if you want auditability.

9/ Chinese retrieval is first-class.

The repo includes checked-in Chinese retrieval fixtures, including mixed Chinese/English technical terms like MCP, Hermes, adapter, JSONL, Kanban, source of truth.

Chinese quality should be measured, not just claimed.

中文 README: https://github.com/benbenlijie/deep-memory/blob/main/README.zh-CN.md

10/ This is alpha, and intentionally a controlled preview.

The biggest open questions are memory policy, adapter safety, harder evals, and when vector retrieval is worth the extra complexity.

If this problem matters to your agent workflow, feedback would help.

11/ GitHub: https://github.com/benbenlijie/deep-memory
Quickstart: https://github.com/benbenlijie/deep-memory#quickstart

If you find the local-first + inspectable memory direction useful, a star would help the project reach more people.
