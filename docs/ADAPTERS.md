# Cross-agent adapter specs

`deep-memory` should work even when your workflow jumps between tools: Claude Code for one task, Codex for another, Hermes for orchestration, OpenCode or OpenClaw-style agents for longer runs.

The adapter layer has one job: let each agent read a small amount of useful memory before work, then write back only facts or procedures that are worth keeping.

No hidden transcript scraping. No silent cloud sync. No auto-installed skills.

## What an adapter must do

An adapter only needs two operations at first:

1. `search` before or during an agent run.
2. `add` after the agent has a durable fact or a verified procedure.

Everything else can wait. Conflict tools, skill generation, richer scopes, and vector search are useful, but they should not make the first adapter hard to build.

## Basic rules

- Use an explicit SQLite DB path, usually project-local: `.deep-memory/deep-memory.db`.
- Keep recall small. Do not paste the whole memory DB into the prompt.
- Write explicit facts, not raw transcripts.
- Write procedural memory only after evidence: tests, review, or user confirmation.
- Preserve source: agent name, session/run id, workspace, and source event when available.
- Do not store secrets, raw credentials, private keys, auth cookies, or temporary task status.

## Minimal common adapter protocol

The common protocol has two operations: `search` before/inside an agent loop, and `add` after the agent has a durable fact or verified procedure. Conflict tools can be layered on top, but they are not required for the first shared adapter contract.

### Search request

```json
{
  "protocol_version": "deep-memory.adapter.v1",
  "operation": "search",
  "agent": {
    "name": "hermes|claude-code|codex|opencode|openclaw|custom",
    "version": "optional-agent-version"
  },
  "context": {
    "session_id": "optional-session-id",
    "workspace": "/absolute/project/path",
    "task": "short task description",
    "user_id": "optional-local-user-or-profile-id"
  },
  "query": "what should be remembered for this task?",
  "filters": {
    "kind": "working|episodic|semantic|procedural|null",
    "source_prefix": "optional-source-prefix"
  },
  "limit": 5
}
```

### Search response

```json
{
  "protocol_version": "deep-memory.adapter.v1",
  "memories": [
    {
      "id": "memory-id",
      "content": "durable fact or procedure",
      "kind": "semantic|episodic|procedural|working",
      "score": 1.23,
      "importance": 0.8,
      "confidence": 0.8,
      "source": "agent:session:message",
      "created_at": "2026-06-16T12:00:00Z"
    }
  ]
}
```

### Add request

```json
{
  "protocol_version": "deep-memory.adapter.v1",
  "operation": "add",
  "agent": {
    "name": "hermes|claude-code|codex|opencode|openclaw|custom",
    "version": "optional-agent-version"
  },
  "context": {
    "session_id": "optional-session-id",
    "workspace": "/absolute/project/path",
    "task": "short task description"
  },
  "facts": [
    {
      "content": "durable fact or procedure",
      "kind": "semantic|episodic|procedural|working",
      "importance": 0.8,
      "confidence": 0.8,
      "source": "agent:session:message",
      "evidence": {
        "type": "tests|review|command|user-confirmed|manual",
        "summary": "uv run pytest -q => 16 passed"
      }
    }
  ]
}
```

### Add response

```json
{
  "protocol_version": "deep-memory.adapter.v1",
  "created": [
    {
      "id": "memory-id",
      "source": "agent:session:message"
    }
  ],
  "skipped": [
    {
      "content": "temporary issue status",
      "reason": "ephemeral_or_unverified"
    }
  ]
}
```

### Required adapter behaviors

- Normalize all writes into the existing `MemoryRecord` fields: `content`, `kind`, `importance`, `confidence`, `source`, timestamps, and optional expiry/conflict metadata.
- Use stable source IDs so duplicate prevention and conflict resolution can be added later.
- Let users choose database scope: user-level, profile-level, or project-local.
- Treat `working` and low-confidence memories as non-durable by default unless the user explicitly opts in.
- Never write secrets, raw credentials, private keys, auth cookies, or full unredacted transcripts.

## Hermes adapter

### Integration point

Best first integration is native because Hermes already has explicit memory, skills, profiles, sessions, tools, and Kanban concepts. The implemented MVP is an explicit facts JSONL import path: Hermes or a plugin emits `facts`, then `deep-memory hermes-import` writes them to a local database. A later plugin can call the Python adapter after a session turn, compression pass, `/memory` action, or Loop Engineering closure.

### Read path

- Query `deep-memory` before prompt/context assembly or before a tool-heavy task starts.
- Inject only a small, ranked memory block into the session context.
- Prefer filters by Hermes profile, workspace, task, and memory kind to avoid leaking context across unrelated projects.
- For Kanban workers, read parent/project memories only when workspace and tenant match.

### Write path

- Conservative MVP: `facts` JSONL → `deep-memory hermes-import <db> <jsonl>`.
- Native plugin path: after a turn/session, extract or receive explicit durable facts and call `DeepMemory.add()`.
- Procedural writes should happen only after the loop closes with evidence: tests pass, review passes, or the user confirms a workflow.
- Skill candidates should remain reviewable artifacts, not automatically installed skills.

