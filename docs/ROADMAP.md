# Roadmap

## North Star

Make `deep-memory` a useful default for developers who want AI agents to
remember across sessions — a machine-local, inspectable, governed, cross-agent
memory substrate that is honest about what it stores and workable across
Claude Code, Codex, OpenCode, OpenClaw-style tools, Hermes, and future
MCP-capable agents.

This is alpha software. The items below describe direction, not a commitment
of shipping order. Status of any line item can always be checked against the
"What works today" table in [`../README.md`](../README.md).

## Current focus

M+12 is the automatic local cross-agent memory phase: turn the working local
memory core into a shared machine-local substrate for one person using many
agents. The main product wedge is no longer generic memory storage or a
cloud/team platform. It is: teach once, then Claude Code, Codex, Hermes,
OpenCode, and future local agents can recall the right project-scoped memory
without re-teaching or cross-project leakage.

See [`AUTOMATIC_LOCAL_AGENT_MEMORY.md`](AUTOMATIC_LOCAL_AGENT_MEMORY.md) for the
current iteration design and
[`plans/2026-07-02-automatic-local-agent-memory.md`](plans/2026-07-02-automatic-local-agent-memory.md)
for the implementation plan.

The next phase is split into public lanes so contributors can pick a bounded
problem and verify it with evidence.

- Adapter lane: automatic pre-task recall and post-task extraction for Claude
  Code, Codex, OpenCode, OpenClaw-style runtimes, Hermes, and future
  MCP-capable agents.
- Eval lane: cross-agent recall, project scope isolation, Chinese-first
  retrieval, privacy-boundary cases, memory/no-memory tasks, and Memory × Skill
  activation regressions.
- Governance lane: automatic write policy, risk filtering, selective
  confirmation for high-risk/high-impact memories, delete/export guarantees,
  and memory hygiene reports.
- Docs lane: quickstart matrix, troubleshooting, contribution paths, and public
  issue templates.
- Good-first-issue lane: small fixtures, docs fixes, CLI output polish, and
  reproducible failure cases.

See [`NEXT_PHASE_BACKLOG.md`](NEXT_PHASE_BACKLOG.md) for concrete issue-sized
work items, acceptance criteria, and verification commands.

## Next execution plan: compressed M+12 scope

The next iteration is intentionally small. We will not expand into a large
adapter, WebUI, language, or benchmark program before the core contracts are
verified.

Work in this order:

1. **Trust regression pack** — combine GitHub issues #6, #7, and #12:
   privacy/secret deny cases, workspace scope isolation, and mixed
   Chinese/English retrieval fixtures.
2. **CLI JSON contract** — complete issue #4 for the core commands. Keep the
   output stable, machine-readable, and tested. Human-readable output must
   keep working.
3. **Backup and setup mini-pack** — combine issues #11 and #10 into a short,
   copyable backup/restore runbook and a small troubleshooting guide for the
   most common local setup failures.
4. **Hermes smoke transcript** — deliver issue #9 as one real, reproducible
   Hermes integration example. Do not expand this into a broad adapter matrix.

Each work package must produce code or docs plus repeatable evidence. At
minimum, run `uv run pytest -q` and `uv run ruff check .` before opening a PR.

### Explicitly deferred

The following are not part of the next iteration:

- WebUI styling (#3); close or leave deferred.
- WebUI empty-state polish (#8); do only as a small opportunistic fix.
- New agent adapters (#1); revisit after the CLI JSON contract is stable.
- Full new-language evaluation (#2); keep only the mixed Chinese/English
  cases in the trust regression pack.
- New-domain benchmark (#5); revisit only when real usage shows a gap.
- Broad launch and community expansion; revisit after the four work packages
  have evidence.

## Phases

### Phase 1 — Foundation memory

- 6-line Python API.
- SQLite local persistence.
- Fact extraction contract.
- Timeline/session index.
- Hermes plugin proof-of-concept.
- Benchmark: memory vs no-memory agent task comparison.

### Phase 2 — Memory governance

- Chinese tokenization and embedding pipeline.
- Importance scoring.
- Forgetting curve and archive compression.
- Conflict detection and user-confirmed resolution.
- Web inspector/editor.

### Phase 3 — Automatic local cross-agent phase

The M+12 phase is about making `deep-memory` useful for individual power users
who move between multiple local agents. The root-node work is to expose stable
contracts, automatic extraction, repeatable verification, and safe contribution
lanes.

- MCP server and conflict lifecycle tools as the shared cross-agent surface.
- Automatic agent-session extraction from redacted summaries, tool traces, and
  facts JSONL; not raw transcript hoarding.
- Memory → skill generator and Skill × Memory activation, always behind review
  boundaries when memory would become active agent behavior.
- Shared memory adapter specs and smoke paths for Hermes, Claude Code, Codex,
  OpenCode/OpenClaw-style tools; MCP and wrappers remain the verified path
  until a native adapter has its own runtime evidence.
- Memory hygiene reports that summarize new, stale, duplicate, conflicting, and
  risky records without asking the user to approve every memory.
- Public internal eval/regression lanes, starting with checked-in fixtures before
  broader claims.
- Community backlog with `good first issue`, `help wanted`, `adapter`, `eval`,
  `governance`, and `docs` lanes.
- Maintainer-ready issue templates and review checklists for adapter proposals,
  eval fixtures, and policy changes.

Each ecosystem contribution should answer three questions: what bottleneck does
it improve, how can a maintainer verify it locally, and what privacy or
governance boundary does it touch?

## Wedge

The non-obvious wedge is not "another vector DB". It is **agent memory
governance with Chinese-first retrieval quality and real developer
ergonomics**:

```text
what to remember → how to represent → when to recall → when to decay/forget
→ how to detect conflict → when to turn procedure into skill
```

The repository should show value in the first 2 minutes, then reveal depth
through architecture, evals, the local WebUI, and integrations while keeping
roadmap items visibly separate from implemented and verified capabilities.

## Non-goals

- Not a vector database.
- Not a hosted memory cloud in this phase.
- Not a claim to beat Mem0, Zep, Graphiti, Cognee, LangMem, or
  TencentDB-Agent-Memory on every dimension. The honest framing is
  "Chinese-first local governance, eval-first quality, Memory × Skill
  direction" — see the proof obligations we hold ourselves to.
- Not a black-box "remember everything" system. Explicit durable writes,
  visible provenance, and user-controlled deletion are part of the product,
  not add-ons.
