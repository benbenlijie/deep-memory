# Architecture

## System model

```text
agent or developer
  -> explicit facts / procedures / project conventions
  -> automatic extraction from redacted agent sessions / tool traces
  -> DeepMemory SDK, CLI, MCP server, or adapter
  -> automatic policy gating, scoping, and lifecycle decisions
  -> local SQLite + FTS5
  -> ranked recall for future agent context
  -> WebUI, export, evals, and skill candidates
```

Everything in `deep-memory` flows through one local SQLite database. There
is no separate memory service, no remote write path, and no hidden global
state by default. If a record exists, it exists in a file you can inspect.

The current product iteration is automatic local cross-agent memory for
individual power users. The goal is not to ask the user to approve every record.
The goal is to let adapters automatically extract durable preferences, project
conventions, verified commands, and reusable workflows from agent-native inputs,
then route those writes through policy, scope, provenance, confidence, and
forgetting controls. See
[`AUTOMATIC_LOCAL_AGENT_MEMORY.md`](AUTOMATIC_LOCAL_AGENT_MEMORY.md).

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

- **candidate**: a memory that needs selective confirmation because it is
  sensitive, high-impact, global-scope, low-confidence/high-importance, or in
  direct conflict with an active memory. Ordinary safe memories should not be
  forced through manual review.
- **active**: a memory that default `search` and `export` will return.
- **superseded**: replaced by a newer record; hidden from default recall,
  still visible in conflict/audit views.
- **deprecated**: soft-deleted, hidden from default recall and export,
  retained for audit and recovery.

Hard delete is a separate, explicit operation that physically removes one
record from the active database. It does not silently rewrite history; it
is for privacy requests, accidental secret ingestion, and data minimization.

## Automatic ingestion boundary

The first-class ingestion surface is agent-native rather than broad multimodal
ingestion:

- agent conversations and summaries;
- tool execution traces;
- facts JSONL emitted by adapters;
- project docs and local Markdown notes;
- verified commands and recurring workflows.

Adapters should ingest summaries or structured observations, not raw transcript
hoards. Automatic writes are stratified:

- reject unsafe or non-durable items;
- store low-confidence working context with TTL;
- store high-confidence durable semantic/procedural memory automatically;
- ask for confirmation only for high-risk or high-impact items.

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
