# Scope ID / Project Namespace Redesign Plan

> **For Hermes:** Use Kanban + Loop Engineering to implement this plan task-by-task. This is a breaking new-version redesign: do not preserve legacy `workspace` / `tenant` / `user_id` API compatibility unless a task explicitly says to add a one-time migration for existing local DBs.

**Goal:** Make `deep-memory` support custom project/workspace/user/tenant namespaces cleanly by separating fixed governance scope type from custom scope identity.

**Architecture:** Keep `scope` as a fixed governance layer (`global | user | tenant | workspace | project`) and introduce `scope_id` as the arbitrary user-defined namespace/name under that layer. Remove the old overloaded boundary columns (`workspace`, `tenant`, `user_id`) from the public API and preferred schema. Retrieval filters become `scope + scope_id`, not `workspace + tenant + user_id`.

**Tech Stack:** Python, SQLite, Typer CLI, MCP FastMCP, pytest, ruff.

---

## Root problem

Current implementation treats `scope` as a fixed taxonomy, which is correct for governance, but it uses `workspace`, `tenant`, and `user_id` as separate boundary fields. That makes the common user need awkward:

```json
{
  "scope": "project",
  "workspace": "deep-memory"
}
```

The desired model is:

```json
{
  "scope": "project",
  "scope_id": "deep-memory"
}
```

Meaning: this memory belongs to the `deep-memory` project namespace.

## Non-goals

- Do not make `scope` an arbitrary string.
- Do not keep duplicate public parameters like both `workspace` and `scope_id`.
- Do not add generic `metadata` / `tags` in this iteration unless required by tests.
- Do not preserve old CLI/MCP argument compatibility; this is a clean new-version change.

## New semantic contract

### Fields

- `scope`: fixed visibility / governance layer.
  - Allowed: `global`, `user`, `tenant`, `workspace`, `project`.
- `scope_id`: optional arbitrary namespace string under the selected `scope`.
  - Required for `user`, `tenant`, `workspace`, `project`.
  - Must be `NULL` / omitted for `global`.
- `agent`: remains separate because it describes the writer/runtime, not the retrieval namespace.

### Examples

```python
mem.add("Project convention: use uv run pytest -q", scope="project", scope_id="deep-memory")
mem.search("test command", scope="project", scope_id="deep-memory")
```

```json
{
  "content": "Deep-memory launch uses Zhihu as the first Chinese channel",
  "scope": "project",
  "scope_id": "deep-memory"
}
```

### Retrieval rule

Default search is deliberately namespace-safe. A search should never leak one named project/workspace/user/tenant namespace into another unless the caller explicitly asks for cross-scope retrieval.

- Exact namespace search:
  - If `scope` and `scope_id` are provided, search only that exact `(scope, scope_id)` namespace.
  - Also include `global` records when `include_global=True`.
- Default local search:
  - If neither `scope` nor `scope_id` is provided and `cross_scope=False`, infer `scope="workspace"` and `scope_id=<cwd-derived workspace>`.
  - This preserves the useful local-default behavior without keeping the old `workspace` public argument.
- Cross-scope search:
  - Use `cross_scope=True`, not `cross_workspace=True`.
  - `cross_scope=True` means search all non-global scoped memories across `user`, `tenant`, `workspace`, and `project` namespaces.
  - It still includes `global` records by default when `include_global=True`.
  - `cross_scope=True` must not require or infer `scope_id`.
- Global search:
  - Direct `scope="global"` searches only global records and must ignore/reject `scope_id`.
  - `global` records are otherwise included only when `include_global=True`.
- Strict isolation:
  - `include_global=False` means no global records are returned unless the direct requested scope is `global`.
  - `scope="project", scope_id="deep-memory"` must not return `scope="project", scope_id="other-project"`.

### Validation rule

- `scope` must be one of the fixed values: `global`, `user`, `tenant`, `workspace`, `project`.
- `scope="global"` rejects non-empty `scope_id`.
- `scope in {"user", "tenant", "workspace", "project"}` requires non-empty `scope_id`.
- Python and CLI may infer `scope_id` from cwd only when all are true:
  - caller omitted both `scope` and `scope_id`, or explicitly requested `scope="workspace"` without `scope_id`;
  - `cross_scope=False`;
  - the operation is `add` or `search`.
