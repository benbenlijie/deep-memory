# Contributing

We are building deep-memory as research-grade developer infrastructure. Please optimize for small, tested pull requests.

## Local setup

```bash
uv sync --extra dev
uv run pytest
uv run ruff check src tests
```

## Community feedback

If you are not ready to write code yet, the highest-leverage contribution is a concrete agent memory failure case: what the agent should have remembered, what it recalled instead, and which runtime you were using. Use the `Memory failure case` issue template and redact any private data.

## Contribution lanes

New contributors should start from one lane in `docs/COMMUNITY.md`:

- Retrieval: Chinese-first and mixed-language recall quality.
- Adapters: Hermes, MCP, Claude Code, Codex, OpenCode and future agent runtimes.
- UI: CLI inspector, correction flows, future web editor and visualizer.
- Evals: memory failure cases, retrieval metrics, memory/no-memory comparisons.
- Docs: quickstarts, troubleshooting, architecture guides and release notes.

For new memory backends or agent adapters, read the contributor paths in `docs/COMMUNITY.md` before implementing. The default path is proposal issue → minimal contract → redacted fixture → optional dependency if needed → tests/smoke transcript → documentation.

## Principles

- Working artifact over broad claims.
- Tests before large rewrites.
- Memory quality must be measurable.
- User control and inspectability are part of the core product, not an add-on.
