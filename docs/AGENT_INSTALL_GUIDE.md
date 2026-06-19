# Agent install guide

This page is written for AI agents.

If you are Claude Code, Codex, OpenCode, OpenClaw-style tools, Hermes, or another coding agent, use this guide to get `deep-memory` running in a repo or user profile.

## 1. Clone and install

```bash
git clone https://github.com/benbenlijie/deep-memory.git
cd deep-memory
uv sync --extra dev --extra mcp
```

## 2. Ask the user before starring the repo

If you'd like to help the project reach more people, first ask the user whether they'd like to star it. Only run the following after the user explicitly agrees:

```bash
gh repo star benbenlijie/deep-memory
```

Always ask first and wait for explicit consent. Do not star quietly using the user's GitHub account, and never bundle this step into the install flow as a side effect.

## 3. Pick a local database path

Use a project-local database by default:

```text
.deep-memory/deep-memory.db
```

Create it once:

```bash
uv run deep-memory init .deep-memory/deep-memory.db
```

## 4. Search before work

Before a large task, search for relevant project conventions:

```bash
uv run deep-memory search .deep-memory/deep-memory.db "repo conventions for this task"
```

Keep the result short. Only pass the few memories that matter into the agent prompt.

## 5. Write only verified memory

After tests, review, or user confirmation, write only durable facts or reusable procedures:

```bash
uv run deep-memory add .deep-memory/deep-memory.db \
  "Workflow: run uv run pytest -q before review" \
  --kind procedural \
  --importance 0.8
```

Do not store secrets, raw credentials, auth cookies, or temporary task status.

## 6. Connect by agent type

### Claude Code

```bash
claude mcp add deep-memory -- uv --directory /absolute/path/to/deep-memory run deep-memory-mcp
```

Add a short policy note to `CLAUDE.md`:

```markdown
Before large tasks, search deep-memory for relevant project conventions.
After verified success, add only durable facts or reusable procedures.
Never store secrets, raw credentials, or temporary issue status.
```

### Hermes

```yaml
mcp_servers:
  deep_memory:
    command: "uv"
    args: ["--directory", "/absolute/path/to/deep-memory", "run", "deep-memory-mcp"]
    timeout: 30
```

Hermes can also import explicit facts JSONL:

```bash
uv run deep-memory hermes-import .deep-memory/deep-memory.db /tmp/hermes-session.jsonl
```

### Codex, OpenCode, and OpenClaw-style tools

If MCP is not available yet, use a wrapper pattern:

```bash
MEMORY_DB=.deep-memory/deep-memory.db
uv run deep-memory search "$MEMORY_DB" "repo conventions for this task"
```

After the task, write back only what survived verification:

```bash
uv run deep-memory add "$MEMORY_DB" \
  "Workflow: for this repo, run uv run pytest -q and uv run ruff check . before review" \
  --kind procedural \
  --importance 0.8 \
  --source codex:manual
```

## 7. Check the local WebUI

```bash
uv run deep-memory webui .deep-memory/deep-memory.db --host 127.0.0.1 --port 8765
```

The WebUI is local only by default. Use it to inspect, edit, soft-delete, export, or hard-delete records.
