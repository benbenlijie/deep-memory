# README Homepage Research for deep-memory

## Goal

Study how strong OSS projects structure their GitHub README landing pages, then extract a homepage pattern that fits `deep-memory`: a machine-local, inspectable memory layer shared across AI agents with explicit scoped records.

Method:
- Reviewed the current checked-in `deep-memory` README.
- Sampled at least 8 reference OSS projects via their public README sources.
- Compared above-the-fold structure, one-sentence value framing, proof/evidence, quickstart shape, docs routing, and claim discipline.

Projects reviewed:
1. FastAPI
2. uv
3. Supabase
4. LangChain
5. LangGraph
6. Playwright
7. Tailwind CSS
8. Next.js
9. OpenTelemetry Collector
10. DuckDB
11. SQLite
12. Litestream
13. Chroma

## Positioning update after product review

The original research leaned toward a `project-local` default because it optimized for safety and easy mental models. Product direction has since shifted: `deep-memory` should be framed as a **machine-local memory substrate shared across agents**, with explicit scopes controlling relevance and safety.

Updated principles:
- machine-local store is the primary substrate;
- cross-agent sharing is a first-class value proposition;
- project/workspace/user/global are scopes, not separate product identities;
- quickstart is primarily an agent-installable protocol, not just a human copy-paste command block;
- safety depends on explicit writes, scoped retrieval, inspect/edit/delete, and no raw transcript scraping.

---

## 1. What excellent OSS homepages do above the fold

### Pattern A: identity -> one-sentence value -> trust signals -> first action

This is the dominant pattern.

Common sequence:
1. Logo / project name
2. One-sentence positioning
3. Badges or trust signals
4. One immediate next step: docs, install, or quickstart
5. Optional image / benchmark / screenshot / architecture visual

Examples:

- FastAPI:
  - Logo
  - Tagline: “FastAPI framework, high performance, easy to learn, fast to code, ready for production”
  - Badges: test, coverage, version, Python versions
  - Immediately links to docs and source

- uv:
  - Name
  - Tagline: “An extremely fast Python package and project manager, written in Rust.”
  - Badges
  - Benchmark image immediately visible
  - Then highlights and install

- Tailwind CSS:
  - Logo
  - One-line value proposition
  - Minimal badges
  - Then straight to docs/community

- LangGraph:
  - Logo
  - One-line positioning
  - Badges
  - Immediate install command

Interpretation:
- Good projects do not force the reader to infer what the project is.
- They answer three questions immediately:
  - What is this?
  - Why should I care?
  - What should I do next?

### Pattern B: proof very early when the claim is strong

Projects with a sharp performance or capability claim often put proof near the top.

Examples:
- uv puts a benchmark chart above the fold.
- FastAPI puts performance language in the tagline and immediately follows with concrete claims in highlights.
- LangGraph says “Trusted by companies…” high on the page.
- Next.js says “Used by some of the world’s largest companies…” near the start.

Interpretation:
- If the claim is non-obvious, serious projects surface evidence early.
- The evidence is usually one of:
  - benchmark
  - adoption / trust
  - architecture clarity
  - docs maturity
  - visible product screenshot

### Pattern C: route by user intent, not by internal architecture

The strongest READMEs let different users self-select quickly.

Examples:
- Playwright gives a “Choose the path that fits your workflow” table.
- Supabase separates docs, community, architecture, self-hosting.
- LangChain and LangGraph route readers to docs, ecosystem pieces, and higher/lower abstraction layers.

Interpretation:
- Good homepage design is really a routing system.
- It should let different users answer:
  - I just want to try it
  - I want to integrate it
  - I want to inspect how it works
  - I want proof it is real
  - I want to know its boundaries

---

## 2. How they explain value in one sentence

### Strong one-sentence formulas observed

1. Category + differentiator
- uv: “An extremely fast Python package and project manager, written in Rust.”
- DuckDB: “a high-performance analytical database system” with fast/reliable/portable/easy to use framing

2. Job-to-be-done + mechanism
- Playwright: framework for web automation and testing; drives multiple browsers with a single API
- OpenTelemetry Collector: vendor-agnostic implementation to receive, process, and export telemetry data

3. Replacement / consolidation framing
- uv: one tool replacing multiple tools
- Supabase: the Postgres development platform; Firebase-like features using open source tools

