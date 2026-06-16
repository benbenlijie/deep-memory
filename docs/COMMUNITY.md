# Community Architecture

`deep-memory` should become an ecosystem, not a single-maintainer repository. The community model is deliberately lane-based: each lane has a clear boundary, a small first contribution path, and a way to graduate into deeper ownership.

If you退后一步看，the root problem is not “more contributors”. The root problem is representation: contributors need to see where their work fits in the memory system, how to test it, and what kind of evidence makes a change credible.

## Contribution principles

- Small, tested pull requests beat broad rewrites.
- Every claim about memory quality should eventually become an eval, fixture, benchmark, or reproducible demo.
- Local-first and inspectable are product constraints, not implementation details.
- Chinese-first retrieval is a benchmark target, not just README positioning.
- New integrations should preserve user control: explicit writes, inspectable sources, and safe handling of private data.

## Community lanes

| Lane | System boundary | Good first issues | Deeper ownership path | Evidence expected |
| --- | --- | --- | --- | --- |
| Retrieval | Query parsing, FTS5, Chinese fallback, future tokenizer/embedding/hybrid retrieval | Add Chinese/English mixed-query fixtures; document a failed recall; add recall@k examples | Own retrieval benchmark design and retrieval strategy changes | `uv run pytest tests/test_core.py` plus benchmark/eval output when ranking changes |
| Adapters | Hermes, MCP, Claude Code, Codex, OpenCode and future agent runtimes | Add a redacted session fixture; improve adapter docs; add runtime-specific smoke tests | Own one runtime adapter and its compatibility matrix | Adapter unit tests, manual command transcript, privacy notes |
| UI | Future CLI inspector, web memory editor, graph/timeline visualizer | Improve CLI output labels; add screenshots/mockups; design record correction flows | Own memory inspection and correction UX | Screenshot/demo, before/after CLI output, usability notes |
| Evals | Memory failure cases, retrieval metrics, memory/no-memory comparisons, Memory × Skill evals | Convert one issue into an eval fixture; add a baseline row; categorize a failure mode | Own public benchmark and leaderboard methodology | Dataset diff, metric script output, failure taxonomy update |
| Docs | README, architecture, roadmap, integration guides, release notes | Fix quickstart gaps; add troubleshooting notes; translate examples; tighten contribution docs | Own documentation information architecture | Link check or manual command transcript; docs reviewed against current code |

## Suggested good-first-issue backlog

Use labels from the proposal below so newcomers can filter by lane and difficulty.

### Retrieval

- Add 10 Chinese user-preference recall fixtures covering aliases, time expressions, and mixed Chinese/English technical terms.
- Add a minimal `recall@k` script for the existing SQLite/FTS5 + Chinese bigram fallback.
- Document one reproducible wrong-recall case using a small local database.
- Add tests for queries containing punctuation-heavy Chinese developer text.

### Adapters

- Add a redacted Hermes JSONL fixture for `write_hermes_session_facts`.
- Add an MCP smoke-test transcript that a maintainer can run manually.
- Propose the minimal contract for a Claude Code / Codex / OpenCode adapter: input events, extracted facts, source strings, and error handling.
- Add adapter documentation for how private data should be redacted before filing issues.

### UI

- Improve `deep-memory search` output so record id, kind, score, source, and conflict status are easy to scan.
- Add a CLI design note for `deep-memory inspect`, `edit`, `delete`, and `export` commands.
- Create a low-fidelity mockup for a memory timeline / conflict resolution screen.
- Add examples showing how a deprecated or superseded memory should appear to a user.

### Evals

- Turn one `Memory failure case` issue into a JSON/JSONL fixture.
- Add an eval category for “should not remember / privacy boundary”.
- Add a memory/no-memory example with a measurable success criterion instead of only qualitative output.
- Add baseline metric documentation for lexical FTS, Chinese bigram fallback, tokenizer retrieval, embedding retrieval, and hybrid retrieval.

### Docs

- Add a “choose your contribution lane” section to `CONTRIBUTING.md`.
- Add troubleshooting for `uv sync`, `uv run pytest`, and optional MCP dependencies.
- Add a glossary for working memory, episodic memory, semantic memory, procedural memory, conflict candidate, superseded, and deprecated.
- Add one complete backend-adapter walkthrough from design to tests.

## Issue templates proposal

The repo already has a `Memory failure case` issue template. The next useful templates are:

