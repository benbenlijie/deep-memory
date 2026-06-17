# 100k-Star Launch / Relaunch Calendar

## Principle

100k stars is a lagging outcome. The controllable loop is:

```text
product evidence -> credible demo -> narrow distribution -> feedback -> issue/PR -> stronger product evidence -> relaunch
```

Every launch below is tied to a concrete artifact, a demo that can be reproduced, a claim that is safe to make at that stage, a metric that changes the next decision, and an explicit feedback collection path. Do not launch a bigger narrative before the underlying evidence exists.

## Launch calendar overview

| Moment | Launch name | Readiness gate | Primary outcome |
| --- | --- | --- | --- |
| M+1 | Controlled preview: local-first memory MVP | Source install, quickstart, examples, tests, benchmark v0, README positioning | Validate activation and memory-governance resonance with early builders |
| M+2 | Chinese retrieval evidence launch | Chinese eval dataset + baseline report + reproducible command | Make Chinese-first a measured direction, not a slogan |
| M+3 | Trust / WebUI relaunch | WebUI inspector/editor MVP or clickable demo + memory failure template | Prove users can inspect, correct, and delete agent memory |
| M+6 | Cross-agent infrastructure launch | Hardened MCP + Hermes/Claude/Codex/OpenCode adapter evidence | Show deep-memory is agent runtime infrastructure, not one CLI demo |
| M+12 | Memory -> Skill ecosystem launch | Memory-to-skill pipeline + registry/governance path + repeated-task eval | Reframe memory as compounding agent capability |

## M+1 — Controlled preview: local-first memory MVP

### Audience

- English: AI agent builders, Hermes users, MCP-curious developers, early OSS infra contributors.
- Chinese: AI 开发者、Hermes/Agent 实践者、对“AI 私域/长期伙伴”有真实工作流的人。

### Artifact

- `README.md` first-screen positioning and 2-minute source quickstart.
- `examples/quickstart.py` and `examples/memory_vs_nomemory.py`.
- `benchmarks/memory_benchmark.py` and `docs/MEMORY_BENCHMARK.md`.
- `docs/LAUNCH_LOOP.md` as the launch operating loop.
- `docs/M1_GO_NO_GO.md` as the launch gate.

### Demo

Use the “你的 AI 记得你吗？” 60–90 second demo from `docs/LAUNCH_LOOP.md`:

```bash
uv sync --extra dev
uv run pytest -q
uv run python examples/quickstart.py
uv run python examples/memory_vs_nomemory.py
uv run python benchmarks/memory_benchmark.py --json
```

The demo must show: add a memory, recall it in a new flow, inspect stats/output, and contrast with a no-memory baseline.

### Claim

Safe claim:

> `deep-memory` is a local-first persistent memory layer for AI agents, with inspectable SQLite records, cross-session recall, forgetting-aware ranking, conflict candidates, and a Chinese-first roadmap.

Do not yet claim: “best memory layer”, “production-ready”, “human-like memory”, or “Chinese retrieval superiority”.

### Metric

- Stars: early recognition signal, not the control variable.
- Weekly activated memory developers (WAMD): people who complete a real quickstart/demo loop.
- Quickstart success rate and time to first recall.
- Clones / unique cloners.
- Memory failure cases submitted.
- Issues/PRs created from real feedback.

### Feedback collection

- GitHub issue template: memory failure case.
- Pinned issue: “Share where your agent forgot something important.”
- Manual launch feedback log using `docs/METRICS.md` schema.
- Weekly triage: setup friction, positioning confusion, retrieval failures, integration requests, trust/safety concerns.

### Distribution — English

- GitHub README + demo GIF/video.
- X thread: local-first memory governance, not longer context.
- Show HN only after source install and examples are smooth; submit as “Show HN: deep-memory — local-first persistent memory for AI agents”.
- Agent-builder communities: Hermes, MCP, Claude/Codex/OpenCode adjacent groups.

### Distribution — Chinese

- 知乎：机制长文《为什么 AI Agent 需要长期记忆，而不只是更长上下文？》
- B站：60–90 秒“AI 金鱼 vs deep-memory”短视频；可追加 5–8 分钟技术 walkthrough。
- 小红书：非代码化 carousel，讲“AI 为什么总像第一次见你”。
- 微信朋友圈/私域：围绕 AI 普惠和个人工作流，收集真实 memory failure cases。
- QQ/微信群：小范围 controlled preview，优先找能跑 quickstart 的开发者。

## M+2 — Chinese retrieval evidence launch

### Audience

- English: agent-memory researchers, retrieval/RAG developers, bilingual agent builders.
- Chinese: 中文 Agent 开发者、RAG/检索工程师、关注中文场景可靠性的开源用户。

### Artifact

- `evals/data/zh_memory_retrieval.jsonl`.
- `evals/chinese_retrieval_eval.py`.
- `docs/CHINESE_RETRIEVAL_EVAL.md` with fixture schema, metrics, and baseline notes.
- A benchmark snapshot in `docs/METRICS.md` or a weekly metric note.

### Demo