4. Level-of-abstraction framing
- LangChain: framework / platform for building agents and LLM-powered applications
- LangGraph: low-level orchestration framework for stateful agents

### What makes the good taglines work

They are usually:
- concrete about category
- concrete about differentiator
- short enough to scan in one breath
- ambitious, but still falsifiable

### Implications for deep-memory

`deep-memory` originally said:
- “Machine-local memory for all your agents. Inspect what they remember. Decide what they keep.”

Updated positioning after product review:
- “Machine-local memory for all your agents. Inspect what they remember. Decide what they keep.”

This is actually directionally strong because it already has:
- category: memory for AI agents
- differentiator: machine-local, cross-agent, explicitly scoped
- governance angle: inspect / decide

What is missing slightly above the fold is a sharper mechanism and a sharper user problem.

The README body explains the real pain well:
- cross-agent memory fragmentation
- no cloud
- inspectable machine-local SQLite store
- no transcript scraping
- explicit governance

That means the homepage should expose that pain and mechanism earlier, not only in paragraph two.

---

## 3. How strong infra READMEs use badges, screenshots, diagrams, quickstart, proof, docs

### Badges

Observed patterns:
- Minimal credible set beats badge overload.
- Common useful badges: CI, version, language/runtime support, license.
- Some projects add community or adoption badges, but only when they reinforce the story.

Examples:
- Tailwind: build/downloads/release/license
- FastAPI: tests/coverage/version/python versions
- OpenTelemetry: build/report/codecov/release/security-quality
- Next.js uses fewer but more branded badges

Takeaway for deep-memory:
- Current set is fine: CI, Python, License, Status
- Do not overload with vanity badges.
- If adding one more, prefer something meaningful like docs or benchmark/eval status, not social noise.

### Screenshots and diagrams

Observed patterns:
- Supabase uses a real product screenshot early.
- uv uses a benchmark chart.
- deep infrastructure projects often use architecture diagrams after the top section, not before the first explanation.
- Tailwind keeps it minimal because brand + docs do most of the work.

Takeaway for deep-memory:
- The architecture diagram is useful, but it may not be the best first visual.
- For this product, the more persuasive top visual may be one of:
  1. a tiny “agent -> SQLite memory -> another agent” flow
  2. a WebUI screenshot showing inspect/edit/delete
  3. a benchmark / eval proof card showing memory vs no-memory

My judgment: for a machine-local memory layer, the most convincing early visual is not abstract architecture alone. It is either:
- inspectability proof (WebUI screenshot), or
- cross-agent continuity proof (small diagram),
preferably both, with one early and one later.

### Quickstart

Observed patterns:
- The best quickstarts are short, runnable, and aligned with the main promise.
- They do not try to teach the whole system.
- They create a first moment of success quickly.

Examples:
- uv: install + a tiny workflow
- LangChain: install + 4-line example
- Playwright: install + tiny test
- DuckDB: query a CSV/Parquet file directly

Takeaway for deep-memory:
- The current quickstart is decent and concrete.
- But the true aha moment is not “I can init/add/search.”
- The true aha moment is “one agent stores a durable convention, another agent can retrieve it later from the same local DB.”

So the top quickstart should probably be reframed around continuity, not CRUD.

### Docs links

Observed patterns:
- Good READMEs link docs very early.
- But they do not dump the whole site map above the fold.
- They present a few clear paths.

Examples:
- FastAPI: docs link immediately after top block
- OpenTelemetry: top navigation links to getting started/config/monitoring/security
- Playwright: docs + API reference on line 1 of the functional content

Takeaway for deep-memory:
- A compact route block near the top would help:
  - Quickstart
  - Agent install guide
  - Safety / privacy
  - Architecture
  - Benchmarks / evals

### Proof blocks

Observed patterns:
- Serious infra projects usually prove one of three things:
  1. performance
  2. reliability / maturity
  3. architectural legitimacy

For deep-memory, the most important proof is different:
1. local-first inspectability is real
2. retrieval quality is measured
3. cross-agent workflow is operational
4. safety boundary is explicit

That means proof for deep-memory should probably look like:
- “SQLite file in your project, inspectable via CLI/WebUI/export”
- checked-in eval numbers
- explicit adapter matrix / support status
- clear non-goals and safety constraints

---

## 4. How serious infra projects avoid overclaiming

This is perhaps the most important pattern.

### Tactics they use