1. `Backend / adapter proposal`
   - Runtime or backend name.
   - Use case and expected memory flow.
   - Minimal API / event contract.
   - Privacy and source/provenance handling.
   - Test plan and maintenance owner.

2. `Good first issue`
   - Lane: retrieval / adapters / UI / evals / docs.
   - Why it matters.
   - Files likely touched.
   - Acceptance checklist.
   - Suggested commands.

3. `Evaluation fixture`
   - Failure category.
   - Redacted input memories / events.
   - Query or task.
   - Expected recall / behavior.
   - Baseline result and gap.

## Labels proposal

### Type labels

- `type:bug` — code behavior is wrong or broken.
- `type:docs` — documentation, examples, or tutorials.
- `type:eval` — datasets, metrics, benchmarks, failure taxonomy.
- `type:feature` — new product capability.
- `type:adapter` — runtime/backend integration.
- `type:research` — design exploration requiring evidence before implementation.

### Lane labels

- `lane:retrieval`
- `lane:adapters`
- `lane:ui`
- `lane:evals`
- `lane:docs`

### Difficulty labels

- `good first issue` — small, well-scoped, no architecture decision required.
- `help wanted` — useful but not necessarily beginner-friendly.
- `needs design` — requires design discussion before code.
- `blocked` — waiting on another issue, maintainer decision, or external dependency.

### Memory-quality labels

- `memory-case` — concrete memory failure report.
- `privacy-boundary` — should-not-remember or data minimization concern.
- `conflict-resolution` — contradictory/stale/superseded memory behavior.
- `chinese-retrieval` — Chinese or mixed-language retrieval quality.
- `memory-skill` — Memory × Skill compounding path.

### Priority labels

- `p0-launch` — blocks launch credibility or first-screen conversion.
- `p1-core` — important for the near-term memory governance loop.
- `p2-ecosystem` — valuable for community expansion.

## Contributor path: new memory backends

A memory backend is any storage/retrieval substrate behind the same conceptual memory contract: records, provenance, ranking, lifecycle state, and inspectability. Do not start by replacing SQLite everywhere. Start by proving the backend improves a bottleneck.

1. Open a `Backend / adapter proposal` issue.
2. State the backend’s root value: better retrieval, scale, graph/time reasoning, interoperability, or deployment fit.
3. Define the minimum interface:
   - add/get/search records;
   - preserve `MemoryRecord` fields;
   - expose source/provenance;
   - preserve conflict status, supersession, deprecation, and timestamps;
   - support deterministic tests.
4. Add fixtures that compare the backend against SQLite/FTS5 on the same memory set.
5. Keep backend-specific dependencies optional.
6. Add docs showing installation, configuration, and a rollback path to SQLite.
7. Include a privacy note: where data is stored, whether it leaves the machine, and how deletion/export works.

A backend should graduate only when it passes the same functional tests as SQLite plus at least one backend-specific value test.

## Contributor path: new adapters

An adapter connects `deep-memory` to an agent runtime, framework, or protocol. The safe default is explicit fact import/export rather than silent automatic memory extraction.

1. Open a `Backend / adapter proposal` issue and label it `lane:adapters`.
2. Define the runtime event contract:
   - what input events are accepted;
   - which fields become memory content, kind, importance, confidence, and source;
   - how malformed or private data is handled.
3. Add a redacted fixture for the runtime.
4. Implement a thin adapter module under `src/deep_memory/adapters/`.
5. Add unit tests for import, skipped records, source strings, and error cases.
6. Add one manual smoke test command in docs.
7. Avoid background “remember everything” behavior until extraction quality and consent boundaries are evaluated.

An adapter should graduate only when a maintainer can run its smoke test from a clean checkout and inspect the written records.

## Maintainer review checklist

Before merging community contributions, ask:

- Does this change map to a lane and a real bottleneck?
- Is there an executable test, fixture, benchmark, or manual command transcript?
- Does it preserve local-first inspectability and user control?
- Are privacy boundaries explicit?
- Does it avoid overstating unproven claims?
- If it adds a dependency, is it optional or clearly justified?

## How to start

1. Run the project locally:

```bash
uv sync --extra dev
uv run pytest
uv run ruff check src tests
```

2. Pick one lane from this document.
3. Choose a `good first issue` with a narrow acceptance checklist.
4. Open a small PR with evidence: tests run, files changed, and any remaining uncertainty.

真正有趣的问题是 whether the repository can turn real memory failures into shared infrastructure. That is the community loop: report a failure, encode it as an eval, improve the mechanism, and document the path so the next contributor can go deeper.
