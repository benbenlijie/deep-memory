# Good first issue drafts

These drafts are written so a maintainer can open them with minimal editing. The goal is not to search the whole contribution space. It is to create a small, verifiable contribution path that teaches contributors how `deep-memory` works.

Use labels from `.github/labels.md`:
- baseline: `good first issue`, `help wanted`
- add one lane label such as `lane:evals`, `lane:ui`, `lane:docs`, `lane:adapters`
- add one type label such as `type:eval`, `type:docs`, `type:adapter`
- add one memory-quality label when relevant

## 1. Add privacy-boundary eval fixtures for obvious deny cases

Suggested labels:
- `good first issue`
- `lane:evals`
- `type:eval`
- `privacy-boundary`
- `p1-core`

Why this matters:
The memory layer is only trustworthy if it remembers useful durable facts and refuses high-risk data. We already test some policy behavior, but the public contributor path should include a small fixture-driven privacy boundary task.

Scope:
- In scope:
  - add a small checked-in fixture file for obvious deny or requires-confirmation memory cases;
  - include examples for secrets, auth cookies, raw identifiers, and temporary task status;
  - add or extend one test that proves the fixture stays aligned with current policy behavior;
  - document one false-positive or tradeoff note near the fixture or in the relevant docs.
- Out of scope:
  - redesigning the full policy system;
  - adding network services or hosted moderation;
  - broad refactors across unrelated files.

Files likely touched:
- `tests/test_memory_policy.py`
- `docs/NEXT_PHASE_BACKLOG.md`
- one new fixture under `evals/data/` or `tests/fixtures/`

Acceptance checklist:
- [ ] Fixture contains at least 5 deny/requires-confirmation examples.
- [ ] At least one example covers temporary task status.
- [ ] Tests prove the examples are still denied or require confirmation.
- [ ] Docs mention one false-positive tradeoff or boundary note.

Suggested commands:
```bash
uv run pytest -q tests/test_memory_policy.py tests/test_cli_export_delete.py
uv run ruff check .
```

## 2. Add workspace scope-isolation regression case with clear contributor narrative

Suggested labels:
- `good first issue`
- `lane:evals`
- `type:eval`
- `p1-core`

Why this matters:
Cross-project leakage is one of the core failure modes for persistent memory. New contributors should be able to improve that safety boundary without needing to redesign retrieval.

Scope:
- In scope:
  - add one small regression case showing that workspace-scoped memories do not leak into another workspace by default;
  - make the case easy to understand from the test name and inline comments;
  - if helpful, add one short note in docs that points contributors to the isolation behavior.
- Out of scope:
  - changing the scope model itself;
  - adding new storage backends;
  - broad search ranking work.

Files likely touched:
- `tests/test_scope_idempotency.py`
- `CONTRIBUTING.md` or `docs/COMMUNITY.md`

Acceptance checklist:
- [ ] Regression case fails if workspace isolation breaks.
- [ ] Test names and comments explain the expected boundary clearly.
- [ ] If docs are touched, they stay aligned with current code behavior.

Suggested commands:
```bash
uv run pytest -q tests/test_scope_idempotency.py
uv run ruff check .
```

## 3. Polish WebUI empty state for a fresh local database

Suggested labels:
- `good first issue`
- `lane:ui`
- `type:docs`
- `p2-ecosystem`

Why this matters:
If you imagine a new contributor or evaluator opening the local inspector on an empty database, the first screen should teach the core loop: add one durable fact, search it, inspect it. That is a small UX wedge with real leverage.

Scope:
- In scope:
  - improve the empty-state copy or layout in the local WebUI when no records exist;
  - keep the UI local-only and dependency-light;
  - preserve accessibility labels and semantic HTML;
  - add or update a test for the empty-state render.
- Out of scope:
  - redesigning the whole WebUI;
  - adding analytics, remote assets, or authentication flows;
  - changing storage behavior.

Files likely touched:
- `src/deep_memory/webui.py`
- `tests/test_webui.py`

Acceptance checklist:
- [ ] Empty state explains what `deep-memory` stores and what a contributor can do next.
- [ ] Render still includes accessible labels and local-only behavior.
- [ ] Tests cover the empty-state output.

Suggested commands:
```bash
uv run pytest -q tests/test_webui.py tests/test_webui_graph.py
uv run ruff check .
```

## 4. Add Hermes adapter smoke transcript example

Suggested labels:
- `good first issue`
- `lane:adapters`
- `type:adapter`
- `p2-ecosystem`

Why this matters:
Adapter claims become much more credible when a maintainer can inspect a small redacted transcript showing pre-task search, explicit durable fact export, and import into the local DB.

Scope:
- In scope:
  - add one redacted Hermes smoke transcript example to docs;
  - include runtime, command, DB path, pre-task search, facts JSONL shape, and import step;
  - make it explicit which parts are verified locally versus runtime-specific.
- Out of scope:
  - changing the Hermes adapter code path itself;
  - auto-capturing raw transcripts;
  - documenting every runtime in one issue.

