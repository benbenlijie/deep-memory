# Hacker News draft

<!-- HN title: A (story-driven). Chosen because the post opens with the founder story,
     and "I built" mirrors the first paragraph. HN rewards genuine frustration over product announcements. -->
Title: Show HN: I built a shared memory layer for my coding agents

URL: https://github.com/benbenlijie/deep-memory

Body:

<!-- Opening: founder story (real experience) → product one-liner → comparison → features.
     Story source: docs/launch/founder-story.md. The "felt stupid" moment is the hook. -->

I was running OpenCode, Codex, and Hermes against the same project. OpenCode would investigate benchmark submission details. Then I’d switch to Codex to prepare the submission materials on the server — and Codex had no idea what the standards were. I had to manually relay everything OpenCode had figured out. After a few rounds, it felt stupid: multiple agents on the same machine, zero shared memory.

I tried the obvious workaround — save shared context as local docs, then @-mention them in each session. It works for a week. Then you’re the one remembering which doc has which convention, which file is still current. During multi-task parallel work, your brain becomes the memory layer — exactly the burden agents were supposed to offload. That’s when I built deep-memory.

`deep-memory` is a local memory layer shared across agents: one SQLite file that Claude Code, Codex, OpenCode, and Hermes can all read and write to. Teach a convention once, every agent remembers it. The store is local, inspectable, and deletable — no cloud, no hidden product state, no transcript scraping.

Most agent memory today is either hidden state you can't audit, or a hosted vector stack you have to trust. `deep-memory` takes the opposite default: the memory layer belongs to your machine, not to any single agent vendor.

What it does today:

- local SQLite database by default; no cloud or API key for the core path
- CLI, Python SDK, MCP server, and wrapper/import paths for agents
- cross-agent workflows for Claude Code, Codex, OpenCode-style tools, and Hermes
- FTS5 search with local Chinese/English token fallback; optional `jieba` retrieval extra
- record metadata: `kind`, `importance`, `confidence`, `source`, timestamps, scope, lifecycle/conflict state
- WebUI MVP for inspecting, editing, exporting, and soft-deleting records
- Memory -> Skill candidate export, but never auto-installing behavior rules

A minimal example:

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

Demo path: clone the repo, run the quickstart above, then open the local WebUI with:

```bash
uv run deep-memory webui .deep-memory/deep-memory.db --host 127.0.0.1 --port 8765
```

Evaluation highlights, with the usual caveat that these are small regression checks rather than a claim that memory is solved:

- Chinese retrieval v1: 55/55 on the checked-in fixture with the default local backend; optional `jieba` also reaches 55/55.
- Chinese retrieval v2: 20/20 top-1 on a harder multi-memory fixture with distractors.
- Memory benchmark v0: 20 bilingual tasks; no-memory baseline 0/20; deep-memory typically 20/20 with the default retrieval limit.

Quickstart: https://github.com/benbenlijie/deep-memory#quickstart

This is alpha software and should be treated as a controlled preview. I would especially appreciate feedback on the memory policy, adapter surface, Chinese retrieval fixtures, and whether the default local-first boundary feels right for developer agents.
