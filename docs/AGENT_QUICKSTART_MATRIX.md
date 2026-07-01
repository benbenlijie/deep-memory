# Cross-agent quickstart matrix

This matrix is the short path for wiring `deep-memory` into different agent runtimes as one shared, local memory layer.

The rule is deliberately conservative:

1. Search before meaningful work.
2. Inject only a small relevant memory block.
3. Write back only durable facts or verified procedures.
4. Never store secrets, raw credentials, auth cookies, private keys, raw transcripts, or temporary issue/PR/task status.

## Command status legend

- **Verified runnable in this repo**: the command was exercised locally against the current checkout, or is a direct CLI command exposed by the current package.
- **Design / pending runtime verification**: the command or integration pattern is documented as the intended runtime setup, but was not executed end-to-end against that agent runtime in this pass.

The current package is source-first. Use `uv run ...` from the `deep-memory` checkout unless you have installed a packaged CLI yourself.

## Shared baseline

| Item | Recommendation |
| --- | --- |
| Default DB path | Project-local: `.deep-memory/deep-memory.db` |
| User/profile DB path | Use only when the user explicitly wants cross-project personal memory, for example `~/.hermes/profiles/<profile>/deep-memory.db` |
| Read timing | Before planning, before a large task, or when task scope changes |
| Write timing | After tests, review, command success, or explicit user confirmation |
| Recall size | Small and ranked; usually 3-5 records, never the whole DB |
| Source value | Include producing agent and context, e.g. `claude-code:project`, `hermes:profile`, `codex:manual`, `opencode:manual` |
| Scope model | `scope` is the fixed layer (`global`, `user`, `tenant`, `workspace`, `project`); `scope_id` is the custom namespace such as `deep-memory` |

Verified runnable baseline:

```bash
git clone https://github.com/benbenlijie/deep-memory.git
cd deep-memory
uv sync --extra dev --extra mcp

uv run deep-memory init .deep-memory/deep-memory.db
uv run deep-memory add .deep-memory/deep-memory.db \
  "Project convention: run uv run pytest -q and uv run ruff check . before review" \
  --kind procedural \
  --scope project \
  --scope-id deep-memory \
  --importance 0.8 \
  --source smoke:verified
uv run deep-memory search .deep-memory/deep-memory.db "how do we verify changes?" --scope project --scope-id deep-memory
```

Note: `uv run deep-memory-mcp` requires the optional MCP dependency. If it fails with `MCP support requires the optional dependency`, run `uv sync --extra mcp` in this checkout and retry.

## Quick matrix

| Agent | Best first integration | Current status | Read path | Write path |
| --- | --- | --- | --- | --- |
| Claude Code | MCP server plus `CLAUDE.md` policy | Design / pending runtime verification | MCP `search` before planning or direct tool call | MCP `add` after tests/review/user confirmation |
| Hermes | MCP server or explicit JSONL import | JSONL import implemented; MCP config design / pending runtime verification | MCP search before tool-heavy tasks, or profile/plugin recall later | `hermes-import` from explicit facts JSONL |
| Codex wrapper | `deep-memory codex-run` wrapper | Wrapper MVP implemented; real Codex runtime smoke pending | Wrapper injects bounded `DEEP_MEMORY_CONTEXT` | Wrapper imports explicit `--facts-out` JSONL only after child success |
| OpenCode / OpenClaw-style wrapper | MCP or pre/post CLI wrapper | Design / pending runtime verification | Pre-run `search` or MCP inside the loop | Explicit JSONL/import or manual `add` after checkpoint |

## Claude Code

### Install method

Design / pending runtime verification:

```bash
uv sync --extra dev --extra mcp
claude mcp add deep-memory -- uv --directory /absolute/path/to/deep-memory run deep-memory-mcp
```

Add a short policy to `CLAUDE.md`:

```markdown
Before large tasks, search deep-memory for relevant project conventions.
After verified success, add only durable facts or reusable procedures.
Never store secrets, raw credentials, auth cookies, private keys, raw transcripts, or temporary issue status.
Use the project-local database at .deep-memory/deep-memory.db unless the user chooses another path.
```

