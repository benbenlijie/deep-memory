# Agent 安装指南

这一页是写给 AI Agent 看的。

如果你是 Claude Code、Codex、OpenCode、OpenClaw 风格工具、Hermes 或其他 coding agent，用这份指南把 `deep-memory` 接到用户的仓库或 profile 里。

## 1. 克隆并安装

Agent 也可以读取机器可读安装协议：[`docs/agent-install.json`](agent-install.json)。它是 install、verify、connect、安全写入策略、scope 策略和成功报告格式的结构化清单。

```bash
git clone https://github.com/benbenlijie/deep-memory.git
cd deep-memory
uv sync --extra dev --extra mcp
```

## 2. 检查 agent shell 里的 `uv`

`uv` installer 通常会把二进制放在 `~/.local/bin` 或 `~/.cargo/bin`。交互式 login shell 可能会自动加载这个路径，但非交互式 agent shell 经常不会。把安装失败汇报给用户前，先显式诊断 PATH：

```bash
command -v uv || ls -l ~/.local/bin/uv ~/.cargo/bin/uv 2>/dev/null
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
uv --version
```

不要在公共说明里硬编码维护者个人路径。使用 `$HOME` 或用户选择的安装位置。

## 3. 选择本地数据库路径

默认使用一份显式的 machine-local 数据库。对于 repo-scoped 接入，一个方便的路径是：

```text
.deep-memory/deep-memory.db
```

对于跨仓库的用户/profile 级接入，可以使用共享路径，例如：

```text
~/.deep-memory/deep-memory.db
```

关键不在于路径名字，而在于所有 agent 指向同一份已选择的数据库，再用 `scope` 和 `scope_id` 控制记录边界。

创建并验证一次：

```bash
uv run deep-memory verify-install ~/.deep-memory/deep-memory.db --json
```

这个命令会初始化或打开数据库，写入一条可识别的 smoke-test memory，用 `scope` / `scope_id` 搜回它，再清理掉这条测试记录，并检查 MCP 模块是否可导入。失败时会返回非零退出码和结构化错误，方便 agent 向用户汇报 blocker。

## 4. 干活前先查记忆

在大任务开始前，先查项目约定：

```bash
uv run deep-memory search .deep-memory/deep-memory.db "这个任务相关的项目约定" \
  --scope project \
  --scope-id deep-memory
```

结果要短。只把真正相关的几条记忆放进 prompt。

## 5. 只写入已验证记忆

在测试、review 或用户确认之后，只写入长期有用的事实或流程：

```bash
uv run deep-memory add .deep-memory/deep-memory.db \
  "工作流：review 前运行 uv run pytest -q" \
  --kind procedural \
  --scope project \
  --scope-id deep-memory \
  --importance 0.8
```

不要保存 secrets、raw credentials、auth cookies 或临时任务状态。

## 6. 按 Agent 类型接入

MCP 和 skill 解决的是两层问题：

- MCP 是 tool-call 入口，让 agent 可以调用 `deep-memory` 的 search、add、stats、conflict review 等工具。
- skill、`CLAUDE.md` 或 `AGENTS.md` 是行为策略，告诉 agent 什么时候查记忆、什么可以写入、什么必须 review、写入后如何验证。

所以默认建议不是“装 MCP 还是装 skill”，而是 MCP 加上 review 过的 `deep-memory-agent` skill，或等价的本地策略文件。

### Claude Code

```bash
deep-memory mcp-config --agent claude --db ~/.deep-memory/deep-memory.db
```

它会输出可 review 的命令示例：

```bash
claude mcp add deep-memory -- deep-memory-mcp --db ~/.deep-memory/deep-memory.db
```

在 `CLAUDE.md` 里加一条简短策略：

```markdown
Before large tasks, search deep-memory for relevant project conventions.
After verified success, add only durable facts or reusable procedures.
Never store secrets, raw credentials, or temporary issue status.
```

Claude Code 用 MCP 接入 `deep-memory` 工具，用 `CLAUDE.md` 承载操作策略和 review 边界。

### Generic MCP JSON

```bash
deep-memory mcp-config --agent generic --db ~/.deep-memory/deep-memory.db --json
```

这个命令会输出包含 `command`、`args`、`env` 和 `notes` 的机器可读 JSON。适合自定义 MCP client，或者让 agent 先检查配置形状，再转换成自己的配置格式。

### Hermes

