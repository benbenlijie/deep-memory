# Install release gate — 2026-07-02

## Scope

Validate the agent-installable deep-memory path after adding:

- `deep-memory verify-install`
- `deep-memory mcp-config`
- `docs/agent-install.json`
- `docs/PACKAGING.md`
- README / `docs/AGENT_INSTALL_GUIDE.md` install-contract links

## Targeted verification

Command:

```bash
uv run pytest -q \
  tests/test_verify_install_cli.py \
  tests/test_mcp_config_cli.py \
  tests/test_agent_install_manifest.py \
  tests/test_agent_install_guide_docs.py \
  tests/test_packaging_docs.py \
  tests/test_skill_activation_loop_docs.py \
  tests/test_skill_export.py \
  && uv run ruff check .
```

Result:

```text
27 passed
All checks passed!
```

## Fresh copied workspace surrogate

Command:

```bash
rm -rf /tmp/deep-memory-install-gate
mkdir -p /tmp/deep-memory-install-gate
cp -a /home/ben/open-source/deep-memory /tmp/deep-memory-install-gate/deep-memory
cd /tmp/deep-memory-install-gate/deep-memory
uv sync --extra dev --extra mcp
uv run deep-memory verify-install /tmp/deep-memory-install-gate/deep-memory.db --json
uv run deep-memory mcp-config --agent generic --db /tmp/deep-memory-install-gate/deep-memory.db --json
uv run python -c 'import deep_memory.mcp_server; print("mcp import ok")'
```

Result summary:

```text
Resolved 77 packages
Built deep-memory @ file:///tmp/deep-memory-install-gate/deep-memory
Installed 25 packages
verify-install success=true
write_ok=true
search_ok=true
cleanup_ok=true
mcp_import_ok=true
mcp-config emitted command=deep-memory-mcp args=["--db", "/tmp/deep-memory-install-gate/deep-memory.db"]
mcp import ok
```

Representative JSON:

```json
{
  "success": true,
  "db": "/tmp/deep-memory-install-gate/deep-memory.db",
  "cli_ok": true,
  "db_ok": true,
  "write_ok": true,
  "search_ok": true,
  "cleanup_ok": true,
  "mcp_import_ok": true,
  "scope": "workspace",
  "scope_id": "verify-install",
  "errors": []
}
```

## Wheel / sdist build and local wheel install

Command:

```bash
cd /tmp/deep-memory-install-gate/deep-memory
uv build
python -m venv /tmp/deep-memory-install-gate/wheel-venv
/tmp/deep-memory-install-gate/wheel-venv/bin/pip install dist/*.whl
/tmp/deep-memory-install-gate/wheel-venv/bin/deep-memory verify-install /tmp/deep-memory-install-gate/wheel.db --json
/tmp/deep-memory-install-gate/wheel-venv/bin/deep-memory mcp-config --agent generic --db /tmp/deep-memory-install-gate/wheel.db --json
```

Result summary:

```text
Successfully built dist/deep_memory-0.1.0.tar.gz
Successfully built dist/deep_memory-0.1.0-py3-none-any.whl
wheel verify-install success=true
write_ok=true
search_ok=true
cleanup_ok=true
mcp_import_ok=true
mcp-config emitted reviewable generic JSON
```

Artifacts:

```text
deep_memory-0.1.0-py3-none-any.whl 67086
deep_memory-0.1.0.tar.gz 60068
```

## Optional MCP extra wheel install

Command:

```bash
python -m venv /tmp/deep-memory-install-gate/wheel-mcp-venv
/tmp/deep-memory-install-gate/wheel-mcp-venv/bin/pip install '/tmp/deep-memory-install-gate/deep-memory/dist/deep_memory-0.1.0-py3-none-any.whl[mcp]'
/tmp/deep-memory-install-gate/wheel-mcp-venv/bin/deep-memory verify-install /tmp/deep-memory-install-gate/wheel-mcp.db --json
/tmp/deep-memory-install-gate/wheel-mcp-venv/bin/python -c 'import deep_memory.mcp_server; import mcp; print("mcp optional import ok")'
```

Result summary:

```text
verify-install success=true
write_ok=true
search_ok=true
cleanup_ok=true
mcp_import_ok=true
mcp optional import ok
```

Note: `deep-memory-mcp --help` enters the MCP server run path rather than printing a conventional help page. Import/startup module checks passed; long-running MCP server supervision should be tested separately by an MCP client.

## MCP client-level smoke

Command:

```bash
uv run --extra mcp pytest -q tests/test_mcp_client_smoke.py
```

Result:

```text
1 passed
```

What this proves:

- A real MCP stdio client starts `deep_memory.mcp_server`.
- The client initializes an MCP session and lists tools.
- The exposed tools include `add`, `search`, and `stats`.
- The client calls `add` through MCP and writes a scoped project memory.
- The client calls `search` through MCP and retrieves the same record.
- The client calls `stats` through MCP and sees `semantic=1`, `total=1`.

This validates the full path:

```text
MCP client → deep-memory-mcp server → deep-memory SQLite DB → MCP response
```

## Known caveats

- Public PyPI was not published in this gate. Wheel install is a local surrogate.
- `uv sync` emitted a hardlink fallback warning because `/tmp` and the uv cache may be on different filesystems; this is performance-only.
- `pip install` printed unrelated `hermes-agent` dependency conflict warnings from the surrounding environment, but the isolated deep-memory CLI and optional MCP import checks passed.

## Verdict

Pass for local source install, machine-local DB verification, generic MCP config generation, wheel/sdist build, local wheel install, optional MCP import verification, and real MCP stdio client add/search/stats smoke. Public PyPI publication remains a maintainer-approved release step.
