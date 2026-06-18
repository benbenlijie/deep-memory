# Reproducible adapter smoke transcripts

This document records small, repeatable smoke transcripts for the cross-agent adapter surface.

Principles:
- use a temporary SQLite database for every smoke;
- do not depend on real user data, private tokens, or raw transcripts;
- verify behavior with real commands, not descriptive claims;
- clean up automatically when the smoke exits.

## 1) CLI baseline smoke

Purpose: prove the core CLI flow works end to end with a temporary DB.

Command:

```bash
uv run python scripts/run_adapter_smoke.py
```

Expected output summary:
- `deep-memory init` succeeds on a temp DB;
- `deep-memory add` stores one procedural memory;
- `deep-memory search` returns that smoke procedure.

DB scope:
- temporary SQLite database under a temp directory;
- discarded automatically when the process exits.

Cleanup:
- no manual cleanup required;
- the script uses `tempfile.TemporaryDirectory()`.

## 2) MCP server tool-surface smoke

Purpose: prove the MCP-facing Python helpers share the same DB and can add/search/stats without a live private environment.

Command:

```bash
uv run python scripts/run_adapter_smoke.py
```

Expected output summary:
- `add_memory()` writes one record;
- `search_memory()` finds the same record;
- `memory_stats()` reports `total == 1`.

DB scope:
- temporary SQLite database under a temp directory;
- discarded automatically when the process exits.

Cleanup:
- no manual cleanup required;
- the script closes the database handle explicitly.

## 3) Codex/OpenCode wrapper prototype smoke

Purpose: prove the wrapper pattern injects bounded recall and only imports explicit JSONL facts after child success.

Command:

```bash
uv run python scripts/run_adapter_smoke.py
```

Expected output summary:
- wrapper injects a short `DEEP_MEMORY_CONTEXT` block;
- child writes explicit JSONL facts;
- wrapper imports the facts only after successful child exit.

DB scope:
- temporary SQLite database under a temp directory;
- discarded automatically when the process exits.

Cleanup:
- no manual cleanup required;
- child facts file and prompt capture live in the temp directory only.

## Automation entrypoint

The reusable smoke entrypoint is:

```bash
uv run python scripts/run_adapter_smoke.py
```

It executes all three smoke transcripts in one pass and prints a JSON summary.
