# Release gate: MCP + skill-layer story end-to-end

Date: 2026-07-02
Kanban task: `t_fef93505`
Workspace under test: clean snapshot copied to `/tmp/deep-memory-release-gate-t_fef93505.BH08kq/repo`

## Goal

Verify the skill-layer changes after the MCP/product-story update, end to end:

1. Install from a clean workspace with `uv sync --extra dev --extra mcp`.
2. Initialize `~/.deep-memory/deep-memory.db`.
3. Add and search a procedural memory.
4. Export a review-only skill candidate or verify the checked-in skill pack documentation.
5. Confirm candidates do not auto-install into active Hermes skill directories.
6. Confirm the MCP server still imports and starts.
7. Confirm README, `AGENT_INSTALL_GUIDE`, and `SKILL_ACTIVATION_LOOP` tell the same story.

## Evidence

### 1. Clean install

Command:

```bash
uv sync --extra dev --extra mcp
```

Result: passed in a clean copied workspace. `uv` created `.venv`, built `deep-memory==0.1.0`, and installed the MCP extra (`mcp==1.27.2`).

Note: `uv` warned that the outer Hermes `VIRTUAL_ENV` did not match `.venv`; this is expected and `uv` ignored it.

### 2. Database initialization

Commands:

```bash
export HOME=/tmp/deep-memory-release-gate-t_fef93505.BH08kq/home
DB="$HOME/.deep-memory/deep-memory.db"
uv run deep-memory init "$DB"
```

Result: passed. Database initialized at:

```text
/tmp/deep-memory-release-gate-t_fef93505.BH08kq/home/.deep-memory/deep-memory.db
```

### 3. Procedural memory add/search

Command:

```bash
uv run deep-memory add "$DB" \
  'When a Kanban worker exits without kanban_complete or kanban_block, inspect prior runs, avoid repeating the path, and finish with a structured block or completion.' \
  --kind procedural \
  --scope project \
  --scope-id release-gate \
  --source release-gate:test

uv run deep-memory search "$DB" 'kanban worker structured completion' \
  --scope project \
  --scope-id release-gate \
  --limit 5
```

Result: passed. Added record:

```text
3d1c402f-c99b-440e-97b1-241b472888b9
```

Search returned the procedural memory with score `0.4647`, scope `project`, and `scope_id=release-gate`.

### 4. Skill candidate export

Command:

```bash
uv run deep-memory export-skill "$DB" \
  3d1c402f-c99b-440e-97b1-241b472888b9 \
  --output /tmp/deep-memory-release-gate-t_fef93505.BH08kq/review-candidates/kanban-protocol-recovery/SKILL.md \
  --name kanban-protocol-recovery \
  --evidence 'release gate add/search smoke test found the procedural memory' \
  --recurrence-hint 'Kanban worker protocol violations can recur after provider or dispatcher interruptions'
```

Result: passed. CLI returned:

```json
{
  "candidate_path": "/tmp/deep-memory-release-gate-t_fef93505.BH08kq/review-candidates/kanban-protocol-recovery/SKILL.md",
  "source_memory_id": "3d1c402f-c99b-440e-97b1-241b472888b9",
  "auto_install": false,
  "auto_install_label": "Auto-install: no"
}
```

Candidate inspection found:

```text
name: kanban-protocol-recovery
memory_id: `3d1c402f-c99b-440e-97b1-241b472888b9`
Auto-install: no
install_boundary: `review_required`
Human review checklist
```

### 5. Active Hermes skill directory protection

Command attempted to export directly into an active Hermes profile skill path under the isolated test `HOME`:

```bash
uv run deep-memory export-skill "$DB" "$ID" \
  --output "$HOME/.hermes/profiles/demis-research/skills/memory/kanban-protocol-recovery/SKILL.md" \
  --name kanban-protocol-recovery
```

Result: correctly blocked with exit code `2`:

```text
Invalid value: --output must be a review directory, not an active Hermes skills directory
```

No file was created under `$HOME/.hermes` in the isolated test home.

### 6. MCP import/start smoke

Commands:

```bash
uv run python - <<'PY'
import deep_memory.mcp_server as m
print('import_ok', m.__name__)
print('has_main', callable(getattr(m, 'main', None)))
PY

timeout 2s uv run deep-memory-mcp
```

Result:

```text
import_ok deep_memory.mcp_server
has_main True
mcp_timeout_rc=0
```

The MCP module imports, exposes `main`, and the CLI entrypoint can start without an immediate crash.

### 7. Documentation story consistency

A direct substring check passed across:

```text
README.md
README.zh-CN.md
docs/AGENT_INSTALL_GUIDE.md
docs/AGENT_INSTALL_GUIDE.zh-CN.md
docs/SKILL_ACTIVATION_LOOP.md
skill-candidates/deep-memory-agent/SKILL.md
```

The checked story is:

- MCP is a tool-call protocol/entry point, not the whole product.
- The skill layer is a behavior policy layer.
- Procedural memories become reviewable skill candidates.
- Candidates are not auto-installed.
- Safe promotion path is evidence → candidate → reviewer gate → explicit installation through normal skill-management.

### 8. Regression suite

Targeted tests:

```bash
uv run pytest tests/test_skill_export.py \
  tests/test_skill_activation_loop_docs.py \
  tests/test_agent_install_guide_docs.py \
  tests/test_mcp_server.py
```

Result:

```text
20 passed in 2.77s
```

Full suite:

```bash
uv run pytest
```

Result:

```text
189 passed, 2 skipped in 89.92s
```

Lint and whitespace checks:

```bash
uv run ruff check .
git diff --check
```

Result:

```text
All checks passed!
```

## Evaluation

Pass.

The release-gate path proves the new skill-layer story is not just documentation copy:

- clean install with MCP extras works;
- local database init works;
- procedural memory add/search works;
- procedural memory can be exported as a review-only skill candidate;
- direct export into active Hermes skill paths is blocked;
- MCP server still imports and starts;
- docs and checked-in candidate skill agree on the review-first boundary;
- targeted and full tests pass.

## Remaining boundary

This gate used a clean local snapshot instead of a fresh remote clone because the task workspace is a shared local repo with uncommitted worker changes. That still validates install/runtime behavior from a clean copied workspace. A final public-release gate may additionally run the same commands from a fresh GitHub clone after these changes are committed and pushed.
