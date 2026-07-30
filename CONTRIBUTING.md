# Contributing

Thanks for helping with `deep-memory`. This project is in controlled preview, so the bar is small, verified changes rather than broad rewrites.

## Start here

1. Read [`README.md`](README.md) for the product boundary and current support status.
2. Pick an issue-sized task from [`docs/NEXT_PHASE_BACKLOG.md`](docs/NEXT_PHASE_BACKLOG.md) or the live GitHub issue list.
3. Check the community lanes and maintainer review checklist in [`docs/COMMUNITY.md`](docs/COMMUNITY.md).
4. Keep the PR scoped to one lane: `good first issue`, `adapter`, `eval`, `governance`, or `docs`.

## Before opening a PR

Run the baseline checks unless the task explicitly narrows them:

```bash
uv run pytest -q
uv run ruff check .
```

For docs-only changes, also run the Markdown link checker from [`docs/AGENT_QUICKSTART_MATRIX.md`](docs/AGENT_QUICKSTART_MATRIX.md#verification-commands-for-this-repository).

## Review expectations

- Include the commands you ran and any remaining uncertainty.
- Do not overstate unverified memory, adapter, or runtime claims.
- Keep memory writes explicit and inspectable; never add hidden transcript scraping.
- Preserve local-first behavior, scoped recall, delete/export paths, and safety boundaries.
- Add or update tests, fixtures, transcripts, or docs evidence when a claim should remain true.

## Useful references

- [`docs/AGENT_INSTALL_GUIDE.md`](docs/AGENT_INSTALL_GUIDE.md) — agent install contract.
- [`docs/AGENT_QUICKSTART_MATRIX.md`](docs/AGENT_QUICKSTART_MATRIX.md) — per-runtime commands and verification status.
- [`docs/TROUBLESHOOTING.md`](docs/TROUBLESHOOTING.md) — first-time local setup, pytest, ruff, MCP extra, and missing runtime CLI failures.
- [`docs/ADAPTERS.md`](docs/ADAPTERS.md) — adapter contracts, permissions, and risks.
- [`docs/MCP_INTEROPERABILITY.md`](docs/MCP_INTEROPERABILITY.md) — MCP protocol smoke evidence.
- [`docs/NEXT_PHASE_BACKLOG.md`](docs/NEXT_PHASE_BACKLOG.md) — concrete backlog and acceptance criteria.
