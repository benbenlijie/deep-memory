# Good first issue drafts

These drafts mirror the first community issues maintainers can create or paste into GitHub. They are intentionally narrow: each has a clear file area, acceptance checklist, and verification command.

If GitHub issue creation is available, these can be created with the `good first issue` label plus the lane/type labels shown below.

## 1. Add adapter smoke test for a new agent

Labels: `good first issue`, `help wanted`, `type:adapter`, `lane:adapters`, `p2-ecosystem`

### Why this matters

Adapter claims are only useful when maintainers can inspect a redacted, replayable smoke path. A new agent smoke test should prove the same loop: search before work, explicit durable write after work, and skipped private or malformed data.

### Suggested files

- `src/deep_memory/adapters/`
- `tests/test_hermes_adapter.py` or a new adapter-specific test file
- `scripts/run_adapter_smoke.py`
- `docs/ADAPTERS.md`
- `docs/internal/SMOKE_TRANSCRIPTS.md`

### Acceptance checklist

- [ ] Pick one agent runtime not already covered by a smoke transcript.
- [ ] Add a redacted fixture or transcript showing pre-task search and explicit post-task write.
- [ ] Verify malformed/private input is skipped or rejected.
- [ ] Preserve source/provenance in created records.
- [ ] Document one manual smoke command.

### Suggested verification

```bash
uv run pytest -q tests/test_hermes_adapter.py tests/test_codex_wrapper.py
uv run ruff check .
```

## 2. Add retrieval eval fixtures for a new language

Labels: `good first issue`, `type:eval`, `lane:evals`, `p2-ecosystem`

### Why this matters

Chinese-first retrieval is the current proof point, but memory systems should be tested against realistic multilingual developer phrasing. A small new-language fixture helps separate true retrieval behavior from README claims.

### Suggested files

- `evals/data/`
- `evals/chinese_retrieval_eval.py` or a new shared retrieval eval runner if needed
- `tests/test_chinese_retrieval_eval.py` or a new eval test file
- `docs/CHINESE_RETRIEVAL_EVAL.md`

### Acceptance checklist

- [ ] Add at least 10 rows for one new language or mixed-language pair.
- [ ] Include distractor memories, aliases, punctuation-heavy text, and technical terms.
- [ ] Include expected target IDs or expected snippets.
- [ ] Add a test that verifies fixture shape and at least one ranking metric.
- [ ] Document the reproduction command.

### Suggested verification

```bash
uv run pytest -q tests/test_chinese_retrieval_eval.py
uv run python evals/chinese_retrieval_eval.py --data evals/data/zh_memory_retrieval_v2.jsonl --json
```

## 3. Improve WebUI styling

Labels: `good first issue`, `type:feature`, `lane:ui`, `p2-ecosystem`

### Why this matters

The WebUI is the first place many users inspect what an agent remembers. Styling should improve scanability without weakening the local-only, inspectable safety boundary.

### Suggested files

- `src/deep_memory/webui.py`
- `tests/test_webui.py`
- `tests/test_webui_graph.py`
- `docs/GRAPH_VIZ.md`

### Acceptance checklist

- [ ] Improve visual hierarchy for records, metadata, actions, and empty states.
- [ ] Preserve semantic HTML and existing accessible labels.
- [ ] Do not add analytics, remote services, or hidden network calls.
- [ ] Keep graph/timeline views usable with existing tests.
- [ ] Add or update a test for a stable UI affordance if behavior changes.

### Suggested verification

```bash
uv run pytest -q tests/test_webui.py tests/test_webui_graph.py
uv run ruff check .
```

## 4. Add CLI `--json` output mode for all commands

Labels: `good first issue`, `type:feature`, `lane:ui`, `p1-core`

### Why this matters

Agents and scripts need stable machine-readable output. The CLI already has some JSON-producing commands, but a consistent `--json` mode across commands would make wrappers and eval automation less brittle.

### Suggested files

- `src/deep_memory/cli.py`
- `tests/test_core.py`
- `tests/test_cli_export_delete.py`
- adapter or wrapper tests that parse CLI output

### Acceptance checklist

- [ ] Inventory commands that currently print tables or prose.
- [ ] Add `--json` to one command first and document the pattern in the PR.
- [ ] Preserve existing human-readable output when `--json` is not passed.
- [ ] Add tests for the JSON schema and backward-compatible behavior.
- [ ] Extend the pattern to remaining commands in small commits or follow-up PRs.

### Suggested verification

```bash
uv run pytest -q tests/test_core.py tests/test_cli_export_delete.py
uv run deep-memory --help
uv run ruff check .
```

## 5. Add benchmark dataset for a new domain

Labels: `good first issue`, `type:eval`, `lane:evals`, `p2-ecosystem`

### Why this matters

Memory quality is domain-sensitive. A small domain benchmark can reveal where retrieval, conflict handling, or memory/no-memory behavior breaks before the project claims broader generality.

### Suggested files

- `benchmarks/fixtures/`
- `benchmarks/memory_benchmark.py`
- `tests/test_benchmark.py`
- `docs/MEMORY_BENCHMARK.md`

### Acceptance checklist

- [ ] Pick one domain, such as legal, medical operations, software maintenance, finance ops, or education.
- [ ] Add at least 10 redacted tasks with required memories and expected answers/behaviors.
- [ ] Include distractors or stale/conflicting memories where appropriate.
- [ ] Add tests that verify fixture shape and benchmark inclusion.
- [ ] Document the reproduction command and what the benchmark does not prove.

### Suggested verification

```bash
uv run pytest -q tests/test_benchmark.py
uv run python benchmarks/memory_benchmark.py
uv run ruff check .
```