### DB path suggestion

- Project memory: `.deep-memory/deep-memory.db`
- User-level private memory: only with explicit user approval; do not generate it from project docs.

### Pre-task search

Verified runnable CLI fallback:

```bash
uv run deep-memory search .deep-memory/deep-memory.db "repo conventions for this task" --scope project --scope-id deep-memory
```

Design / pending runtime verification via MCP:

```text
Use the deep-memory MCP search tool with db_path=.deep-memory/deep-memory.db, query=<task-specific query>, scope=project, scope_id=deep-memory, limit=5.
```

### Post-task write

Verified runnable CLI fallback:

```bash
uv run deep-memory add .deep-memory/deep-memory.db \
  "Workflow: for this repo, run uv run pytest -q and uv run ruff check . before review" \
  --kind procedural \
  --scope project \
  --scope-id deep-memory \
  --importance 0.8 \
  --source claude-code:manual
```

Design / pending runtime verification via MCP:

```text
Use the deep-memory MCP add tool only after tests, review, or explicit user confirmation. Pass scope=project and scope_id=deep-memory for project memory.
```

### Do not store

- Raw Claude Code transcripts or chain-of-thought-like scratch text.
- Secrets, `.env` values, tokens, SSH keys, cookies, or private credentials.
- Temporary branch names, issue numbers, PR numbers, failing intermediate attempts, or stale task status.
- Private user preferences into a team/project DB unless the user asked for that scope.

### Minimal smoke command

Verified runnable:

```bash
TMPDIR=$(mktemp -d)
DB="$TMPDIR/deep-memory.db"
uv run deep-memory init "$DB"
uv run deep-memory add "$DB" "Project convention: run tests before review" --kind procedural --importance 0.8 --source claude-code:smoke
uv run deep-memory search "$DB" "what should happen before review?"
```

## Hermes

### Install method

Design / pending runtime verification for MCP config:

```yaml
mcp_servers:
  deep_memory:
    command: "uv"
    args: ["--directory", "/absolute/path/to/deep-memory", "run", "deep-memory-mcp"]
    timeout: 30
```

Verified runnable import command shape:

```bash
uv run deep-memory hermes-import .deep-memory/deep-memory.db /tmp/hermes-session-facts.jsonl
```

### DB path suggestion

- Project-local for repo work: `.deep-memory/deep-memory.db`
- Hermes profile-level for personal agent memory: `~/.hermes/profiles/<profile>/deep-memory.db`
- Kanban or multi-profile work should keep tenant/profile boundaries explicit with `scope="tenant"` and a concrete `scope_id`. Do not read a global DB by default.

### Pre-task search

Verified runnable CLI fallback:

```bash
uv run deep-memory search .deep-memory/deep-memory.db "Hermes workflow conventions for this task" --scope project --scope-id deep-memory
```

Design / pending runtime verification via MCP:

```text
Before a large tool-heavy task, call the MCP search tool with a task-specific query, scope, and scope_id; inject only the top few relevant records.
```

### Post-task write

Verified runnable JSONL import:

```bash
cat > /tmp/hermes-session-facts.jsonl <<'JSONL'
{"session_id":"s_demo","facts":[{"content":"Workflow: successful procedures should become reviewable skill candidates, not auto-installed skills","kind":"procedural","importance":0.8,"confidence":0.8,"source":"hermes:manual"}]}
JSONL

uv run deep-memory hermes-import .deep-memory/deep-memory.db /tmp/hermes-session-facts.jsonl
```

Verified runnable manual add fallback:

```bash
uv run deep-memory add .deep-memory/deep-memory.db \
  "Project convention: verify docs changes with local link check, pytest, and ruff" \
  --kind procedural \
  --scope project \
  --scope-id deep-memory \
  --importance 0.8 \
  --source hermes:manual
```

### Do not store

