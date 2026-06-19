#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if ! command -v uv >/dev/null 2>&1; then
  echo "error: uv is required. Install it from https://docs.astral.sh/uv/" >&2
  exit 1
fi

echo "==> Syncing contributor environment"
uv sync --extra dev --extra vector --extra mcp

echo "==> Installing pre-commit hooks when available"
if uv run python -c "import pre_commit" >/dev/null 2>&1; then
  uv run pre-commit install
elif command -v pre-commit >/dev/null 2>&1; then
  pre-commit install
else
  echo "pre-commit is not installed in this environment; skipping hook install"
  echo "tip: add pre-commit to the dev extra if maintainers want this enforced by default"
fi

echo "==> Running pytest"
uv run pytest -q

echo "==> Running ruff"
uv run ruff check .

echo "==> Dev setup verified"
