# Roadmap: deep-memory → 100k-star open-source project

## North Star

Build the default open-source persistent memory layer for AI agents: local-first, Chinese-first, inspectable, conflict-aware, and cross-agent through SDK + MCP.

## Success metrics

| Time | Product milestone | Community target |
| --- | --- | --- |
| M+1 | MVP + Hermes plugin | 3k stars |
| M+2 | Claude Code/Codex/OpenCode adapters + Chinese retrieval | 15k stars |
| M+3 | Web memory graph/editor | 30k stars |
| M+6 | Skill linkage + MCP server | 60k stars |
| M+12 | Cross-agent shared memory ecosystem | 100k stars |

## Phases

### Phase 1 — Foundation memory, 4 weeks

- 6-line Python API
- SQLite local persistence
- Fact extraction contract
- Timeline/session index
- Hermes plugin proof-of-concept
- Benchmark: memory/no-memory agent task comparison

### Phase 2 — Memory governance, 8 weeks

- Chinese tokenization + embedding pipeline
- Importance scoring
- Forgetting curve and archive compression
- Conflict detection and user-confirmed resolution
- Web inspector/editor

### Phase 3 — Ecosystem, 12 weeks

- MCP server
- Memory → Skill generator
- Skill × Memory activation
- Shared memory adapters for Hermes, Claude Code, Codex, OpenCode/OpenClaw-style tools
- Public benchmark + leaderboard

## 100k-star wedge

The non-obvious wedge is not “another vector DB”. It is **agent memory governance with Chinese-first quality and real developer ergonomics**. The repo must show value in the first 2 minutes, then reveal depth through architecture, benchmarks, visualizer, and integrations.