```bash
uv run python evals/chinese_retrieval_eval.py --data evals/data/zh_memory_retrieval.jsonl
uv run python evals/chinese_retrieval_eval.py --data evals/data/zh_memory_retrieval.jsonl --json
```

Show at least three cases: Chinese preference recall, mixed Chinese/English technical term recall, and contradiction/time-sensitive recall.

### Claim

Safe claim:

> Chinese-first retrieval is now an executable benchmark target in `deep-memory`; we can measure where lexical/bigram retrieval works and where it fails.

Claim only if evidence supports it:

> The current baseline improves over no-memory / naive search on the v1 Chinese memory retrieval fixture.

Do not claim broad superiority over Mem0/Zep/Graphiti/Cognee/LangMem/TencentDB-Agent-Memory.

### Metric

- Eval pass rate / recall@k / MRR from the Chinese fixture.
- Number of fixture PRs or issue-submitted Chinese memory cases.
- Failure categories: tokenization, aliasing, temporal phrasing, contradiction, mixed-language technical terms.
- Chinese-channel activation: quickstart completions, comments with run output, issue conversions.

### Feedback collection

- GitHub issue label: `eval:chinese-retrieval`.
- Request redacted Chinese memory failure cases.
- Invite PRs that add fixtures before adding retrieval complexity.
- Weekly failure taxonomy: which retrieval class is blocking the next improvement?

### Distribution — English

- X thread: “What Chinese agent-memory retrieval exposes that English-only demos miss.”
- GitHub release/discussion with commands and JSON output.
- RAG/retrieval communities: ask for benchmark critique, not applause.
- HN only if the dataset and command are sufficiently reproducible.

### Distribution — Chinese

- 知乎：从中文分词、时间表达、混合术语解释 eval 设计。
- B站：跑 eval 的 live demo，展示 pass/fail examples。
- 微信/朋友圈/私域：征集真实中文 memory failure cases。
- QQ/微信群：发 fixture contribution guide，推动小 PR。

## M+3 — Trust / WebUI relaunch

### Audience

- English: developers skeptical of hidden agent memory, privacy-conscious OSS users, tool builders.
- Chinese: 普通 AI 高阶用户、Agent 开发者、担心“AI 乱记/记错/删不掉”的用户。

### Artifact

- `docs/WEBUI_SPEC.md` plus either a working WebUI MVP or a clickable demo/screenshot prototype.
- Memory inspector/editor flows: inspect, correct, delete, source trail, conflict candidates.
- Memory failure case issue template and triage loop.
- Updated README section: “How to inspect and correct memory.”

### Demo

Show a wrong or stale memory being found, corrected/deleted, and no longer dominating recall. The demo should include:

1. memory record with source/confidence/timestamp;
2. search result before correction;
3. edit/delete action;
4. search result after correction;
5. conflict candidate or provenance view.

### Claim

Safe claim:

> Trustworthy agent memory must be inspectable and correctable; `deep-memory` exposes memory as reviewable state rather than hidden prompt stuffing.

Do not claim full safety, automatic truth, or enterprise-grade governance.

### Metric

- WebUI/demo launches or inspector sessions.
- Edit/delete/correction actions in demo reports.
- Number of submitted memory failure cases.
- Ratio of failure cases converted into issues/tests/eval fixtures.
- Trust-related feedback: “can I see why this memory exists?” yes/no.

### Feedback collection

- GitHub memory failure template with fields: expected memory, wrong recall, source, runtime, privacy redactions.
- Collect screenshots/transcripts only after redaction guidance.
- Weekly issue triage: correction UX, provenance confusion, deletion semantics, conflict noise.

### Distribution — English

- GitHub discussion: “What should an agent memory inspector show?”
- X demo clip: wrong memory -> inspect -> correct -> recall changes.
- Privacy/local-first communities: focus on control, not hype.
- Agent framework communities: ask what metadata their users need to trust memory.

### Distribution — Chinese

- 知乎：写“AI 记忆为什么必须可检查、可删除、可纠错”。
- B站：WebUI walkthrough，重点展示纠错前后对比。
- 小红书：面向高级用户讲“不要让 AI 偷偷记错你”。
- 微信/私域：邀请用户提交 redacted failure cases。

## M+6 — Cross-agent infrastructure launch

### Audience

- English: agent framework maintainers, MCP users, Claude Code/Codex/OpenCode builders, OSS infra developers.
- Chinese: Agent 框架开发者、MCP/插件生态开发者、开源基础设施贡献者。

### Artifact

- `docs/MCP_INTEROPERABILITY.md` with real smoke-test transcript.
- `docs/ADAPTERS.md` covering Hermes, Claude Code, Codex, OpenCode/OpenClaw-style tools.
- Compatibility matrix: runtime, install command, read/write policy, verification command, known limitations.
- Example agent workflow using shared persistent memory across at least two clients, if feasible.

### Demo

A cross-client smoke test:

1. Add memory through MCP or Hermes-style adapter.
2. Search the same memory through another client or wrapper.
3. Show stats / DB evidence.
4. Demonstrate write policy and permission boundary.