1. They define scope precisely.
- OpenTelemetry Collector explains exactly what it does: receive/process/export telemetry.
- LangGraph says it is a low-level orchestration framework, not all of agent engineering.
- SQLite README says the README is about the source repository, not how SQLite is used.

2. They separate implemented from aspirational.
- Mature projects often distinguish docs, roadmap, supported features, and future work.
- Your current README already does this well with “What works today”.

3. They qualify claims with evidence or bounded language.
- uv links its speed claim to benchmarks.
- FastAPI includes a note about the basis of estimates.
- deep-memory already says evals are small and not proof that memory is solved. That is exactly the right tone.

4. They do not promise magic.
- Good infra copy avoids “solves memory forever” style language.
- It describes mechanism, scope, and tradeoff.

### Implications for deep-memory

The right tone is:
- not “perfect memory for all agents”
- but “a local-first, inspectable memory substrate for explicit durable facts and procedures”

The key claim should be mechanistic, not mystical.

Good framing:
- shared local memory layer
- explicit facts, not transcript scraping
- inspectable records and governance
- measured retrieval on checked-in evals
- adapters first, magical autonomy later if ever

---

## 5. Which homepage pattern fits deep-memory

If you退后一步看, `deep-memory` is not mainly a database project, and not mainly a memory-theory project. It is a trust-and-control layer for persistent agent memory.

So the homepage pattern should combine four things:
1. infra credibility
2. agent workflow relevance
3. inspectability / governance proof
4. explicit safety boundary

That suggests a hybrid pattern:
- Not as minimal as Tailwind.
- Not as sprawling as Supabase.
- More evidence-driven than generic AI tooling READMEs.
- More operationally concrete than abstract “AI memory” copy.

My recommendation is this pattern:

### Recommended homepage spine for deep-memory

1. Hero / above the fold
2. One paragraph problem statement
3. “Why this exists” / key value props
4. Tiny continuity quickstart
5. Proof / evidence
6. Connect your agent
7. Inspect and govern memory
8. What works today / support matrix
9. Architecture
10. Safety boundary
11. Contributing / roadmap

This is close to the current README, but the ordering should shift to make the first screen more legible and more persuasive.

---

## 6. Proposed above-the-fold structure for deep-memory

### Recommended structure

1. Project name + language switch
2. Tagline
3. Short subhead paragraph (2-3 lines)
4. 4 small trust badges max
5. Primary action links
   - Quickstart
   - Agent install guide
   - Safety / privacy
   - Benchmarks / evals
6. One hero visual
   - preferably WebUI screenshot or simple cross-agent memory flow
7. 3 concise value bullets

### Proposed above-the-fold wireframe

```text
# deep-memory
Machine-local memory for all your agents. Inspect what they remember. Decide what they keep.

A shared, inspectable memory layer for agents like Claude Code, Codex, OpenCode, and Hermes.
Store explicit durable facts and procedures in a machine-local SQLite database with scoped records — not hidden cloud state, not raw transcript scraping.

[CI] [Python 3.10+] [MIT] [Alpha]

Quickstart | Agent install guide | Safety & privacy | Evals

[hero visual: WebUI screenshot or agent -> SQLite -> agent diagram]

- Shared memory across agents
- Inspectable and editable by humans
- Local-first with explicit write boundaries
```

### Why this works

It answers, in order:
- what it is
- what problem it solves
- why it is trustworthy
- where to go next

And importantly, it makes the governance story visible immediately. That is the non-obvious wedge.

---

## 7. Concrete copy blocks

### A. Tagline options

Option 1
Machine-local memory for all your agents. Inspect what they remember. Decide what they keep.

Why it works:
- already strong
- crisp
- governance signal is unusual and memorable

Option 2
A shared, local-first memory layer for AI agents.

Why it works:
- slightly more infrastructural
- better if you want a more platform-like tone
- a bit less vivid than Option 1

Option 3
Persistent agent memory you can inspect, edit, export, and delete.

Why it works:
- very concrete
- strongest control/governance framing
- weaker on cross-agent story unless supported by subhead

Recommendation:
- Keep current tagline as the main line.
- Add a sharper subhead beneath it.

### B. Subhead options

Option 1
A shared, inspectable memory layer for Claude Code, Codex, OpenCode, and Hermes. Store explicit durable facts and procedures in a machine-local SQLite database with scoped records — no hidden cloud state, no transcript scraping, no opaque global memory.

