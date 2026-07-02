# Release notes draft — v0.1.0

Status: draft. Do not publish to PyPI until a maintainer explicitly approves the upload and provides the required credentials.

## Highlights

- Adds `deep-memory verify-install` for one-shot machine-readable install validation.
- Adds `deep-memory mcp-config` for reviewable Hermes, Claude, and generic MCP configuration snippets.
- Adds `docs/agent-install.json`, a machine-readable agent install contract.
- Adds packaging guidance for source, local wheel, future `uv tool install`, GitHub Release, and PyPI readiness.
- Adds a first-party `deep-memory-agent` skill candidate for review-first procedural memory usage.
- Clarifies that deep-memory is not only an MCP server: it is a memory substrate with CLI, MCP, WebUI, Python SDK, adapters, and a skill layer.

## Verification evidence

Targeted gate:

```bash
uv run --extra mcp pytest -q \
  tests/test_mcp_client_smoke.py \
  tests/test_mcp_server.py \
  tests/test_verify_install_cli.py \
  tests/test_mcp_config_cli.py \
  tests/test_agent_install_manifest.py \
  tests/test_packaging_docs.py \
  && uv run ruff check . \
  && git diff --check
```

Result:

```text
20 passed
All checks passed!
```

Install release gate evidence:

- `docs/release-gate-install-2026-07-02.md`
- Source copied workspace install passed.
- `verify-install --json` passed with `write_ok`, `search_ok`, `cleanup_ok`, and `mcp_import_ok` true.
- Generic MCP config generation passed.
- `uv build` produced wheel and sdist.
- Local wheel install passed `verify-install`.
- Optional `[mcp]` wheel install imported `mcp` and `deep_memory.mcp_server`.
- MCP client-level smoke passed: real MCP stdio client listed tools and called `add`, `search`, and `stats`.

## User-facing install path before PyPI

```bash
git clone https://github.com/benbenlijie/deep-memory.git
cd deep-memory
uv sync --extra mcp
uv run deep-memory verify-install ~/.deep-memory/deep-memory.db --json
uv run deep-memory mcp-config --agent generic --db ~/.deep-memory/deep-memory.db --json
```

## Future PyPI install path after approval and publish

```bash
uv tool install "deep-memory[mcp]"
deep-memory verify-install ~/.deep-memory/deep-memory.db --json
```

## Safety boundaries

- No automatic PyPI publish.
- No automatic repository starring.
- No automatic writes into active Hermes skill directories.
- MCP config generation prints reviewable snippets only; it does not edit user config files.
- Smoke-test memories are cleaned up by `verify-install`.
