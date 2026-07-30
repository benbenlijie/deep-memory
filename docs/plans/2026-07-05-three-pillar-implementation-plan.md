# Deep Memory Three-Pillar Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task after the design is accepted.

**Goal:** Build the next Deep Memory iteration around three product pillars: unified cross-agent memory substrate, memory governance/audit/curation, and Memory → Skill/Docs/Tests capability loop.

**Architecture:** Extend the existing local SQLite + CLI/MCP/SDK architecture with a stable adapter event schema, centralized policy/scope/provenance gate, audit events, hygiene reports, and candidate artifact generators. Keep the product local-first and review-gated for behavior-changing outputs.

**Tech Stack:** Python 3.10+, SQLite/FTS5, existing `src/deep_memory/` SDK/CLI/MCP modules, pytest, ruff, Markdown docs.

**Primary design doc:** `docs/design/2026-07-05-deep-memory-strategic-design.md`

---

## Phase 0 — Planning and Scope Lock

### Task 0.1: Confirm milestone acceptance criteria

**Objective:** Freeze the first milestone as a testable product slice.

**Files:**
- Read: `docs/design/2026-07-05-deep-memory-strategic-design.md`
- Modify: `docs/ROADMAP.md`
- Create/Modify: `docs/NEXT_PHASE_BACKLOG.md`

**Steps:**
1. Add a section named `Three-Pillar M1` to `docs/ROADMAP.md`.
2. State the demo acceptance criteria:
   - one agent/import shim writes a project-scoped procedural memory;
   - another agent/recall shim retrieves it in the same project;
   - a different project does not retrieve it;
   - the write emits an audit event;
   - governance/hygiene report shows the record;
   - procedural memory exports a reviewable skill candidate with evidence.
3. Add issue-sized backlog items under adapter, governance, curation, promotion, and eval lanes.
4. Do not start implementation until the roadmap/backlog wording matches the design doc.

**Verification:**

```bash
grep -n "Three-Pillar M1" docs/ROADMAP.md
grep -n "cross-agent" docs/NEXT_PHASE_BACKLOG.md
```

---

## Phase 1 — Unified Memory Substrate

### Task 1.1: Define adapter event schema

**Objective:** Create a stable machine-readable contract for agents to submit memory observations.

**Files:**
- Create: `docs/adapter-event-schema.json`
- Create: `docs/ADAPTER_EVENT_SCHEMA.md`
- Test: `tests/test_adapter_event_schema.py`

**Expected schema concepts:**

```json
{
  "agent": "codex",
  "event": "post_task_extraction",
  "cwd": "/repo/path",
  "scope": "project",
  "scope_id": "github.com/org/repo",
  "observations": [
    {
      "kind": "procedural",
      "content": "Workflow: run uv run pytest -q before release review.",
      "confidence": 0.84,
      "importance": 0.78,
      "origin_type": "verified_workflow",
      "evidence": ["command: uv run pytest -q => passed"]
    }
  ]
}
```

**Steps:**
1. Write JSON schema with required fields: `agent`, `event`, `observations`.
2. Allow optional `cwd`, `scope`, `scope_id`, `tenant`, `workspace`.
3. Require each observation to include `kind`, `content`, `confidence`, `importance`, `origin_type`.
4. Document examples for Hermes, Codex, Claude Code, and OpenClaw/OpenCode-style agents.
5. Add tests validating one good fixture and several bad fixtures.

**Verification:**

```bash
uv run pytest -q tests/test_adapter_event_schema.py
uv run ruff check tests/test_adapter_event_schema.py
```

---

### Task 1.2: Add scope derivation and explanation command

**Objective:** Make project/workspace scope derivation inspectable before writes or recalls.

**Files:**
- Modify/Create: `src/deep_memory/scope.py`
- Modify: `src/deep_memory/cli.py`
- Test: `tests/test_scope_derivation.py`
- Test: `tests/test_cli_scope_explain.py`

**Behavior:**

```bash
deep-memory scope explain --cwd /path/to/repo --json
```

Expected output shape:

```json
{
  "scope": "project",
  "scope_id": "github.com/org/repo",
  "method": "git_remote",
  "cwd": "/path/to/repo"
}
```

**Steps:**
1. Implement `derive_scope(cwd, explicit_scope=None, explicit_scope_id=None)`.
2. Prefer explicit arguments when provided.
3. If inside git repo with remote, derive stable normalized remote identity.
4. If no remote, fall back to repo root path hash or configured project name.
5. Expose CLI command `scope explain`.
6. Add tests for explicit values, git remote, no remote fallback, and non-repo path.

