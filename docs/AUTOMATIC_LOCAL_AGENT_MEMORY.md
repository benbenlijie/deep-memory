# Automatic Local Agent Memory

## Why this document exists

This note captures the July 2026 product iteration after comparing `deep-memory` with memU and revisiting the intended user experience.

If you step back, the root problem is not whether an agent can store more context. The root problem is whether one local user can let many AI agents learn from prior work automatically without turning memory into an opaque, cross-project, hard-to-delete black box.

The updated direction is:

> `deep-memory` is a local shared memory layer for personal AI-agent users. It automatically extracts durable preferences, project conventions, and reusable workflows from agent sessions, then makes them available across Claude Code, Codex, Hermes, OpenCode, and other local agents — scoped, inspectable, deletable, and Chinese-capable by default.

Short version:

> Teach once. Every local agent remembers, within the right scope.

## Strategic clarification

This is a new product iteration. It narrows the early target and changes the default experience:

- **Target user:** individual power users running multiple local/coding agents.
- **Storage stance:** local-first SQLite by default; no cloud or team-sharing requirement for this phase.
- **Main wedge:** cross-agent shared memory.
- **UX stance:** automatic extraction, automatic classification, automatic organization, and automatic cleanup; no manual approval for every memory.
- **Safety stance:** automated governance, not heavy human review.

The previous “review-gated” language should be interpreted narrowly. Human decision points are reserved for high-risk or high-impact actions, not for every ordinary memory write.

## What “ingestion surface” means here

`deep-memory` has a strong storage, retrieval, scope, lifecycle, deletion, and audit core. Its ingestion surface is narrower: it does not yet have a first-class path for automatically turning raw agent activity into durable memories.

The important early ingestion surfaces are not generic multimodal ingestion. They are agent-native sources:

1. agent conversations and session summaries;
2. tool execution traces;
3. project docs and local Markdown notes;
4. repo conventions discovered during coding tasks;
5. verified command/test workflows;
6. user corrections and repeated preferences.

Non-goal for this phase: competing with broad multimodal memory compilers on PDFs, images, video, and audio. Those can come later if evidence says they are needed.

## Automatic memory with automatic governance

The desired model is not “remember everything” and not “ask the user to approve everything.”

The desired model is:

```text
Before task:
  detect agent + project
  retrieve scoped memory
  inject compact context

During / after task:
  observe transcript/tool trace summary
  extract candidate facts/procedures
  classify kind + scope + confidence
  reject unsafe or temporary items
  merge/update/conflict-resolve
  write automatically
  log source

Periodic:
  summarize memory health
  decay stale memories
  surface only conflicts, sensitive cases, or high-impact changes
```

## Memory levels

Automatic writes should be stratified by risk and durability.

### Level 0 — Do not store

Automatically reject:

- secrets, credentials, tokens, cookies, private keys, `.env` values;
- raw sensitive personal data;
- raw private transcripts or files by default;
- one-off task status, issue numbers, PR numbers, commit SHAs;
- unverified model speculation;
- harmful operational content.

### Level 1 — Automatic short-term memory

Store with TTL and lower confidence:

- current task context;
- recently observed but unverified facts;
- working assumptions that may help the immediate next task.

Typical shape:

```text
kind = working
confidence = 0.3-0.5
expires_at = 3-14 days
scope = project or workspace
```

### Level 2 — Automatic long-term memory

Store without interrupting the user when confidence and safety are high:

- explicit user preferences;
- stable project conventions;
- verified commands;
- recurring workflows;
- mistakes to avoid after evidence;
- durable tool/environment quirks.

Typical shape:

```text
kind = semantic or procedural
confidence = 0.7-0.9
scope = user, workspace, or project
source_info.origin_type = auto-extracted or explicit
```

### Level 3 — Selective user confirmation

Ask only when the item is high-risk or high-impact:

- sensitive personal data;
- global-scope behavior changes;
- low-confidence but high-importance memories;
- direct conflict with an active memory;
- promotion from procedural memory into an active agent skill or policy.

This is not “review every memory.” It is selective interruption.

## Memory governance, redefined

In this project, memory governance means automated lifecycle control:

```text
select → classify → scope → risk-filter → merge/conflict-handle → decay/forget → observe usage → export/delete
```

