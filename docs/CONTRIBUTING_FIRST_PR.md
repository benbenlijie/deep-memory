# First PR guide

This guide is for a first-time contributor who wants to go from clone to a small, reviewable PR quickly.

The trick is not to search the whole contribution space. Pick one narrow issue, make one verifiable change, and leave a clean evidence trail.

## 1. Set up the project

```bash
git clone https://github.com/benbenlijie/deep-memory.git
cd deep-memory
./scripts/dev_setup.sh
```

If you prefer manual setup:

```bash
uv sync --extra dev --extra vector --extra mcp
uv run pytest -q
uv run ruff check .
```

You should now have a working virtual environment managed by `uv`.

## 2. Pick a small issue

Good first PRs usually fit one of these shapes:

- Add or extend a small retrieval fixture.
- Add one adapter smoke transcript or smoke test.
- Improve one CLI output or documentation path.
- Improve WebUI HTML/CSS without changing storage behavior.
- Add one benchmark fixture for a new domain.

Avoid broad rewrites, new architecture, hidden background memory writes, or non-local services in your first PR.

## 3. Create a branch

```bash
git checkout -b docs-or-test/my-first-deep-memory-pr
```

Use a descriptive branch name:

```text
adapter/claude-smoke-test
eval/spanish-retrieval-fixtures
ui/webui-style-polish
cli/json-output-mode
benchmarks/legal-domain-fixture
```

## 4. Make the smallest useful change

Examples:

### Add an eval fixture

1. Add fixture rows under `evals/data/` or `benchmarks/fixtures/`.
2. Update or add a test under `tests/` that proves the fixture is used.
3. Run the targeted eval/test command.

### Add an adapter smoke test

1. Read `docs/ADAPTERS.md`.
2. Add a redacted fixture or transcript.
3. Add or update tests for import, skipped malformed data, and source/provenance.
4. Document the manual smoke command.

### Improve WebUI styling

1. Keep the local-only safety boundary intact.
2. Avoid external services or analytics.
3. Preserve accessible labels and semantic HTML.
4. Run WebUI tests.

### Add CLI JSON output

1. Choose one command first.
2. Add `--json` without breaking the current human-readable output.
3. Add tests for the machine-readable shape.
4. Repeat for other commands only after the pattern is clear.

## 5. Verify locally

Run the baseline commands:

```bash
uv run pytest -q
uv run ruff check .
```

For docs-only changes, also check important local links or run a small Python assertion if the PR changes docs paths.

Targeted examples:

```bash
uv run pytest -q tests/test_chinese_retrieval_eval.py
uv run pytest -q tests/test_hermes_adapter.py tests/test_codex_wrapper.py
uv run pytest -q tests/test_webui.py tests/test_webui_graph.py
uv run python evals/chinese_retrieval_eval.py --data evals/data/zh_memory_retrieval_v2.jsonl --json
```

## 6. Open the PR

Use a compact PR description:

```markdown
## What changed
- <one or two bullets>

## Why
- <which issue or bottleneck this addresses>

## Verification
- `uv run pytest -q` -> passed
- `uv run ruff check .` -> passed

## Safety / privacy
- No secrets or raw transcripts added.
- Local-first behavior unchanged.

## Remaining uncertainty
- <anything the maintainer should know>
```

## Maintainer expectations

A good first PR does not need to be large. It needs to be clear:

- one lane;
- small diff;
- no private data;
- tests or evidence;
- no exaggerated claims.

If you are unsure, open a draft PR early and describe the verification command you plan to make pass.