- MCP should prefer explicit `scope_id`; if inference exists there, it must be documented as server-cwd inference and treated as a convenience, not as the canonical project API.
- `scope_id` should be stored as the exact caller-provided namespace string after trimming surrounding whitespace. Do not basename arbitrary explicit paths; only cwd inference may use basename if that is the existing product decision.
- Error messages must teach the model: “scope is a fixed layer; use scope_id for custom names such as project names.”

## Files likely affected

Implementation should treat these as acceptance-surface files, not as an exhaustive grep result.

Core model and retrieval:

- `src/deep_memory/core.py`
  - `MemoryRecord`: replace `workspace`, `tenant`, `user_id` boundary fields with `scope_id`.
  - Schema creation / rebuild / migration: preferred schema has `scope TEXT` + `scope_id TEXT`; old boundary columns are migration inputs, not ongoing public model fields.
  - `_row_to_record`: emits `scope_id` and no longer requires boundary-specific columns in the steady-state schema.
  - `add`, `search`, `_scope_filter_sql`, `scope_distribution`, `promote_scope`.
  - Vector, FTS, supplement, and fallback retrieval paths must all use the same scope filter semantics.

Public API surfaces:

- `src/deep_memory/mcp_server.py`
  - MCP `add` and `search` expose `scope_id` and `cross_scope`.
  - Remove public `workspace`, `tenant`, `user_id`, `cross_workspace` arguments.
- `src/deep_memory/cli.py`
  - `add`, `search`, `scope promote`, `scope demote`, `scope list` use `--scope-id` and `--all-scopes` / `cross_scope` naming.
  - `scope list` table columns become `scope`, `scope_id`, `count`.
- Python API / package exports wherever `DeepMemory.add`, `DeepMemory.search`, or `build_idempotency_key` are documented or wrapped.

Adapters and import/export:

- `src/deep_memory/adapters/hermes.py`
- `src/deep_memory/adapters/agent_wrapper.py`
- `src/deep_memory/portable.py`
  - Portable identity/dedupe must key on `(scope, scope_id, content/idempotency)` rather than `(scope, workspace, tenant, user_id, ...)`.

Tests:

- `tests/test_scope_idempotency.py`
- `tests/test_core.py`
- `tests/test_mcp_server.py`
- `tests/test_hermes_adapter.py`
- `tests/test_portable_sync.py`
- `tests/test_embedding_backfill.py`

Docs:

- `README.md`
- `README.zh-CN.md`
- `docs/AGENT_INSTALL_GUIDE.md`
- `docs/AGENT_QUICKSTART_MATRIX.md`

## Migration boundary

This is a clean new-version redesign, but existing local SQLite databases may still exist. Treat compatibility as a one-time data migration, not as public API compatibility.

- Preferred steady-state table:

```sql
scope TEXT NOT NULL DEFAULT 'global'
scope_id TEXT
```

- Preferred invariant:

```text
(scope = 'global' AND scope_id IS NULL)
OR
(scope IN ('user', 'tenant', 'workspace', 'project') AND scope_id IS NOT NULL AND scope_id != '')
```

- One-time migration from older DBs:

```text
scope == 'workspace' -> scope_id = workspace
scope == 'project'   -> scope_id = workspace   # old implementation used workspace as project namespace carrier
scope == 'tenant'    -> scope_id = tenant
scope == 'user'      -> scope_id = user_id
scope == 'global'    -> scope_id = NULL
```

- If the old DB has no boundary columns, existing records remain `scope='global', scope_id=NULL` unless a previous `scope` value says otherwise.
- After migration/rebuild, normal code should no longer read or write `workspace`, `tenant`, or `user_id` columns.
- No old CLI/MCP/Python public parameters should remain as accepted aliases unless a future task explicitly chooses a transitional compatibility layer.

## Task graph

1. Core schema/model redesign.
2. Retrieval/filtering redesign.
3. MCP/CLI/Python API surface redesign.
4. Adapters/portable/docs cleanup.
5. Full verification and release-gate cleanup.

---

## Implementer-ready acceptance checklist

### A. Field semantics

- [ ] `scope` remains a closed taxonomy: `global | user | tenant | workspace | project`.
- [ ] `scope_id` is the only custom namespace field for non-global memories.
- [ ] `agent` remains orthogonal to namespace filtering.
- [ ] `workspace`, `tenant`, and `user_id` are removed from preferred public API payloads, docs, CLI flags, MCP tool signatures, and `MemoryRecord` steady-state semantics.
- [ ] Error messages reject arbitrary `scope` values and point users to `scope_id` for custom names.

