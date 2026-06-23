# Troubleshooting local contributor setup

This project is intentionally local-first and source-first. Most setup failures happen before contributors reach the interesting memory problem. This guide keeps the path narrow: get `uv`, install the right extras, run the baseline checks, then isolate the failing lane.

## 1. `uv sync --extra dev` fails

What to check:
- `uv` is installed and on `PATH`
- your Python version is 3.10+
- you are running from the repository root

Useful checks:
```bash
uv --version
python3 --version
pwd
```

If `uv` is missing, install it from the Astral docs:
- <https://docs.astral.sh/uv/>

Then retry:
```bash
uv sync --extra dev
```

If you need MCP commands in this checkout, install the optional extra too:
```bash
uv sync --extra dev --extra mcp
```

## 2. `uv run pytest -q` fails

Step back and isolate the lane first. The interesting question is not just “what failed?” but “which subsystem failed?”

Try one targeted test file before re-running the whole suite:
```bash
uv run pytest -q tests/test_core.py
uv run pytest -q tests/test_memory_policy.py
uv run pytest -q tests/test_webui.py
```

Common patterns:
- import error after setup: re-run `uv sync --extra dev`
- MCP-related failure: install `--extra mcp`
- optional integration path failure: check whether the test expects an optional extra or a runtime-specific binary

If the failure is real, include the exact failing command and traceback snippet in your PR or issue.

## 3. `uv run ruff check .` fails

This usually means formatting, unused imports, or a small style issue rather than a design problem.

Run:
```bash
uv run ruff check .
```

Then fix the narrow issue it reports. Avoid broad drive-by refactors in a first PR.

## 4. `deep-memory-mcp` or MCP-related commands fail

The MCP server is optional. If you see an error indicating MCP support is missing, install the extra:
```bash
uv sync --extra dev --extra mcp
```

Then verify the CLI surface:
```bash
uv run deep-memory-mcp --help
uv run pytest -q tests/test_mcp_server.py
```

If a runtime-specific MCP setup command fails, separate repo-local verification from runtime verification:
- repo-local: `uv run deep-memory-mcp --help`, related tests
- runtime-specific: the external agent CLI configuration step

## 5. Runtime CLI is missing

Some docs mention external runtimes such as Claude Code, Hermes, Codex, or OpenCode. Those are not required for most first PRs.

If a CLI like `claude`, `codex`, or another runtime command is missing:
- skip that runtime-specific path for now;
- choose a docs, eval, or core test issue instead;
- make sure the docs clearly mark which commands are verified locally versus pending runtime verification.

Good fallback lanes:
- docs troubleshooting
- good-first eval fixtures
- WebUI polish
- scope-isolation regressions

## 6. Docs-only changes still need verification

For docs-only changes, run the baseline docs-adjacent checks that still prove the repo is in a good state:
```bash
uv run pytest -q
uv run ruff check .
```

If the docs change links or contributor paths, add a small local assertion when appropriate. Example:
```bash
uv run python - <<'PY'
from pathlib import Path
text = Path('CONTRIBUTING.md').read_text(encoding='utf-8')
assert 'docs/TROUBLESHOOTING.md' in text
print('contributing troubleshooting link ok')
PY
```

## 7. When to open an issue instead of pushing further

Open or update an issue when:
- setup fails even after installing the documented extras;
- the docs and the actual command surface disagree;
- a first-time contributor path depends on hidden maintainer knowledge;
- a runtime-specific integration claim cannot be reproduced locally.

A good report includes:
- exact command run
- operating system
- observed error
- whether this was a docs lane, eval lane, UI lane, or adapter lane
- any small reproduction step you found

## Baseline success state

You are in a good place for a first contribution if these commands pass:
```bash
uv sync --extra dev
uv run pytest -q
uv run ruff check .
```

If your issue touches MCP, also verify:
```bash
uv sync --extra dev --extra mcp
uv run deep-memory-mcp --help
```
