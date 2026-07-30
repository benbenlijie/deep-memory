# Automatic Local Agent Memory Iteration Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task when moving from planning to code.

**Goal:** Build the next `deep-memory` iteration around automatic local cross-agent memory for individual power users.

**Architecture:** Keep the SQLite/local-first core. Add agent-native ingestion, automatic governance, cross-agent adapter flows, hygiene/reporting, and benchmark coverage as incremental layers around the existing `DeepMemory` model, MCP server, CLI, and adapters.

**Tech Stack:** Python 3.10-3.12, SQLite/FTS5, Typer CLI, pytest, optional MCP, existing `src/deep_memory` package.

---

## Success criteria for this iteration

1. A user can run a reproducible demo where one agent/source writes a project-scoped memory and another agent/source recalls it from the same local DB.
2. Automatic extraction can ingest a session-summary or facts JSONL file and classify durable memories without storing secrets, raw transcripts, or temporary status.
3. The system has a `hygiene` or equivalent report that summarizes new/conflicting/stale/low-confidence memories without requiring manual approval for every record.
4. Scope isolation, deletion correctness, and cross-agent recall are covered by executable tests or evals.
5. The docs clearly say this iteration is local-first, personal-user-focused, automatic by default, and not a cloud/team-sharing push.

---

## Execution order

README homepage optimization is important, but it should follow the core version
iteration. The README should showcase a working loop, not become the loop.

Recommended order:

1. **Core loop first:** Task 2 automatic extraction contract + Task 3 project
   scope auto-detection + Task 4 cross-agent demo.
2. **Safety and automation:** Task 5 policy-gated automatic write + Task 6 memory
   hygiene report.
3. **Evidence:** Task 7 Cross-Agent Memory Benchmark + Task 8 scoped Markdown
   export pack.
4. **Homepage refresh last:** Task 9 README redesign after the demo/evals produce
   concrete evidence to show above the fold.

Decision rule: do not update the README hero to imply automatic extraction is
fully shipped until Tasks 2, 4, and 5 have passing tests or reproducible demo
evidence.

---

## Task 1: Align public docs with the new iteration

**Objective:** Link the new design note from roadmap/architecture/adapter docs so the direction is discoverable.

**Files:**
- Modify: `docs/ROADMAP.md`
- Modify: `docs/ARCHITECTURE.md`
- Modify: `docs/ADAPTERS.md`
- Already created: `docs/AUTOMATIC_LOCAL_AGENT_MEMORY.md`

**Steps:**
1. Add a “Current iteration” section to `docs/ROADMAP.md` pointing to automatic local cross-agent memory.
2. Add an ingestion/governance paragraph to `docs/ARCHITECTURE.md` explaining automatic extraction + automatic policy gating.
3. Update `docs/ADAPTERS.md` language from “write only explicit facts” to “automatic extraction through policy-gated facts/procedures,” preserving no raw transcript scraping.
4. Run Markdown sanity checks.

**Verification:**

```bash
python - <<'PY'
from pathlib import Path
for file in ['docs/ROADMAP.md', 'docs/ARCHITECTURE.md', 'docs/ADAPTERS.md']:
    text = Path(file).read_text(encoding='utf-8')
    assert 'AUTOMATIC_LOCAL_AGENT_MEMORY.md' in text or 'automatic' in text.lower()
print('docs linked')
PY
```

---

## Task 2: Define the automatic extraction contract

**Objective:** Specify and test the input/output schema for automatic session-summary ingestion.

**Files:**
- Create or modify: `docs/research/extraction-contract.md`
- Create: `tests/test_automatic_extraction_contract.py`
- Modify or create later: `src/deep_memory/extraction.py`

**Design:**

Input shape should support a redacted session summary or facts JSONL, not raw transcript hoarding:

```json
{
  "agent": "claude-code",
  "workspace": "/repo/path",
  "task": "fix failing tests",
  "observations": [
    {
      "text": "Project uses uv run pytest -q for verification",
      "evidence": "command succeeded",
      "type_hint": "project_convention"
    }
  ]
}
```

Output memory candidate shape:

```json
{
  "content": "Project convention: run uv run pytest -q before review",
  "kind": "procedural",
  "scope": "project",
  "scope_id": "deep-memory",
  "confidence": 0.85,
  "importance": 0.8,
  "decision": "write|skip|short_term|confirm",
  "reason": "verified command"
}
```

**Verification:**

```bash
uv run pytest -q tests/test_automatic_extraction_contract.py
```

---

## Task 3: Implement project scope auto-detection

**Objective:** Make cross-agent memory easy by deriving stable project scope IDs.

**Files:**
- Modify or create: `src/deep_memory/project.py`
- Test: `tests/test_project_scope.py`

**Behavior:**
1. If inside a git repo with remote origin, derive `scope_id` from normalized remote slug.
2. Else use repo root directory name plus stable path hash.
3. Allow explicit override from CLI/API.

**Verification:**

```bash
uv run pytest -q tests/test_project_scope.py
```

---

## Task 4: Build the cross-agent shared-memory demo

**Objective:** Create a reproducible local demo where source agent A writes and source agent B recalls.

**Files:**
- Create: `docs/launch/CROSS_AGENT_DEMO.md`
- Create: `scripts/cross_agent_demo.py` or `examples/cross_agent_demo.py`
- Test: `tests/test_cross_agent_demo.py` if script is deterministic enough

**Demo flow:**

```text
1. Initialize temp DB.
2. Simulate Claude Code writing project convention memory.
3. Simulate Codex searching for task context.
4. Assert recalled memory includes the convention.
5. Simulate unrelated project search and assert isolation.
```

**Verification:**

