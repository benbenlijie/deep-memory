# deep-memory sync patterns

`deep-memory` stays local-first: the database lives on your machine and there is no hosted sync service. Cross-machine portability is handled through explicit export/import bundles and storage patterns you control.

## Portable bundle format

Use:

```bash
deep-memory export .deep-memory/deep-memory.db --portable --output .deep-memory/export
```

The output directory contains:

- `memories.jsonl` — one JSON object per portable memory record.
- `manifest.json` — bundle metadata:
  - `schema_version`
  - `record_count`
  - `checksum`
  - `exported_at`
  - `records_file`

Import with merge semantics:

```bash
deep-memory import .deep-memory/deep-memory.db .deep-memory/export --merge
```

Merge behavior:

- exact duplicates are deduplicated by an idempotency key derived from content hash + scope boundary;
- competing records in the same semantic family are resolved by trust level first, then newer `event_time`;
- old portable schema versions are upgraded during import when possible;
- unsupported future schema versions fail fast instead of silently corrupting data.

## 1. Git pattern

Best for developers who already move dotfiles and project state through git.

Recommended layout:

```text
.deep-memory/
  deep-memory.db
  export/
    manifest.json
    memories.jsonl
```

Workflow:

```bash
# Machine A
deep-memory export .deep-memory/deep-memory.db --portable --output .deep-memory/export
git add .deep-memory/export
git commit -m "sync deep-memory export"
git push

# Machine B
git pull
deep-memory import .deep-memory/deep-memory.db .deep-memory/export --merge
```

You can also version the live `.deep-memory/` directory, but the portable export is safer for review and cross-version upgrades because it is text-based JSONL plus a manifest.

Conflict handling:

```bash
deep-memory diff laptop.db desktop.db
```

Review `only_in_a`, `only_in_b`, and `conflicts` before choosing which DB to export/import.

## 2. Dropbox / iCloud / synced-folder pattern

Best when you want automatic file transfer but still want local-first ownership.

Recommended approach:

1. Keep the live SQLite DB outside the synced folder when possible.
2. Put only portable exports in Dropbox/iCloud.
3. Optionally symlink the export directory:

```bash
mkdir -p ~/Dropbox/deep-memory-export
ln -s ~/Dropbox/deep-memory-export .deep-memory/export
```

Then run:

```bash
deep-memory export .deep-memory/deep-memory.db --portable --output .deep-memory/export
deep-memory import .deep-memory/deep-memory.db .deep-memory/export --merge
```

Avoid writing to the same SQLite DB from two machines through a file-sync provider. SQLite is robust locally, but cloud conflict copies can produce divergent databases. If conflict copies appear, compare them with `deep-memory diff <db1> <db2>`, export the winner or both, then merge through portable import.

## 3. Manual pattern

Best for air-gapped machines, cautious users, and periodic backups.

Machine A:

```bash
deep-memory export .deep-memory/deep-memory.db --portable --output deep-memory-portable
zip -r deep-memory-portable.zip deep-memory-portable
```

Transfer `deep-memory-portable.zip` by USB, scp, or any secure channel.

Machine B:

```bash
unzip deep-memory-portable.zip
deep-memory import .deep-memory/deep-memory.db deep-memory-portable --merge
```

Before importing into an important DB, you can inspect the bundle:

```bash
cat deep-memory-portable/manifest.json
head deep-memory-portable/memories.jsonl
```

## Operational recommendations

- Prefer portable text exports over direct DB sync for cross-version compatibility.
- Run `deep-memory diff` before destructive cleanup or after a long period of divergence.
- Treat `.deep-memory/export/` as user-controlled data: do not commit secrets, raw PII, or private transcripts unless you intentionally want them in git or synced storage.
- Keep backups before first-time large imports.
