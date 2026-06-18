# Architecture

## System model

```text
agent or developer
  -> explicit facts / procedures / project conventions
  -> DeepMemory SDK, CLI, MCP server, or adapter
  -> local SQLite + FTS5
  -> ranked recall for future agent context
  -> WebUI, export, evals, and skill candidates
```

Everything in `deep-memory` flows through one local SQLite database. There
is no separate memory service, no remote write path, and no hidden global
state by default. If a record exists, it exists in a file you can inspect.

## Core entities

- `MemoryRecord`: the durable unit. Carries `content`, `kind`, `importance`,
  `confidence`, `source`, timestamps, optional expiry, and conflict status.
- `SearchResult`: a recalled record plus its ranking score.
- `MemoryEngine`: the SDK surface for `add`, `search`, `stats`, conflict
  lifecycle, decay, and skill-candidate export. CLI, MCP, WebUI, and
  adapters all reach memory through this surface, so guardrails (such as
  refusing obvious credentials) apply no matter which entry point the agent
  uses.

## Storage decisions

The root bottleneck is representation and lifecycle, not distributed
storage. SQLite is chosen on purpose:

- transparent: state is a file you can open, query, copy, back up, or delete;
- deterministic: tests run against a fresh temp DB and reproduce on CI;
- boring: no extra services, no version churn, no operational surface;
- extensible: FTS5 plus a Chinese bigram fallback today; tokenizer and
  embedding backends are optional extras, not replacements for the local
  baseline.

Vector retrieval, graph retrieval, and hosted sync remain on the roadmap
(see [`ROADMAP.md`](ROADMAP.md)). They will land only when evals and privacy
boundaries justify adding them, and they will not remove the local-first
default.

## Memory lifecycle

```text
candidate -> active -> superseded or deprecated
```

- **candidate**: a memory proposed for review, not yet authoritative.
- **active**: a memory that default `search` and `export` will return.
- **superseded**: replaced by a newer record; hidden from default recall,
  still visible in conflict/audit views.
- **deprecated**: soft-deleted, hidden from default recall and export,
  retained for audit and recovery.

Hard delete is a separate, explicit operation that physically removes one
record from the active database. It does not silently rewrite history; it
is for privacy requests, accidental secret ingestion, and data minimization.

## Where things live

| Component | Location |
| --- | --- |
| SDK and CLI | `src/deep_memory/` |
| MCP server | `src/deep_memory/mcp_server.py` |
| Adapters (Hermes import, Codex wrapper) | `src/deep_memory/adapters/` |
| WebUI | `src/deep_memory/webui.py` |
| Skill candidate export | `src/deep_memory/skill_export.py` |
| Privacy guardrails | `src/deep_memory/privacy.py` |
| Eval harnesses | `evals/`, `benchmarks/` |
| Architecture and safety model | `docs/ARCHITECTURE.md`, `docs/SAFETY_AND_PRIVACY.md` |

Read [`SAFETY_AND_PRIVACY.md`](SAFETY_AND_PRIVACY.md) before adding new
write or recall paths.
