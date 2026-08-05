# Twitter/X thread draft

<!-- v4: all tweets under 280 chars. Code block in tweet 9 replaced with short commands + link.
     Video attachment moved to tweet 9. URLs consolidated in tweet 11. -->

1/ The most annoying thing about multiple AI coding agents:

Claude Code learns a convention. Codex doesn't know it. Hermes proves a workflow. OpenCode rediscovers it.

You teach the same thing to every agent, every session.

deep-memory fixes this.

2/ Why I built this:

OpenCode investigated benchmark details. Codex was supposed to act on them. Codex had no idea what OpenCode found.

I manually relayed everything. My brain became the memory layer.

After round 3, I started building deep-memory.

3/ Teach once, every agent remembers.

A SQLite file on your machine that Claude Code, Codex, OpenCode, and Hermes can all read and write to.

No cloud. No hidden state. No transcript scraping.

4/ The core design choice:

Boring is good if you want auditability.

- SQLite file in your project
- CLI + Python SDK + MCP server
- No cloud/API key for the core path
- Local WebUI to inspect, edit, delete

5/ A memory record is not just text.

It carries kind, importance, confidence, source, scope, timestamps, conflict status, and lifecycle state.

Memory should be auditable, not a pile of opaque embeddings.

6/ Chinese retrieval is first-class, not a badge on a README.

Chinese quality should be measured, not just claimed.

✅ Chinese retrieval v1: 55/55
✅ Chinese retrieval v2: 20/20 top-1
✅ Memory benchmark: 0/20 → 18/20

7/ Some facts expire. Some are superseded. Some should never become global.

Agent memory needs lifecycle, not just retrieval.

This is where memory becomes a governance problem, not a search problem.

8/ Cross-agent is the core use case.

A useful memory layer should work across Claude Code, Codex, OpenCode, Hermes, and future agents.

The interface should be boring: CLI, SDK, MCP, JSONL import/export.

9/ 30-second demo 👇

init → add → search. Local SQLite, no cloud, no API key.

Full quickstart: https://github.com/benbenlijie/deep-memory#quickstart

[attach demo.mp4]

10/ This is alpha, and intentionally a controlled preview.

The biggest open questions are memory policy, adapter safety, harder evals, and when vector retrieval is worth the extra complexity.

11/ If this matters to your agent workflow, I'd love feedback.

🔗 github.com/benbenlijie/deep-memory
🔗 中文 README in repo

If local-first + cross-agent memory is the right direction, a star helps more people find it. 🌟
