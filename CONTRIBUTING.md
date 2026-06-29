# Contributing

`deep-memory` is alpha-quality developer infrastructure for agent memory. The bar for merging is small, tested pull requests, not broad rewrites.

Contributing starts from a clear mechanism, boundary, and evidence trail: what memory bottleneck does this change address, how is it verified, and does it preserve the local-first, inspectable, user-controlled safety boundary?

## Start with a good first issue

New here? Start with the published [`good first issue` list](https://github.com/benbenlijie/deep-memory/labels/good%20first%20issue).

1. Browse the good-first-issues and pick one narrow task.
2. Comment on the issue to claim it and share any assumptions before starting.
3. Run the suggested setup and verification commands from the issue body.
4. Keep the change scoped to the files and acceptance checklist in that issue.
5. Open a PR with the commands you ran and any remaining uncertainty.

## 5-minute dev setup

Prerequisites:

- Python 3.10+
- `uv` installed: <https://docs.astral.sh/uv/>
- Git

From a fresh clone:

```bash
git clone https://github.com/benbenlijie/deep-memory.git
cd deep-memory
uv sync --extra dev --extra vector --extra mcp
uv run pytest -q
uv run ruff check .
```

Or run the automated setup check:

```bash
./scripts/dev_setup.sh
```

The setup script installs all contributor extras, installs pre-commit hooks when `pre-commit` is available, then verifies pytest and ruff.

If setup fails before you can reach the actual contribution, use [`docs/TROUBLESHOOTING.md`](docs/TROUBLESHOOTING.md). It covers `uv sync --extra dev`, optional `--extra mcp`, pytest/ruff failures, and missing runtime CLIs.

## Project structure

```text
src/deep_memory/          Core package: SDK, CLI, MCP server, adapters, WebUI.
src/deep_memory/core.py   SQLite memory model, retrieval, lifecycle, trust/scope logic.
src/deep_memory/cli.py    Typer CLI commands exposed through `deep-memory`.
src/deep_memory/webui.py  Local inspector UI for searching, editing, and graph/timeline views.
src/deep_memory/adapters/ Agent/runtime integration surfaces.
tests/                    Unit and regression tests.
evals/                    Retrieval eval runners and checked-in fixture data.
benchmarks/               Internal eval/regression benchmark code/data.
docs/                     User docs, architecture docs, roadmap, governance, community paths.
scripts/                  Maintainer/contributor helper scripts.
.github/                  CI, issue templates, and label proposal.
```

## How to run tests

Baseline before opening a PR:

```bash
uv run pytest -q
uv run ruff check .
```

Useful targeted commands:

```bash
uv run pytest -q tests/test_core.py
uv run pytest -q tests/test_chinese_retrieval_eval.py
uv run python evals/chinese_retrieval_eval.py --data evals/data/zh_memory_retrieval_v2.jsonl --json
uv run python benchmarks/memory_benchmark.py
```

If your change touches optional integrations, include the relevant extra in setup:

```bash
uv sync --extra dev --extra mcp
uv sync --extra dev --extra vector
```

## How to add a new eval

A good eval starts with a concrete memory failure or quality claim. Do not start with a broad benchmark; start with the smallest fixture that would have caught the failure.

1. Pick the lane: retrieval, memory/no-memory behavior, privacy boundary, adapter smoke, skill activation, or benchmark domain.
2. Add redacted fixture data under `evals/data/` or `benchmarks/fixtures/`.
3. Include expected behavior in the fixture: target id, expected snippet, pass threshold, or explicit should-not-remember classification.
4. Add or update an eval runner only if the current runner cannot express the case.
5. Add a regression test under `tests/` that checks the fixture shape and the reported metrics.
6. Document the command in the relevant doc, usually `docs/CHINESE_RETRIEVAL_EVAL.md`, `docs/MEMORY_BENCHMARK.md`, `docs/VECTOR_EVALUATION.md`, or `docs/NEXT_PHASE_BACKLOG.md`.

Verification examples:

```bash
uv run pytest -q tests/test_chinese_retrieval_eval.py
uv run python evals/chinese_retrieval_eval.py --data evals/data/zh_memory_retrieval_v2.jsonl --json
```

## How to add a new adapter

An adapter connects `deep-memory` to an agent runtime, framework, or protocol. The safe default is explicit search before work and explicit durable writes after verified work — not silent transcript scraping.

1. Open or draft a `Backend / adapter proposal` issue.
2. Define the runtime event contract:
   - what input events are accepted;
   - which fields become memory content, kind, importance, confidence, and source;
   - how malformed, private, or temporary data is skipped.
3. Add a redacted fixture or smoke transcript.
4. Implement a thin adapter under `src/deep_memory/adapters/` only after the contract is clear.
5. Add tests for import, skipped records, source/provenance, malformed input, and privacy boundaries.
6. Add one manual smoke command in docs.
7. Keep new dependencies optional unless they are already core project dependencies.

Read `docs/ADAPTERS.md` and `docs/COMMUNITY.md` before implementing. An adapter should graduate only when a maintainer can run its smoke test from a clean checkout and inspect the written records.

## Coding conventions

- Use `uv` for environment and command execution.
- Use type hints for new public functions and data structures.
- Keep functions small enough that their behavior is obvious from tests.
- Prefer deterministic local tests over network-dependent tests.
- Keep optional dependencies behind extras.
- Preserve local-first behavior: no hidden cloud sync, no global transcript scraping.
- Preserve inspectability: records should keep source/provenance and be exportable/deletable.
- Run `uv run ruff check .` before review.

## Community feedback

If you are not ready to write code yet, the highest-leverage contribution is a concrete agent memory failure case: what the agent should have remembered, what it recalled instead, and which runtime you were using. Use the `Memory failure case` issue template and redact any private data.

## Good first issues

If you want a small first contribution, start with the published [`good first issue` list](https://github.com/benbenlijie/deep-memory/labels/good%20first%20issue). `docs/GOOD_FIRST_ISSUE_DRAFTS.md` keeps the source draft list and maps the current batch to issue numbers.

Priority newcomer paths from the current draft batch:

- privacy-boundary eval fixtures;
- workspace scope-isolation regression case;
- WebUI empty-state polish;
- Hermes adapter smoke transcript example;
- docs troubleshooting for local setup failures;
- export/delete example flow;
- mixed Chinese/English retrieval fixtures.

When opening one of these, keep the issue small enough that a maintainer can review it from a single lane with explicit verification commands.

## Contribution lanes

New contributors should start from one lane in `docs/COMMUNITY.md` and `docs/NEXT_PHASE_BACKLOG.md`:

- Retrieval: Chinese-first and mixed-language recall quality.
- Adapters: Hermes, MCP, Claude Code, Codex, OpenCode and future agent runtimes.
- UI: CLI inspector, correction flows, future web editor and visualizer.
- Evals: memory failure cases, retrieval metrics, memory/no-memory comparisons.
- Docs: quickstarts, troubleshooting, architecture guides and release notes.

For new memory backends or agent adapters, read the contributor paths in `docs/COMMUNITY.md` before implementing. The default path is proposal issue → minimal contract → redacted fixture → optional dependency if needed → tests/smoke transcript → documentation.

## PR checklist

Before opening a PR, check:

- [ ] The change is small and scoped to one lane.
- [ ] New behavior has tests or an explicit verification command.
- [ ] `uv run pytest -q` passes, or the PR explains exactly why it could not be run.
- [ ] `uv run ruff check .` passes.
- [ ] Docs are updated when commands, behavior, safety boundaries, or contributor paths change.
- [ ] New fixtures are redacted and contain no secrets, raw credentials, auth cookies, or private transcript dumps.
- [ ] New dependencies are optional or clearly justified.
- [ ] The PR description includes evidence: commands run, files changed, and remaining uncertainty.

## Principles

- Working artifact over broad claims.
- Tests before large rewrites.
- Memory quality must be measurable.
- User control and inspectability are part of the core product, not an add-on.
