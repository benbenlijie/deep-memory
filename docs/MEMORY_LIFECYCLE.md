# Memory Lifecycle

`deep-memory` keeps memory useful by treating records as lifecycle-managed state, not an append-only log. The lifecycle loop has three signals:

1. access tracking: every search hit increments `access_count` and updates `last_accessed_at`;
2. kind-specific decay: default half-lives are `working=7d`, `episodic=30d`, `semantic=180d`, and `procedural=365d`;
3. consolidation: highly similar active records are merged into a summary record and originals are archived.

## Trigger policy

Manual trigger:

```bash
uv run deep-memory consolidate --dry-run .deep-memory/deep-memory.db
uv run deep-memory consolidate .deep-memory/deep-memory.db
```

Automatic trigger is intentionally conservative. A host agent may run consolidation when the active record count exceeds a configured threshold `auto_consolidate_after` (default: 1000). It should first run a dry-run and surface the candidate groups if the operation would affect many records.

## Consolidation rule

The default candidate rule is token-overlap similarity greater than `0.6` among active records of the same memory kind. Records already marked `deprecated`, `superseded`, or `archived` are excluded.

For each candidate group:

- create one summary memory with the same kind;
- set summary `importance` to the maximum importance in the group;
- set summary `confidence` to the group average;
- write source provenance as `consolidated from <ids>`;
- mark original records as `archived` and point `superseded_by_id` at the summary.

`--dry-run` returns the same candidate groups but does not create summary rows and does not archive anything.

## Irreversible or high-risk operations

The following operations should be treated as requiring extra caution:

- running consolidation without `--dry-run` on a production database;
- changing archived originals back to active after downstream agents may have relied on the summary;
- physically deleting records with `hard-delete`;
- lowering the similarity threshold far below `0.6`, which can merge unrelated memories;
- running automatic consolidation without inspecting affected counts.

Archived records remain in the local database for audit/export when explicitly requested, but they are excluded from default search and export paths.

## Backups and retention

Destructive operations create a local SQLite copy before modifying the database:

- schema rebuilds triggered by `_rebuild_memories_table()`;
- `consolidate` when run without `--dry-run` and with candidate groups;
- `hard-delete`.

Backups live next to the database in `<db_path>.backups/` and use the name `deep-memory.db.bak-YYYYMMDD-HHMMSS` (or the current DB filename with the same suffix). Each backup has a sidecar manifest named `<backup>.manifest.json` with:

- `created_at`;
- `trigger_reason`;
- `source_db_size`;
- `record_count`.

The default retention TTL is 7 days. Override it with `DEEP_MEMORY_BACKUP_TTL_DAYS` or with the programmatic `DeepMemory(..., backup_retention_days=...)` option. Set the TTL to `0` in development to skip backup creation.

DeepMemory lazily prunes expired backups on startup using backup file `mtime`, so old backup directories do not grow without bound. You can also run manual pruning:

```bash
uv run deep-memory prune-backups --dry-run
uv run deep-memory prune-backups .deep-memory/deep-memory.db
```

If backup creation fails (for example disk full or permission denied), the destructive operation aborts before modifying the original DB. It is intentionally not allowed to continue after a failed required backup.