# Metrics: deep-memory → 100k-star loop dashboard

## Purpose

100k stars is an outcome metric, not the control variable. If you退后一步看，真正要建模的是一个开源 flywheel：

```text
useful product surface → fast activation → credible demos → distribution → feedback → issues/PRs → better product → more trust
```

This document defines leading indicators for that loop so the project does not optimize for vanity stars while missing the underlying bottleneck: developer trust that persistent agent memory is real, local-first, inspectable, and useful in Chinese + agent workflows.

## North-star metric

**Weekly activated memory developers (WAMD)**

A developer counts as activated for a week when they complete at least one real or demo memory loop with `deep-memory`:

1. install or run from source;
2. initialize a memory database;
3. add at least one memory record;
4. successfully search/recall it;
5. inspect evidence through CLI output, tests, or a visible DB/file artifact.

Why this is the north star: it measures the project’s root promise — developers can make an agent remember something across sessions — before counting secondary social signals.

Minimum manual proxy before telemetry exists:

- unique GitHub users who open an issue/discussion/PR or comment with a completed quickstart/demo result;
- demo form / launch post replies containing successful run output;
- public forks or examples that show `deep-memory init/add/search/stats` or the Python API working.

## Metric hierarchy

### 1. Activation metrics

Activation asks: can a new developer experience the core value quickly?

| Metric | Definition | Target / threshold | Source |
| --- | --- | --- | --- |
| Time to first recall | Minutes from clone to successful `deep-memory search` returning an added memory | P50 ≤ 2 min, P90 ≤ 5 min | user reports, demo recordings, local smoke test |
| Quickstart success rate | Successful source install + test + CLI flow attempts / total reported attempts | ≥ 80% early, ≥ 90% after package release | issues, discussions, launch feedback |
| 6-line API success | Users who run the Python API snippet without modification | ≥ 70% of reported attempts | issues/discussions/examples |
| First useful memory rate | Activated users who add a non-trivial preference/project fact, not only toy text | ≥ 50% of activated reports | demo submissions, examples |
| Install friction count | New install/setup failures per week | trend down weekly | issues labeled `setup`, CI failures |

### 2. Retention metrics

Retention asks: does memory remain useful after the first demo?

| Metric | Definition | Target / threshold | Source |
| --- | --- | --- | --- |
| Week-2 returning developers | Activated developers who report or commit a second use ≥ 7 days later | ≥ 25% in early community | repeat issues/discussions/PRs |
| Repeat recall loops | Count of users/examples showing multiple add/search sessions over time | increasing weekly | examples, discussions |
| Integration continuation | Users who connect `deep-memory` to an agent/plugin/MCP workflow after CLI/API trial | ≥ 10 by M+2 | PRs, examples, adapter issues |
| Memory DB persistence proof | Reports where a DB is reused across sessions or processes | increasing weekly | demo outputs, examples |

### 3. Quality metrics

Quality asks: is the memory system trustworthy rather than merely flashy?

| Metric | Definition | Target / threshold | Source |
| --- | --- | --- | --- |
| Test health | Passing tests / total tests on main | 100% for protected main | CI, `uv run pytest` |
| Recall@k on benchmark v0 | Correct target memory appears in top-k for benchmark queries | define baseline in P0 benchmark; improve each phase | benchmark task |
| Chinese retrieval pass rate | Chinese preference/project fact queries that retrieve the expected memory | baseline first, then monotonic improvement | Chinese eval dataset |
| Conflict candidate precision | Human-judged useful conflict candidates / candidates shown | start manual; avoid noisy alerts | conflict loop eval |
| Inspectability score | Can a developer explain why a memory exists and where it came from? | yes for every stored record in MVP | schema/docs review |
| Bug escape rate | Regressions found by users but not covered by tests | trend down; every escape gets a regression test or issue | issues + tests |

### 4. Growth metrics

Growth asks: is distribution compounding because the product is legible and useful?

| Metric | Definition | Target / threshold | Source |
| --- | --- | --- | --- |
| Stars | GitHub stars | M+1 3k, M+2 15k, M+3 30k, M+6 60k, M+12 100k | GitHub |
| Star conversion from demos | Stars gained within 48h of each demo / unique demo viewers or impressions | compare across demos; improve hooks | GitHub + platform analytics |
| Clones / unique cloners | Weekly repository clones and unique cloners | increasing after each release/demo | GitHub traffic |
| Issue conversion rate | Issues opened from feedback events / meaningful feedback events | ≥ 20% for actionable feedback | feedback log + GitHub |
| PR conversion rate | PRs opened / issues labeled `good-first-issue` or `help-wanted` | ≥ 10% early | GitHub |
| Contributor activation | New contributors whose PR passes CI or review | ≥ 3 by M+1, ≥ 10 by M+3 | GitHub |
| External examples | Third-party repos/posts using `deep-memory` | increasing monthly | search/manual log |