### Permissions

- Database path must be explicit in config, e.g. profile-level `~/.hermes/profiles/<profile>/deep-memory.db` or project-local `.deep-memory/deep-memory.db`.
- Plugin needs read/write permission only to the configured database and read access to minimal session metadata/facts.
- Cross-profile reads require explicit configuration; default isolation should follow Hermes profile boundaries.

### Install UX

```bash
uv run deep-memory init ~/.hermes/profiles/demis-research/deep-memory.db
uv run deep-memory hermes-import ~/.hermes/profiles/demis-research/deep-memory.db /path/to/session-facts.jsonl
```

Future Hermes plugin UX should be one explicit config block rather than hidden global behavior:

```yaml
plugins:
  deep_memory:
    db_path: ~/.hermes/profiles/demis-research/deep-memory.db
    write_policy: explicit_facts_only
    read_limit: 5
```

### Risks

- Storing transient Kanban/task progress as durable memory.
- Violating profile or tenant isolation by reading a global database too early.
- Treating model-generated extraction as verified truth.
- Prompt bloat if recall is not ranked and capped.

## Claude Code adapter

### Integration point

Claude Code has three practical adapter surfaces:

1. MCP server: configure `deep-memory-mcp` as a Claude MCP server and expose `add`, `search`, `stats`, and future conflict tools.
2. Project memory files: use `CLAUDE.md` or `.claude/rules/*.md` to document how Claude should call the memory tool.
3. Hooks/wrappers: pre-task wrapper searches memory and appends context; post-task hook writes verified durable facts.

MCP should be the default because it maps cleanly to a tool protocol and avoids brittle transcript parsing.

### Read path

- At session start or before planning, call MCP `search(query, db_path, limit, kind)` with a task-specific query.
- Inject a short “Relevant durable memories” block into the task prompt or let Claude call the MCP tool directly.
- Keep recalled content bounded; do not dump the database into `CLAUDE.md`.

### Write path

- Post-task hook or explicit instruction calls MCP `add()` for stable project facts, user preferences, and successful procedures.
- For procedural memory, require evidence such as “tests run,” “command output,” or “review passed.”
- For skill promotion, generate a candidate markdown file for human review rather than modifying `.claude/skills/` automatically.

### Permissions

- Claude MCP config should point to a project-local or user-approved database path.
- If using hooks, hook commands must not read `.env`, tokens, or private transcript directories by default.
- Use project-local configuration for team-shared behavior and user-level configuration for private preferences.

### Install UX

```bash
uv sync --extra mcp --extra dev
claude mcp add deep-memory -- uv --directory /absolute/path/to/deep-memory run deep-memory-mcp
```

Recommended project note in `CLAUDE.md`:

```markdown
Before large tasks, search deep-memory for relevant project conventions. After verified success, add only durable facts or reusable procedures; never store secrets or temporary issue status.
```

### Risks

- Claude may over-write plausible but unverified summaries unless the prompt/hook enforces evidence.
- Project-level `CLAUDE.md` can accidentally expose private user preferences if generated from a user database.
- Hooks can become too powerful; keep them narrow and auditable.
- Duplicate memories may appear if both hooks and direct MCP calls write the same fact without source IDs.

## Codex adapter

### Integration point

Codex is best served by a wrapper plus MCP. It runs inside a git repo and can execute bounded tasks, so the adapter should supply memory before `codex exec` and expose MCP tools when Codex needs interactive recall/write during planning.

Practical surfaces:

1. MCP server configured for Codex if supported by the local Codex setup.
2. CLI wrapper: `deep-memory search` before `codex exec`, then post-run `deep-memory add` or JSONL import.
3. Repo instruction file, such as `AGENTS.md`, describing memory policy.

### Read path

- Wrapper receives the user task, searches the configured database, and prepends a compact context block to the Codex prompt.
- If MCP is available, Codex can call `search` directly before modifying code.
- Filters should include workspace/repo source prefixes to reduce cross-project contamination.

### Write path

- After Codex exits, wrapper inspects a structured handoff file or explicit JSONL facts file produced by Codex.
- Write only stable conventions, implementation decisions, and reusable procedures with evidence.
- Do not infer durable memories from raw diffs alone; require a summary plus verification output.

### Permissions

- Codex often runs with broad filesystem permissions in trusted repos; the adapter must still restrict memory writes to the configured DB path.
- The wrapper should not pass secrets from environment variables into memory prompts.
- Source IDs should include repo path or git remote hash, session ID, and optional commit/working-tree marker when safe.

### Install UX

Wrapper-style UX:

```bash
MEMORY_DB=.deep-memory/deep-memory.db \
  deep-memory search "$MEMORY_DB" "repo conventions for this task"

codex --ask-for-approval never --sandbox danger-full-access exec \
  "Use the recalled memory block below only if relevant. <task>"
```

Future helper command could look like:

