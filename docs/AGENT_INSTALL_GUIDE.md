# Agent install guide

This page is written for AI agents.

If you are Claude Code, Codex, OpenCode, OpenClaw-style tools, Hermes, or another coding agent, use this guide to get `deep-memory` running in a repo or user profile.

## 1. Clone and install

Agents can also consume the machine-readable install contract at [`docs/agent-install.json`](agent-install.json). Treat it as the canonical checklist for install, verify, connect, safe-write policy, scope policy, and success reporting.

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

Use one explicit machine-local database by default. For a repo-scoped setup, a convenient path is:

```text
.deep-memory/deep-memory.db
```

For a cross-repo user/profile setup, use a shared path such as:

```text
~/.deep-memory/deep-memory.db
```

The important invariant is that every agent points at the same chosen database, while `scope` and `scope_id` keep records bounded.

Create it once:

```bash
uv run deep-memory verify-install ~/.deep-memory/deep-memory.db --json
```

The verifier initializes or opens the database, writes a recognizable smoke-test memory, searches it back by `scope`/`scope_id`, cleans up the smoke record, checks that the MCP module is importable, and returns non-zero with structured errors if any step fails.

## 4. Search before work

Before a large task, search for relevant project conventions:

```bash
uv run deep-memory search .deep-memory/deep-memory.db "repo conventions for this task" \
  --scope project \
  --scope-id deep-memory
```

Keep the result short. Only pass the few memories that matter into the agent prompt.

## 5. Write only verified memory

After tests, review, or user confirmation, write only durable facts or reusable procedures:

```bash
uv run deep-memory add .deep-memory/deep-memory.db \
  "Workflow: run uv run pytest -q before review" \
  --kind procedural \
  --scope project \
  --scope-id deep-memory \
  --importance 0.8
```

`scope` is the fixed layer (`global`, `user`, `tenant`, `workspace`, or `project`). `scope_id` is the custom namespace under that layer, such as a project name.

Do not store secrets, raw credentials, auth cookies, or temporary task status.

## 6. Connect by agent type

MCP and skills solve different layers of the problem:

- MCP is the tool-call entry point. It lets an agent invoke `deep-memory` operations such as search, add, stats, and conflict review.
- A skill, `CLAUDE.md`, or `AGENTS.md` is the behavior policy. It tells the agent when to search, what is safe to remember, what must be reviewed, and how to verify writes.

So the default recommendation is not “MCP or skill”. It is MCP plus the reviewed `deep-memory-agent` skill or equivalent local policy.

### Claude Code

```bash
deep-memory mcp-config --agent claude --db ~/.deep-memory/deep-memory.db
```

This prints a reviewable command example:

```bash
claude mcp add deep-memory -- deep-memory-mcp --db ~/.deep-memory/deep-memory.db
```

Add a short policy note to `CLAUDE.md`:

```markdown
Before large tasks, search deep-memory for relevant project conventions.
After verified success, add only durable facts or reusable procedures.
Never store secrets, raw credentials, or temporary issue status.
```

Claude Code uses MCP for the `deep-memory` tools. `CLAUDE.md` provides the operating strategy and review boundaries.

### Generic MCP JSON

```bash
deep-memory mcp-config --agent generic --db ~/.deep-memory/deep-memory.db --json
```

This prints the same MCP launch shape as machine-readable JSON with `command`, `args`, `env`, and `notes` fields. Use this when an agent expects a custom MCP config format, or when you want to inspect the generated command before adapting it.

### Hermes

```bash
deep-memory mcp-config --agent hermes --db ~/.deep-memory/deep-memory.db
```

This prints a reviewable `config.yaml` snippet:

```yaml
mcp_servers:
  deep_memory:
    command: "deep-memory-mcp"
    args: ["--db", "~/.deep-memory/deep-memory.db"]
    timeout: 30
```

For Hermes, also install the reviewed `deep-memory-agent` skill when the user wants consistent memory behavior across sessions. Installation should be explicit and profile-scoped; do not let `deep-memory` write directly into another Hermes profile's skills directory.

Safe installation options after review include:

```bash
# Install from a published skill URL or registry id when available.
hermes skills install <skill-id-or-url>

# Or manually place the reviewed candidate in the active profile's skills tree.
mkdir -p ~/.hermes/profiles/<profile>/skills/memory/deep-memory-agent
cp skill-candidates/deep-memory-agent/SKILL.md \
  ~/.hermes/profiles/<profile>/skills/memory/deep-memory-agent/SKILL.md
```

A Hermes agent can also ask its local `skill_manage` tool to create or patch a skill in its own active profile, but only after review. It should not bypass profile boundaries or write to another profile's skills unless the user explicitly requests that.

Hermes can also import explicit facts JSONL:

```bash
uv run deep-memory hermes-import .deep-memory/deep-memory.db /tmp/hermes-session.jsonl
```

### Codex

Codex can use MCP when the environment exposes a compatible MCP client. If that path is not available, use a wrapper pattern and keep the same behavior policy in `AGENTS.md` or the task prompt:

```bash
MEMORY_DB=.deep-memory/deep-memory.db
uv run deep-memory search "$MEMORY_DB" "repo conventions for this task" --scope project --scope-id deep-memory
```

After the task, write back only what survived verification:

```bash
uv run deep-memory add "$MEMORY_DB" \
  "Workflow: for this repo, run uv run pytest -q and uv run ruff check . before review" \
  --kind procedural \
  --scope project \
  --scope-id deep-memory \
  --importance 0.8 \
  --source codex:manual
```

Codex needs the same policy boundary even when it uses wrappers: search before large work, write only verified durable records, and never store secrets or transient task status.

### OpenCode

OpenCode follows the same split: use MCP if available for tool access, and use `AGENTS.md` or a reviewed skill-like policy for behavior. If MCP is not configured, use the wrapper commands above with an explicit `MEMORY_DB`.

### OpenClaw-style tools

For OpenClaw-style agents, treat `deep-memory` as an explicit external tool. Put the policy in the agent's project instructions, then either connect MCP or call the CLI wrapper from the task loop.

## 7. Skill review and installation policy

`skill-candidates/deep-memory-agent/SKILL.md` is a candidate, not an auto-installed runtime artifact.

Review before installation:

1. Check frontmatter and description.
2. Confirm it says when to search, when to write, and when not to remember.
3. Confirm it forbids secrets, raw transcripts, raw PII, stale task IDs, PR numbers, issue numbers, commit SHAs, and unverified speculation.
4. Confirm its database path and `scope` / `scope_id` examples match the user's setup.
5. Install only into the active profile or project instruction location that the user approved.
6. Run a smoke test: search, add a temporary verified procedural memory, search it back, then delete or keep it according to the review plan.

This boundary is intentional. MCP can expose powerful write tools; the skill/policy layer is what prevents broad, stale, or unsafe memory writes.

## 8. Check the local WebUI

```bash
uv run deep-memory webui .deep-memory/deep-memory.db --host 127.0.0.1 --port 8765
```

The WebUI is local only by default. Use it to inspect, edit, soft-delete, export, or hard-delete records.