```bash
uv run python examples/cross_agent_demo.py
uv run pytest -q tests/test_scope_idempotency.py tests/test_mcp_server.py
```

---

## Task 5: Add policy-gated automatic write path

**Objective:** Let extraction outputs write automatically when safe, skip unsafe/temporary items, and mark uncertain cases for confirmation without blocking normal flow.

**Files:**
- Modify: `src/deep_memory/core.py`
- Modify or create: `src/deep_memory/policy.py`
- Test: `tests/test_automatic_write_policy.py`

**Rules:**
- `write`: high-confidence durable project/user facts.
- `short_term`: useful but low-confidence/temporary working context with TTL.
- `skip`: secrets, raw PII, raw transcripts, task status, issue IDs, commit SHAs.
- `confirm`: high-impact global scope or conflict/low-confidence high-importance item.

**Verification:**

```bash
uv run pytest -q tests/test_automatic_write_policy.py tests/test_core.py
```

---

## Task 6: Add memory hygiene report

**Objective:** Replace heavy manual review with a lightweight health report.

**Files:**
- Modify: `src/deep_memory/cli.py`
- Modify: `src/deep_memory/core.py`
- Test: `tests/test_memory_hygiene.py`
- Docs: `docs/MEMORY_LIFECYCLE.md`

**CLI shape:**

```bash
deep-memory hygiene ~/.deep-memory/deep-memory.db --scope project --scope-id deep-memory --json
```

**Report categories:**
- new recent memories;
- possible duplicates;
- conflicts;
- stale or low-confidence memories;
- expiring working memories;
- skipped/rejected sensitive items if tracked.

**Verification:**

```bash
uv run pytest -q tests/test_memory_hygiene.py
```

---

## Task 7: Add Cross-Agent Memory Benchmark

**Objective:** Turn the main product wedge into executable evidence.

**Files:**
- Create: `evals/cross_agent_memory_eval.py`
- Create: `evals/data/cross_agent_memory.jsonl`
- Test: `tests/test_cross_agent_memory_eval.py`
- Docs: `docs/CROSS_AGENT_MEMORY_BENCHMARK.md`

**Benchmark lanes:**
1. preference recall;
2. project convention recall;
3. scope isolation;
4. stale memory handling;
5. deletion correctness;
6. procedural recall;
7. Chinese mixed-token recall.

**Verification:**

```bash
uv run python evals/cross_agent_memory_eval.py --data evals/data/cross_agent_memory.jsonl --json
uv run pytest -q tests/test_cross_agent_memory_eval.py
```

---

## Task 8: Add scoped Markdown export pack

**Objective:** Strengthen the inspect/export story for personal local users.

**Files:**
- Modify: `src/deep_memory/cli.py`
- Modify or create: `src/deep_memory/export_markdown.py`
- Test: `tests/test_markdown_export_pack.py`
- Docs: `docs/EXPORT_AND_INSPECTION.md`

**Output files:**

```text
MEMORY.md
PROCEDURES.md
PREFERENCES.md
PROJECT_RULES.md
CONFLICTS.md
AUDIT_SUMMARY.md
```

**Verification:**

```bash
uv run pytest -q tests/test_markdown_export_pack.py
```

---

## Task 9: Redesign README homepage using memU-inspired clarity

**Objective:** Improve the README homepage structure by borrowing memU's clarity pattern — category, mechanism, tiny example, mental model, capability table, use cases, proof, ecosystem links — without copying memU's broad multimodal/cloud positioning.

**Files:**
- Modify: `README.md`
- Modify: `README.zh-CN.md`
- Reference: `docs/AUTOMATIC_LOCAL_AGENT_MEMORY.md`
- Reference: `docs/research/README_HOMEPAGE_RESEARCH.md`

**Important:** Do not overclaim automatic extraction before Tasks 2-5 pass. Phrase automatic extraction as the current iteration / roadmap unless the implementation and tests exist.

**Target top structure:**

```text
1. Hero: local shared memory for all your agents
2. One-paragraph mechanism: agent-session extraction, scoped local SQLite, inspect/delete/export
3. Tiny cross-agent example: Claude Code writes → Codex retrieves
4. Mental model: agents → local DB → scopes → inspection/export
5. Core capabilities table
6. Use cases
7. Quickstart
8. Evidence / benchmarks
9. Connect your agent
10. Safety boundary and architecture
```

**README changes:**

1. Replace or tighten the hero copy so the first screen says “local shared memory for all your agents.”
2. Add a short cross-agent code/CLI example above the deeper philosophy sections.
3. Add a simple mental-model block similar in scanability to memU's tree, but using deep-memory's real architecture:

```text
Claude Code ─┐
Codex      ──┼── ~/.deep-memory/deep-memory.db ── scoped recall
Hermes     ──┘            │
                          └── inspect / export / delete
```

4. Add a feature table centered on cross-agent continuity, local SQLite, scope isolation, inspection/export/delete, Chinese retrieval, and future automatic extraction/hygiene.
5. Add use cases before architecture: cross-agent coding memory, local preferences, project conventions, procedural workflows, Chinese mixed-token recall.
6. Move proof/eval links earlier, but keep claims modest.
7. Keep cloud/team-sharing and broad multimodal ingestion out of the primary story.

**Verification:**

```bash
python - <<'PY'
from pathlib import Path
for file in ['README.md', 'README.zh-CN.md']:
    text = Path(file).read_text(encoding='utf-8')
    assert 'local' in text.lower() or '本地' in text
    assert 'Claude Code' in text
    assert 'Codex' in text
    assert 'Hermes' in text
    assert 'scope' in text.lower() or '范围' in text
print('README homepage positioning checks passed')
PY
uv run pytest -q
uv run ruff check .
```
