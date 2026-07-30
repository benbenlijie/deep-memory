# MCP Interoperability Smoke Test

## Goal

`deep-memory-mcp` is the shared cross-agent access layer for local persistent memory. The stable surface is intentionally small:

- `add(content, db_path, kind, importance, confidence, source, expires_at)`
- `search(query, db_path, limit, kind)`
- `stats(db_path)`

The scoped memory parameters are part of the verified MCP contract for `add` and `search`: `scope`, `scope_id`, `include_global`, and `cross_scope`.

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

## Reproducible stdio client transcript

The current P1 protocol smoke uses a real MCP stdio client, not direct Python helper calls. Full transcript: [`docs/evidence/p1-cross-agent-smoke-2026-07-23.md`](evidence/p1-cross-agent-smoke-2026-07-23.md).

It verifies that `list_tools` discovers the server tools, then calls `add`, `search`, and `stats` against one local SQLite database with scoped parameters.

Command:

```bash
uv run pytest tests/test_mcp_client_smoke.py -q
```

Observed output on 2026-07-23:

```text
.                                                                        [100%]
```

Pass criteria:

- `list_tools` exposes at least `add`, `search`, and `stats`.
- `add` returns a record with the requested content, kind, scope, scope_id, and source.
- `search` with `scope=project`, `scope_id=mcp-client-smoke`, and `include_global=false` returns the same record from the same local database.
- `stats` reports `semantic: 1` and `total: 1` for that database.

## Automated coverage

The focused regression test is:

```bash
uv run pytest tests/test_mcp_server.py -q
```

It covers:

- add/search/stats sharing a local DB;
- kind-filtered search;
- conflict lifecycle tool helpers.
