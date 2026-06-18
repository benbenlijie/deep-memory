# Scoping and idempotency model

`deep-memory` is moving from a single-agent local memory record toward a cross-agent record model. The root problem is not search; it is boundary control: the same fact can be written by multiple adapters, and memories from one workspace or tenant can contaminate another agent's context if retrieval has no explicit scope.

## Scope model

The minimal model is:

- `workspace`: the default for new writes. Use it for repo-local build commands, architecture notes, project conventions, adapter facts, and procedural memories learned while working in one directory. When `workspace` is omitted, `DeepMemory.add()` infers a privacy-preserving workspace name from `cwd` (usually `basename(cwd)`, not the full home path).
- `global`: explicit opt-in for genuinely cross-project facts, for example "User prefers concise answers" or "The organization writes Python with Ruff formatting." Do not use it for project status, client facts, temporary task progress, or workspace-only conventions.
- `tenant`: use it when a shared deployment serves a named customer, board, organization, or external namespace. Tenant reads require the caller to provide the matching tenant.
- `user`: use it for facts bound to one user/profile identity when multiple users share a database.
- `project`: retained as a compatibility alias for project/workspace-style boundaries; retrieval treats it like `workspace`.

Boundary fields:

- `workspace`: privacy-preserving project/workspace identifier. For automatic inference, store `basename(cwd)` or a short hash fallback, not the full absolute path.
- `tenant`: external tenant/project namespace.
- `user_id`: local user/profile identity.
- `agent`: adapter/agent identity such as `hermes`, `codex`, `claude-code`, `opencode`.
- `source`: human-readable provenance string, still useful for display and audit, e.g. `hermes:s_123`.
- `idempotency_key`: stable duplicate-prevention key for one adapter-emitted fact inside its boundary.

Indexes added by the schema:

- unique partial index on `idempotency_key` where non-null;
- `scope, workspace` index;
- `tenant, user_id` index;
- `agent` index.

## Default write behavior

`DeepMemory.add()` now defaults to `scope="workspace"`.

If `scope` is `workspace` or `project` and `workspace=None`, the core infers `workspace = _infer_workspace_from_cwd()`. The inference intentionally avoids leaking full paths. In ordinary repositories it returns `basename(cwd)`; in edge cases such as filesystem roots it returns a short hash.

Examples:

```python
mem.add("Project convention: run uv run pytest -q before review")
# => scope="workspace", workspace inferred from cwd

mem.add("User prefers concise answers", scope="global")
# => visible across projects because the caller explicitly opted in
```

CLI and MCP follow the same default. `deep-memory add` without `--scope` writes workspace-scoped records.

## Retrieval boundary

`DeepMemory.search()` accepts `workspace`, `tenant`, `user_id`, `agent`, `include_global`, and `cross_workspace`.

Default behavior:

- `workspace` omitted -> infer current workspace from `cwd`.
- `include_global=True` -> explicitly global records are also visible.
- `cross_workspace=False` -> only the current workspace/project records are visible.
- `tenant` and `user_id` records are visible only when the caller supplies the matching boundary.
- `agent` narrows results to records with no agent or the matching agent.

Explicit broader reads:

```python
mem.search("build command")
# current workspace + global

mem.search("build command", include_global=False)
# current workspace only

mem.search("build command", cross_workspace=True)
# all workspace/project records + global

mem.search("build command", cross_workspace=True, include_global=False)
# all workspace/project records only
```

CLI equivalents:

```bash
uv run deep-memory search .deep-memory/deep-memory.db "build command"
uv run deep-memory search .deep-memory/deep-memory.db "build command" --no-include-global
uv run deep-memory search .deep-memory/deep-memory.db "build command" --all-workspaces
```

## Scope promotion

Use promotion when a workspace memory later proves to be genuinely reusable elsewhere:

```bash
uv run deep-memory scope promote .deep-memory/deep-memory.db <memory-id> --to global
uv run deep-memory scope promote .deep-memory/deep-memory.db <memory-id> --to tenant --tenant acme
uv run deep-memory scope promote .deep-memory/deep-memory.db <memory-id> --to user --user-id ben
```

Use demotion when a record was promoted too broadly and needs to be narrowed again:

```bash
uv run deep-memory scope demote .deep-memory/deep-memory.db <memory-id> --to workspace --workspace repo-a
uv run deep-memory scope demote .deep-memory/deep-memory.db <memory-id> --to tenant --tenant acme
uv run deep-memory scope demote .deep-memory/deep-memory.db <memory-id> --to user --user-id ben
```

Audit scope distribution before or after migration:

```bash
uv run deep-memory scope list .deep-memory/deep-memory.db
```

## Duplicate policy

`DeepMemory.add()` supports:

- `duplicate_policy="create"`: keep old behavior. This remains the default for manual writes.
- `duplicate_policy="skip"`: if `idempotency_key` exists, return the existing record without creating another row.
- `duplicate_policy="update"`: if `idempotency_key` exists, update the existing row with the new values.

The helper `build_idempotency_key()` hashes normalized content plus kind/source/workspace/tenant/user/agent. Adapters should normally use `skip` unless they intentionally want revision behavior.

## Adapter behavior

Hermes import:

- accepts workspace/tenant/user/agent from event-level fields or `context`;
- stores them in first-class fields;
- derives `scope` from the strongest provided boundary;
- writes with an idempotency key and `duplicate_policy="skip"`.

Codex wrapper:

- uses the child `cwd` as workspace when available;
- filters pre-task recall by workspace;
- imports explicit facts with workspace-aware idempotency.

## Migration guide

Existing databases keep existing `scope="global"` records unchanged for backwards compatibility. The schema migration does not try to infer workspace/tenant/user from old free-form `source` strings because doing so would be unsafe.

Recommended migration loop:

1. Run `uv run deep-memory scope list .deep-memory/deep-memory.db` to see current distribution.
2. Leave true global memories as global.
3. For newly learned project facts, rely on default workspace scope.
4. If a workspace fact later becomes cross-project guidance, promote it explicitly with `scope promote`.
5. Update `CLAUDE.md` / `AGENTS.md` templates to say:

```markdown
Before large tasks, search deep-memory for relevant project conventions.
After verified success, add only durable facts or reusable procedures.
Default writes are workspace-scoped. Use `scope="global"` only for genuinely cross-project facts such as stable user preferences or org-wide coding standards.
Never store secrets, raw credentials, or temporary issue status.
```

## Known edges

- Existing global records remain global until a user edits or re-scopes them.
- Cross-tenant reads should remain deny-by-default unless a future server/API layer adds explicit authorization.
- `workspace` inference is intentionally privacy-preserving; if two different directories share the same basename, pass `workspace=` explicitly for stronger separation.
