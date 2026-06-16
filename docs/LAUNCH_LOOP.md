# Launch Loop: 你的 AI 记得你吗？

## 问题本质

如果你退后一步看，`deep-memory` 的第一次 GitHub launch 不是在卖一个 SQLite 小工具，而是在验证一个更底层的问题：开发者是否已经痛到需要一个可检查、可治理、local-first 的 Agent 长期记忆层。

首轮 launch 的目标不是一次性爆红，而是建立一个可重复的反馈回路：

```text
clear demo → developer recognition → GitHub star/watch/clone → local activation → issue/PR feedback → better demo/product → next launch
```

## Demo script/storyboard — “你的 AI 记得你吗？”

### 核心叙事

一句话 hook：

> 你的 AI 很聪明，但它每次重启都像第一次见你。`deep-memory` 给 Agent 装上一个 local-first、可检查、会遗忘、能发现矛盾的长期记忆层。

### 60–90 秒短视频脚本

| Time | Visual | Voiceover / Caption | Product proof |
| --- | --- | --- | --- |
| 0–5s | Terminal split-screen: left “普通 Agent”, right “with deep-memory” | “你的 AI 记得你吗？” | Hook |
| 5–15s | User tells agent: “我喜欢中文为主，技术术语用英文；回答要简洁。” Then session closes. | “很多 Agent 只在当前 session 里聪明。” | Show preference input |
| 15–25s | New terminal/session. Ordinary agent is asked: “我喜欢什么风格？” It cannot know. | “一重启，它就失忆。” | Pain contrast |
| 25–40s | Run `deep-memory add agent.db ...` and `deep-memory search agent.db 用户喜欢什么风格？` | “`deep-memory` 把值得保存的事实放进本地数据库。” | CLI demo |
| 40–55s | Show search result with score/kind/content; show SQLite file path. | “不是黑盒 SaaS 记忆，而是你能 inspect、edit、delete 的 memory layer。” | Local-first trust |
| 55–70s | Add conflicting preference: “用户偏好：英文为主”。 Show conflict candidate / governance angle. | “真正关键的不是只会记住，而是知道什么时候可能记错、冲突、过期。” | Conflict/decay direction |
| 70–85s | Show README architecture: memory extractor → engine → retrieval planner → context injector. | “我们从一个小 SDK 开始，但目标是 Agent memory governance。” | Depth |
| 85–90s | GitHub repo page + CTA | “如果你也觉得 Agent 不该是金鱼，star `deep-memory`，一起把这层基础设施做扎实。” | CTA |

### Terminal demo commands

```bash
git clone https://github.com/benbenlijie/deep-memory.git
cd deep-memory
uv sync --extra dev
uv run pytest

uv run deep-memory init demo-agent.db
uv run deep-memory add demo-agent.db "用户偏好：中文为主，技术术语用英文；回答要简洁" --kind semantic --importance 0.9
uv run deep-memory add demo-agent.db "2026-06-16: discussed deep-memory GitHub launch" --kind episodic
uv run deep-memory search demo-agent.db "用户喜欢什么风格？"
uv run deep-memory stats demo-agent.db
```

### Shot list for B站 / 小红书 / X video

1. Title card: “你的 AI 记得你吗？”
2. Before: Agent forgets preferences after restart.
3. After: `deep-memory search` recalls the preference.
4. Trust: local `demo-agent.db`, inspectable SQLite, no closed SaaS memory lock-in.
5. Governance: forgetting curve + conflict candidates are the real bottleneck.
6. CTA: star, try quickstart, open issues with memory failure cases.

### Copy variants

#### GitHub README / pinned issue

```text
Most agents are still goldfish: brilliant in one session, blank in the next.

deep-memory is a local-first persistent memory layer for AI agents: SQLite/FTS5, memory kinds, importance/confidence, forgetting-aware ranking, conflict candidates, Python API + CLI.

Try it in 2 minutes. If your agent should remember project conventions, user preferences, and reusable procedures without sending memory to a closed SaaS, this is the layer we are building.
```

#### X / HN short post

```text
I’m building deep-memory: a local-first persistent memory layer for AI agents.

The bet: the bottleneck is not just longer context. It is memory governance — what to remember, when to recall, when to forget, and how to detect contradictions.

MVP: Python SDK + CLI, SQLite/FTS5, forgetting-aware ranking, conflict candidates, Chinese-first retrieval path.

Would love feedback from people building agents that currently feel like goldfish.
```

#### 知乎 / B站 / 小红书中文开头

```text
你有没有发现：现在的 AI Agent 很聪明，但每次重启都像第一次见你。

它不记得你的项目约定，不记得你喜欢的表达风格，也不记得上次踩过的坑。更深一层的问题是：就算它能记住，什么该记、什么该忘、记忆冲突时怎么办？

我做了一个开源项目 deep-memory，从一个很小的 local-first Python SDK + CLI 开始，尝试把 Agent 长期记忆做成可检查、可治理的基础设施。
```

## Launch channels

### 1. GitHub — conversion home

Purpose: turn curiosity into star/watch/clone/issue.

Actions:

- Pin README hook around “Agent goldfish → local-first memory governance”.
- Add a demo GIF/video link from the storyboard above.
- Create a pinned issue: “Share your agent memory failure case”.
- Use GitHub Discussions later only after first 20–30 real issues/feedback items exist.

Primary CTA:

- Star the repo.
- Run quickstart.
- Open an issue with one memory failure case or integration request.

### 2. X / Hacker News — developer discovery

Purpose: test whether the problem framing resonates with builders outside the existing network.

