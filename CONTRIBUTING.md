# Contributing

We are building deep-memory as research-grade developer infrastructure. Please optimize for small, tested pull requests.

## Local setup

```bash
uv sync --extra dev
uv run pytest
uv run ruff check src tests
```

## Principles

- Working artifact over broad claims.
- Tests before large rewrites.
- Memory quality must be measurable.
- User control and inspectability are part of the core product, not an add-on.
