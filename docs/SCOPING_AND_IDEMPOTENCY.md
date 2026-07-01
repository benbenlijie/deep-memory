# Scoping and idempotency model

`deep-memory` is moving from single-agent local memory toward a cross-agent memory substrate. The root problem is not only search quality; it is boundary control: the same fact can be written by multiple adapters, and memories from one project, workspace, tenant, or user can contaminate another agent's context if retrieval has no explicit namespace model.

## Scope model

The current model separates governance from naming:

```text
scope     = fixed visibility / governance layer
scope_id  = custom namespace inside that layer
```

Allowed `scope` values are fixed:

```text
global | user | tenant | workspace | project
```

Examples:

```json
{"scope": "project", "scope_id": "deep-memory"}
{"scope": "workspace", "scope_id": "deep-memory"}
{"scope": "tenant", "scope_id": "acme"}
{"scope": "user", "scope_id": "ben"}
{"scope": "global", "scope_id": null}
```

One-line rule:

> `scope` controls the governance layer; `scope_id` controls the custom project/workspace/user/tenant namespace.

Do not put arbitrary project names directly into `scope`:

```json
{"scope": "deep-memory"}
```

That makes it impossible for retrieval policy to know whether `deep-memory` is a project, user, tenant, workspace, tag, or something else.

## Boundary fields

Primary boundary fields:

- `scope`: fixed governance layer.
- `scope_id`: namespace identifier inside the fixed layer.
- `agent`: adapter/agent identity such as `hermes`, `codex`, `claude-code`, `opencode`.
- `source`: human-readable provenance string, still useful for display and audit, e.g. `hermes:s_123`.
- `idempotency_key`: stable duplicate-prevention key for one adapter-emitted fact inside its boundary.

Schema/indexing uses `scope` + `scope_id` as the namespace pair. Legacy `workspace`, `tenant`, and `user_id` concepts are represented as `scope_id` values under their corresponding fixed `scope`.

## Default write behavior

`DeepMemory.add()` defaults to `scope="workspace"`.

If callers omit `scope_id` for `workspace` scope, the core infers a privacy-preserving namespace from the current working directory. In ordinary repositories this is usually `basename(cwd)`, not the full home path; edge cases such as filesystem roots use a short hash fallback.

Examples:

```python
mem.add("Project convention: run uv run pytest -q before review")
# => scope="workspace", scope_id inferred from cwd

mem.add("User prefers concise answers", scope="global")
# => visible across projects because the caller explicitly opted in

mem.add("README positioning: shared memory layer", scope="project", scope_id="deep-memory")
# => project-scoped fact under the custom namespace "deep-memory"
```

CLI and MCP follow the same model. `deep-memory add` without `--scope` writes workspace-scoped records; project-specific public examples should prefer `--scope project --scope-id <name>`.

## Retrieval boundary

`DeepMemory.search()` accepts:

- `scope`
- `scope_id`
- `include_global`
- `cross_scope`
- `agent`

Default behavior:

- If `scope` / `scope_id` are omitted and `cross_scope=False`, retrieval uses the current workspace namespace inferred from `cwd`.
- `include_global=True` also includes explicitly global records.
- `include_global=False` excludes global records.
- `cross_scope=False` restricts search to the exact current or provided `scope` + `scope_id` namespace.
- `cross_scope=True` searches across scoped memories; pair it with `include_global=False` when you want only non-global scoped records.
- `agent` narrows results to records with no agent or the matching agent.

Explicit reads:

```python
mem.search("build command")
# current workspace + global

mem.search("build command", include_global=False)
# current workspace only

mem.search("README positioning", scope="project", scope_id="deep-memory", include_global=False)
# only project:deep-memory

mem.search("build command", cross_scope=True)
# all scoped records + global

mem.search("build command", cross_scope=True, include_global=False)
# all scoped records only
```

CLI equivalents:

```bash
uv run deep-memory search .deep-memory/deep-memory.db "build command"
uv run deep-memory search .deep-memory/deep-memory.db "build command" --no-include-global
uv run deep-memory search .deep-memory/deep-memory.db "README positioning" --scope project --scope-id deep-memory --no-include-global
uv run deep-memory search .deep-memory/deep-memory.db "build command" --all-scopes
```