Actions:

- X: post the 60–90s video plus concise technical thread.
- HN: avoid marketing tone; submit as “Show HN: deep-memory — local-first persistent memory for AI agents”.
- Answer comments with mechanism: memory kinds, decay, conflict detection, Chinese retrieval, local SQLite baseline.

Primary CTA:

- Try the quickstart and report where memory retrieval fails.

### 3. 知乎 — mechanism explanation

Purpose: explain why “long context” is not the same as durable memory.

Actions:

- Publish a structured post: “为什么 AI Agent 需要长期记忆，而不只是更长上下文？”
- Use `deep-memory` as the concrete implementation, not as the whole article.
- Invite examples from developers: lost preferences, repeated project setup mistakes, contradictory memory.

Primary CTA:

- Star + submit Chinese memory/retrieval cases.

### 4. B站 — visual demo and credibility

Purpose: make the “AI 金鱼” contrast obvious in under 90 seconds, then follow with a 5–8 minute technical walkthrough.

Actions:

- Short video: storyboard above.
- Long video: architecture + quickstart + roadmap.
- Put GitHub link and commands in description.

Primary CTA:

- Run the commands and comment with actual agent memory use cases.

### 5. 小红书 — high-level awareness

Purpose: reach AI tool builders and advanced users with a simple narrative.

Actions:

- Carousel: “AI Agent 为什么总像金鱼？”
- Slides: problem → demo → local-first trust → what should be remembered → GitHub link.
- Keep it less code-heavy than B站/知乎.

Primary CTA:

- Follow project, star repo, join feedback loop.

## Weekly metrics and feedback loop

### North-star loop

```text
impressions → repo visits → stars/watchers → clones/installs → quickstart success → issues/PRs/use cases → product fixes → stronger demo → next launch
```

### Weekly dashboard

| Layer | Metric | Target for week 1 | Why it matters | Source |
| --- | --- | ---: | --- | --- |
| Attention | GitHub stars | 100+ | First proof of problem recognition | GitHub insights/API |
| Attention | Repo visitors | 500+ | Measures launch reach independent of conversion | GitHub traffic |
| Intent | Clone count | 50+ | Stronger than star; indicates trial intent | GitHub traffic |
| Activation | Quickstart success reports | 10+ | Proves first 2 minutes work | Issues/comments/manual form |
| Activation | CLI/API demo completions | 10+ | Confirms local developer value | Self-reported issue template initially |
| Feedback | Memory failure cases submitted | 10+ | Feeds product/eval roadmap | GitHub issue template |
| Feedback | Integration requests | 5+ | Reveals ecosystem wedge: Hermes/MCP/Claude/Codex/OpenCode | Issues |
| Quality | New bugs/regressions | <5 blocking | Keeps launch trust high | Issues/CI |
| Community | PRs or serious contributors | 1–3 | Early signal of open-source pull | GitHub |

### Activation definition

A user counts as activated when they complete at least one of:

1. Runs the local quickstart and retrieves one memory successfully.
2. Opens an issue with a real memory failure case from their agent workflow.
3. Builds or requests an integration for Hermes, Claude Code, Codex, OpenCode, MCP, or another agent runtime.

### Weekly operating cadence

| Day | Action | Output |
| --- | --- | --- |
| Monday | Collect GitHub traffic, stars, clones, issues, comments | `docs/launch/weekly-metrics/YYYY-WW.md` |
| Tuesday | Classify feedback into: retrieval, governance, integration, docs, packaging | Top 3 bottlenecks |
| Wednesday–Thursday | Fix the highest-leverage bottleneck | PR/commit + test evidence |
| Friday | Publish “what changed this week” update | GitHub release/discussion + social post |
| Weekend | Run one new launch experiment | New channel/post/video variant |

### Feedback taxonomy

- Positioning confusion: users think it is “just a vector DB”.
- Quickstart friction: install, uv, Python version, CLI ergonomics.
- Retrieval failure: Chinese tokenization, semantic mismatch, time/entity ambiguity.
- Memory governance: what to save, decay, conflict resolution, user control.
- Integration demand: Hermes plugin, MCP, Claude Code/Codex/OpenCode adapters.
- Trust/safety: local-first, privacy, deletion, inspectability.

### Decision rules

- If stars are high but clones low: README/demo is interesting but not actionable; improve quickstart and first command path.
- If clones are high but activation low: install or demo is failing; prioritize packaging/docs over new features.
- If issues cluster around “vector DB comparison”: positioning is unclear; sharpen governance framing.
- If Chinese retrieval complaints dominate: accelerate tokenizer/eval dataset tasks before ecosystem expansion.
- If integration requests dominate: prioritize Hermes/MCP adapter docs and examples.

## First-week launch checklist

- [ ] Record 60–90s demo video using the storyboard.
- [ ] Add demo GIF/video link near README first screen.
- [ ] Create issue template: memory failure case.
- [ ] Publish X thread + Show HN post.
- [ ] Publish 知乎 mechanism article.
- [ ] Publish B站 short demo and optional technical walkthrough.
- [ ] Publish 小红书 carousel.
- [ ] Create first weekly metrics note.
- [ ] Run Friday feedback triage and choose next bottleneck.

## Risk boundaries

- Do not overclaim “human-like memory” or AGI relevance. The credible claim is local-first agent memory infrastructure.
- Do not imply private user data should be stored casually. Emphasize inspectability, deletion, confidence, source, decay, and future governance.
- Do not chase all channels equally if activation is weak. The bottleneck should decide next week’s work.