**Verification:**

```bash
uv run pytest -q tests/test_scope_derivation.py tests/test_cli_scope_explain.py
uv run ruff check src/deep_memory/scope.py src/deep_memory/cli.py tests/test_scope_derivation.py tests/test_cli_scope_explain.py
```

---

### Task 1.3: Persist source agent and origin metadata on writes

**Objective:** Track which agent/source produced a memory so audit and curation can explain it.

**Files:**
- Modify: `src/deep_memory/core.py` or current memory engine module
- Modify: `src/deep_memory/storage.py` or current DB schema module
- Modify: `src/deep_memory/cli.py`
- Test: `tests/test_memory_source_metadata.py`

**Data fields:**

- `source_agent`
- `origin_type`
- `evidence_refs` or equivalent serialized evidence field

**Steps:**
1. Inspect current schema/migrations and add fields in the least disruptive way.
2. Update `DeepMemory.add(...)` to accept optional source metadata.
3. Update CLI add/import paths to pass metadata.
4. Ensure old DBs migrate or default safely.
5. Add tests proving search/export surfaces the metadata.

**Verification:**

```bash
uv run pytest -q tests/test_memory_source_metadata.py
uv run pytest -q tests/test_core.py tests/test_cli.py
uv run ruff check src/deep_memory tests/test_memory_source_metadata.py
```

---

### Task 1.4: Implement adapter event import CLI

**Objective:** Let agent adapters submit structured observations through one policy/scope-aware import path.

**Files:**
- Modify/Create: `src/deep_memory/adapters/events.py`
- Modify: `src/deep_memory/cli.py`
- Test: `tests/test_adapter_event_import.py`
- Fixture: `tests/fixtures/adapter_events/codex_post_task.json`

**CLI:**

```bash
deep-memory agent import-events ~/.deep-memory/deep-memory.db tests/fixtures/adapter_events/codex_post_task.json --json
```

**Steps:**
1. Parse and validate adapter event JSON.
2. Derive scope if absent.
3. Route observations through the existing automatic write policy, not direct durable writes.
4. Persist accepted memories with `source_agent`, `origin_type`, evidence, confidence, and importance.
5. Return counts: written, short_term, denied, confirmation_required, errors.

**Verification:**

```bash
uv run pytest -q tests/test_adapter_event_import.py
uv run ruff check src/deep_memory/adapters/events.py src/deep_memory/cli.py tests/test_adapter_event_import.py
```

---

### Task 1.5: Implement pre-task recall CLI for agents

**Objective:** Provide a compact scoped recall command usable by Hermes/Codex/Claude/OpenClaw wrappers.

**Files:**
- Modify: `src/deep_memory/cli.py`
- Test: `tests/test_agent_recall_cli.py`

**CLI:**

```bash
deep-memory agent recall ~/.deep-memory/deep-memory.db \
  --agent hermes \
  --cwd /path/to/repo \
  --query "release review commands" \
  --limit 5 \
  --json
```

**Steps:**
1. Derive scope from `--cwd` unless explicit scope is supplied.
2. Search only within allowed scope plus optionally broader user/global records.
3. Return compact records with content, kind, score, scope, source_agent, origin_type, confidence.
4. Add text and JSON output.
5. Add tests proving scope isolation.

**Verification:**

```bash
uv run pytest -q tests/test_agent_recall_cli.py
uv run ruff check src/deep_memory/cli.py tests/test_agent_recall_cli.py
```

---

## Phase 2 — Governance / Audit / Curation

### Task 2.1: Add audit event model

**Objective:** Record durable write/lifecycle/recall/export events with enough metadata for audit reports.

**Files:**
- Modify/Create: `src/deep_memory/audit.py`
- Modify: DB schema/migration module
- Test: `tests/test_audit_events.py`

**Audit event fields:**

- `event_id`
- `memory_id`
- `event_type`
- `actor`
- `source_agent`
- `scope`
- `scope_id`
- `policy_decision`
- `evidence_refs`
- `created_at`

**Steps:**
1. Add audit table or append-only storage in SQLite.
2. Record events for accepted writes from SDK/CLI/import path.
3. Record lifecycle changes: supersede, deprecate, hard delete if currently supported.
4. Keep recall event logging optional or aggregate-only if full recall logs are too noisy.
5. Add tests for write and delete/deprecate audit events.