- Raw Hermes session logs, full gateway dumps, or Kanban event histories.
- Temporary task progress, task IDs, PR numbers, branch names, or one-off run status.
- Secrets, auth files, gateway tokens, private chat identifiers, or raw PII.
- Cross-profile memories unless the user configured that boundary explicitly.

### Minimal smoke command

Verified runnable:

```bash
TMPDIR=$(mktemp -d)
DB="$TMPDIR/deep-memory.db"
FACTS="$TMPDIR/hermes-facts.jsonl"
uv run deep-memory init "$DB"
cat > "$FACTS" <<'JSONL'
{"session_id":"s_smoke","facts":[{"content":"User prefers concise technical answers","kind":"semantic","importance":0.8,"source":"hermes:smoke"}]}
JSONL
uv run deep-memory hermes-import "$DB" "$FACTS"
uv run deep-memory search "$DB" "what answer style does the user prefer?"
```

## Codex wrapper

### Install method

Verified runnable CLI surface:

```bash
uv run deep-memory codex-run --help
```

Design / pending real Codex runtime verification:

```bash
uv run deep-memory codex-run \
  --db .deep-memory/deep-memory.db \
  --task "Fix the parser tests" \
  --facts-out /tmp/deep-memory-codex-facts.jsonl \
  -- codex exec "Fix the parser tests and write explicit durable facts to /tmp/deep-memory-codex-facts.jsonl only after tests pass"
```

The wrapper MVP injects a bounded `DEEP_MEMORY_CONTEXT` block into the child process environment, runs only the command after `--`, and imports only the explicit JSONL file passed by `--facts-out` after the child exits with status 0.

### DB path suggestion

- Repo-scoped default: `.deep-memory/deep-memory.db`
- Avoid global DB writes from sandboxed or throwaway repos.

### Pre-task search

Verified runnable CLI fallback:

```bash
MEMORY_DB=.deep-memory/deep-memory.db
uv run deep-memory search "$MEMORY_DB" "repo conventions for this Codex task"
```

Verified wrapper behavior by CLI contract, pending full Codex runtime smoke:

```bash
uv run deep-memory codex-run --db .deep-memory/deep-memory.db --task "Inspect parser conventions" -- echo "child command smoke"
```

### Post-task write

Verified runnable manual add fallback:

```bash
uv run deep-memory add .deep-memory/deep-memory.db \
  "Decision: Codex wrapper should import only explicit facts JSONL after a successful child exit" \
  --kind semantic \
  --importance 0.8 \
  --source codex:manual
```

Design / pending real Codex runtime verification through wrapper:

```jsonl
{"session_id":"codex_demo","facts":[{"content":"Workflow: parser changes require parser tests and ruff before review","kind":"procedural","importance":0.8,"confidence":0.8,"source":"codex:facts-out"}]}
```

### Do not store

- Raw Codex stdout/stderr, diffs, `.env`, token files, or sandbox logs.
- Facts from failed or partially completed runs.
- Issue/PR numbers, temporary branches, failing test counts, or short-lived debugging notes.
- Model-generated summaries that lack evidence.

### Minimal smoke command

Verified runnable without Codex dependency:

```bash
TMPDIR=$(mktemp -d)
DB="$TMPDIR/deep-memory.db"
FACTS="$TMPDIR/codex-facts.jsonl"
uv run deep-memory init "$DB"
cat > "$FACTS" <<'JSONL'
{"session_id":"codex_smoke","facts":[{"content":"Wrapper smoke succeeded after child exit","kind":"semantic","importance":0.7,"source":"codex:smoke"}]}
JSONL
uv run deep-memory codex-run \
  --db "$DB" \
  --task "Check wrapper smoke" \
  --facts-out "$FACTS" \
  -- true
uv run deep-memory search "$DB" "wrapper smoke"
```

## OpenCode / OpenClaw-style wrapper

### Install method

Use MCP when the runtime supports it; otherwise use a pre/post wrapper pattern.

Design / pending runtime verification for MCP:

