# Reddit drafts

## r/LocalLLaMA

Title: Local-first memory layer for coding agents: SQLite, MCP, inspectable records

I have been working on `deep-memory`, a local-first memory layer for AI coding agents.

The problem I wanted to isolate is simple: agents forget useful state between runs, and different agents do not share the project conventions they discover. Claude Code might learn how a repo should be tested. Codex or OpenCode will not know it unless the user repeats it. A lot of memory tooling also assumes a hosted service, opaque product memory, or a vector stack before you can even inspect the records.

`deep-memory` takes the opposite default:

- project-local SQLite DB
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