Minimum command evidence should include `uv run pytest -q`, `uv run ruff check .`, and the MCP/manual adapter smoke command documented in the repo.

### Claim

Safe claim:

> `deep-memory` is becoming a small local memory substrate that different agent runtimes can share through explicit adapters and MCP.

Do not claim universal compatibility until the matrix is maintained by real users.

### Metric

- MCP installs / smoke-test completions.
- Adapter PRs and integration issues.
- Runtime compatibility rows verified.
- External examples or downstream repos.
- Percentage of integration feedback converted into docs/tests.

### Feedback collection

- GitHub issue labels: `adapter`, `mcp`, `runtime:hermes`, `runtime:claude`, `runtime:codex`, `runtime:opencode`.
- Compatibility matrix PR template.
- Ask every integration report for exact command, OS, runtime version, expected behavior, actual behavior.

### Distribution — English

- GitHub release: “deep-memory MCP + cross-agent adapter preview.”
- X technical thread with compatibility matrix.
- MCP/agent framework Discords, GitHub discussions, and relevant OSS repos.
- HN relaunch only if the demo proves a non-obvious cross-agent workflow.

### Distribution — Chinese

- 知乎：讲 MCP 与 Agent 记忆基础设施的关系。
- B站：跨客户端 demo，强调不是某一个聊天 UI 的记忆。
- QQ/微信群：找框架作者试 adapter，收集兼容性问题。
- 微信/朋友圈：偏战略叙事：Agent 生态需要可共享、可审计的 memory substrate。

## M+12 — Memory -> Skill ecosystem launch

### Audience

- English: OSS maintainers, agent researchers, workflow automation builders, advanced AI engineers.
- Chinese: AI 自动化团队、Agent 工程师、希望把经验沉淀成可复用能力的开发者。

### Artifact

- `docs/MEMORY_TO_SKILL.md` and working Memory -> Skill export pipeline.
- Repeated-task eval comparing no memory vs fact memory vs memory + generated skill.
- Reviewable skill candidate format with provenance, safety checks, and human approval.
- Community registry path: examples, governance, contribution rules.

### Demo

Show a repeated workflow becoming a reviewable skill candidate:

1. store procedural memory from a successful repeated task;
2. export a skill candidate markdown;
3. show provenance/source trail;
4. human review approves/edits;
5. repeat the task with the skill and compare success/tool-call/time metrics.

### Claim

Safe claim:

> `deep-memory` is exploring the path from remembered facts to reusable agent skills, with provenance and review rather than automatic behavior mutation.

Stronger claim only if eval supports it:

> Memory + reviewed skill candidates improves repeated-task success over fact memory alone on the project’s repeated-task benchmark.

Do not claim autonomous self-improvement without review, safety checks, and eval evidence.

### Metric

- Repeated-task benchmark delta: success rate, turns/tool calls, token use, review pass rate.
- Skill candidates generated, reviewed, accepted, rejected.
- Contributor-submitted procedural examples.
- Downstream repos using exported skills/playbooks.
- Safety issues: overbroad skills, stale instructions, missing provenance.

### Feedback collection

- GitHub label: `memory-to-skill`.
- Skill candidate review template: source memory IDs, examples, non-goals, safety boundaries.
- Collect rejected candidates as training/eval data for better gating.
- Maintain a public registry only after review criteria are stable.

### Distribution — English

- Long-form technical essay: “Memory is not enough; agents need reviewed procedural learning.”
- X thread with before/after repeated-task eval.
- GitHub release + examples registry.
- Research/agent communities: ask for critique on eval design and safety boundary.

### Distribution — Chinese

- 知乎：解释“从记住事实到学会流程”的边界。
- B站：Memory -> Skill demo，强调 human review 和 provenance。
- 微信/私域：面向 AI 自动化团队收集重复流程案例。
- QQ/微信群：组织小型贡献 sprint，贡献 reviewable procedural examples。

## Relaunch decision rules

- If attention is high but activation is low: pause broad distribution; fix README, install path, quickstart, and examples.
- If activation is high but feedback is vague: sharpen issue templates and ask for concrete transcripts.
- If Chinese channels produce many failures: prioritize eval fixtures and retrieval improvements before more launch copy.
- If trust concerns dominate: prioritize WebUI/provenance/delete/edit before ecosystem expansion.
- If adapter demand dominates: shift M+6 work earlier and publish a compatibility matrix.
- If Memory -> Skill creates safety concern: slow down public registry and require stricter review/provenance gates.

## Weekly relaunch checklist

For each launch or relaunch, fill this before publishing:

| Field | Answer |
| --- | --- |
| Evidence shipped | |
| Demo command/video | |
| Safe claim | |
| Claim we must not make yet | |
| Primary audience | |
| English channels | |
| Chinese channels | |
| Metric to watch for 48h | |
| Feedback collection path | |
| Next bottleneck decision rule | |

## What this plan deliberately avoids

- No “100k stars” hype without activation evidence.
- No broad launch before the demo is reproducible.
- No Chinese-first superiority claim before the eval supports it.
- No memory trust claim without inspect/correct/delete evidence.
- No self-improving-agent claim without human review and repeated-task evaluation.
