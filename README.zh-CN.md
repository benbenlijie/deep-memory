# deep-memory

[English](README.md) | [简体中文](README.zh-CN.md)

> 给 AI Agent 一个本地记忆层。看得见记住了什么，决定留下什么。

[![CI](https://github.com/benbenlijie/deep-memory/actions/workflows/ci.yml/badge.svg)](https://github.com/benbenlijie/deep-memory/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-alpha-orange)

Agent 跨会话之后会忘记很多有用的东西。Claude Code 这个会话里刚弄清楚的项目约定，Codex 不知道；Hermes 刚跑通的工作流，OpenCode 下次也未必记得。`deep-memory` 给这些工具一个共享的、可检视的记忆层——项目里的一个 SQLite 文件，没有云端，不抓 transcript，没有隐藏的全局状态。

## 核心特性

- **默认本地优先。** 项目里的 SQLite 文件，可以 `cp`、`scp`、检查、备份，也可以随时删除。
- **跨 Agent。** 通过 MCP、CLI wrapper 或显式 JSONL 导入，支持 Claude Code、Codex、OpenCode、OpenClaw 风格工具、Hermes。
- **可检视。** CLI、Python SDK、本地 WebUI 都能读、改、软删除、导出每一条记录，不只有黑盒 embedding。
- **中文检索优先。** FTS5 加本地中英文 token fallback，可选 `jieba` backend；用仓库内 checked-in 的中文检索 fixture 衡量，而不是文案上写一句就算。
- **记忆治理，不只是存储。** 每条记录都带 `kind`、`importance`、`confidence`、`source`、时间戳、冲突状态、衰减——记忆可以被审计、纠正、过期。
- **从记忆到 skill 的路径。** procedural memory 可以导出为可审查的 skill candidate，不会自动装成行为规则。

<p align="center">
  <img src="docs/assets/deep-memory-architecture.svg" alt="deep-memory architecture" width="920">
</p>

## 快速开始

```bash
git clone https://github.com/benbenlijie/deep-memory.git
cd deep-memory
uv sync --extra dev --extra mcp

uv run deep-memory init .deep-memory/deep-memory.db
uv run deep-memory add .deep-memory/deep-memory.db \
  "项目约定：提交前先运行 uv run pytest -q" \
  --kind procedural \
  --importance 0.8
uv run deep-memory search .deep-memory/deep-memory.db "这个项目怎么验证修改？"
```

如果你是 AI Agent，正在替用户安装或接入这个项目，请看 [`docs/AGENT_INSTALL_GUIDE.zh-CN.md`](docs/AGENT_INSTALL_GUIDE.zh-CN.md)。里面包含 MCP 配置、Codex wrapper 用法、安全写入规则，以及用户允许时给项目点 star 的步骤。

## 接入你的 Agent

优先用 MCP。如果你的 Agent 暂时不好接 MCP，就用 wrapper。无论哪种方式，都指向同一个项目本地数据库：

```text
.deep-memory/deep-memory.db
```

### Claude Code

```bash
claude mcp add deep-memory -- uv --directory /absolute/path/to/deep-memory run deep-memory-mcp
```

在 `CLAUDE.md` 里加一段，让策略显式：

```markdown
Before large tasks, search deep-memory for relevant project conventions.
After verified success, add only durable facts or reusable procedures.
Never store secrets, raw credentials, or temporary issue status.
```

### Hermes

```yaml
mcp_servers:
  deep_memory:
    command: "uv"
    args: ["--directory", "/absolute/path/to/deep-memory", "run", "deep-memory-mcp"]
    timeout: 30
```

连接后通常会出现 `mcp_deep_memory_add`、`mcp_deep_memory_search`、`mcp_deep_memory_stats` 这几个工具。

Hermes 也可以导入显式 facts JSONL：

```bash
cat > /tmp/hermes-session.jsonl <<'JSONL'
{"session_id":"s_demo","facts":[{"content":"用户偏好：中文为主，技术术语用英文","kind":"semantic","importance":0.9}]}
{"session_id":"s_demo","facts":[{"content":"成功流程应该沉淀为可审查 skill candidate","kind":"procedural","confidence":0.8}]}
JSONL

uv run deep-memory hermes-import .deep-memory/deep-memory.db /tmp/hermes-session.jsonl
```

### Codex、OpenCode、OpenClaw 风格工具

在 MCP 接好之前，先用 wrapper。任务开始前查，任务结束后只写经验证的事实：

```bash
MEMORY_DB=.deep-memory/deep-memory.db
uv run deep-memory search "$MEMORY_DB" "这个任务相关的项目约定"
# 把结果作为短的"相关记忆"塞进 Agent prompt
# ...运行 Agent...
uv run deep-memory add "$MEMORY_DB" \
  "工作流：这个仓库 review 前需要运行 uv run pytest -q 和 uv run ruff check ." \
  --kind procedural \
  --importance 0.8 \
  --source codex:manual
```

完整的接入面——集成点、读写路径、权限、风险——见 [`docs/ADAPTERS.md`](docs/ADAPTERS.md)；按 Agent 分的命令清单见 [`docs/AGENT_QUICKSTART_MATRIX.md`](docs/AGENT_QUICKSTART_MATRIX.md)。

## 查看和管理记忆

```bash
uv run deep-memory webui .deep-memory/deep-memory.db --host 127.0.0.1 --port 8765
# 打开 http://127.0.0.1:8765
```

WebUI 可以查看、搜索、编辑、软删除记录，默认只绑定 `127.0.0.1`。

导出与审计：

```bash
uv run deep-memory export .deep-memory/deep-memory.db                      # 只导出 active records
uv run deep-memory export .deep-memory/deep-memory.db --include-deprecated # 审计 / 备份
uv run deep-memory hard-delete .deep-memory/deep-memory.db <memory-id>     # 物理删除单条记录
```

## Python API

```python
from deep_memory import DeepMemory

mem = DeepMemory(".deep-memory/deep-memory.db")
mem.add("用户偏好：中文为主，技术术语用英文", kind="semantic", importance=0.9)
mem.add("项目约定：使用 uv 运行测试", kind="procedural", importance=0.8)

for result in mem.search("这个仓库怎么跑测试？", limit=3):
    print(result.score, result.record.kind, result.record.content)
```

## 现在能用什么

| 能力 | 状态 | 说明 |
| --- | --- | --- |
| 本地持久化 | 已实现 | 用户或项目自己控制的 SQLite DB。 |
| 搜索 | 已实现 | FTS5，加上本地中英文 token fallback。 |
| 可选中文分词 | 已实现 | 通过 `uv sync --extra retrieval` 使用 `jieba` backend。 |
| 记录元数据 | 已实现 | `kind`、`importance`、`confidence`、`source`、时间戳、冲突状态。 |
| 冲突处理 | 已实现 | candidate、resolved、superseded、deprecated。 |
| Python SDK + CLI | 已实现 | `add`、`search`、`stats`、`conflicts`、`resolve-conflict`、`export`、`hard-delete`、`hermes-import`、`webui`。 |
| MCP server | 已实现 | stdio tools：`add`、`search`、`stats`、冲突相关 helper。 |
| Hermes import | 已实现 | 显式 session facts JSONL 导入为 `deep-memory` records。 |
| 本地 WebUI MVP | 已实现 | 查看、搜索、编辑、软删除 memory records。 |
| Memory to skill candidate | 已实现 | 把 procedural memory 导出为可审查 skill markdown；不会自动安装。 |
| Codex wrapper MVP | 已实现 | `deep-memory codex-run` 注入有界上下文，仅在子进程成功退出后导入显式 `--facts-out` JSONL。 |
| 各 Agent 的 native adapter | 设计 / 原型中 | 先用 MCP 或 wrapper；见 `docs/ADAPTERS.md`。 |
| Vector retrieval / hosted sync | Roadmap | 等评估和隐私边界更扎实后再做。 |

## 评估结果

这些 eval 都很小，是防止当前检索能力倒退的回归测试，不是"记忆问题已经解决"的证明。

| Evaluation | 当前 checked-in 结果 | 复现命令 |
| --- | --- | --- |
| Chinese retrieval v1 | 默认本地 backend 55/55；可选 `jieba` 55/55；早期纯 SQLite FTS baseline 为 24/55 | `uv run python evals/chinese_retrieval_eval.py --data evals/data/zh_memory_retrieval.jsonl` |
| Chinese retrieval v2 | 20 个更难的 multi-memory distractor cases；当前本地 baseline top-1 accuracy 1.0、MRR 1.0 | `uv run python evals/chinese_retrieval_eval.py --data evals/data/zh_memory_retrieval_v2.jsonl --json` |
| Memory benchmark v0 | 20 个 bilingual tasks；no-memory baseline 0/20；测试要求至少 16/20，默认 retrieval limit 通常 20/20 | `uv run python benchmarks/memory_benchmark.py` |
| Test suite | pytest + CI 覆盖 | `uv run pytest -q` |

细节见 [`docs/CHINESE_RETRIEVAL_EVAL.md`](docs/CHINESE_RETRIEVAL_EVAL.md) 和 [`docs/MEMORY_BENCHMARK.md`](docs/MEMORY_BENCHMARK.md)。

## 架构

```text
agent or developer
  -> explicit facts / procedures / project conventions
  -> DeepMemory SDK, CLI, MCP, or adapter
  -> local SQLite + FTS5
  -> ranked recall for future agent context
  -> WebUI, export, evals, and skill candidates
```

故意选 SQLite。它方便安装、方便检查、方便测试、方便备份，将来也方便替换。

继续阅读：

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
- [`docs/SAFETY_AND_PRIVACY.md`](docs/SAFETY_AND_PRIVACY.md)
- [`docs/MEMORY_POLICY.md`](docs/MEMORY_POLICY.md)
- [`docs/MCP_INTEROPERABILITY.md`](docs/MCP_INTEROPERABILITY.md)
- [`docs/ADAPTERS.md`](docs/ADAPTERS.md)
- [`docs/ROADMAP.md`](docs/ROADMAP.md)

## 安全边界

持久记忆会影响 Agent 之后的行为，所以默认边界要窄：

- 只存显式的 durable facts，不存 raw transcripts；
- 默认使用本地 SQLite；
- 每次只取回少量相关上下文；
- 不保存 secrets、private keys、auth cookies、raw credentials、临时任务状态；
- procedural memory 要等测试、review 或用户确认之后再写入；
- Memory to Skill 只导出候选文件，不会自动装成行为规则。

做自动写入或团队共享记忆之前，先看 [`docs/MEMORY_POLICY.md`](docs/MEMORY_POLICY.md) 了解 allow / deny / requires-confirmation 边界，再看 [`docs/SAFETY_AND_PRIVACY.md`](docs/SAFETY_AND_PRIVACY.md)。

## 贡献


当前这仍然应被看作 controlled preview，而不是 broad launch。下面的公开 backlog 只收敛到小而可验证的贡献，以及保持 launch gate 诚实的剩余 blocker。

- `good first issue`：小型 fixture、文档修复、CLI 输出打磨、可复现 failure case；
- `adapter`：Claude Code、Codex、OpenCode、OpenClaw 风格工具、Hermes 的 smoke transcript 与 wrapper/MCP 兼容说明；
- `eval`：中文检索、隐私边界、memory/no-memory、Memory × Skill 回归用例；
- `governance`：写入策略、用户同意、导出/删除、冲突生命周期检查；
- `docs`：quickstart、troubleshooting、glossary、贡献路径。

开 PR 前建议先读 [`CONTRIBUTING.md`](CONTRIBUTING.md)、[`docs/COMMUNITY.md`](docs/COMMUNITY.md) 和 [`docs/NEXT_PHASE_BACKLOG.md`](docs/NEXT_PHASE_BACKLOG.md)。

## License

MIT