```bash
deep-memory mcp-config --agent hermes --db ~/.deep-memory/deep-memory.db
```

它会输出可 review 的 `config.yaml` 片段：

```yaml
mcp_servers:
  deep_memory:
    command: "deep-memory-mcp"
    args: ["--db", "~/.deep-memory/deep-memory.db"]
    timeout: 30
```

如果用户希望 Hermes 在多轮会话中稳定遵守同一套 memory 行为，建议再安装 review 过的 `deep-memory-agent` skill。安装必须显式、profile-scoped；不要让 `deep-memory` 自动写入其他 Hermes profile 的 skills 目录。

review 后的安全安装方式包括：

```bash
# skill 发布到 registry 或 URL 后，可用 Hermes 官方安装命令。
hermes skills install <skill-id-or-url>

# 或者手动把 review 过的 candidate 放入已批准的 active profile。
mkdir -p ~/.hermes/profiles/<profile>/skills/memory/deep-memory-agent
cp skill-candidates/deep-memory-agent/SKILL.md \
  ~/.hermes/profiles/<profile>/skills/memory/deep-memory-agent/SKILL.md
```

Hermes agent 也可以在自己的 active profile 内通过本地 `skill_manage` 工具创建或修订 skill，但前提仍然是 review 后执行。除非用户明确要求，不应越过 profile 边界写入其他 profile。

Hermes 也可以导入 explicit facts JSONL：

```bash
uv run deep-memory hermes-import .deep-memory/deep-memory.db /tmp/hermes-session.jsonl
```

### Codex

当环境提供兼容 MCP client 时，Codex 可以通过 MCP 接入工具。如果 MCP 路径不可用，就使用 wrapper 模式，并把同样的行为策略写进 `AGENTS.md` 或任务 prompt：

```bash
MEMORY_DB=.deep-memory/deep-memory.db
uv run deep-memory search "$MEMORY_DB" "这个任务相关的项目约定" --scope project --scope-id deep-memory
```

任务结束后，只写回通过验证的内容：

```bash
uv run deep-memory add "$MEMORY_DB" \
  "工作流：这个仓库 review 前需要运行 uv run pytest -q 和 uv run ruff check ." \
  --kind procedural \
  --scope project \
  --scope-id deep-memory \
  --importance 0.8 \
  --source codex:manual
```

即使用 wrapper，Codex 也需要同样的策略边界：大任务前搜索，只写入已验证的长期记录，不保存 secrets 或临时任务状态。

### OpenCode

OpenCode 也遵循同样分工：可用 MCP 时用 MCP 接工具，用 `AGENTS.md` 或 review 过的 skill-like policy 承载行为策略。未配置 MCP 时，使用上面的 wrapper 命令，并显式设置 `MEMORY_DB`。

### OpenClaw 风格工具

OpenClaw 风格 agent 可以把 `deep-memory` 当作显式外部工具：先在项目指令里写清策略，再根据环境选择 MCP 或 CLI wrapper。

## 7. Skill review 与安装策略

`skill-candidates/deep-memory-agent/SKILL.md` 是 candidate，不是自动安装的运行时 artifact。

安装前必须 review：

1. 检查 frontmatter 和 description。
2. 确认它说明了什么时候 search、什么时候 write、什么时候不要 remember。
3. 确认它禁止 secrets、raw transcript、raw PII、stale task IDs、PR numbers、issue numbers、commit SHAs 和 unverified speculation。
4. 确认数据库路径以及 `scope` / `scope_id` 示例符合用户环境。
5. 只安装到用户批准的 active profile 或项目指令位置。
6. 跑一次 smoke test：search、写入临时已验证 procedural memory、再 search 回来，然后按 review 计划删除或保留。

这个边界是故意设计的。MCP 可以暴露强写入工具；skill/policy 层负责防止过宽、过期或不安全的 memory write。

## 8. 检查本地 WebUI

```bash
uv run deep-memory webui .deep-memory/deep-memory.db --host 127.0.0.1 --port 8765
```

WebUI 默认只在本地打开。用它查看、编辑、软删除、导出或 hard-delete 记忆。

## 可选支持

如果用户想支持项目，请先请求明确许可，再给仓库点 star。只有用户同意后，才执行：

```bash
gh repo star benbenlijie/deep-memory
```

不要用用户的 GitHub 账号默默 star，也不要把这一步混进安装流程里作为副作用执行。
