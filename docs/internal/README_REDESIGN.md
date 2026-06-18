# README homepage redesign

This document captures the research pass and proposed information architecture for turning `deep-memory`'s GitHub homepage into a professional, English-first OSS landing page with a clear Chinese localization path.

## Research set

Compared homepage README patterns from 8 high-star OSS projects relevant to AI, developer tools, infrastructure, and product-led open source:

| Project | Relevant pattern | What to reuse for deep-memory |
| --- | --- | --- |
| LangChain | Logo/hero, badges, quickstart, ecosystem map, clear resource links | Put the product category and first command above the fold; explain ecosystem role without trying to document everything inline. |
| LlamaIndex | Strong badge cluster, community links, concise project identity | Use badges for CI/license/Python, then a simple community/contribution path. |
| Chroma | Minimal API-first README and quick code sample | Show the smallest memory flow quickly; avoid burying value under theory. |
| Qdrant | Trust signals, docs/OpenAPI/roadmap badges, deployment caveats | Pair capability claims with security notes and docs links; don't hide local/security boundaries. |
| Weaviate | Feature examples and client/API section | Present integrations as a compatibility surface: SDK, CLI, Hermes import, MCP server, WebUI. |
| FastAPI | Strong positioning, docs/source links, performance/trust proof | Lead with why developers care; use benchmarks/evals as evidence rather than hype. |
| Supabase | Product screenshot, feature checklist, architecture image | Add an architecture visual and a feature matrix with implemented/roadmap status. |
| PostHog | All-in-one product framing, demo media, self-host/cloud path | Add a 2-minute demo and community path; make the current local-first scope explicit. |

## Reusable homepage patterns

1. Above-the-fold clarity
   - One-line category: what it is, who it is for, and why now.
   - Language switch near the top.
   - Badges immediately after the hero.
   - A short value proposition before installation details.

2. Visual proof
   - Logo or architecture diagram near the first screen.
   - Screenshot/GIF when a UI exists; placeholder only if the asset is not ready.
   - A compact benchmark/eval table for evidence.

3. Fast path to value
   - Install from source or package.
   - 2-minute demo commands.
   - 6-line API sample.
   - CLI sample.

4. Capability matrix
   - Separate implemented MVP features from roadmap items.
   - Include explicit integration surfaces: Hermes JSONL adapter, MCP server, local WebUI, optional retrieval backend.

5. Trust and safety
   - Local-first default.
   - No telemetry in core add/search/stats.
   - Explicit facts instead of raw transcript hoarding.
   - Link to a dedicated safety/privacy model.

6. Community path
   - Contribution guide.
   - Good first lanes.
   - Roadmap and benchmark links.
   - Clear statement that the project is alpha rather than production-mature.

## Recommended README information architecture

1. Hero
   - `deep-memory` title.
   - Language switch: English / 简体中文.
   - Badges: CI, license, Python, package status/alpha.
   - One-sentence positioning: local-first persistent memory layer for AI agents.
   - 3 bullets: remember durable facts, retrieve across sessions, inspect/govern locally.

2. Why this exists
   - Problem: agents lose user/project state between sessions.
   - Non-goal: not another vector database and not a raw transcript warehouse.
   - Root bottleneck: representation, lifecycle, recall quality, and user control.

3. 2-minute demo
   - `uv sync --extra dev`.
   - quickstart example.
   - memory vs no-memory example.
   - small CLI add/search/stats example.

4. Architecture
   - Embed `docs/assets/deep-memory-architecture.svg`.
   - Explain: explicit facts/events -> DeepMemory SDK/CLI -> SQLite/FTS5 -> retrieval/eval -> agent context / WebUI / MCP / skill candidates.

5. Feature matrix
   - Implemented: SQLite/FTS5, record metadata, forgetting score, conflict candidates, CLI/SDK, Hermes import, MCP server, local WebUI MVP, Chinese retrieval eval, Memory-to-Skill candidate export.
   - Optional: jieba backend via retrieval extra.
   - Roadmap: embeddings/vector backend, richer graph UI, hosted/team sync, automatic extraction policy gates.

6. Evidence
   - Chinese retrieval eval v1: local and jieba 55/55 on checked-in fixture; older plain FTS baseline 24/55.
   - Memory benchmark v0: 20 bilingual tasks; baseline 0/20; deep-memory should reach at least 16/20 in tests and typically 20/20 with default retrieval limit.
   - Link to docs and commands so readers can reproduce.

7. Integrations
   - Python SDK.
   - CLI.
   - Hermes explicit facts JSONL import.
   - MCP server for Hermes/Claude Code/Codex-style clients.
   - Local WebUI inspector/editor.

8. Safety/privacy
   - Local-first.
   - Explicit writes.
   - No secrets/raw transcript storage by default.
   - Soft delete and governance direction.

9. Roadmap/community
   - Alpha status.
   - Contribution lanes.
   - Roadmap link.
   - License.

## Visual asset plan

Implemented in this pass:

- `docs/assets/deep-memory-architecture.svg`: GitHub-renderable architecture diagram.

Recommended follow-up assets:

- `docs/assets/webui-screenshot.png`: real screenshot after a polished WebUI pass.
- `docs/assets/deep-memory-demo.gif`: terminal or WebUI demo GIF for the first screen.
- `docs/assets/benchmark-chart.svg`: small chart comparing no-memory baseline vs deep-memory on the checked-in fixture.
- `.github/social-preview.png`: optional repository social preview image once branding is stable.

## Copy constraints

- English README must not mix unexplained Chinese prose into the main narrative. Chinese examples are allowed only when demonstrating Chinese retrieval or memory records.
- Chinese README should be a real localization, not a partial appendix.
- Do not claim production maturity, 100k stars, hosted cloud, automatic extraction, or embedding retrieval until implemented.
- Claims should point to implemented capabilities and reproducible commands.
