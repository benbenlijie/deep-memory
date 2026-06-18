# Product Positioning: deep-memory

## 1. Root positioning

如果你退后一步看，agent memory 不是“把更多历史塞回 prompt”的问题。真正的问题是：一个长期运行的 agent 如何把经验转化成可检索、可审计、可遗忘、可纠错、可复用的状态。

`deep-memory` 的当前定位：

> Chinese-first, local-first, inspectable memory governance for AI agents, with a deliberate path from remembered facts to reusable skills.

更短一点：

> The memory governance layer for agents that need durable context, Chinese retrieval quality, and Memory × Skill compounding.

这不是另一个 vector DB，也暂时不应声称自己已经超过 Mem0/Zep/Graphiti/Cognee/LangMem/TencentDB-Agent-Memory。当前更 defensible 的 wedge 是：把“长期记忆质量”拆成可测量的生命周期问题，而不是只讲存储结构或 demo 效果。

## 2. Facts / assumptions / hypotheses

### Facts grounded in this repository

- `deep-memory` is currently a Python SDK + CLI backed by SQLite/FTS5.
- Current MVP supports memory records with layer/kind, source, confidence, importance, timestamps, lexical retrieval, Chinese bigram fallback, decay scoring, and simple conflict-candidate detection.
- README explicitly positions the project around local-first persistence, Chinese-first retrieval direction, conflict candidates, inspectability, and Memory → Skill generation.
- Roadmap names these future milestones: Hermes plugin, MCP server, Chinese tokenizer + embedding retrieval, Web memory inspector/editor, Memory → Skill generation, and cross-agent shared memory ecosystem.
- Current architecture document says the root bottleneck is representation and lifecycle, not distributed storage.

### Facts from public competitor materials checked during this task

- Mem0 describes itself as a universal memory layer for AI agents and publishes benchmark claims for LoCoMo and LongMemEval, with token and latency numbers.
- Zep positions itself as an end-to-end context engineering platform using temporal knowledge graphs and relationship-aware retrieval, with a cloud-first enterprise posture.
- Graphiti positions itself as a framework for temporal context graphs for AI agents, supporting provenance, evolving facts, and hybrid retrieval.
- Cognee positions itself as an open-source AI memory platform for agents, centered on persistent long-term memory and self-hosted knowledge graphs.
- LangMem provides memory tools for LangGraph agents, including hot-path memory management tools and background memory management.
- TencentDB-Agent-Memory positions itself around symbolic short-term memory plus layered long-term memory, and publicly claims token reduction and pass-rate improvements in OpenClaw-style long-horizon sessions.

### Assumptions

- The early adopter is a developer building agents, not a non-technical end user.
- The first credible niche is local development + Chinese-heavy workflows + Hermes/MCP style agent integration, rather than enterprise SaaS context engineering.
- Developers will care about inspectability and controllability if the quickstart proves value within minutes.
- Chinese-first quality is under-served enough to be a wedge, but only if measured by a real Chinese retrieval benchmark rather than asserted in copy.
- Memory × Skill is a meaningful long-term differentiator, but only if it produces observable improvements in repeated task success, token use, or setup friction.

### Hypotheses requiring benchmarks

- H1: Chinese-first retrieval can beat generic lexical/vector baselines on Chinese user-preference, project-convention, and temporal-recall tasks.
- H2: Local-first inspectable memory improves developer trust compared with opaque cloud memory, especially when records include source, confidence, timestamps, decay, and conflict candidates.
- H3: Memory × Skill can compound: repeated successful procedures can be distilled into reusable playbooks that improve future agent task success beyond fact recall alone.
- H4: A small SQLite/FTS5 baseline with good governance can beat heavier graph/vector systems on setup time, debuggability, and first-week developer retention.
- H5: Conflict detection and forgetting-aware ranking matter more for long-term agent quality than raw recall volume once memory stores grow beyond toy examples.

## 3. Competitor truth table

| System | Public positioning | Core representation / mechanism | Strength | Likely blind spot | deep-memory wedge |
| --- | --- | --- | --- | --- | --- |
| Mem0 | Universal memory layer for AI agents | Memory extraction + retrieval, benchmarked on long-memory tasks | Strong mindshare, polished SDK/product, public benchmark claims | May be perceived as generic/personalization-first; Chinese-first and inspectable local governance are not the obvious center | Do not compete on generic “memory layer” first. Compete on transparent governance, Chinese evals, and local developer control. |
| Zep | End-to-end context engineering platform | Temporal knowledge graph + relationship-aware context assembly | Production/enterprise orientation, low-latency context blocks, cloud service posture | Cloud-first and platform-heavy for developers wanting local inspectable primitives | Be the small local-first substrate that developers can inspect, test, and adapt before adopting heavier platforms. |
| Graphiti | Temporal context graphs for AI agents | Evolving temporal knowledge graph with provenance and hybrid retrieval | Strong graph/time model; good fit for dynamic facts and relationship queries | Graph infrastructure can be more complex than needed for first memory governance loop | Start simpler: records, lifecycle, decay, conflict candidates, Chinese retrieval; add graph only when evals show it is necessary. |
| Cognee | Open-source AI memory platform for agents | Self-hosted knowledge graph / GraphRAG style memory | Broad AI memory platform story, open-source traction, graph-based ingestion | Broad platform surface may dilute the narrow developer wedge | Focus on minimal SDK/CLI, eval-first memory quality, Hermes/MCP integration, and Memory × Skill as a sharper mechanism. |
| LangMem | LangGraph-native tools for agents to learn/adapt | Hot-path memory tools + background memory manager + LangGraph store integration | Excellent fit inside LangGraph ecosystem; pragmatic primitives | Ecosystem-tied; less differentiated for non-LangGraph agents or Chinese local workflows | Stay framework-agnostic and local-first; provide adapters rather than becoming one framework’s memory feature. |
| TencentDB-Agent-Memory | Symbolic short-term memory + layered long-term memory | L0→L3 layered memory, symbolic/Mermaid task state, traceability, local pipeline | Very strong mechanistic story for long-horizon agents; public long-session benchmark claims | Heavier conceptual system; current strongest wedge is OpenClaw/TencentDB-style ecosystem | Treat it as the closest conceptual competitor. Differentiate through Python SDK ergonomics, Chinese retrieval benchmark, Hermes-first integration, and Memory × Skill evals. |