```bash
uv run deep-memory codex-run \
  --db .deep-memory/deep-memory.db \
  --task "Fix the parser tests" \
  --facts-out /tmp/deep-memory-codex-facts.jsonl \
  -- codex exec "Fix the parser tests and write explicit durable facts to /tmp/deep-memory-codex-facts.jsonl only after tests pass"
```

The implemented MVP injects a bounded `DEEP_MEMORY_CONTEXT` block into the child process environment, runs only the command after `--`, and imports only the explicit JSONL file passed by `--facts-out` after the child exits with status 0. It does not read `.env`, token files, raw transcripts, or infer memory from diffs/stdout.

### Risks

- Confusing model-generated summaries with verified facts.
- Writing memories from failed or partially completed runs.
- Storing issue numbers, PR numbers, or temporary branch state that will go stale.
- Sandbox and permission differences across machines may make a wrapper appear to work locally but fail in CI.

## OpenCode / OpenClaw-style adapter

### Integration point

OpenCode and OpenClaw-style tools are provider-agnostic coding agents with CLI/TUI loops. The safest common adapter is MCP plus command hooks. For tools that emit JSONL session artifacts, an importer can map explicit facts into the same adapter protocol.

Surfaces:

1. MCP `deep-memory-mcp` for direct `search`/`add` calls.
2. `opencode run` wrapper for pre-task recall and post-task durable-fact import.
3. Session artifact importer for JSONL logs that contain explicit `facts` arrays.
4. Workspace instruction file such as `AGENTS.md` or tool-specific config.

### Read path

- Before `opencode run` or an OpenClaw-style autonomous loop, search the project/user database for relevant facts.
- Inject only a bounded context block or rely on MCP `search` inside the agent.
- For long-running TUI sessions, repeat search when task scope changes rather than carrying stale memory indefinitely.

### Write path

- Write only at clear checkpoints: command succeeded, tests passed, review completed, or user approved.
- Prefer explicit JSON output from the agent containing candidate facts and evidence.
- Add procedural memories as candidates for later skill export when the process is repeatable.

### Permissions

- Require explicit workspace-to-database mapping, e.g. `.deep-memory/deep-memory.db` for a repo.
- Avoid global writes from anonymous scratch sessions unless the user has configured a user-level DB.
- If a TUI agent runs in background, do not let it silently write memory without a visible policy in the prompt/config.

### Install UX

```bash
uv sync --extra mcp --extra dev
opencode run "Search deep-memory for relevant project conventions, then implement the task" \
  -f AGENTS.md
```

Future wrapper UX:

```bash
deep-memory opencode-run --db .deep-memory/deep-memory.db -- opencode run "Add retry tests"
```

### Risks

- Provider-agnostic tools may vary in MCP support and output schemas.
- TUI sessions can blur the boundary between planning notes and durable facts.
- Duplicate records across Claude/Codex/OpenCode unless source IDs and idempotency keys are standardized.
- Hidden background writes would damage user trust; make writes visible and reviewable.

## Compatibility matrix

| Agent | Integration point | Read path | Write path | Permissions | Install UX | Key risk | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Hermes | Native plugin, explicit JSONL import, MCP | Before prompt/context assembly; profile/workspace filters | Explicit facts JSONL or plugin after verified session/loop closure | Profile/project DB path; cross-profile opt-in | `deep-memory hermes-import`; future plugin config | Ephemeral task progress becoming durable memory | MVP import implemented; native plugin planned |
| Claude Code | MCP, `CLAUDE.md`, hooks/wrapper | MCP `search` before planning or direct tool call | MCP `add` after tests/review/user confirmation | Project/user MCP config; narrow hooks | `claude mcp add deep-memory -- uv ... deep-memory-mcp` | Unverified summaries and private preference leakage | Spec |
| Codex | Wrapper, MCP, `AGENTS.md` | Prepend wrapper recall block or MCP search | Structured post-run facts with evidence | Repo-scoped DB; env secret scrubbing | `deep-memory codex-run --db ... --task ... --facts-out ... -- codex exec ...` | Writing from failed/partial runs | Wrapper MVP implemented |
| OpenCode/OpenClaw | MCP, wrapper, JSONL artifact importer | Pre-run recall or MCP inside loop | Checkpoint-based explicit facts/import | Explicit workspace DB mapping | Future `deep-memory opencode-run` helper | Duplicate/hidden writes from long TUI loops | Spec |

## Suggested implementation sequence

1. Keep Hermes JSONL import as the conservative baseline and document examples.
2. Harden `deep-memory-mcp` as the shared tool surface for Claude Code, Codex, and OpenCode/OpenClaw.
3. Add project-local wrapper prototypes for Codex and OpenCode with pre-task recall and post-task explicit fact import.
4. Add source ID/idempotency strategy before enabling automatic writes.
5. Add conflict lifecycle and memory-to-skill review flows once basic search/add behavior is stable.

## Non-goals

- No hidden scraping of private transcripts.
- No cloud sync by default.
- No automatic skill generation or installation without review.
- No storing raw secrets, credentials, or full unredacted conversations.
- No guarantee that recalled memory is sufficient context; adapters must still let the agent inspect current files and run tests.