Option 2
Agents lose useful context between sessions, and they cannot usually share what they have learned. `deep-memory` gives them one machine-local memory store with search, scopes, governance, and reviewable writes.

Option 3
Use one machine-local SQLite database as persistent memory across agents. Search before work, write back only durable facts after verified success, bound records with scope, and inspect every record through CLI, SDK, export, or WebUI.

Recommendation:
- Option 1 is best for homepage precision.
- Option 2 is best if you want stronger pain framing.

### C. Value props block

Recommended 3-bullet version:

- Cross-agent continuity. One shared memory layer for Claude Code, Codex, OpenCode, and Hermes.
- Inspectable by default. Read, edit, soft-delete, export, and audit every record through CLI, SDK, or local WebUI.
- Machine-local governance. One local SQLite store shared across agents, explicit scopes for user/workspace/project boundaries, and reviewable paths from memory to skill.

Alternative 4-bullet version:

- Shared across agents
- Machine-local SQLite, not cloud state
- Measured retrieval, including Chinese fixtures
- Reviewable writes and safety boundaries

### D. Quickstart block

The current quickstart is good mechanically. I would add a continuity-oriented quickstart higher up and move the more detailed CRUD quickstart slightly later.

Proposed top quickstart:

```bash
uv sync --extra dev --extra mcp
uv run deep-memory init ~/.deep-memory/deep-memory.db
uv run deep-memory add ~/.deep-memory/deep-memory.db \
  "User wants agents to use deep-memory as shared persistent memory" \
  --kind semantic --importance 0.8
uv run deep-memory search ~/.deep-memory/deep-memory.db "shared persistent memory"
```

Suggested one-line explanation under it:
This is the core loop: install one machine-local memory store, let agents share it, and keep records bounded with explicit scopes.

### E. Evidence block

This should be tighter and closer to the top than it is now.

Proposed copy:

Evidence, not magic:
- Chinese retrieval evals: 55/55 on v1 and 20/20 on harder v2 checked-in fixtures
- Memory benchmark: checked-in bilingual task benchmark with reproducible commands
- Inspectability: CLI, export, soft delete, hard delete, and local WebUI

This is strong because it ties claims to reproducible artifacts.

### F. Safety boundary block

Current section is good. Above the fold, use a compressed version:

Safety boundary:
- explicit durable facts, not raw transcripts
- local SQLite by default
- no secrets or temporary task status
- procedural writes only after verification or confirmation
- memory-to-skill export is reviewable, never auto-installed

This is especially important because “persistent memory” changes behavior over time. Serious readers will look for this.

---

## 8. Recommended structural edits relative to the current README

### Keep

Strong elements already present:
- current tagline
- strong body paragraph explaining the pain
- highlights section
- concrete quickstart
- connect-your-agent section
- evidence section with measured tone
- safety boundary section
- what works today table

### Change order

Recommended order:

1. Title / language switch
2. Tagline
3. Stronger subhead paragraph
4. Badges
5. Primary route links
6. Hero visual
7. 3-bullet value props
8. Tiny quickstart
9. Evidence / proof block
10. Connect your agent
11. Inspect memory
12. What works today
13. Architecture
14. Safety boundary
15. Contributing

### Why reorder this way

Because the current README explains well, but some of the best parts arrive slightly too late.

The critical top-level story is:
- shared memory across agents
- local SQLite
- inspectable/governed
- reproducible evidence

That should be visible before the reader scrolls into the longer sections.

---

## 9. A concrete proposed top-of-README draft

Here is a draft that fits the observed OSS pattern while staying honest.

```md
# deep-memory

[English](README.md) | [简体中文](README.zh-CN.md)

> Machine-local memory for all your agents. Inspect what they remember. Decide what they keep.

A shared, inspectable memory layer for Claude Code, Codex, OpenCode, and Hermes.
Store explicit durable facts and procedures in a machine-local SQLite database with scoped records — not hidden cloud state, not raw transcript scraping, not opaque global memory.

[![CI](https://github.com/benbenlijie/deep-memory/actions/workflows/ci.yml/badge.svg)](https://github.com/benbenlijie/deep-memory/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-alpha-orange)

Quick links: [Quickstart](#quickstart) · [Agent install guide](docs/AGENT_INSTALL_GUIDE.md) · [Safety & privacy](docs/SAFETY_AND_PRIVACY.md) · [Benchmarks & evals](docs/MEMORY_BENCHMARK.md)

- Cross-agent continuity: one shared memory layer across multiple agent tools
- Inspectable by default: read, edit, export, soft-delete, and audit every record
- Machine-local governance: one shared SQLite store, explicit scopes, reviewable memory-to-skill export

<p align="center">
  <img src="docs/assets/deep-memory-architecture.svg" alt="deep-memory architecture" width="920">
</p>

Agents forget useful things between sessions. The convention Claude Code just learned is invisible to Codex. The workflow Hermes just proved has to be re-explained in OpenCode. `deep-memory` gives those tools one shared, inspectable memory layer — a machine-local SQLite store with scoped records, no cloud, no transcript scraping, no hidden global state.
```