### B. Storage and migration

- [ ] New or rebuilt DB schema stores `scope` and `scope_id`.
- [ ] Old boundary columns are used only to compute `scope_id` during one-time migration.
- [ ] Migration maps old `workspace`, `tenant`, and `user_id` into `scope_id` according to the migration boundary above.
- [ ] Global records store `scope_id=NULL`.
- [ ] Non-global records cannot be inserted with empty `scope_id` after validation.

### C. Add APIs

- [ ] Python: `DeepMemory.add(..., scope="project", scope_id="deep-memory")` works.
- [ ] CLI: `deep-memory add DB "..." --scope project --scope-id deep-memory` works.
- [ ] MCP: `add(content="...", scope="project", scope_id="deep-memory")` works.
- [ ] Default add without namespace still creates a workspace-scoped memory with inferred `scope_id`.
- [ ] `scope="global"` with any non-empty `scope_id` fails with a teaching error.

### D. Search APIs

- [ ] Python: `search(query, scope="project", scope_id="deep-memory")` returns that project namespace plus global when `include_global=True`.
- [ ] CLI exposes `--scope`, `--scope-id`, `--include-global/--no-include-global`, and `--all-scopes` or equivalent `cross_scope` naming.
- [ ] MCP exposes `scope`, `scope_id`, `include_global`, and `cross_scope`.
- [ ] `cross_workspace` is removed or renamed everywhere to `cross_scope`.
- [ ] Search with no `scope`/`scope_id` infers local `workspace` namespace unless `cross_scope=True`.
- [ ] `include_global=False` strictly excludes global results from non-global searches.
- [ ] Direct `scope="global"` search returns global records only.

### E. Isolation tests

- [ ] `project:deep-memory` does not return `project:other-project` by default.
- [ ] `workspace:repo-a` does not return `workspace:repo-b` by default.
- [ ] `tenant:acme` does not return `tenant:other` by default.
- [ ] `user:ben` does not return `user:ada` by default.
- [ ] `cross_scope=True` returns non-global memories across all scope types when requested.
- [ ] Global inclusion/exclusion behavior is tested for exact namespace search and cross-scope search.

### F. Retrieval path consistency

- [ ] FTS search uses the new scope filter.
- [ ] Vector search uses the new scope filter.
- [ ] Hybrid search uses the new scope filter.
- [ ] Supplement/fallback result filling uses the same scope filter.
- [ ] Retrieval logging still records returned IDs and caller without changing namespace semantics.

### G. Promotion, demotion, listing

- [ ] `promote_scope(record_id, to="project", scope_id="deep-memory")` moves the record into that namespace.
- [ ] CLI `scope promote` / `scope demote` use `--scope-id` rather than boundary-specific flags.
- [ ] `scope list` groups by `scope, scope_id`.
- [ ] Global promotion clears `scope_id`.

### H. Portable/adapters/docs

- [ ] Portable import/export serializes `scope_id`.
- [ ] Portable dedupe identity no longer depends on `workspace`, `tenant`, or `user_id`.
- [ ] Hermes adapter and agent wrapper pass `scope_id` through correctly.
- [ ] README and MCP docs show `scope="project", scope_id="deep-memory"` as the canonical custom project example.
- [ ] Docs explicitly say: `scope` is the governance layer; `scope_id` is the custom namespace.

### I. Verification commands

- [ ] `uv run pytest tests/test_scope_idempotency.py -q`
- [ ] `uv run pytest tests/test_mcp_server.py -q`
- [ ] `uv run pytest tests/test_core.py -q`
- [ ] `uv run pytest tests/test_hermes_adapter.py tests/test_portable_sync.py tests/test_embedding_backfill.py -q`
- [ ] `uv run pytest -q`
- [ ] `uv run ruff check .`

## Acceptance criteria

- Custom project namespace works through Python, CLI, and MCP:

```text
scope="project", scope_id="deep-memory"
```

- Old public arguments are gone from the preferred API and docs:

```text
workspace=..., tenant=..., user_id=...
```

- No new redundant compatibility layer remains.
- Tests prove namespace isolation: `project:deep-memory` does not leak into `project:other-project` by default.
- Tests prove global inclusion behavior.
- `uv run pytest -q` passes.
- `uv run ruff check .` passes.
- README and MCP docs explain: `scope` is the layer, `scope_id` is the custom namespace.
