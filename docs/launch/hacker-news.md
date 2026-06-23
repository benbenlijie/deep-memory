# Hacker News draft

Title: deep-memory: local-first memory for AI coding agents

URL: https://github.com/benbenlijie/deep-memory

Body:

Agents are getting better at individual tasks, but they still forget useful project context between runs.

A Claude Code session might learn a repo convention. Codex will not know it. Hermes may prove a workflow and then OpenCode has to rediscover it. Most memory systems also make a tradeoff I do not like: either they are hidden product state, or they require a hosted/vector setup before you can inspect what is happening.

`deep-memory` is a small local-first memory layer for AI agents. It stores explicit durable facts, project conventions, and reviewed procedural memories in a project-local SQLite database. The goal is not to scrape transcripts. The goal is to make memory inspectable, portable, auditable, and usable across agents.

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
