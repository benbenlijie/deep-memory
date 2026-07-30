# Reddit drafts

<!-- FOUNDER STORY INSERT POINT: Before posting, insert a condensed personal pain story here (2-3 sentences).
     See docs/launch/founder-story.md for the canonical draft.
     r/LocalLLaMA responds to genuine frustration, not product announcements. -->

## r/LocalLLaMA

Title: Local-first memory layer for coding agents: SQLite, MCP, inspectable records

The most annoying thing about running multiple AI coding agents: Claude Code learns how a repo should be tested, Codex doesn't know it, Hermes proves a workflow, OpenCode rediscovers it. You teach the same conventions, preferences, and corrections to every agent, every session.

I hit this concretely: I was using OpenCode to investigate benchmark submission details, then switching to Codex to prepare the materials and run inference on the server. Codex had no idea what OpenCode had found. I manually relayed everything. After a few rounds, I tried the @-mention-a-local-doc workaround — which worked until I was juggling docs across parallel tasks and couldn't remember which one was current. That's when I started building deep-memory.

`deep-memory` is a local memory layer shared across agents: one SQLite file that Claude Code, Codex, OpenCode, and Hermes can all read and write to. Teach once, every agent remembers.

The store is local, inspectable, and deletable — no cloud, no hidden product state, no transcript scraping. Most agent memory today is either hidden state you can't audit, or a hosted vector stack you have to trust. This takes the opposite default.

What's under the hood:

- local SQLite DB, with project/workspace scopes
- no cloud/API key for the core retrieval path
- CLI + Python SDK + MCP server
- wrappers/import paths for Claude Code, Codex, OpenCode-style tools, and Hermes
- explicit facts/procedures only, not transcript scraping
- inspect/edit/export/soft-delete through CLI or local WebUI
- Chinese-first lexical retrieval with local fallback tokens and optional `jieba`
- governance metadata: source, confidence, importance, scope, timestamps, conflict/lifecycle state

The key design choice is that memory should be something you can audit. It should not silently become hidden global behavior. Procedural memories can be exported as reviewable skill candidates, but they are not auto-installed.

Quickstart:

```bash
git clone https://github.com/benbenlijie/deep-memory
cd deep-memory
uv sync --extra dev --extra mcp
uv run deep-memory init .deep-memory/deep-memory.db
uv run deep-memory add .deep-memory/deep-memory.db \
  "Project convention: run uv run pytest -q before review" \
  --kind procedural \
  --importance 0.8
uv run deep-memory search .deep-memory/deep-memory.db "how do we verify changes?"
```

Current checked-in evaluations:

| Evaluation | Current result | What it tests |
| --- | --- | --- |
| Chinese retrieval v1 | 55/55 local backend; 55/55 optional `jieba` | Chinese-first memory lookup with mixed technical terms |
| Chinese retrieval v2 | 20/20 top-1, MRR 1.0 | Multi-memory cases with distractors and stale facts |
| Memory benchmark v0 | no-memory 0/20; deep-memory usually 20/20 | Whether retrieval recovers missing cross-session facts |

Quickstart: https://github.com/benbenlijie/deep-memory#quickstart
GitHub: https://github.com/benbenlijie/deep-memory

This is alpha. The most useful feedback would be from people who run local agents across real repos: what should the default write policy allow, what should require confirmation, and what adapter surface would make this feel safe rather than creepy?

---

## r/MachineLearning

Title: [D] Local-first, inspectable memory for AI agents: what should we benchmark?

I am building `deep-memory`, a small local-first memory layer for AI agents, and I would like feedback on the evaluation framing.

The working hypothesis is that agent memory should be treated less like “chat history” and more like a governed retrieval system:

- explicit durable facts and procedures, not raw transcript ingestion
- local, inspectable storage by default
- metadata for source, confidence, importance, timestamps, scope, and lifecycle/conflict state
- cross-agent access through CLI/SDK/MCP/adapters
- memory-to-skill export as a reviewable candidate, not automatic behavioral modification

The current implementation uses SQLite + FTS5 with local token fallback. For Chinese retrieval, it adds Chinese bigram-style fallback tokens and an optional `jieba` backend. Vector retrieval is on the roadmap, but intentionally not required for the base package.

Current checked-in evaluations:

| Evaluation | Current result | What it tests |
| --- | --- | --- |
| Chinese retrieval v1 | 55/55 local backend; 55/55 optional `jieba` | Chinese-first memory lookup with mixed technical terms |
| Chinese retrieval v2 | 20/20 top-1, MRR 1.0 | Multi-memory cases with distractors and stale facts |
| Memory benchmark v0 | no-memory 0/20; deep-memory usually 20/20 | Whether retrieval recovers missing cross-session facts |

Repo: https://github.com/benbenlijie/deep-memory
Quickstart: https://github.com/benbenlijie/deep-memory#quickstart

The part I would most like critique on is the eval design. If you think of memory as a system with representations, retrieval, update rules, and governance, what are the right failure cases? Contradictions? Temporal validity? Privacy boundaries? Cross-agent contamination? Chinese/English mixed project facts? I am trying to keep the evals small and executable rather than impressive-looking.