Files likely touched:
- `docs/AGENT_QUICKSTART_MATRIX.md`
- `docs/ADAPTERS.md` or a new doc under `docs/`

Acceptance checklist:
- [ ] Transcript is redacted and contains no secrets or raw private logs.
- [ ] It shows pre-task search and post-task explicit write/import.
- [ ] The doc clearly separates verified local commands from pending runtime verification.

Suggested commands:
```bash
uv run pytest -q tests/test_hermes_adapter.py
uv run python - <<'PY'
from pathlib import Path
text = Path('docs/AGENT_QUICKSTART_MATRIX.md').read_text(encoding='utf-8')
assert 'hermes-import' in text
assert 'search before meaningful work' in text.lower()
print('hermes smoke transcript references ok')
PY
```

## 5. Expand docs troubleshooting for first-time local setup failures

Suggested labels:
- `good first issue`
- `lane:docs`
- `type:docs`
- `p2-ecosystem`

Why this matters:
A lot of contributors fail before they even reach the interesting memory problem. A small troubleshooting path is one of the highest-leverage docs contributions.

Scope:
- In scope:
  - add a short troubleshooting section or doc for `uv sync --extra dev`, optional `--extra mcp`, pytest failures, ruff failures, and missing runtime CLIs;
  - link it from `CONTRIBUTING.md`;
  - keep platform-specific notes minimal and only where behavior differs.
- Out of scope:
  - packaging redesign;
  - support for every external runtime;
  - rewriting the entire quickstart.

Files likely touched:
- `CONTRIBUTING.md`
- one new doc such as `docs/TROUBLESHOOTING.md`

Acceptance checklist:
- [ ] Covers setup, pytest, ruff, optional MCP extra, and missing CLI cases.
- [ ] `CONTRIBUTING.md` links to the troubleshooting path.
- [ ] Guidance stays local-first and reproducible.

Suggested commands:
```bash
uv sync --extra dev
uv run pytest -q
uv run ruff check .
```

## 6. Add export/import example for inspectable backup and restore flow

Suggested labels:
- `good first issue`
- `lane:docs`
- `type:docs`
- `p2-ecosystem`

Why this matters:
If users cannot understand export/delete/restore behavior, they will not trust persistent memory. A small example makes the inspectability story more concrete.

Scope:
- In scope:
  - add one docs example showing export, include-deprecated export, and what a safe restore/import path would look like today;
  - explain provenance expectations and what is and is not preserved;
  - keep the example local and file-based.
- Out of scope:
  - building a full restore command if it does not already exist;
  - cloud sync or hosted backup flows.

Files likely touched:
- `README.md`
- `docs/MEMORY_POLICY.md` or `docs/SAFETY_AND_PRIVACY.md`
- possibly `docs/COMMUNITY.md`

Acceptance checklist:
- [ ] Example includes active export and `--include-deprecated` audit export.
- [ ] Docs do not overclaim a restore path that does not exist.
- [ ] Provenance and deletion semantics are explained clearly.

Suggested commands:
```bash
uv run pytest -q tests/test_cli_export_delete.py
uv run python - <<'PY'
from pathlib import Path
text = Path('README.md').read_text(encoding='utf-8')
assert 'include-deprecated' in text
print('export docs reference ok')
PY
```

## 7. Add mixed Chinese/English retrieval fixture examples with contributor notes

Suggested labels:
- `good first issue`
- `lane:evals`
- `type:eval`
- `chinese-retrieval`
- `p1-core`

Why this matters:
Chinese-first retrieval is part of the positioning, but realistic developer phrasing is often mixed-language. This is a strong newcomer issue because it is concrete, measurable, and directly tied to product claims.

Scope:
- In scope:
  - add at least 10 mixed Chinese/English fixture rows with aliases, punctuation, and technical terms;
  - include expected top result ids or content snippets;
  - add a short note explaining what retrieval behavior the examples stress.
- Out of scope:
  - changing the retrieval architecture itself;
  - adding hosted embedding services.

Files likely touched:
- `evals/data/zh_memory_retrieval_v2.jsonl`
- `tests/test_chinese_retrieval_eval.py`
- `docs/CHINESE_RETRIEVAL_EVAL.md`

Acceptance checklist:
- [ ] At least 10 new fixture rows added.
- [ ] Expected behavior is explicit for each new case.
- [ ] Eval and tests still pass.

Suggested commands:
```bash
uv run python evals/chinese_retrieval_eval.py --data evals/data/zh_memory_retrieval_v2.jsonl --json
uv run pytest -q tests/test_chinese_retrieval_eval.py
```

## Published issues

| Draft | GitHub issue |
| --- | --- |
| Add privacy-boundary eval fixtures for obvious deny cases | #6 |
| Add workspace scope-isolation regression case with clear contributor narrative | #7 |
| Polish WebUI empty state for a fresh local database | #8 |
| Add Hermes adapter smoke transcript example | #9 |
| Expand docs troubleshooting for first-time local setup failures | #10 |
| Add export/import example for inspectable backup and restore flow | #11 |
| Add mixed Chinese/English retrieval fixture examples with contributor notes | #12 |
