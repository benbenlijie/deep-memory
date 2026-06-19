# deep-memory

[English](README.md) | [简体中文](README.zh-CN.md)

> Local-first memory for AI agents. Inspect what they remember. Decide what they keep.

[![CI](https://github.com/benbenlijie/deep-memory/actions/workflows/ci.yml/badge.svg)](https://github.com/benbenlijie/deep-memory/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-alpha-orange)

Agents forget useful things between sessions. The convention Claude Code just learned is invisible to Codex. The workflow Hermes just proved has to be re-explained in OpenCode. `deep-memory` gives those tools one shared, inspectable memory layer — a SQLite file in your project, no cloud, no transcript scraping, no hidden global state.

## Highlights

- **Local-first by default.** SQLite in your project. The database is something you can `cp`, `scp`, inspect, back up, or delete. New writes default to workspace scope inferred from the current working directory, while global remains an explicit opt-in.
- **Cross-agent.** Works with Claude Code, Codex, OpenCode, OpenClaw-style tools, and Hermes through MCP, a CLI wrapper, or explicit JSONL import.
- **Inspectable.** CLI, Python SDK, and a local WebUI to read, edit, soft-delete, and export every record. No opaque embeddings-only view.
- **Chinese-first retrieval.** FTS5 with a Chinese bigram fallback, plus an optional `jieba` backend. Measured on a checked-in Chinese retrieval fixture, not just claimed in copy.
- **Memory governance, not just storage.** Records carry `kind`, `importance`, `confidence`, `source`, timestamps, conflict status, and decay — so memory can be audited, corrected, and aged out.
- **A path from memory to skill.** Procedural memories can be exported as reviewable skill candidates — never auto-installed as behavior.

<p align="center">
  <img src="docs/assets/deep-memory-architecture.svg" alt="deep-memory architecture" width="920">
</p>

## Quickstart

```bash
git clone https://github.com/benbenlijie/deep-memory.git
cd deep-memory
uv sync --extra dev --extra mcp

uv run deep-memory init .deep-memory/deep-memory.db
uv run deep-memory add .deep-memory/deep-memory.db \
  "Project convention: run uv run pytest -q before review" \
  --kind procedural \
  --importance 0.8
uv run deep-memory search .deep-memory/deep-memory.db "how do we verify changes?"
```

If you are an AI agent installing this for a user, follow [`docs/AGENT_INSTALL_GUIDE.md`](docs/AGENT_INSTALL_GUIDE.md) — it covers MCP setup, the Codex wrapper, safe memory-write rules, and how to ask the user before starring the repo.

## Connect your agent

Use MCP when your agent supports it. Use a wrapper when it does not. Either way, point every tool at the same project-local database:

```text
.deep-memory/deep-memory.db
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

uv run deep-memory hermes-import .deep-memory/deep-memory.db /tmp/hermes-session.jsonl
```

### Codex, OpenCode, and OpenClaw-style agents

Until MCP is wired in, use a wrapper. Search before the task, write only verified facts after:

```bash
MEMORY_DB=.deep-memory/deep-memory.db
uv run deep-memory search "$MEMORY_DB" "repo conventions for this task"
# pass the result into the agent as a short "relevant memory" block
# ...run the agent...
uv run deep-memory add "$MEMORY_DB" \
  "Workflow: for this repo, run uv run pytest -q and uv run ruff check . before review" \
  --kind procedural \
  --importance 0.8 \
  --source codex:manual
```

For the full adapter surface — integration points, read/write paths, permissions, risks — see [`docs/ADAPTERS.md`](docs/ADAPTERS.md) and the per-agent commands in [`docs/AGENT_QUICKSTART_MATRIX.md`](docs/AGENT_QUICKSTART_MATRIX.md).

## Inspect memory

```bash
uv run deep-memory webui .deep-memory/deep-memory.db --host 127.0.0.1 --port 8765
# open http://127.0.0.1:8765
```

The WebUI can list, search, edit, and soft-delete records. It binds to `127.0.0.1` by default.

Export and audit:

```bash
uv run deep-memory export .deep-memory/deep-memory.db                      # active records only
uv run deep-memory export .deep-memory/deep-memory.db --include-deprecated # audit / backup
uv run deep-memory hard-delete .deep-memory/deep-memory.db <memory-id>     # physically remove one record
```

## Python API

```python
from deep_memory import DeepMemory

mem = DeepMemory(".deep-memory/deep-memory.db")
mem.add("User prefers concise answers with English technical terms", kind="semantic", importance=0.9)
mem.add("Project convention: use uv for tests", kind="procedural", importance=0.8)

for result in mem.search("how should this repo be tested?", limit=3):
    print(result.score, result.record.kind, result.record.content)
```

## What works today

| Area | Status | Notes |
| --- | --- | --- |
| Local persistence | Implemented | SQLite DB controlled by the user or project. |
| Search | Implemented | FTS5 plus local Chinese/English token fallback. |
| Optional Chinese tokenizer | Implemented | `jieba` backend via `uv sync --extra retrieval`. |
| Metadata | Implemented | `kind`, `importance`, `confidence`, `source`, timestamps, conflict states. |
| Conflict handling | Implemented | Candidate, resolved, superseded, deprecated. |
| Python SDK + CLI | Implemented | `add`, `search`, `stats`, `conflicts`, `resolve-conflict`, `export`, `hard-delete`, `hermes-import`, `webui`. |
| MCP server | Implemented | Stdio tools for `add`, `search`, `stats`, and conflict helpers. |
| Hermes import | Implemented | Explicit session facts JSONL to `deep-memory` records. |
| Local WebUI MVP | Implemented | Inspect, search, edit, and soft-delete memory records. |
| Memory to skill candidate | Implemented | Exports procedural memories as reviewable skill markdown; no auto-install. |
| Codex wrapper MVP | Implemented | `deep-memory codex-run` injects bounded context and imports only explicit `--facts-out` JSONL after success. |
| Native adapters for every agent | Spec / prototype | Use MCP or wrapper first. See `docs/ADAPTERS.md`. |
| Vector retrieval / hosted sync | Roadmap | Later, if evals and privacy boundaries justify it. |

## Evidence

These evals are small. They are regression checks, not a claim that memory is solved.

| Evaluation | Current checked-in result | Reproduce |
| --- | --- | --- |
| Chinese retrieval v1 | 55/55 with default local backend; 55/55 with optional `jieba`; earlier plain SQLite FTS baseline was 24/55 | `uv run python evals/chinese_retrieval_eval.py --data evals/data/zh_memory_retrieval.jsonl` |
| Chinese retrieval v2 | 20/20 harder multi-memory cases with distractors; local top-1 accuracy 1.0 and MRR 1.0 in this checked-in baseline | `uv run python evals/chinese_retrieval_eval.py --data evals/data/zh_memory_retrieval_v2.jsonl --json` |
| Memory benchmark v0 | 20 bilingual tasks; no-memory baseline 0/20; `deep-memory` should pass at least 16/20 in tests and usually 20/20 with the default retrieval limit | `uv run python benchmarks/memory_benchmark.py` |
| Test suite | Covered by pytest and CI | `uv run pytest -q` |

Details: [`docs/CHINESE_RETRIEVAL_EVAL.md`](docs/CHINESE_RETRIEVAL_EVAL.md), [`docs/MEMORY_BENCHMARK.md`](docs/MEMORY_BENCHMARK.md).

## Architecture

```text
agent or developer
  -> explicit facts / procedures / project conventions
  -> DeepMemory SDK, CLI, MCP, or adapter
  -> local SQLite + FTS5
  -> ranked recall for future agent context
  -> WebUI, export, evals, and skill candidates
```

SQLite is boring on purpose. It is easy to install, inspect, test, back up, and replace later. Vector retrieval stays on the roadmap with schema placeholders and an opt-in migration path; see [`docs/VECTOR_ROADMAP.md`](docs/VECTOR_ROADMAP.md).

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
- use local SQLite by default;
- retrieve a small relevant context block;
- retrieval telemetry (queries, hit memories, caller type) is local-only and can be disabled with `DEEP_MEMORY_TELEMETRY=off` — see [`docs/SAFETY_AND_PRIVACY.md`](docs/SAFETY_AND_PRIVACY.md);
- never store secrets, private keys, auth cookies, raw credentials, or temporary task status;
- write procedural memories only after tests, review, or user confirmation;
- auto-backup destructive operations with a configurable 7-day TTL;
- export skill candidates for review instead of auto-installing them.

Read [`docs/MEMORY_POLICY.md`](docs/MEMORY_POLICY.md) for the allow / deny / requires-confirmation write policy, and [`docs/SAFETY_AND_PRIVACY.md`](docs/SAFETY_AND_PRIVACY.md) before adding automatic writes or shared team memory.

## Contributing


For now this should be treated as a controlled preview lane, not a broad launch lane. The public backlog below is intentionally framed around small, verifiable contributions and the remaining blockers that keep the launch gate honest.

- `good first issue`: small fixtures, docs fixes, CLI output polish, and reproducible failure cases;
- `adapter`: smoke transcripts and wrapper/MCP compatibility notes for Claude Code, Codex, OpenCode, OpenClaw-style tools, and Hermes;
- `eval`: Chinese retrieval, privacy-boundary, memory/no-memory, and Memory × Skill regression cases;
- `governance`: write policy, consent, export/delete, and conflict-lifecycle checks;
- `docs`: quickstarts, troubleshooting, glossary, and contribution paths.

Start with [`CONTRIBUTING.md`](CONTRIBUTING.md), [`docs/COMMUNITY.md`](docs/COMMUNITY.md), and [`docs/NEXT_PHASE_BACKLOG.md`](docs/NEXT_PHASE_BACKLOG.md).

## License

MIT
