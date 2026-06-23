# deep-memory

[English](README.md) | [简体中文](README.zh-CN.md)

> Machine-local memory for all your agents. Inspect what they remember. Decide what they keep.

A shared, inspectable memory layer for Claude Code, Codex, OpenCode, and Hermes. Store explicit durable facts and procedures in a machine-local SQLite database, with scoped records for users, workspaces, projects, and agent workflows — not hidden cloud state, not raw transcript scraping, not opaque global memory.

[![CI](https://github.com/benbenlijie/deep-memory/actions/workflows/ci.yml/badge.svg)](https://github.com/benbenlijie/deep-memory/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-alpha-orange)

Quick links: [Quickstart](#quickstart) · [Agent install guide](docs/AGENT_INSTALL_GUIDE.md) · [Safety & privacy](docs/SAFETY_AND_PRIVACY.md) · [Benchmarks & evals](docs/MEMORY_BENCHMARK.md) · [Contributing](#contributing)

- **Cross-agent continuity.** One shared memory layer for multiple agent tools, so useful conventions do not have to be re-taught from scratch.
- **Inspectable by default.** Read, edit, export, soft-delete, hard-delete, and audit records through the CLI, Python SDK, or local WebUI.
- **Machine-local governance.** One local SQLite store can be shared across agents, while explicit scopes keep records bounded to users, workspaces, projects, or workflows.
- **Regression-tested retrieval.** Checked-in evals cover Chinese retrieval, bilingual memory/no-memory tasks, and the core CLI/SDK behavior.

```text
Claude Code / Codex / OpenCode / Hermes
        │
        │  explicit facts, procedures, project conventions
        ▼
DeepMemory SDK / CLI / MCP / wrappers
        │
        ▼
machine-local SQLite + FTS5 + scoped records
        │
        ├─ ranked recall for future agent context
        ├─ CLI / SDK / local WebUI inspection
        ├─ export, soft-delete, hard-delete
        └─ regression evals + reviewable skill candidates
```

Persistent agent memory is powerful precisely because it changes future behavior. `deep-memory` keeps the mechanism narrow: store durable facts and reusable procedures, keep them local and inspectable, retrieve only relevant context, and make deletion and policy boundaries explicit.

## Why agent memory needs control

Most agent memory fails in one of two ways: it forgets everything useful between sessions, or it remembers too much in a place the user cannot inspect. Both are bad substrates for serious work.

A useful memory layer needs more than storage:

- **Inspectability:** humans should be able to see what an agent will carry forward.
- **Deletion:** wrong, stale, private, or unsafe records must be removable, not merely hidden by ranking.
- **Scoping:** machine-level memory should stay relevant through explicit user, workspace, project, and workflow scopes.
- **Regression tests:** retrieval quality and safety boundaries should be checked with fixtures, not asserted in copy.

`deep-memory` is deliberately boring infrastructure: a local SQLite file, explicit metadata, reproducible commands, and human-visible records.

## Quickstart

If you want the fastest path, ask your coding agent:

> Install deep-memory for this machine, set it up as a shared memory layer across my agent tools, and verify that you can write and retrieve a durable memory.

Agent checklist:
1. Read [`docs/AGENT_INSTALL_GUIDE.md`](docs/AGENT_INSTALL_GUIDE.md).
2. Install dependencies and initialize a machine-local memory store.
3. Connect your agent through MCP or a wrapper.
4. Verify that one durable memory can be written and retrieved.
5. Report which scopes you configured (for example: global, workspace, or project).

For agents or advanced users who want the minimal command path:

```bash
uv sync --extra dev --extra mcp
uv run deep-memory init ~/.deep-memory/deep-memory.db
uv run deep-memory add ~/.deep-memory/deep-memory.db \
  "User wants agents to use deep-memory as shared persistent memory" \
  --kind semantic \
  --importance 0.8
uv run deep-memory search ~/.deep-memory/deep-memory.db "shared persistent memory"
```

This is the core loop: install one machine-local memory store, let agents share it, and keep records bounded with explicit scopes.

If you are an AI agent installing this for a user, follow [`docs/AGENT_INSTALL_GUIDE.md`](docs/AGENT_INSTALL_GUIDE.md) — it covers MCP setup, wrappers, safe memory-write rules, and how to ask the user before starring the repo.

## Evidence, not magic

These checks are intentionally modest. They are internal evals and regressions, not a claim that memory is solved.

| Evaluation | Current checked-in result | Reproduce |
| --- | --- | --- |
| Chinese retrieval v1 | 55/55 with the default local backend; 55/55 with optional `jieba`; earlier plain SQLite FTS baseline was 24/55 | `uv run python evals/chinese_retrieval_eval.py --data evals/data/zh_memory_retrieval.jsonl` |
| Chinese retrieval v2 | 20/20 harder multi-memory cases with distractors; local top-1 accuracy 1.0 and MRR 1.0 in this checked-in baseline | `uv run python evals/chinese_retrieval_eval.py --data evals/data/zh_memory_retrieval_v2.jsonl --json` |
| Memory benchmark v0 | 20 bilingual tasks; no-memory baseline 0/20; `deep-memory` should pass at least 16/20 in tests and usually 20/20 with the default retrieval limit | `uv run python benchmarks/memory_benchmark.py` |
| Test suite | Core behavior, policy, import/export, CLI paths, and regressions are covered by pytest and CI | `uv run pytest -q` |

Details: [`docs/CHINESE_RETRIEVAL_EVAL.md`](docs/CHINESE_RETRIEVAL_EVAL.md), [`docs/MEMORY_BENCHMARK.md`](docs/MEMORY_BENCHMARK.md).

## Connect your agent

Use MCP when your agent supports it. Use a wrapper when it does not. Either way, point every tool at the same machine-local database, then rely on scope to keep records relevant:

```text
~/.deep-memory/deep-memory.db
```

### Claude Code

```bash
claude mcp add deep-memory -- uv --directory /absolute/path/to/deep-memory run deep-memory-mcp
```

Add this to `CLAUDE.md` so the policy is explicit:

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

Hermes should then expose tools such as `mcp_deep_memory_add`, `mcp_deep_memory_search`, and `mcp_deep_memory_stats`.

Hermes can also import explicit facts JSONL:

```bash
cat > /tmp/hermes-session.jsonl <<'JSONL'
{"session_id":"s_demo","facts":[{"content":"User prefers concise answers with English technical terms","kind":"semantic","importance":0.9}]}
{"session_id":"s_demo","facts":[{"content":"Successful workflows should become reviewable skill candidates","kind":"procedural","confidence":0.8}]}
JSONL

uv run deep-memory hermes-import ~/.deep-memory/deep-memory.db /tmp/hermes-session.jsonl
```

### Codex, OpenCode, and OpenClaw-style agents

Until MCP is wired in, use a wrapper. Search before the task, write only verified facts after:

```bash
MEMORY_DB=~/.deep-memory/deep-memory.db
uv run deep-memory search "$MEMORY_DB" "this task's relevant conventions"
# pass the result into the agent as a short "relevant memory" block
# ...run the agent...
uv run deep-memory add "$MEMORY_DB" \
  "Workflow: for this repo, run uv run pytest -q and uv run ruff check . before review" \
  --kind procedural \
  --importance 0.8 \
  --source codex:manual
```

For the full adapter surface — integration points, read/write paths, permissions, risks — see [`docs/ADAPTERS.md`](docs/ADAPTERS.md) and the per-agent commands in [`docs/AGENT_QUICKSTART_MATRIX.md`](docs/AGENT_QUICKSTART_MATRIX.md).

## Memory scopes

`deep-memory` is machine-local by default, but records can still be bounded explicitly:

- **global** — durable user preferences and long-lived facts that should follow every workflow on the machine.
- **user** — facts tied to one user identity when multiple people share a host.
- **workspace** — shared working context across related repos or folders.
- **project** — repo-specific conventions and procedures.
- **tenant** — team or environment partitioning when one database serves more than one lane.

The database is shared; scope keeps retrieval relevant. Start with the narrowest scope that preserves the behavior you want, then widen only when the memory should truly travel across projects or agents.

## Inspect memory

```bash
uv run deep-memory webui ~/.deep-memory/deep-memory.db --host 127.0.0.1 --port 8765
# open http://127.0.0.1:8765
```

The WebUI can list, search, edit, and soft-delete records. It binds to `127.0.0.1` by default.

Export and audit:

```bash
uv run deep-memory export ~/.deep-memory/deep-memory.db                      # active records only
uv run deep-memory export ~/.deep-memory/deep-memory.db --include-deprecated # audit / backup
uv run deep-memory hard-delete ~/.deep-memory/deep-memory.db <memory-id>     # physically remove one record
```

## Python API

```python
from pathlib import Path
from deep_memory import DeepMemory

mem = DeepMemory(Path("~/.deep-memory/deep-memory.db").expanduser())
mem.add("User prefers concise answers with English technical terms", kind="semantic", importance=0.9, scope="user")
mem.add("Project convention: use uv for tests", kind="procedural", importance=0.8, scope="project")

for result in mem.search("how should this repo be tested?", limit=3):
    print(result.score, result.record.kind, result.record.content)
```

## What works today

| Area | Status | Notes |
| --- | --- | --- |
| Local persistence | Implemented | Machine-local SQLite DB controlled by the user, with explicit scopes for users, workspaces, projects, and tenants. |
| Search | Implemented | FTS5 plus local Chinese/English token fallback. |
| Optional Chinese tokenizer | Implemented | `jieba` backend via `uv sync --extra retrieval`. |
| Metadata | Implemented | `kind`, `importance`, `confidence`, `source`, timestamps, conflict states, scope, and decay. |
| Conflict handling | Implemented | Candidate, resolved, superseded, deprecated. |
| Python SDK + CLI | Implemented | `add`, `search`, `stats`, `conflicts`, `resolve-conflict`, `export`, `hard-delete`, `hermes-import`, `webui`. |
| MCP server | Implemented | Stdio tools for `add`, `search`, `stats`, and conflict helpers. |
| Hermes import | Implemented | Explicit session facts JSONL to `deep-memory` records. |
| Local WebUI MVP | Implemented | Inspect, search, edit, and soft-delete memory records. |
| Memory to skill candidate | Implemented | Exports procedural memories as reviewable skill markdown; no auto-install. |
| Codex wrapper MVP | Implemented | `deep-memory codex-run` injects bounded context and imports only explicit `--facts-out` JSONL after success. |
| Native adapters for every agent | Spec / prototype | Use MCP or wrapper first. See `docs/ADAPTERS.md`. |
| Vector retrieval / hosted sync | Roadmap | Later, if evals and privacy boundaries justify it. |

## Architecture

The core system is small on purpose:

1. agents or developers produce explicit facts, procedures, and durable conventions;
2. SDK, CLI, MCP, or wrapper paths validate and write records;
3. machine-local SQLite + FTS5 stores searchable memory with metadata and scope;
4. future agents retrieve a bounded context block before work;
5. humans inspect, edit, export, delete, evaluate, or promote procedural records into skill candidates.

SQLite is boring on purpose. It is easy to install, inspect, test, back up, and replace later. A single machine-local store keeps agents interoperable; scopes keep retrieval bounded. Vector retrieval stays on the roadmap with schema placeholders and an opt-in migration path; see [`docs/VECTOR_ROADMAP.md`](docs/VECTOR_ROADMAP.md).

Read more:

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
- [`docs/SAFETY_AND_PRIVACY.md`](docs/SAFETY_AND_PRIVACY.md)
- [`docs/MEMORY_POLICY.md`](docs/MEMORY_POLICY.md)
- [`docs/MCP_INTEROPERABILITY.md`](docs/MCP_INTEROPERABILITY.md)
- [`docs/ADAPTERS.md`](docs/ADAPTERS.md)
- [`docs/ROADMAP.md`](docs/ROADMAP.md)
- [`docs/VECTOR_ROADMAP.md`](docs/VECTOR_ROADMAP.md)

## Safety boundary

Persistent memory changes future behavior. Keep the default narrow:

- store explicit durable facts, not raw transcripts;
- use machine-local SQLite by default;
- keep scope explicit so global memories are intentional and project/workspace memories stay bounded;
- retrieve a small relevant context block;
- retrieval telemetry is local-only and can be disabled with `DEEP_MEMORY_TELEMETRY=off` — see [`docs/SAFETY_AND_PRIVACY.md`](docs/SAFETY_AND_PRIVACY.md);
- never store secrets, private keys, auth cookies, raw credentials, raw private transcripts, or temporary task status;
- write procedural memories only after tests, review, or user confirmation;
- auto-backup destructive operations with a configurable 7-day TTL;
- export skill candidates for review instead of auto-installing them.

Read [`docs/MEMORY_POLICY.md`](docs/MEMORY_POLICY.md) for the allow / deny / requires-confirmation write policy, and [`docs/SAFETY_AND_PRIVACY.md`](docs/SAFETY_AND_PRIVACY.md) before adding automatic writes or shared team memory.

## Contributing

This is a controlled preview lane, not a broad launch claim. Contributions should make the memory layer more inspectable, reproducible, scoped, or easier to run.

Good starting paths:

- `good first issue`: small fixtures, docs fixes, CLI output polish, and reproducible failure cases;
- `adapter`: smoke transcripts and wrapper/MCP compatibility notes for Claude Code, Codex, OpenCode, OpenClaw-style tools, and Hermes;
- `eval`: Chinese retrieval, privacy-boundary, memory/no-memory, and Memory × Skill regression cases;
- `governance`: write policy, consent, export/delete, and conflict-lifecycle checks;
- `docs`: quickstarts, troubleshooting, glossary, and contribution paths.

Start with [`CONTRIBUTING.md`](CONTRIBUTING.md), [`docs/COMMUNITY.md`](docs/COMMUNITY.md), and [`docs/NEXT_PHASE_BACKLOG.md`](docs/NEXT_PHASE_BACKLOG.md).

## License

MIT
