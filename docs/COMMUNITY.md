# Community Architecture


This repository is in controlled preview for the public launch track, not broad launch. The backlog below is written to keep the gate honest: small contributions, explicit verification, and remaining blockers called out clearly.

Stepping back, the root problem is not “more contributors” — it is representation. Contributors need to see where their work fits in the memory system, how to test it, and what kind of evidence makes a change credible.

## Contribution principles

- Small, tested pull requests beat broad rewrites.
- Every claim about memory quality should eventually become an eval, fixture, benchmark, or reproducible demo.
- Local-first and inspectable are product constraints, not implementation details.
- Chinese-first retrieval is a benchmark target, not just README positioning.
- New integrations should preserve user control: explicit writes, inspectable sources, and safe handling of private data.

## M+12 cross-agent ecosystem phase

The next public phase is not “add every integration.” It is to make the
repository easy to extend without weakening the memory-governance model.
Contributors should treat each lane as a small environment: define the contract,
add a fixture or transcript, run the verification command, and document the
safety boundary.

Primary lanes:

- `good first issue`: narrow docs, fixture, CLI output, or reproducible-failure
  tasks that do not require architecture decisions.
- `help wanted`: useful work that needs domain context, maintainer review, or
  cross-file coordination.
- `adapter`: runtime-specific wrappers, MCP setup docs, redacted transcripts,
  and compatibility notes.
- `eval`: retrieval fixtures, privacy-boundary cases, memory/no-memory checks,
  and benchmark reporting.
- `governance`: write policy, consent, export/delete, conflict lifecycle, and
  review checklists.
- `docs`: quickstarts, troubleshooting, contribution paths, glossary, and
  release-facing explanations.

Use [`NEXT_PHASE_BACKLOG.md`](NEXT_PHASE_BACKLOG.md) as the public backlog. Each
item there has acceptance criteria and suggested commands so a contributor can
know when the work is credible.

## Suggested backlog

The issue-sized backlog now lives in [`NEXT_PHASE_BACKLOG.md`](NEXT_PHASE_BACKLOG.md).
Keep this document focused on community architecture and contribution paths;
keep the backlog document focused on concrete tasks, acceptance criteria, and
verification commands.

## Issue templates proposal

The repo already has a `Memory failure case` issue template. The next useful templates are:

1. `Backend / adapter proposal`
   - Runtime or backend name.
   - Use case and expected memory flow.
   - Minimal API / event contract.
   - Privacy and source/provenance handling.
   - Test plan and maintenance owner.

2. `Good first issue`
   - Lane: good-first-issue / help-wanted / adapter / eval / governance / docs.
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
- `lane:governance`
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

The interesting question is whether the repository can turn real memory failures into shared infrastructure. That is the community loop: report a failure, encode it as an eval, improve the mechanism, and document the path so the next contributor can go deeper.
