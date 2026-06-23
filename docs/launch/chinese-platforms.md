# 中文平台发布草稿

## V2EX

标题：做了一个给 AI Agent 用的本地记忆层：deep-memory（SQLite / MCP / 中文检索优先）

正文：

最近在做一个开源项目：`deep-memory`。

GitHub：https://github.com/benbenlijie/deep-memory
中文 README：https://github.com/benbenlijie/deep-memory/blob/main/README.zh-CN.md
快速开始：https://github.com/benbenlijie/deep-memory/blob/main/README.zh-CN.md#快速开始

它想解决的问题很具体：AI Agent 经常在跨会话、跨工具时忘记有用上下文。

比如 Claude Code 在一个 repo 里刚学会“提交前要跑 `uv run pytest -q`”，Codex 不知道；Hermes 刚跑通一个工作流，OpenCode 下次也未必知道。最后用户还是要反复解释项目约定、偏好、验证流程和一些长期事实。

我不太想把这个问题做成“偷偷存所有聊天记录”的系统，所以 `deep-memory` 的默认边界比较窄：

- 默认本地优先：项目里的一个 SQLite 文件
- 不抓 raw transcript，只存显式 durable facts / project conventions / reviewed procedures
- CLI、Python SDK、MCP server、JSONL import / wrapper 路径
- 本地 WebUI 可以查看、搜索、编辑、软删除、导出记录
- 每条 memory 有 `kind`、`importance`、`confidence`、`source`、时间戳、scope、conflict/lifecycle 状态
- procedural memory 可以导出成可 review 的 skill candidate，但不会自动安装成行为规则

快速开始：

```bash
git clone https://github.com/benbenlijie/deep-memory
cd deep-memory
uv sync --extra dev --extra mcp

uv run deep-memory init .deep-memory/deep-memory.db
uv run deep-memory add .deep-memory/deep-memory.db \
  "项目约定：提交前先运行 uv run pytest -q" \
  --kind procedural \
  --importance 0.8
uv run deep-memory search .deep-memory/deep-memory.db "这个项目怎么验证修改？"
```

也可以打开本地 WebUI：

```bash
uv run deep-memory webui .deep-memory/deep-memory.db --host 127.0.0.1 --port 8765
```

为什么强调中文检索？因为很多 agent memory 在中文项目里会遇到非常真实的混合文本：中文偏好、英文技术词、日期、项目名、MCP、Hermes、adapter、JSONL、Kanban、Loop Engineering 这些词混在一起。如果检索只在英文语境下看起来不错，实际用起来会很别扭。

目前仓库里放了 checked-in 的中文检索评估：

| 评估 | 当前结果 | 说明 |
| --- | --- | --- |
| Chinese retrieval v1 | 默认 local backend 55/55；可选 `jieba` 55/55 | 中文 + 中英混合技术词检索 |
| Chinese retrieval v2 | 20/20 top-1，MRR 1.0 | 多 memory + distractor + stale facts |
| Memory benchmark v0 | no-memory baseline 0/20；deep-memory 默认通常 20/20 | 验证 memory 是否能补足跨会话缺失事实 |

我现在更想听真实使用场景里的反馈：

1. 什么内容应该允许 agent 自动写入 memory？
2. 什么内容必须用户确认？
3. memory 的过期、冲突、scope 应该怎么设计才不会污染上下文？
4. 中文检索 fixture 还应该覆盖哪些 case？
5. 对 Claude Code / Codex / Hermes / OpenCode 这类工具，什么 adapter 形态最自然？

项目现在还是 alpha，更像 controlled preview，不是“记忆问题已经解决”的宣传。真正有趣的问题是：Agent memory 应该是隐藏状态，还是一个用户可审计、可治理、可迁移的本地系统？我倾向后者，所以先做了这个小工具。

如果你也在做本地 agent workflow，欢迎试一下，也欢迎提 issue / PR。

GitHub：https://github.com/benbenlijie/deep-memory
中文 README：https://github.com/benbenlijie/deep-memory/blob/main/README.zh-CN.md
快速开始：https://github.com/benbenlijie/deep-memory/blob/main/README.zh-CN.md#快速开始

---

## 掘金

标题：给 AI Agent 做一个可审计的本地记忆层：deep-memory 的设计与评估

正文：

如果你长期用 AI coding agent，会遇到一个很朴素的问题：它们很强，但很健忘。

一个会话里刚确认的项目约定，下一个会话不知道；Claude Code 学到的上下文，Codex 不知道；Hermes 跑通的流程，OpenCode 也无法自动继承。最后用户要不断重复“这个项目怎么测试”“我的输出偏好是什么”“哪些 workflow 已经验证过”。

