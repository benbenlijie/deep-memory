# Packaging and release checklist

This document keeps the package-install path explicit. It is a maintainer checklist, not an instruction for an agent to publish on its own.

## Build locally

```bash
uv sync --extra dev --extra mcp
uv build
```

Expected artifacts:

- `dist/deep_memory-<version>-py3-none-any.whl`
- `dist/deep_memory-<version>.tar.gz`

## Local wheel / tool smoke

Use a temporary tool environment or virtualenv, then verify both console scripts are present:

```bash
uv tool install --force dist/deep_memory-<version>-py3-none-any.whl
which deep-memory
which deep-memory-mcp
deep-memory verify-install ~/.deep-memory/deep-memory.db --json
deep-memory mcp-config --agent generic --db ~/.deep-memory/deep-memory.db --json
```

If the package has not been published to PyPI yet, report the wheel install as a local surrogate. Do not describe it as a public package install.

## User-facing install commands

Before PyPI publication:

```bash
git clone https://github.com/benbenlijie/deep-memory.git
cd deep-memory
uv sync --extra mcp
uv run deep-memory verify-install ~/.deep-memory/deep-memory.db --json
```

After PyPI publication:

```bash
uv tool install "deep-memory[mcp]"
deep-memory verify-install ~/.deep-memory/deep-memory.db --json
```

## Release checklist

1. Update version in `pyproject.toml`.
2. Run targeted install tests and the full suite.
3. Run `uv build` and inspect wheel/sdist contents.
4. Smoke local wheel install with `deep-memory` and `deep-memory-mcp`.
5. Create a signed tag and GitHub Release with install notes.
6. Publish to PyPI only after explicit maintainer approval.
7. Re-run `deep-memory verify-install ~/.deep-memory/deep-memory.db --json` from the published package.
8. Update README / agent install guide if install commands changed.

## Safety boundary

Do not publish to PyPI without explicit maintainer approval. Do not modify user agent configs during packaging verification; use `deep-memory mcp-config` to print reviewable snippets instead.