```bash
uv sync --extra dev --extra mcp
# Configure the runtime to launch:
uv --directory /absolute/path/to/deep-memory run deep-memory-mcp
```

Design / pending runtime verification for a generic wrapper:

```bash
MEMORY_DB=.deep-memory/deep-memory.db
uv run deep-memory search "$MEMORY_DB" "repo conventions for this task" > /tmp/deep-memory-context.txt
opencode run "Use the relevant memory context in /tmp/deep-memory-context.txt, then implement the task"
```

For OpenClaw-style tools, use the same structure: pre-run `search`, bounded prompt injection, explicit post-run facts, then `add` or `hermes-import`.

### DB path suggestion

- Workspace-local default: `.deep-memory/deep-memory.db`
- User-level DB only for explicitly personal preferences.
- Long-running TUI sessions should not silently write to memory; make write policy visible in the prompt/config.

### Pre-task search

Verified runnable CLI fallback:

```bash
uv run deep-memory search .deep-memory/deep-memory.db "OpenCode task conventions and safety rules"
```

Design / pending runtime verification via MCP:

```text
Call MCP search inside the agent loop when task scope changes, with limit=5 and an explicit db_path.
```

### Post-task write

Verified runnable manual add fallback:

```bash
uv run deep-memory add .deep-memory/deep-memory.db \
  "Workflow: OpenCode/OpenClaw-style sessions should write memory only at verified checkpoints" \
  --kind procedural \
  --importance 0.8 \
  --source opencode:manual
```

Design / pending wrapper verification:

```bash
uv run deep-memory hermes-import .deep-memory/deep-memory.db /tmp/opencode-explicit-facts.jsonl
```

Use JSONL only when the agent deliberately emitted explicit durable facts with evidence.

### Do not store

- Raw TUI logs, full JSONL transcripts, hidden chain-of-thought, or unreviewed planning notes.
- Provider credentials, shell environment secrets, config tokens, cookies, or private keys.
- Temporary task status, stale branch/PR/issue identifiers, or background progress updates.
- Duplicate records from multiple hooks without a clear source ID.

### Minimal smoke command

Verified runnable without OpenCode/OpenClaw dependency:

```bash
TMPDIR=$(mktemp -d)
DB="$TMPDIR/deep-memory.db"
uv run deep-memory init "$DB"
uv run deep-memory add "$DB" \
  "Workflow: wrapper agents search before work and write only verified durable facts" \
  --kind procedural \
  --importance 0.8 \
  --source opencode:smoke
uv run deep-memory search "$DB" "what should wrapper agents do before work?"
```

## Verification commands for this repository

Run these before review:

```bash
uv run pytest -q
uv run ruff check .
```

For docs changes, also run a local Markdown link check. One minimal local checker is:

```bash
uv run python - <<'PY'
from pathlib import Path
import re
root = Path('.')
missing = []
for md in root.rglob('*.md'):
    if any(part in {'.git', '.venv', '.pytest_cache', '.ruff_cache'} for part in md.parts):
        continue
    text = md.read_text(encoding='utf-8')
    for target in re.findall(r'\[[^\]]+\]\(([^)]+)\)', text):
        if '://' in target or target.startswith('#') or target.startswith('mailto:'):
            continue
        path = target.split('#', 1)[0]
        if not path:
            continue
        if not (md.parent / path).exists():
            missing.append((str(md), target))
if missing:
    for source, target in missing:
        print(f'{source}: missing {target}')
    raise SystemExit(1)
print('markdown links ok')
PY
```

## Scope boundaries

This matrix does not claim that every listed agent has a fully native adapter today. Current truth:

- `deep-memory` CLI add/search/init is implemented.
- MCP server entrypoint exists and requires the `mcp` optional dependency.
- Hermes explicit facts JSONL import is implemented.
- `deep-memory codex-run` wrapper MVP is implemented.
- Claude Code MCP setup, Hermes MCP setup, real Codex runtime smoke, and OpenCode/OpenClaw wrapper flows still need runtime-specific smoke transcripts before being marked fully verified.