### Note on the visual

If a local WebUI screenshot exists or can be made cleanly, I would consider replacing the architecture diagram in the first screen with the screenshot, and moving the architecture diagram lower.

Reason:
- a screenshot proves inspectability immediately
- architecture proves design clarity later
- for this project, trust comes from control and observability more than from abstract structure

---

## 10. Final recommendation

### Is the problem worth emphasizing this way?

Yes.

If you退后一步看, the most differentiated thing about `deep-memory` is not merely “persistent memory.” Many projects can say that. The real wedge is:
- machine-local
- cross-agent
- scoped
- inspectable
- governed
- evidence-backed

That is the root positioning.

### Why now

Because agents are proliferating faster than shared memory conventions.
The bottleneck is not just retrieval quality. It is trust, interoperability, and control.
A memory layer people cannot inspect will struggle to become foundational infrastructure.

### Real homepage bottleneck

The key homepage bottleneck is not lack of content. It is ordering.
The README already contains much of the right substance. The opportunity is to compress the core story into the first screen:
- what it is
- what pain it resolves
- what makes it trustworthy
- how to try it

### Recommended decision

Do:
- keep the current tagline
- strengthen the subhead
- move routing links and proof closer to the top
- make inspectability and safety visible earlier
- consider using a WebUI screenshot as the first visual

Avoid:
- overclaiming general “agent memory solved” language
- pushing too much architecture before the user understands the job-to-be-done
- hiding the safety boundary too low on the page

### Most important sentence to optimize

If I had to optimize one line, it would be this:

A shared, inspectable memory layer for Claude Code, Codex, OpenCode, and Hermes — stored in a machine-local SQLite database with scoped records, explicit writes, reproducible evals, and human control over what persists.

That line captures the system’s real shape.

---

## 11. Source appendix

README sources sampled during this pass:

- FastAPI: https://github.com/fastapi/fastapi / https://raw.githubusercontent.com/fastapi/fastapi/master/README.md
- uv: https://github.com/astral-sh/uv / https://raw.githubusercontent.com/astral-sh/uv/main/README.md
- Supabase: https://github.com/supabase/supabase / https://raw.githubusercontent.com/supabase/supabase/master/README.md
- LangChain: https://github.com/langchain-ai/langchain / https://raw.githubusercontent.com/langchain-ai/langchain/master/README.md
- LangGraph: https://github.com/langchain-ai/langgraph / https://raw.githubusercontent.com/langchain-ai/langgraph/main/README.md
- Playwright: https://github.com/microsoft/playwright / https://raw.githubusercontent.com/microsoft/playwright/main/README.md
- Tailwind CSS: https://github.com/tailwindlabs/tailwindcss / https://raw.githubusercontent.com/tailwindlabs/tailwindcss/main/README.md
- Next.js: https://github.com/vercel/next.js / https://raw.githubusercontent.com/vercel/next.js/canary/packages/next/README.md
- OpenTelemetry Collector: https://github.com/open-telemetry/opentelemetry-collector / https://raw.githubusercontent.com/open-telemetry/opentelemetry-collector/main/README.md
- DuckDB: https://github.com/duckdb/duckdb / https://raw.githubusercontent.com/duckdb/duckdb/main/README.md
- SQLite: https://github.com/sqlite/sqlite / https://raw.githubusercontent.com/sqlite/sqlite/master/README.md
- Litestream: https://github.com/benbjohnson/litestream / https://raw.githubusercontent.com/benbjohnson/litestream/main/README.md
- Chroma: https://github.com/chroma-core/chroma / https://raw.githubusercontent.com/chroma-core/chroma/main/README.md
