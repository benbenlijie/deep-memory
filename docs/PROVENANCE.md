# Provenance and bi-temporal memory

Deep-memory stores two different timelines for every memory record:

1. `event_time` — when the fact was true or the event happened.
2. `learned_at` — when deep-memory learned and wrote the record.

`created_at` remains for backwards compatibility and is currently synonymous with `learned_at`. New records also keep `updated_at` for storage mutations such as access counts, conflict resolution, or metadata edits.

## Record fields

- `event_time`: fact/event time. Defaults to the write time for manual `add` calls. Hermes imports infer it from session metadata such as `timestamp`, `created_at`, or `session_timestamp` when present.
- `learned_at`: write time. Defaults to the same value as `created_at`.
- `valid_until`: exclusive end of the fact-validity interval. `NULL` means the record remains valid indefinitely.

Legacy databases without these columns are migrated in place. Old rows get `event_time = created_at` and `learned_at = created_at`, so existing records remain searchable and auditable.

## As-of queries

Use `--as-of` to ask what the memory store believed was valid at a point in event time:

```bash
uv run deep-memory search memory.db "用户偏好" --as-of 2026-06-01
```

A record is returned only when:

```text
event_time <= as_of AND (valid_until IS NULL OR valid_until > as_of)
```

The `valid_until` comparison is exclusive. If one fact stops being valid exactly at `2026-06-01T00:00:00Z`, it is not returned for an as-of query at that instant.

## `expires_at` vs `valid_until`

`expires_at` and `valid_until` both describe temporal boundaries, but they answer different questions:

| Field | Purpose | Affects | Default | Set by |
|---|---|---|---|---|
| `expires_at` | Cleanup TTL | Garbage collection, lifecycle consolidation | `NULL` (no auto-cleanup) | Manual write or lifecycle policy |
| `valid_until` | Fact validity end | As-of queries, temporal filtering | `NULL` (fact valid forever) | `resolve_conflict` automatically, or manual write |

For example, if a user preference changed last month, the older record might use:

- `valid_until = 2026-05-15` because the fact stopped being true at that point.
- `expires_at = NULL` or `2027-05-15` so the record is still kept for audit, rollback, or explanation.

In other words, `valid_until` controls historical truth; `expires_at` controls storage lifecycle.

## Relationship to conflict chains

Conflict fields (`conflict_status`, `supersedes_id`, `superseded_by_id`) describe the lineage of contradictory or replaced records. They answer “which record replaced which?”

Bi-temporal fields answer a different question: “during which event-time interval was this fact valid?”

When `resolve_conflict(..., confirmed_by_user=True)` supersedes an old record, deep-memory now also sets the old record’s `valid_until` to the resolution time. This preserves the conflict chain while making historical queries precise:

- normal search excludes superseded records by default;
- as-of search can still return the older fact for dates before its `valid_until`;
- future queries return only the replacement record once its own `event_time` is in range.

## Typical audit scenarios

- “What did I know about this project last Tuesday?” Search with `--as-of` for that date.
- “When did a preference change?” Inspect the newer record’s `event_time` and the older record’s `valid_until` plus `superseded_by_id`.
- “Was this imported later than the session where it happened?” Compare `learned_at` with `event_time`.

This model keeps the write chronology and the real-world fact chronology separate. That is the small but important distinction that makes memory records debuggable instead of merely append-only.