## 4. Wedge

The non-obvious wedge is not storage. It is memory governance under real agent pressure:

```text
what to remember → how to represent → when to recall → when to decay/forget → how to detect conflict → when to turn procedure into skill
```

`deep-memory` should make this loop measurable and inspectable.

### Primary wedge

Chinese-first local memory governance for developers building persistent agents.

This means:

- Chinese retrieval is not an afterthought or translated README badge; it is a first-class benchmark target.
- Local-first is not just privacy language; it enables inspection, debugging, deterministic tests, and user-controlled correction.
- Memory governance is not just storing embeddings; it includes lifecycle, decay, contradiction, provenance, and user control.

### Secondary wedge

Memory × Skill compounding.

Most memory systems optimize recall of facts. The deeper opportunity is to decide when an agent’s repeated successful behavior should become procedural infrastructure:

```text
conversation trace → atomic fact / event → scenario pattern → reusable skill / playbook → future task improvement
```

This should stay a claim requiring benchmarks until the project has a working Memory → Skill pipeline and repeated-task evals.

## 5. Non-goals

- Not a vector database.
- Not an enterprise context-engineering cloud platform in the first phase.
- Not a full knowledge-graph platform until evidence shows graph structure is the bottleneck.
- Not a claim to beat Mem0/Zep/Graphiti/Cognee/LangMem/TencentDB-Agent-Memory on all dimensions.
- Not a black-box “remember everything” system.
- Not a replacement for model context windows, RAG, or project documentation.
- Not a memory system that silently rewrites user identity or preferences without traceability and correction.

## 6. Proof obligations

如果这是真的，那它必须被证明，而不是靠 positioning 说服。

### Chinese-first claim

Required evidence:

- A Chinese memory retrieval eval set covering user preferences, project conventions, temporal facts, contradictions, aliases, and mixed Chinese/English technical terms.
- Baselines: SQLite FTS5 lexical, Chinese bigram fallback, tokenizer-based retrieval, embedding retrieval, hybrid retrieval.
- Metrics: recall@k, MRR, contradiction-detection precision/recall, latency, storage size, and qualitative failure categories.
- Public examples where Chinese queries retrieve the right memory despite paraphrase, time expressions, and mixed-language terms.

Decision rule:

- Keep “Chinese-first” as a differentiation claim only if benchmark deltas are visible and reproducible.
- If not, downgrade the claim to “Chinese-first roadmap” until the eval passes.

### Memory × Skill claim

Required evidence:

- A repeated-task benchmark with three modes: no memory, fact memory only, memory + generated skill.
- Tasks should include project conventions, tool quirks, debugging workflows, and recurring user preferences.
- Metrics: task success rate, turns/tool calls to completion, token use, repeated correction rate, and human review pass rate.
- Generated skills must preserve provenance: every skill should trace back to examples or successful runs.

Decision rule:

- Claim “path to Memory × Skill” now.
- Claim “Memory × Skill improves agents” only after repeated-task evals show statistically meaningful improvement.

### Local-first inspectability claim

Required evidence:

- CLI commands that let a developer inspect, edit, delete, and export memory records.
- Deterministic tests for conflict candidates, decay, and retrieval ranking.
- A small demo showing how a wrong memory is found, corrected, and no longer dominates recall.

Decision rule:

- This can be claimed earlier than Chinese-first superiority because the current SQLite/CLI architecture already supports the direction, but it still needs UX proof.

## 7. Recommended positioning copy

### README short line

> `deep-memory` is a local-first memory governance layer for AI agents: inspectable records, Chinese-first retrieval, conflict candidates, forgetting-aware ranking, and a path from memory to reusable skills.

### One-paragraph version

`deep-memory` helps AI agents remember what should persist across sessions without turning chat history into an opaque prompt dump. It starts with a small SQLite/FTS5 SDK and CLI, then builds toward Chinese-first retrieval quality, conflict-aware memory governance, and Memory × Skill compounding, where repeated successful workflows become reusable playbooks.

### What to say carefully

- Say: “Chinese-first retrieval is a core benchmark target.”
- Do not yet say: “Best Chinese memory system.”
- Say: “Memory × Skill is our long-term differentiator.”
- Do not yet say: “Automatically generates reliable skills from memory.”
- Say: “Local-first and inspectable baseline.”
- Do not yet say: “Enterprise-ready memory governance.”

## 8. Near-term execution implications

1. Build the Chinese retrieval evaluation set before adding more retrieval complexity.
2. Add benchmark pages before making stronger competitive claims.
3. Keep the storage layer boring until the evidence says graph/vector structure is the bottleneck.
4. Make correction/deletion/export flows visible in CLI and docs.
5. Treat TencentDB-Agent-Memory as the strongest mechanistic benchmark for long-horizon memory, not as a project to dismiss.
6. Turn Memory × Skill into an eval loop, not a slogan.
