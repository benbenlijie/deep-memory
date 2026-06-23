# Project Sync — 2026-06-23

## Decision

Conditional GO remains correct for controlled preview. Do not treat this as broad launch readiness yet.

## Status distribution

Source: Hermes Kanban board `deep-memory` at `/home/ben/.hermes/kanban/boards/deep-memory/kanban.db`.

- running: 1 — this project sync card.
- blocked: 1 — preserved as the active review/decision lane.
- todo: 3 — future/backlog work, not launch-blocking for the controlled-preview gate.
- done: 69 — includes the completed launch cleanup, README redesign, contributor-readiness, demo asset, and release-gate cards.
- archived: 1.
- superseded: 1.

## Parent-card evidence folded into project status

### Launch cleanup

Status: done.

Evidence:

- Competitive benchmark posture removed from the launch surface.
- Internal eval/regression posture preserved.
- Search verification reported no remaining matches for competitive benchmark / leaderboard artifacts.
- `uv run pytest -q` passed: 156 passed, 2 skipped.
- `uv run ruff check .` passed.

Project implication: launch claims should stay around controlled-preview memory infrastructure, not competitive leaderboard language.

### README redesign

Status: done.

Evidence:

- `README.md` now frames `deep-memory` as trustable local-first agent memory.
- README quickstart was exercised with a temporary database.
- Local README links and anchors were verified.
- `uv run ruff check .` passed.
- `uv run pytest -q` passed.

Project implication: GitHub first screen is aligned with the current value proposition and no longer depends on summary-only positioning.

### Community readiness

Status: done.

Evidence:

- `docs/GOOD_FIRST_ISSUE_DRAFTS.md` contains 7 maintainer-ready issue drafts.
- `docs/TROUBLESHOOTING.md` documents common local setup failures.
- `CONTRIBUTING.md`, `docs/COMMUNITY.md`, and `docs/NEXT_PHASE_BACKLOG.md` point newcomers at controlled-preview contribution paths.
- Targeted policy/scope/WebUI/Hermes adapter/export-delete tests passed: 34 tests.
- `uv run ruff check .` passed.

Project implication: contributor entry is now inspectable and reviewable; issue opening can proceed from drafts rather than improvised board summaries.

### Launch demo asset

Status: done.

Evidence:

- Capture plan: `.tmp/demo-video/artifacts/demo_capture_plan.txt`.
- WebUI proof screenshot: `.tmp/demo-video/artifacts/webui-memory-inspector-proof.png`.
- Demo DB: `.tmp/demo-video/demo-agent.db`.
- Benchmark evidence from the demo package: baseline 0/20 vs deep-memory 18/20.
- Local WebUI graph/timeline/edit/delete affordances were verified against the demo database.

Project implication: demo proof exists locally, but public distribution should still wait for the chosen posting/gif/video packaging path.

### Release gate

Status: done.

Evidence:

- Verified commit: `16d6aa2e67c3e67b6bc2ab6341f40a5c23b7e4d2`.
- Fresh local no-hardlinks clone surrogate passed install/sync, README quickstart, memory benchmark, Chinese retrieval evals, pytest, and ruff.
- Working tree stayed clean after the documented first-user path.
- Caveat: public GitHub HTTPS clone from this host was flaky/unreachable; origin URL and commit were still checked against the public GitHub URL in the surrogate clone.

Project implication: release-gate evidence is strong enough for controlled preview, but the public-network clone caveat should remain visible if asked for verification details.

## Teambition/backlog mapping

Source: `docs/internal/TEAMBITION_BACKLOG.csv` plus current repo state.

| Teambition item | Current status | Evidence / note |
| --- | --- | --- |
| TB-001 Repo launch polish | done for controlled preview | README redesign, quickstart verification, release-gate rerun, tests/lint evidence. |
| TB-002 Hermes plugin MVP | partially done / evidence-backed MVP path | Hermes import/adapter docs and tests exist; keep as preview integration, not full plugin launch. |
| TB-003 Memory benchmark v0 | done | Demo package and release gate report memory benchmark success; demo evidence reports 0/20 baseline vs 18/20 deep-memory. |
| TB-004 Chinese retrieval baseline | done as executable eval baseline, still next-loop improvement area | Chinese retrieval evals passed in release gate; avoid stronger superiority claims. |
| TB-005 Conflict resolution loop | in backlog / next credibility loop | Keep under governance/trust work; not required to claim M+1 controlled preview. |
| TB-006 Memory Web UI | MVP/demo evidence done, hardening remains | WebUI proof screenshot and affordance verification exist; keep as controlled-preview proof. |
| TB-007 MCP server | later ecosystem lane | Not part of this launch-cleanup/readme/release-gate sync. |
| TB-008 Launch assets | demo package prepared, public media packaging remains | Capture plan, storyboard/recording guide, demo DB, screenshot exist. |

## Privacy-safe verification summary

- No secrets or raw private transcripts were added to this sync note.
- Temporary task status was not written as durable memory.
- The only durable status artifact added by this sync is a project-local evidence summary plus a weekly metrics CSV starter:
  - `docs/internal/PROJECT_SYNC_2026-06-23.md`
  - `docs/internal/launch/weekly-metrics/2026-06-23.csv`

## Current recommendation

Keep the project in controlled-preview mode. The root bottleneck is no longer repo polish; it is now real activation evidence after distribution plus stronger Chinese retrieval / trust-WebUI loops before any broad-launch claim.
