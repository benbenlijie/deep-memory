# MCP Interoperability Smoke Test

## Goal

`deep-memory-mcp` is the shared cross-agent access layer for local persistent memory. The stable surface is intentionally small:

- `add(content, db_path, kind, importance, confidence, source, expires_at)`
- `search(query, db_path, limit, kind)`
- `stats(db_path)`

Conflict lifecycle tools (`resolve_conflict`, `conflicts`) are exposed too, but `add` / `search` / `stats` are the minimum interoperability contract for Hermes, Claude Code, Codex-style wrappers, and other MCP-capable agents.

## Install

```bash
uv sync --extra mcp --extra dev
```

Run the stdio MCP server from this repository:

```bash
uv --directory /absolute/path/to/deep-memory run deep-memory-mcp
```

## Hermes Agent client

Hermes can connect to the server through its native MCP client. Add this to the active Hermes profile config:

```yaml
mcp_servers:
  deep_memory:
    command: "uv"
    args: ["--directory", "/absolute/path/to/deep-memory", "run", "deep-memory-mcp"]
    timeout: 30
```

After restarting Hermes, the tools are discovered with the `mcp_deep_memory_` prefix, for example:

- `mcp_deep_memory_add`
- `mcp_deep_memory_search`
- `mcp_deep_memory_stats`

Recommended usage policy:

1. Search before large tasks with a task-specific query and a bounded `limit`.
2. Add only durable facts or reusable procedures after evidence exists.
3. Use an explicit project-local or profile-local `db_path`; do not default to a hidden global database.
4. Never store secrets, raw credentials, or temporary task status.

Example tool arguments:

```json
{
  "content": "Project convention: run uv run pytest -q before review",
  "db_path": ".deep-memory/deep-memory.db",
  "kind": "procedural",
  "importance": 0.8,
  "confidence": 0.9,
  "source": "hermes:profile:session"
}
```

## Claude Code client

Claude Code can use the same stdio server as a project MCP server:

```bash
claude mcp add deep-memory -- uv --directory /absolute/path/to/deep-memory run deep-memory-mcp
```

Add a short project policy to `CLAUDE.md` rather than storing raw recalled memories there:

```markdown
Before large tasks, search deep-memory for relevant project conventions. After verified success, add only durable facts or reusable procedures with evidence. Never store secrets or temporary issue status.
```

Use a repo-local database when the memory is project-specific:

```text
.deep-memory/deep-memory.db
```

## Codex-style wrapper client

For Codex or another coding agent without a stable MCP configuration path, use a wrapper pattern:

```bash
MEMORY_DB=.deep-memory/deep-memory.db
uv run deep-memory search "$MEMORY_DB" "repo conventions for this task"

codex exec "Use the recalled memory block only if relevant. <task>"
```

After the run, import only explicit verified facts:

```bash
uv run deep-memory hermes-import "$MEMORY_DB" /path/to/explicit-facts.jsonl
```

This keeps memory writes visible, auditable, and separate from raw transcript scraping.

## Reproducible manual transcript

This transcript verifies that the MCP server tool implementations work against one local SQLite database. It calls the same Python functions registered by `deep_memory.mcp_server.create_mcp_server()` for the MCP `add`, `search`, and `stats` tools.

Command:

```bash
DB="/tmp/deep-memory-mcp-phase4-$(date +%s).db"; export DB
uv run python - <<'PY'
import os
from deep_memory.mcp_server import add_memory, search_memory, memory_stats

DB = os.environ["DB"]
print("DB", DB)
print("ADD")
print(add_memory(
    "MCP smoke: Hermes and Claude/Codex clients should use explicit durable writes only",
    db_path=DB,
    kind="procedural",
    importance=0.8,
    confidence=0.9,
    source="phase4:mcp-smoke",
))
print("SEARCH")
print(search_memory("explicit durable writes", db_path=DB, limit=2))
print("STATS")
print(memory_stats(db_path=DB))
PY
```

Observed output on 2026-06-16:

```text
DB /tmp/deep-memory-mcp-phase4-1781630057.db
ADD
{'id': 'f42caeec-a208-4680-a80f-4d555758ef93', 'content': 'MCP smoke: Hermes and Claude/Codex clients should use explicit durable writes only', 'kind': 'procedural', 'importance': 0.8, 'confidence': 0.9, 'source': 'phase4:mcp-smoke', 'created_at': '2026-06-16T17:14:17.856312+00:00', 'updated_at': '2026-06-16T17:14:17.856312+00:00', 'expires_at': None, 'conflict_status': 'active', 'supersedes_id': None, 'superseded_by_id': None}
SEARCH
[{'score': 0.935, 'record': {'id': 'f42caeec-a208-4680-a80f-4d555758ef93', 'content': 'MCP smoke: Hermes and Claude/Codex clients should use explicit durable writes only', 'kind': 'procedural', 'importance': 0.8, 'confidence': 0.9, 'source': 'phase4:mcp-smoke', 'created_at': '2026-06-16T17:14:17.856312+00:00', 'updated_at': '2026-06-16T17:14:17.856312+00:00', 'expires_at': None, 'conflict_status': 'active', 'supersedes_id': None, 'superseded_by_id': None}}]
STATS
{'working': 0, 'episodic': 0, 'semantic': 0, 'procedural': 1, 'total': 1}
```

Pass criteria:

- `add` returns a record with the requested content, kind, confidence, importance, and source.
- `search` returns the same record from the same local database.
- `stats` reports `procedural: 1` and `total: 1` for that database.

## Automated coverage

The focused regression test is:

```bash
uv run pytest tests/test_mcp_server.py -q
```

It covers:

- add/search/stats sharing a local DB;
- kind-filtered search;
- conflict lifecycle tool helpers.