## Weekly build → demo → distribute → feedback → issue/PR loop

Run this loop every week. The point is not content cadence for its own sake; it is to create a measurement environment where product bottlenecks become visible.

1. **Build**
   - Choose one root bottleneck: activation, retrieval quality, integration, inspectability, or trust.
   - Ship the smallest artifact that can be demonstrated: feature, benchmark, example, doc, or adapter.
   - Required evidence: passing tests or an executable demo command.

2. **Demo**
   - Record or write one minimal proof: “here is the memory, here is recall across a session, here is why it is inspectable.”
   - Prefer reproducible CLI/API transcripts over vague screenshots.
   - Required evidence: link/path to demo script, recording, post draft, or terminal transcript.

3. **Distribute**
   - Publish to the narrowest high-signal audience first: agent builders, Chinese AI devs, Hermes/MCP users, open-source tool builders.
   - Reuse one core demo across GitHub README, X/WeChat, Discord/Telegram/QQ communities, and issue templates.
   - Required evidence: distribution channel, post URL or manual note, timestamp.

4. **Feedback**
   - Classify every meaningful response into: setup failure, unclear positioning, missing integration, retrieval quality, safety/privacy, docs, feature request, contribution offer.
   - Do not debate taste prematurely; look for repeated friction.
   - Required evidence: feedback item logged with category and severity.

5. **Issue / PR conversion**
   - Convert repeated or actionable feedback into GitHub issues with labels and acceptance criteria.
   - Convert contributor interest into small PR-sized tasks.
   - Required evidence: issue/PR URL or local backlog entry.

6. **Dashboard update**
   - Update the markdown/CSV dashboard schema below.
   - Write a 5-line weekly interpretation: what moved, what did not, and the next bottleneck.

## Minimum dashboard schema

Before automation, keep the dashboard as `docs/METRICS.md` plus an optional CSV file such as `docs/metrics-weekly.csv`. Each weekly row should use this schema:

| Field | Type | Meaning |
| --- | --- | --- |
| week_start | date | Monday or chosen week boundary |
| shipped_artifact | string | Feature/demo/doc/benchmark shipped that week |
| bottleneck_targeted | enum | activation / retention / quality / growth / safety / contribution |
| demo_url_or_path | string | Demo post, script, recording, or transcript |
| distribution_channels | list[string] | GitHub, X, WeChat, QQ, Discord, Hacker News, etc. |
| meaningful_feedback_count | integer | Non-trivial feedback items, excluding pure likes |
| setup_failure_count | integer | Install/run failures reported |
| activated_developers | integer | Manual proxy for WAMD |
| returning_developers | integer | Week-2+ returning users or repeat examples |
| issues_opened | integer | GitHub issues created from feedback |
| prs_opened | integer | PRs opened from community or maintainers |
| prs_merged | integer | PRs merged that week |
| tests_passed | integer | Passing tests in the relevant verification run |
| tests_total | integer | Total tests in the relevant verification run |
| recall_quality_snapshot | string | Benchmark or manual retrieval result, e.g. `Recall@3=0.72` |
| stars_start | integer | Stars at beginning of week |
| stars_end | integer | Stars at end of week |
| clones_unique | integer | GitHub unique cloners, if available |
| top_failure_mode | string | The highest-leverage bottleneck observed |
| next_loop_decision | string | What to build/demo next week |

### CSV starter

```csv
week_start,shipped_artifact,bottleneck_targeted,demo_url_or_path,distribution_channels,meaningful_feedback_count,setup_failure_count,activated_developers,returning_developers,issues_opened,prs_opened,prs_merged,tests_passed,tests_total,recall_quality_snapshot,stars_start,stars_end,clones_unique,top_failure_mode,next_loop_decision
YYYY-MM-DD,"README quickstart + CLI recall demo",activation,"README.md#quickstart","GitHub,QQ",0,0,0,0,0,0,0,0,0,"manual baseline pending",0,0,0,"unknown until first demo","instrument feedback log"
```

## Weekly interpretation template

```text
Week of YYYY-MM-DD
- Shipped:
- Evidence:
- What improved:
- Bottleneck observed:
- Next loop decision:
```

## Guardrails

- Do not treat stars as proof of product quality. Stars are a lagging distribution signal.
- Do not optimize growth before activation evidence exists.
- Do not add telemetry that violates the local-first trust promise. Prefer opt-in reports and public contribution signals.
- Every repeated failure mode should become either a doc fix, test, benchmark case, issue, or PR.
- Every metric should answer: “what action would change if this moved?” If no action changes, remove the metric.
