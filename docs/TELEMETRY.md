# deep-memory telemetry

Telemetry turns retrieval from a black box into a measurable feedback loop. It answers three operational questions:

1. Which searches happened?
2. Which memories were returned, and with what scores?
3. Did the returned memory help the caller?

The goal is not centralized analytics. The database remains local-first; telemetry is stored in the same SQLite database that stores memories.

## Tables

### `retrieval_log`

Each `DeepMemory.search(...)` call writes one row unless telemetry is disabled.

Columns:

- `id`: auto-increment row id.
- `query`: raw search query by default, or `NULL` in hash-only mode.
- `query_hash`: SHA-256 hash of the query, always populated.
- `returned_ids`: JSON array of memory ids returned by the search.
- `scores`: JSON array of retrieval scores aligned with `returned_ids`.
- `caller`: caller boundary, such as `cli`, `mcp`, `wrapper`, or `python`.
- `created_at`: UTC ISO-8601 timestamp.

### `memory_feedback`

Feedback is explicit and user/caller initiated.

Columns:

- `id`: auto-increment row id.
- `memory_id`: memory record id receiving feedback.
- `helpful`: `1` for helpful, `0` for not helpful.
- `note`: optional free-form note.
- `created_at`: UTC ISO-8601 timestamp.

## How search logging works

All search paths use the same core `DeepMemory.search(...)` implementation. The caller can label the boundary:

- CLI search logs `caller="cli"`.
- MCP search logs `caller="mcp"`.
- Adapter wrappers should pass `caller="wrapper"`.
- Direct Python calls default to `caller="python"`.

Telemetry is written after final ranking and after access counters are updated. Empty-result searches are still logged with empty `returned_ids` and `scores`, which lets the report compute hit rate.

## Disable telemetry

Set:

```bash
DEEP_MEMORY_TELEMETRY=off
```

Accepted off values are `off`, `false`, `no`, and `0`.

Example:

```bash
DEEP_MEMORY_TELEMETRY=off deep-memory search .deep-memory/deep-memory.db "用户偏好"
```

## Hash-only query mode

By default, `retrieval_log.query` stores the raw query because it is the most useful mode for local debugging. If queries may contain sensitive content, store only the hash:

```bash
DEEP_MEMORY_TELEMETRY_QUERY=hash
```

In this mode:

- `query` is `NULL`.
- `query_hash` is still populated.
- `returned_ids`, `scores`, `caller`, and `created_at` are unchanged.

This is the safer setting for shared demos, support bundles, or team environments where the SQLite database might be copied.

## Feedback API

CLI:

```bash
deep-memory feedback .deep-memory/deep-memory.db <memory_id> --helpful --note "used in answer"
deep-memory feedback .deep-memory/deep-memory.db <memory_id> --not-helpful --note "stale preference"
```

MCP tool:

```text
memory_feedback(memory_id, helpful: bool, note?: str, db_path?: str)
```

Core Python:

```python
from deep_memory import DeepMemory

mem = DeepMemory(".deep-memory/deep-memory.db")
mem.add_feedback(memory_id, helpful=True, note="used in answer")
```

## Report

CLI:

```bash
deep-memory report .deep-memory/deep-memory.db
```

If no database path is provided, the command defaults to `.deep-memory/deep-memory.db`.

The report is markdown and includes:

- recent retrieval count, defaulting to 7 days;
- hit rate: searches with at least one returned id divided by total searches;
- helpful / not-helpful feedback distribution;
- retrieval growth compared with the previous window;
- score distribution buckets;
- high-usage / low-feedback memory candidates.

## WebUI Insights

The local WebUI now has an `Insights` view:

```bash
deep-memory webui .deep-memory/deep-memory.db
```

Open `http://127.0.0.1:8765/?view=insights`.

It shows the same retrieval-quality signals as the report, optimized for quick local inspection.

## Privacy boundary

Telemetry can improve retrieval quality, but it can also record sensitive intent. The safe operating model is:

- keep the SQLite database local by default;
- disable telemetry when running on especially sensitive tasks;
- use `DEEP_MEMORY_TELEMETRY_QUERY=hash` before sharing databases or support bundles;
- treat `memory_feedback.note` as user-controlled text that may contain sensitive context;
- do not upload telemetry unless the user explicitly opts in.

Hash-only mode is not perfect anonymization. A party with the likely query can recompute the hash. It is best understood as a practical local privacy boundary, not a cryptographic privacy guarantee against dictionary attacks.