MCP equivalents should use the same shape:

```json
{
  "query": "README positioning",
  "scope": "project",
  "scope_id": "deep-memory",
  "include_global": false
}
```

## Scope promotion and demotion

Use promotion when a namespace-local memory later proves genuinely reusable elsewhere:

```bash
uv run deep-memory scope promote .deep-memory/deep-memory.db <memory-id> --to global
uv run deep-memory scope promote .deep-memory/deep-memory.db <memory-id> --to tenant --scope-id acme
uv run deep-memory scope promote .deep-memory/deep-memory.db <memory-id> --to user --scope-id ben
```

Use demotion when a record was promoted too broadly and needs to be narrowed again:

```bash
uv run deep-memory scope demote .deep-memory/deep-memory.db <memory-id> --to workspace --scope-id repo-a
uv run deep-memory scope demote .deep-memory/deep-memory.db <memory-id> --to tenant --scope-id acme
uv run deep-memory scope demote .deep-memory/deep-memory.db <memory-id> --to user --scope-id ben
```

Audit scope distribution before or after migration:

```bash
uv run deep-memory scope list .deep-memory/deep-memory.db
```

The table/JSON output includes `scope_id` so namespace distribution is inspectable.

## Duplicate policy

`DeepMemory.add()` supports:

- `duplicate_policy="create"`: keep old behavior. This remains the default for manual writes.
- `duplicate_policy="skip"`: if `idempotency_key` exists, return the existing record without creating another row.
- `duplicate_policy="update"`: if `idempotency_key` exists, update the existing row with the new values.

The helper `build_idempotency_key()` hashes normalized content plus kind/source/scope/scope_id/agent. Adapters should normally use `skip` unless they intentionally want revision behavior.

Example:

```python
key = build_idempotency_key(
    "Project convention: run uv run pytest -q before review",
    kind="procedural",
    source="codex:run-123",
    scope="project",
    scope_id="deep-memory",
    agent="codex",
)
mem.add(
    "Project convention: run uv run pytest -q before review",
    kind="procedural",
    source="codex:run-123",
    scope="project",
    scope_id="deep-memory",
    agent="codex",
    idempotency_key=key,
    duplicate_policy="skip",
)
```

## Adapter behavior

Hermes import:

- accepts `scope` and `scope_id` from event-level fields, fact-level fields, or `context`;
- maps legacy event payloads such as `workspace`, `tenant`, or `user_id` into `scope` + `scope_id` for compatibility;
- writes with an idempotency key and `duplicate_policy="skip"`.

Codex wrapper:

- uses the child `cwd` as a workspace `scope_id` when available;
- filters pre-task recall by `scope="workspace"` + that `scope_id`;
- imports explicit facts with scope-aware idempotency.

## Migration guide

Existing databases keep true `scope="global"` records as global. Legacy namespace columns, where present in older databases, are migration inputs into `scope_id` rather than long-term public API fields.

Recommended migration loop:

1. Run `uv run deep-memory scope list .deep-memory/deep-memory.db` to see current distribution.
2. Leave true global memories as global.
3. For newly learned project facts, use `scope="project", scope_id="<project-name>"`.
4. For workspace-local operational facts, rely on default workspace scope or pass `scope="workspace", scope_id="<workspace-name>"` explicitly.
5. If a workspace or project fact later becomes cross-project guidance, promote it explicitly with `scope promote`.
6. Update `CLAUDE.md` / `AGENTS.md` templates to say:

```markdown
Before large tasks, search deep-memory for relevant project conventions.
After verified success, add only durable facts or reusable procedures.
Default writes are workspace-scoped. Use `scope="global"` only for genuinely cross-project facts such as stable user preferences or org-wide coding standards.
Use `scope="project", scope_id="<project-name>"` for named project memories.
Never store secrets, raw credentials, or temporary issue status.
```

## Known edges

- Existing global records remain global until a user edits or re-scopes them.
- Cross-tenant reads should remain deny-by-default unless a future server/API layer adds explicit authorization.
- Workspace inference is intentionally privacy-preserving; if two different directories share the same basename, pass an explicit `scope_id` for stronger separation.
- `scope_id` is a namespace, not a permission boundary by itself. Server/API layers still need authorization checks for multi-user or multi-tenant deployments.
