# Next Phase Backlog


The backlog below is part of the controlled preview track, not a signal that the broader launch gate has been opened. Each item should still produce a local artifact, fixture, transcript, or command output that a maintainer can inspect.

Recommended baseline before opening a PR:

```bash
uv run pytest -q
uv run ruff check .
```

For docs-only changes, also run the Markdown link check from [`AGENT_QUICKSTART_MATRIX.md`](AGENT_QUICKSTART_MATRIX.md#verification-commands-for-this-repository).

## Labels to use

- `good first issue`: small, well-scoped, no architecture decision required.
- `help wanted`: useful, but needs domain context or maintainer review.
- `adapter`: agent runtime, wrapper, MCP, or explicit import/export integration.
- `eval`: fixture, benchmark, metric script, or failure taxonomy.
- `governance`: consent, privacy, policy, delete/export, conflict lifecycle.
- `docs`: README, guides, troubleshooting, glossary, architecture explanation.

## Good-first-issue lane

The first maintainer-ready batch now lives in [`GOOD_FIRST_ISSUE_DRAFTS.md`](GOOD_FIRST_ISSUE_DRAFTS.md). Use the items below as the backlog map and use the draft file when opening the actual GitHub issues.

### 1. Add mixed Chinese/English query fixtures

Why it matters: Chinese-first retrieval should be proven with realistic developer phrasing, not only clean examples.

Acceptance criteria:

- Add at least 10 fixture rows covering aliases, time expressions, punctuation-heavy text, and mixed Chinese/English technical terms.
- Include expected top result IDs or expected content snippets.
- Document the case category in the fixture or eval notes.

Suggested verification:

```bash
uv run python evals/chinese_retrieval_eval.py --data evals/data/zh_memory_retrieval_v2.jsonl --json
uv run pytest -q tests/test_chinese_retrieval_eval.py
```

### 2. Improve CLI search output scanability

Why it matters: contributors and agents need to inspect record ID, kind, score, source, and conflict state quickly.

Acceptance criteria:

- `deep-memory search` output clearly shows record id, kind, score, source, and conflict/deprecated status.
- Existing search behavior remains backward compatible at the data level.
- Add or update tests for the output shape.

Suggested verification:

```bash
uv run pytest -q tests/test_core.py
uv run deep-memory search .deep-memory/deep-memory.db "repo conventions" || true
```

### 3. Add a small glossary to the docs

Why it matters: memory governance terms should be consistent before the project gets more contributors.

Acceptance criteria:

- Define working memory, episodic memory, semantic memory, procedural memory, conflict candidate, superseded, deprecated, and skill candidate.
- Link the glossary from `docs/COMMUNITY.md` or `CONTRIBUTING.md`.
- Keep definitions short and aligned with current code behavior.

Suggested verification:

```bash
uv run python - <<'PY'
from pathlib import Path
for target in ['working memory', 'procedural memory', 'deprecated']:
    assert target in Path('docs/GLOSSARY.md').read_text(encoding='utf-8').lower()
print('glossary terms ok')
PY
```

## Help-wanted lane

### 4. Create a memory failure case taxonomy

Why it matters: good issues should become evals rather than anecdotes.

Acceptance criteria:

- Add a short taxonomy for failed recall, wrong recall, stale recall, over-memory, privacy-boundary write, and missing provenance.
- Map each category to at least one suggested fixture shape.
- Link the taxonomy from the community contribution path.

Suggested verification:

```bash
uv run pytest -q
uv run ruff check .
```

### 5. Add a maintainer smoke-transcript format

Why it matters: adapter claims are only useful when a maintainer can replay or inspect the evidence.

Acceptance criteria:

- Define a redacted transcript template for adapter smoke tests.
- Include fields for runtime, command, DB path, pre-task search, post-task write, skipped private data, and observed output.
- Add one filled example for an existing wrapper or Hermes import path.

Suggested verification:

```bash
uv run pytest -q tests/test_hermes_adapter.py tests/test_codex_wrapper.py
```

## Adapter lane

### 6. Add a Claude Code MCP smoke transcript

Why it matters: MCP is the cleanest cross-agent surface when supported by the runtime.

Acceptance criteria:

- Document the exact `claude mcp add deep-memory -- ...` command with placeholders for absolute paths.
- Include a redacted transcript showing pre-task search and an explicit durable write.
- State what is verified locally and what remains runtime-specific.

Suggested verification:

```bash
uv run deep-memory-mcp --help || true
uv run pytest -q tests/test_mcp_server.py
```

### 7. Expand Codex/OpenCode wrapper compatibility notes

Why it matters: wrapper integrations should preserve the same consent and provenance model as MCP.

Acceptance criteria:

- Document command shape, environment variables, DB path, and facts-out JSONL contract.
- Add at least one malformed facts-out example that should be skipped or rejected.
- Include privacy guidance for redacting prompts and session data.

Suggested verification:

```bash
uv run pytest -q tests/test_codex_wrapper.py tests/test_hermes_adapter.py
```

## Eval lane

### 8. Add privacy-boundary eval fixtures

Why it matters: “should not remember” behavior is part of memory quality.

Acceptance criteria:

- Add examples for secrets, raw credentials, auth cookies, raw private identifiers, and temporary task status.
- Verify deny or requires-confirmation classification using the memory policy layer.
- Document at least one false-positive tradeoff.

Suggested verification:

```bash
uv run pytest -q tests/test_memory_policy.py tests/test_cli_export_delete.py
```

### 9. Add Memory × Skill activation regression cases

Why it matters: procedural memory should become reviewable skill candidates, not silent behavior changes.

Acceptance criteria:

- Add procedural-memory examples that should and should not become skill candidates.
- Verify exported candidates include review boundaries and safety notes.
- Document the activation loop in the relevant docs.

Suggested verification:

```bash
uv run pytest -q tests/test_skill_export.py tests/test_skill_activation_loop_docs.py
```

## Governance lane

### 10. Tighten write-policy documentation with examples

Why it matters: contributors need concrete allow / deny / requires-confirmation examples before adding automatic writes.

Acceptance criteria:

- Add examples for durable project conventions, user preferences, secrets, private data, and stale task state.
- Keep the docs aligned with the policy tests.
- Link from README, community docs, or adapter docs where automatic writes are mentioned.

Suggested verification:

```bash
uv run pytest -q tests/test_memory_policy.py
```

### 11. Review export/delete guarantees across adapters

Why it matters: cross-agent memory only works if deletion and export semantics remain inspectable.

Acceptance criteria:

- Document how CLI, MCP, Hermes import, and wrapper paths preserve source/provenance.
- Add or update tests for deprecated records not leaking into default export/search paths.
- Note any adapter-specific limitation explicitly.

Suggested verification:

```bash
uv run pytest -q tests/test_cli_export_delete.py tests/test_core.py tests/test_hermes_adapter.py
```

## Docs lane

### 12. Add troubleshooting for local setup failures

Why it matters: early contributors often fail before reaching the interesting memory problem.

Acceptance criteria:

- Cover `uv sync --extra dev`, optional `--extra mcp`, pytest failures, ruff failures, and missing runtime CLIs.
- Include Linux/macOS/Windows notes only where behavior differs.
- Link from `CONTRIBUTING.md`.

Suggested verification:

```bash
uv sync --extra dev
uv run pytest -q
uv run ruff check .
```

### 13. Keep README contributor links current

Why it matters: new contributors should land on the backlog, not infer priorities from stale bullets.

Acceptance criteria:

- README and README.zh-CN link to this backlog and `docs/COMMUNITY.md`.
- The visible contribution bullets match the current lanes.
- Markdown links resolve locally.

Suggested verification:

```bash
uv run python - <<'PY'
from pathlib import Path
for file in ['README.md', 'README.zh-CN.md']:
    text = Path(file).read_text(encoding='utf-8')
    assert 'docs/NEXT_PHASE_BACKLOG.md' in text
    assert 'docs/COMMUNITY.md' in text
print('readme contributor links ok')
PY
```
