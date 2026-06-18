# M+1 MVP Credibility Review

## Decision

**Conditional GO for controlled preview**, not broad HN-scale launch yet.

## Evidence inspected

- Repo polish and README first-screen positioning.
- Quickstart and memory-vs-no-memory examples.
- Package readiness / source install path.
- Extraction API contract.
- Hermes adapter MVP.
- MCP server adapter.
- Benchmark v0.

## Verification commands

```bash
uv run pytest -q
uv run ruff check .
uv run python examples/quickstart.py
uv run python examples/memory_vs_nomemory.py
uv run python benchmarks/memory_benchmark.py --fixture benchmarks/fixtures/memory_benchmark_v0.json --json
```

Current evidence: full test suite passes, lint passes, examples run, benchmark v0 shows a strong synthetic memory/no-memory delta.

## Why not broad launch yet

The benchmark is still synthetic and easy. Chinese retrieval needs a dedicated dataset and baseline before the strongest differentiation claim is public.

## Remaining preview blockers / next loop

- Keep the launch narrative explicitly framed as controlled preview.
- Verify the launch path in smoke -> scope tests -> full pytest + ruff order before broadening claims.
- Chinese retrieval evaluation dataset v1 + baseline before any stronger differentiation claim.
- Adapter specs and WebUI trust spec remain part of the next credibility loop.
