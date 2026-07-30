# P1 cross-agent integration smoke transcript — 2026-07-23

Environment: home server checkout `/home/ben/open-source/deep-memory`, invoked from the Hermes worker through `ssh webserver 'ssh home "cd /home/ben/open-source/deep-memory && ..."'`.

## MCP stdio client smoke

Command:

```bash
PATH=/home/ben/.hermes/bin:/home/ben/.local/bin:$PATH \
  uv run pytest tests/test_mcp_client_smoke.py -q
```

Observed output:

```text
.                                                                        [100%]
```

What this proves:

- A real MCP stdio client (`mcp.ClientSession` + `mcp.client.stdio.stdio_client`) can launch `python -m deep_memory.mcp_server`.
- `list_tools` discovers at least `add`, `search`, and `stats`.
- `add` accepts `scope=project` and `scope_id=mcp-client-smoke`.
- `search` with the same scope finds the written record.
- `stats` reports `semantic: 1` and `total: 1` for the smoke DB.

This is protocol/client smoke, not a full runtime smoke for Hermes, Claude Code, Codex, OpenCode, or OpenClaw.

## Hermes MCP config generation smoke

Command:

```bash
PATH=/home/ben/.hermes/bin:/home/ben/.local/bin:$PATH \
  uv run deep-memory mcp-config --agent hermes --db .deep-memory/deep-memory.db
```

Observed output:

```yaml
# Review this snippet, then add it to the chosen Hermes profile config.yaml if correct.
# deep-memory does not modify user configuration files.
mcp_servers:
  deep_memory:
    command: "deep-memory-mcp"
    args: ["--db", ".deep-memory/deep-memory.db"]
    timeout: 30
```

Public Hermes documentation checked in this pass says Hermes reads MCP config from `~/.hermes/config.yaml` under `mcp_servers`, supports stdio keys `command`, `args`, `env`, `timeout`, and prefixes registered MCP tools as `mcp_<server>_<tool>`.

Status: config snippet generation is verified. Full Hermes runtime discovery remains pending because the target host does not have `hermes` on `PATH`.

## Codex wrapper smoke

Command:

```bash
PATH=/home/ben/.hermes/bin:/home/ben/.local/bin:$PATH \
TMPDIR=$(mktemp -d) && \
DB=$TMPDIR/codex.db && FACTS=$TMPDIR/facts.jsonl && \
uv run deep-memory init $DB >/tmp/dm_init.out && \
printf '%s' '{"session_id":"codex_smoke","facts":[{"content":"Wrapper smoke succeeded after child exit","kind":"semantic","importance":0.7,"source":"codex:smoke"}]}' > $FACTS && \
uv run deep-memory codex-run --db $DB --task "Check wrapper smoke" --facts-out $FACTS -- true && \
uv run deep-memory search $DB "wrapper smoke"
```

Observed output excerpt:

```text
imported 1 Codex fact into /tmp/tmp.c4kNYeGDns/codex.db
score=0.4922 scope=global scope_id= kind=semantic content=Wrapper smoke succeeded after child exit
```

Status: wrapper function smoke is verified without the Codex CLI. Full Codex runtime smoke remains pending because the target host does not have `codex` on `PATH`.

## Runtime CLI availability on target host

Command:

```bash
for c in hermes codex claude opencode openclaw; do
  echo CMD:$c
  command -v $c || echo missing
done
```

Observed output:

```text
CMD:hermes
missing
CMD:codex
missing
CMD:claude
missing
CMD:opencode
missing
CMD:openclaw
missing
```

Status consequence:

- Hermes: config generation and protocol assumptions documented; runtime discovery pending.
- Codex: wrapper smoke verified; Codex CLI runtime pending.
- Claude Code: MCP command shape documented; runtime pending.
- OpenCode/OpenClaw: design / pending runtime verification.