It is a system mechanism, not an enterprise approval process.

Required automatic governance components:

1. **Selection:** decide whether a fact is durable enough to store.
2. **Scoping:** choose `global`, `user`, `tenant`, `workspace`, or `project` plus `scope_id`.
3. **Risk filtering:** reject or redact secrets, sensitive PII, raw transcript hoarding, and harmful content.
4. **Conflict handling:** update, supersede, deprecate, or lower confidence when new information contradicts old memory.
5. **Trust/confidence:** weight explicit user statements, verified command evidence, and agent-generated inferences differently.
6. **Forgetting:** apply TTL, decay, and low-usage cleanup.
7. **Observability:** let the user inspect, export, edit, and delete memory when needed.

## Cross-agent shared memory as the primary wedge

The first compelling demo should show one local memory database shared by multiple agents:

```text
Claude Code learns a project convention
→ deep-memory stores it under project scope
→ Codex retrieves it before the next task
→ Hermes can inspect the source and recall history
→ OpenCode uses the same memory without re-teaching
```

Core promise:

> One person. One machine. Many agents. One scoped memory store.

The common adapter loop:

1. detect current project and agent;
2. derive stable `scope_id` from repo remote, repo root, or configured project name;
3. pre-task search scoped memories;
4. inject a compact “relevant durable memories” block;
5. post-task extract only durable facts/procedures from summarized traces;
6. write automatically through the same policy and provenance layer.

## Inspect/export story

Inspect/export means the user can see and carry their memory, not just trust that it exists.

Minimum inspect surfaces:

- show current project memories;
- show source agent and origin type;
- show scope, confidence, kind, timestamps, conflict/deprecated status;
- show why a memory was recalled when possible;
- show memory health: duplicates, conflicts, stale records, low-confidence records.

Minimum export surfaces:

```text
MEMORY.md             active semantic/project memories
PROCEDURES.md         procedural memories and verified workflows
PREFERENCES.md        user-level preferences
PROJECT_RULES.md      project conventions
CONFLICTS.md          active conflicts and superseded records
AUDIT_SUMMARY.md      source/agent/write summary
```

Machine export remains JSONL. Markdown export is for user trust, portability, and debugging.

## Benchmark direction

External benchmark work should support the new wedge instead of becoming generic memory marketing.

### Standard benchmark bridge

Evaluate against existing long-memory tasks where practical:

- long conversation memory QA;
- multi-session memory recall;
- preference recall and personalization;
- procedural/coding-agent task recurrence.

### deep-memory benchmark

Create a “Cross-Agent Memory Benchmark” with these lanes:

| Lane | What it proves |
| --- | --- |
| Preference recall | stable user preferences survive across agents |
| Project convention recall | one agent’s learned project rule helps another agent |
| Scope isolation | project A does not pollute project B |
| Stale memory handling | newer preference/rule wins over old memory |
| Deletion correctness | deleted/deprecated memory does not reappear in default recall |
| Procedural recall | verified workflows reduce repeated correction |
| Chinese mixed-token recall | Chinese queries with English technical terms retrieve correctly |

Suggested baselines:

- no-memory baseline;
- simple transcript stuffing;
- simple local RAG baseline;
- deep-memory lexical/local backend;
- optional tokenizer/vector/hybrid backends;
- selected external systems when feasible.

## Near-term implementation priorities

### P0 — Cross-agent shared-memory demo

Show agent A writing and agent B recalling from the same local DB with correct project scope.

Acceptance evidence:

- a reproducible script or transcript;
- one shared DB path;
- at least two agent names in source metadata;
- project-scope recall works;
- unrelated project memory is not recalled.

### P1 — Automatic agent-session extraction

Build a first-class extraction path from session summaries or facts JSONL into memory records.

Target memory types:

- user preference;
- project convention;
- verified command;
- tool/environment quirk;
- recurring workflow;
- mistake to avoid.

### P2 — Memory hygiene instead of manual review

Provide a local cleanup/report command that summarizes what changed and only surfaces risky items.

Possible CLI:

```bash
deep-memory hygiene ~/.deep-memory/deep-memory.db --scope project --scope-id deep-memory
```

Output categories:

- new durable memories;
- duplicates or near-duplicates;
- conflicts;
- stale/low-usage records;
- records nearing expiry;
- sensitive records rejected or requiring confirmation.

### P3 — Cross-agent benchmark

Turn the cross-agent demo into a regression benchmark.

### P4 — Markdown review/export pack

Implement scoped Markdown export for user-visible memory inspection and portability.

## Updated non-goals

- No cloud product in this iteration.
- No team-sharing platform in this iteration.
- No manual approval flow for every memory.
- No broad multimodal ingestion race in this iteration.
- No automatic installation of skills or active agent policies from memory without a higher bar.

## Product copy

English:

> `deep-memory` is a local shared memory layer for AI agents. It automatically extracts durable preferences, project rules, and reusable workflows from agent sessions, then makes them available across Claude Code, Codex, Hermes, OpenCode, and other tools — scoped, inspectable, and deletable by default.

Chinese:

> `deep-memory` 是给本地 AI agents 用的共享记忆层。它会自动从 agent 工作过程中抽取用户偏好、项目规则和可复用流程，让 Claude Code、Codex、Hermes、OpenCode 等工具共享同一套本地记忆，同时保持 scope 隔离、可查看、可删除、可追溯。

## README homepage lessons from memU

memU's README is useful as a homepage reference because it makes the product
shape legible quickly:

1. **One immediate category sentence.** memU says “Personal memory, stored as
   files” and then explains the mechanism in one paragraph. `deep-memory` should
   similarly say early and plainly: “local shared memory for all your agents.”
2. **A tiny code path before theory.** memU shows `memorize()` then `retrieve()`
   almost immediately. `deep-memory` should show the cross-agent equivalent:
   one agent writes a scoped memory, another agent retrieves it from the same
   local DB.
3. **A visual mental model.** memU's `INDEX.md / MEMORY.md / SKILL.md` tree is
   easy to scan. `deep-memory` should show its own mental model, not copy the
   file tree: `agents → shared SQLite memory → scoped recall → inspect/export`.
4. **Capability table.** memU's feature table helps readers classify the system.
   `deep-memory` needs a similar table centered on cross-agent continuity,
   automatic agent-session extraction, scope isolation, local inspection,
   deletion, Chinese retrieval, and memory hygiene.
5. **Use cases before deep architecture.** memU routes readers through personal
   memory, coding agents, multimodal knowledge, and tool learning. `deep-memory`
   should route through cross-agent coding memory, local personal preferences,
   project conventions, procedural workflows, and Chinese mixed-token recall.
6. **Proof section with external shape.** memU surfaces benchmark claims.
   `deep-memory` should keep claim discipline, but move evidence earlier:
   Chinese retrieval, memory/no-memory benchmark, scope isolation, deletion
   correctness, and the future Cross-Agent Memory Benchmark.
7. **Clear ecosystem framing.** memU lists cloud/server/UI. `deep-memory` should
   instead list local surfaces: CLI, SDK, MCP, WebUI, adapters/wrappers, export
   pack, and benchmarks.

The important adaptation: do not copy memU's broad multimodal/cloud story. Copy
the homepage clarity: category, mechanism, runnable example, mental model,
feature table, use cases, proof, ecosystem links.

### Suggested README top structure

After the current logo/badges block, the README should be rearranged toward this
homepage shape:

```text
1. Hero: local shared memory for all your agents
2. One-paragraph mechanism: automatic extraction from agent sessions, scoped local SQLite, inspect/delete/export
3. Tiny cross-agent example: Claude Code writes → Codex retrieves
4. Mental model diagram/tree: agents → local DB → scopes → inspection/export
5. Core capabilities table
6. Use cases
7. Quickstart
8. Evidence / benchmarks
9. Connect your agent
10. Safety boundary and architecture
```

README claim discipline:

- Say now: local shared memory, explicit/manual write paths, MCP/wrapper
  surfaces, scope isolation, inspect/export/delete, Chinese retrieval evals.
- Say as roadmap until implemented: automatic extraction from all agent
  sessions, memory hygiene command, Cross-Agent Memory Benchmark, Markdown
  export pack.
- Do not imply cloud/team sharing or broad multimodal ingestion is the current
  focus.