`deep-memory` 想把这个问题收敛成一个更可控的系统：给 AI Agent 一个本地、可检视、跨工具的记忆层。

项目地址：https://github.com/benbenlijie/deep-memory
中文 README：https://github.com/benbenlijie/deep-memory/blob/main/README.zh-CN.md
Quickstart：https://github.com/benbenlijie/deep-memory/blob/main/README.zh-CN.md#快速开始

### 设计原则

第一，默认本地优先。

`deep-memory` 的核心存储是项目目录下的 SQLite 文件：

```text
.deep-memory/deep-memory.db
```

它可以被复制、备份、检查，也可以直接删除。默认路径不依赖云端服务，也不需要 API key。

第二，只存显式的 durable facts，而不是抓取完整聊天记录。

这点很重要。Agent memory 如果没有治理边界，很容易变成隐藏的长期行为状态。`deep-memory` 默认鼓励存储项目约定、用户确认过的偏好、经过验证的 workflow，而不是把 raw transcript 全部塞进去。

第三，每条 memory 都应该可审计。

记录里不只有 content，还有：

- `kind`：working / episodic / semantic / procedural
- `importance`
- `confidence`
- `source`
- timestamps
- scope
- conflict / lifecycle state

这样 memory 可以被检查、纠正、软删除、导出，而不是只剩一坨 opaque embedding。

第四，跨 Agent。

现在提供 CLI、Python SDK、MCP server、Hermes import、Codex wrapper 等路径。理想情况下，同一个项目里的 Claude Code、Codex、OpenCode、Hermes 都能读取同一个本地 memory DB，但写入策略要保持保守。

### 快速开始

```bash
git clone https://github.com/benbenlijie/deep-memory
cd deep-memory
uv sync --extra dev --extra mcp

uv run deep-memory init .deep-memory/deep-memory.db
uv run deep-memory add .deep-memory/deep-memory.db \
  "项目约定：提交前先运行 uv run pytest -q" \
  --kind procedural \
  --importance 0.8
uv run deep-memory search .deep-memory/deep-memory.db "这个项目怎么验证修改？"
```

本地 WebUI：

```bash
uv run deep-memory webui .deep-memory/deep-memory.db --host 127.0.0.1 --port 8765
```

### 中文检索为什么是重点

很多 memory 不是纯英文，也不是纯中文，而是“中文描述 + 英文技术词 + 项目名 + 工具名”的混合文本。

比如：

- 用户偏好：中文为主，技术术语用英文
- 项目约定：所有 agent 配置输出到独立目录
- Hermes Kanban 承载复杂 loop
- MCP adapter 需要显式 JSONL import

所以 deep-memory 现在把中文检索当成一等能力来测。默认路径是 SQLite FTS5 加本地中英文 token fallback，可选 `jieba` backend。后续 vector retrieval 会做，但不会让 base install 一上来就变重。

### 当前评估

这些评估都很小，更像 regression checks，不是夸张 benchmark。

| Evaluation | 当前结果 | 复现方式 |
| --- | --- | --- |
| Chinese retrieval v1 | 默认 local backend 55/55；可选 `jieba` 55/55 | `uv run python evals/chinese_retrieval_eval.py --data evals/data/zh_memory_retrieval.jsonl` |
| Chinese retrieval v2 | 20/20 top-1，MRR 1.0 | `uv run python evals/chinese_retrieval_eval.py --data evals/data/zh_memory_retrieval_v2.jsonl --json` |
| Memory benchmark v0 | no-memory baseline 0/20；deep-memory 默认通常 20/20 | `uv run python benchmarks/memory_benchmark.py` |

### 我最关心的反馈

如果你退后一步看，Agent memory 的关键瓶颈不只是 retrieval，而是治理：什么能记、谁允许记、记多久、怎么纠错、怎么避免跨项目污染。

所以我现在最想收集这些反馈：

- 真实项目里哪些 memory 最有价值？
- 自动写入的边界应该多保守？
- scope 是按 workspace / project / user / tenant 怎么分更合理？
- 中文检索还缺哪些典型失败样本？
- Memory to Skill 应该怎样 review 才安全？

项目还是 alpha。如果你在做 AI Agent、本地工作流、MCP 或中文 coding agent 场景，欢迎试用和提 issue。

GitHub：https://github.com/benbenlijie/deep-memory
中文 README：https://github.com/benbenlijie/deep-memory/blob/main/README.zh-CN.md
快速开始：https://github.com/benbenlijie/deep-memory/blob/main/README.zh-CN.md#快速开始