**Verification:**

```bash
uv run pytest -q tests/test_audit_events.py
uv run ruff check src/deep_memory/audit.py tests/test_audit_events.py
```

---

### Task 2.2: Verify all write paths use shared policy gate

**Objective:** Prevent bypasses where older helpers write durable memory without policy/scope/governance checks.

**Files:**
- Modify: relevant SDK/CLI/MCP/import modules
- Test: `tests/test_write_policy_coverage.py`

**Steps:**
1. Enumerate write paths:
   - SDK `DeepMemory.add(...)`;
   - CLI `add`;
   - MCP add tool;
   - Hermes/Codex import;
   - new adapter event import;
   - WebUI edit path if in scope.
2. Write regression tests for secret/raw transcript/task-status denial across paths.
3. Ensure procedural verified facts are allowed.
4. Ensure high-risk/confirmation cases do not auto-write.

**Verification:**

```bash
uv run pytest -q tests/test_write_policy_coverage.py tests/test_memory_policy.py tests/test_automatic_write_policy.py
uv run ruff check src/deep_memory tests/test_write_policy_coverage.py
```

---

### Task 2.3: Add hygiene report CLI

**Objective:** Give users a governance view without forcing per-memory approval.

**Files:**
- Create/Modify: `src/deep_memory/hygiene.py`
- Modify: `src/deep_memory/cli.py`
- Test: `tests/test_hygiene_report.py`

**CLI:**

```bash
deep-memory hygiene report ~/.deep-memory/deep-memory.db --scope project --scope-id <id> --format markdown
```

**Report sections:**

- new records;
- stale records;
- duplicates/merge candidates;
- conflicts/candidates;
- risky denied/confirmation-required attempts if recorded;
- frequently recalled records;
- never recalled records;
- skill/docs/test candidates.

**Steps:**
1. Start with deterministic simple heuristics.
2. Produce markdown and JSON output.
3. Include source_agent, origin_type, scope, confidence, status.
4. Add tests with a fixture DB.

**Verification:**

```bash
uv run pytest -q tests/test_hygiene_report.py
uv run ruff check src/deep_memory/hygiene.py src/deep_memory/cli.py tests/test_hygiene_report.py
```

---

### Task 2.4: Add Markdown export pack

**Objective:** Let users inspect and carry scoped memory as markdown files.

**Files:**
- Create/Modify: `src/deep_memory/export_pack.py`
- Modify: `src/deep_memory/cli.py`
- Test: `tests/test_export_pack.py`

**CLI:**

```bash
deep-memory export pack ~/.deep-memory/deep-memory.db --scope project --scope-id <id> --out /tmp/memory-pack
```

**Files generated:**

- `MEMORY.md`
- `PROCEDURES.md`
- `PROJECT_RULES.md`
- `PREFERENCES.md`
- `CONFLICTS.md`
- `AUDIT_SUMMARY.md`

**Verification:**

```bash
uv run pytest -q tests/test_export_pack.py
uv run ruff check src/deep_memory/export_pack.py src/deep_memory/cli.py tests/test_export_pack.py
```

---

## Phase 3 — Memory → Skill / Docs / Tests Loop

### Task 3.1: Extend procedural skill candidate export with evidence metadata

**Objective:** Ensure skill candidates preserve source/evidence/safety metadata and never auto-install.

**Files:**
- Modify: `src/deep_memory/skill_export.py`
- Modify: `docs/MEMORY_TO_SKILL.md`
- Test: `tests/test_skill_export.py`

**Steps:**
1. Add fields for source_agent, origin_type, evidence, scope, scope_id.
2. Add stale/private data guard to candidate generation.
3. Ensure output includes `auto_install: false`.
4. Update docs and tests.

**Verification:**

```bash
uv run pytest -q tests/test_skill_export.py
uv run ruff check src/deep_memory/skill_export.py tests/test_skill_export.py
```

---

### Task 3.2: Add docs candidate generator

**Objective:** Convert stable semantic/project-rule memory into reviewable docs patch drafts.

**Files:**
- Create: `src/deep_memory/candidates/docs.py`
- Create: `tests/test_docs_candidate_export.py`
- Modify: `src/deep_memory/cli.py`

**CLI:**

```bash
deep-memory candidates docs ~/.deep-memory/deep-memory.db --scope project --scope-id <id> --format markdown
```

**Output:**

A markdown draft with:

- proposed doc section;
- source memory IDs;
- evidence/source summary;
- why it should become docs;
- review checklist.

**Verification:**

```bash
uv run pytest -q tests/test_docs_candidate_export.py
uv run ruff check src/deep_memory/candidates/docs.py src/deep_memory/cli.py tests/test_docs_candidate_export.py
```

---

### Task 3.3: Add test/eval candidate generator

**Objective:** Turn failures, conflicts, and retrieval misses into candidate regression tests or eval fixtures.

**Files:**
- Create: `src/deep_memory/candidates/tests.py`
- Create: `tests/test_test_candidate_export.py`
- Modify: `src/deep_memory/cli.py`

**Candidate types:**

- policy regression;
- scope isolation regression;
- retrieval fixture;
- conflict lifecycle fixture;
- skill activation regression.

**Verification:**

```bash
uv run pytest -q tests/test_test_candidate_export.py
uv run ruff check src/deep_memory/candidates/tests.py src/deep_memory/cli.py tests/test_test_candidate_export.py
```

---

### Task 3.4: Build full capability bundle demo

**Objective:** Demonstrate one verified procedural memory becoming a skill/docs/test candidate bundle.

**Files:**
- Create: `examples/three_pillar_demo/README.md`
- Create: `examples/three_pillar_demo/codex_post_task.json`
- Create: `tests/test_three_pillar_demo.py`

**Demo steps:**
1. Initialize temp DB.
2. Import adapter event containing verified procedural workflow.
3. Recall from another agent identity in same scope.
4. Confirm other scope does not recall it.
5. Generate hygiene report.
6. Export skill candidate.
7. Export docs candidate.
8. Export test/eval candidate.

**Verification:**

```bash
uv run pytest -q tests/test_three_pillar_demo.py
uv run ruff check examples/three_pillar_demo tests/test_three_pillar_demo.py
```

---

## Phase 4 — Evaluation and Release Gate

### Task 4.1: Add cross-agent memory benchmark

**Objective:** Measure the primary product wedge explicitly.

**Files:**
- Create: `evals/cross_agent_memory/`
- Create: `benchmarks/cross_agent_memory.py`
- Create/Modify: `docs/MEMORY_BENCHMARK.md`

**Cases:**
- preference recall across agents;
- project convention recall across agents;
- scope isolation;
- stale memory handling;
- deletion correctness;
- procedural recall;
- Chinese mixed-token recall.

**Verification:**

```bash
uv run python benchmarks/cross_agent_memory.py --json
uv run pytest -q tests/test_memory_benchmark.py
```

---

### Task 4.2: Add release-gate checklist

**Objective:** Prevent shipping the next iteration without evidence.

**Files:**
- Create: `docs/release-gate-three-pillar-m1.md`

**Required evidence:**

```bash
uv run pytest -q
uv run ruff check .
git diff --check
uv run python benchmarks/cross_agent_memory.py --json
```

Also include:
- demo transcript;
- generated hygiene report path;
- generated candidate bundle path;
- known limitations.

---

## Parallelization Plan

After Phase 0/1.1 schema is accepted, work can split into lanes:

1. **Adapter lane:** Tasks 1.2–1.5.
2. **Governance lane:** Tasks 2.1–2.4.
3. **Promotion lane:** Tasks 3.1–3.4.
4. **Eval lane:** Tasks 4.1–4.2.

Use Kanban only once implementation starts because this is multi-lane, auditable work. Each lane should report:

- changed files;
- tests run;
- policy/scope boundary touched;
- evidence artifact paths;
- blockers or open questions.

## Stop Conditions

Stop or ask for product decision if:

- scope derivation cannot be made deterministic enough;
- write policy would require high-friction per-memory approval;
- candidate generation starts auto-installing behavior changes;
- cross-agent demo cannot prove scope isolation;
- implementation requires cloud/service dependencies for the local-first M1.

## Final Acceptance Criteria

The M1 is complete only when all are true:

- [ ] Design doc saved and accepted.
- [ ] Adapter event import works.
- [ ] Scope explain and agent recall work.
- [ ] Cross-agent same-scope recall passes.
- [ ] Cross-project isolation passes.
- [ ] Audit event exists for write/import.
- [ ] Hygiene report works.
- [ ] Skill candidate export includes evidence and `auto_install: false`.
- [ ] Docs/test/eval candidate path exists.
- [ ] Full tests, ruff, and diff-check pass.
- [ ] Release-gate doc records real command output.
