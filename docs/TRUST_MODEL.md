# deep-memory Trust Model

如果你退后一步看，cross-agent memory 的核心风险不是“谁能说话”，而是“谁写下来的东西会在未来被别的 agent 当成事实”。这和 prompt injection 是不同攻击面：一次低质量或恶意的记忆写入，可能在之后很多次检索中复利放大。

本模型把 memory source 从普通字符串扩展为可解释的 trust metadata，同时保留旧格式兼容。真正有趣的问题是：source 不只是注释，而是检索、冲突处理和审核流程都能使用的安全边界。

## Threat model boundary

| Threat | Defense status |
|---|---|
| Honest agent writes wrong low-trust content | Full defense |
| Cross-kind low-trust overriding high-trust | Full defense |
| Same-kind low-trust overriding high-trust | Partial mitigation (trust ranking, but coexist) |
| Attacker spoofs trust_level=user | Cannot defend (no auth) |
| Write-order race (low-trust writes first) | Partial mitigation (high-trust ranks higher) |
| Multi-kind content flooding (4 kinds) | Partial mitigation (trust ranking, multiple active) |

Notes:

- deep-memory is a local library with no authentication.
- The trust system defends against honest mistakes, not adversarial attackers.
- The real attack surface is the agent being induced, especially via prompt injection.
- A future trust v2 reputation system can further reduce these edge cases.
- High-security deployments should pair this layer with external audit and manual candidate review.


## Source shape

新格式：

```json
{
  "agent": "hermes",
  "trust_level": "agent-high",
  "origin_type": "auto-extracted"
}
```

字段：

- `agent`: 写入者或导入通道，例如 `human`, `user`, `hermes`, `codex`, `web-import`。
- `trust_level`: 检索和冲突处理使用的信任等级。
- `origin_type`: 这条记忆的来源方式：`explicit`, `auto-extracted`, `imported`。

旧格式仍可读：

```text
codex:s_123
```

旧字符串会在读取时自动解释为：

```json
{
  "agent": "codex:s_123",
  "trust_level": "agent-auto",
  "origin_type": "auto-extracted"
}
```

例外：如果旧字符串显式表现为外部来源，并且 `trust.auto_detect = true`，会自动判定为 `external`，因为它更像网页抓取来源而不是 agent 写入者。当前识别 `http(s)://`、`ftp(s)://`、`mailto:`、IPv4（如 `10.0.0.1:8080`）和方括号 IPv6（如 `[fe80::1]:80`）。裸域名（如 `example.com`）仍保持 `agent-auto`，避免和 agent name 混淆；`file://` 视为本地文件路径，也不自动判定为 external。

数据库仍使用 `source TEXT` 存储，结构化 source 会以 JSON 字符串落库；API 读取时会反序列化为结构化对象，旧字符串保持原样。

## Trust ladder

| trust_level | factor | 自动触发条件 | 手动触发条件 | 推荐使用场景 |
| --- | ---: | --- | --- | --- |
| `user` | 1.0 | `agent` 为 `human` 或 `user` 且 `origin_type=explicit` | `deep-memory trust promote <db> <id> --to user` | 用户直接表达、用户审核确认后的偏好或事实 |
| `verified` | 0.9 | 无默认自动判定 | `deep-memory trust promote <db> <id> --to verified` 或调用方显式传入 | 经测试、人审、权威来源核验后的记忆 |
| `agent-high` | 0.8 | 无默认自动判定 | 可信 agent / 受控 pipeline 显式传入 | 高质量自动写入，例如有策略约束和可审计来源的 agent |
| `agent-auto` | 0.5 | 默认 fallback；旧 plain string source；关闭 auto-detect 后所有未指定 trust 的来源 | 调用方显式传入 | 普通 agent 自动提取，兼容旧写入路径 |
| `external` | 0.5 | `origin_type=imported` 且无 `agent`；source 字符串显式匹配外部 URL / 地址（`http(s)://`、`ftp(s)://`、`mailto:`、IPv4、方括号 IPv6） | 调用方显式传入 | 网页抓取、外部导入、第三方输出；可召回但不应压过高信任记忆 |
| `untrusted` | 0.2 | 无默认自动判定 | 调用方显式传入 | 明确可疑、恶意、隔离区内容；用于保留证据但强降权 |

`external` 与 `agent-auto` 同为 0.5 是有意设计：外部资料不应完全隐形，但仍会在冲突处理里低于 `user` / `verified` / `agent-high`。如果内容被判断为恶意或明显可疑，应显式标记为 `untrusted`。

## 自动判定矩阵

默认配置：

```toml
[tool.deep-memory.trust]
auto_detect = true
```

也可以用环境变量临时覆盖：

```bash
DEEP_MEMORY_TRUST_AUTO_DETECT=false
```

当 auto-detect 开启，且调用方没有显式传入 `trust_level` 时：

| source 输入 | 自动 trust_level | origin_type | 说明 |
| --- | --- | --- | --- |
| `"https://example.com/page"` | `external` | `auto-extracted` | 兼容旧字符串，同时识别网页抓取来源 |
| `"ftp://example.com/archive.tar.gz"` | `external` | `auto-extracted` | 显式 FTP 外部来源 |
| `"mailto:security@example.com"` | `external` | `auto-extracted` | 显式邮件外部来源 |
| `"10.0.0.1:8080/status"` | `external` | `auto-extracted` | IPv4 地址来源 |
| `"[fe80::1]:80/status"` | `external` | `auto-extracted` | 方括号 IPv6 地址来源 |
| `"example.com"` | `agent-auto` | `auto-extracted` | 裸域名可能和 agent name 混淆，不自动判定为 external |
| `"file:///tmp/memory.json"` | `agent-auto` | `auto-extracted` | 本地文件路径，不自动判定为 external |
| `{ "origin_type": "imported" }` | `external` | `imported` | 导入内容无 agent 溯源 |
| `{ "agent": "human", "origin_type": "explicit" }` | `user` | `explicit` | 用户/人类明确输入 |
| `{ "agent": "user", "origin_type": "explicit" }` | `user` | `explicit` | 用户明确输入 |
| `"codex:s_123"` | `agent-auto` | `auto-extracted` | 旧 plain string source，保持向后兼容 |
| `{ "agent": "codex", "origin_type": "auto-extracted" }` | `agent-auto` | `auto-extracted` | 普通 agent 自动提取 |

当 auto-detect 关闭，所有未指定 `trust_level` 的来源都会回到 `agent-auto`。显式传入的 `trust_level` 不受 auto-detect 影响。

## Two-layer trust model

v2 把 trust 从单层 `trust_level -> factor` 升级为两层：

```text
trust_factor = baseline_trust * reputation
```

- `baseline_trust`：写入时由 source identity × origin matrix 决定，表示“这个来源身份在这个来源方式下的默认可信度”。它是相对稳定的 baseline，后续不会因为普通反馈自动改变。
- `reputation`：每条 memory 独立维护的动态信誉，默认 `1.0`，由反馈和时间衰减更新。

baseline matrix：

| source identity \ origin | explicit | auto-extracted | imported | web string |
| --- | ---: | ---: | ---: | ---: |
| user / human | 1.0 | — | — | — |
| trusted agent | 0.85 | 0.65 | — | — |
| known agent | 0.7 | 0.55 | — | — |
| unknown agent | 0.7 | 0.45 | 0.35 | — |
| bulk import without agent | — | — | 0.3 | — |
| external URL/address string | — | — | — | 0.2 |

`agent_registry` 保存 agent 的 known/trusted 状态。首次迁移时默认 trusted agents 为：`claude-code`, `codex`, `hermes`, `opencode`, `openclaw`。新 agent 第一次出现会自动注册为 known，explicit 冷启动 baseline 为 `0.7`。

reputation 规则：

- 写入时 `reputation = 1.0`。
- helpful feedback：`+0.02`。
- not-helpful feedback：`-0.05`。
- clamp：`[0.3, 1.5]`。
- lazy decay on read：按 `reputation_updated_at` 每天 `-0.001`，变化超过 `0.01` 时在 search 返回后写回。

## Retrieval weighting and bucket retrieval

检索时先计算原有 score：

```text
lexical * 0.55 + importance * 0.25 + confidence * 0.15 + decay * 0.05
```

然后乘以两层 trust factor：

```text
final_score = base_score * baseline_trust * reputation
```

默认 search 还使用 bucket retrieval：

1. 先填充 `trust_factor >= 0.7` 的 high-trust pool。
2. 只有 high-trust 结果不足时，才从 fallback pool 补齐。
3. `allow_fallback=False` 时只返回 high-trust pool。

这意味着：

- 高信任记忆永远优先，不会被高 importance/confidence 的 external 抢位。
- 低信任记忆仍可被召回，但只在高信任池不足时补位。
- 旧格式 source 默认按 unknown auto-extracted agent 处理，保持可用但不会拥有高权重。
- `untrusted = 0.2` 主要用于隔离，不应作为普通外部资料的默认等级。

## Contradiction / poisoning defense

写入新记忆时，系统会检查 active 高信任记忆：

- 已有记忆必须是 `active`。
- 已有记忆的 `trust_level` 属于 `user` / `verified` / `agent-high`。
- 新记忆的 trust factor 低于已有记忆。
- 跨 `kind` 时，两者 Jaccard overlap > 0.33。
- 同 `kind` 时，两者 Jaccard overlap > 0.7。

满足这些条件时，新记忆不会直接进入 active 状态，而是标记为：

```text
conflict_status = candidate
supersedes_id = <high-trust-memory-id>
```

`candidate` 记忆默认不参与普通 `search` 结果，等待用户或审核流程确认。这样能防止低信任导入通过高 importance/confidence 覆盖用户确认过的事实。

同 `kind` 分支是一个更保守的 partial mitigation：合法的同类 procedural/semantic 改写很常见，所以阈值高于跨类冲突；只有近乎相同的低信任写入才会被怀疑为覆盖高信任 sibling 的篡改尝试。

## Who may write

当前实现允许所有既有写入路径继续调用 `DeepMemory.add()`，但写入者应尽量提供结构化 source：

- 用户显式输入：`trust_level=user`, `origin_type=explicit`
- 通过测试或人审确认：`trust_level=verified`, `origin_type=explicit/imported`
- 可信 agent 自动提取：`trust_level=agent-high`, `origin_type=auto-extracted`
- 普通 agent 自动提取：`trust_level=agent-auto`, `origin_type=auto-extracted`
- 外部导入：`trust_level=external`, `origin_type=imported`
- 可疑或恶意内容：`trust_level=untrusted`, `origin_type=imported`

没有结构化 source 的旧调用不会失败，会按自动判定矩阵处理。

## Inspection and promotion commands

按 trust 排序查看记忆：

```bash
deep-memory trust list .deep-memory/deep-memory.db
```

输出包含：`id`, `trust`, `factor`, `origin`, `agent`, `status`, `kind`, `content`。

人工 review 后提升 trust：

```bash
deep-memory trust promote .deep-memory/deep-memory.db <record-id> --to verified
deep-memory trust promote .deep-memory/deep-memory.db <record-id> --to user
deep-memory trust promote .deep-memory/deep-memory.db <record-id> --to verified --by reviewer-name --reason "manual review"
```

`promote` 会保留原始 `agent`，只把 trust 提升事实追加到 source metadata：

```json
{
  "agent": "codex",
  "trust_level": "verified",
  "origin_type": "explicit",
  "promoted_by": "reviewer-name",
  "promoted_at": "2026-06-17T15:30:00+00:00"
}
```

旧 source 没有 `promoted_by` / `promoted_at` 时，读取结果为 `None`，不会报错。

## Audit trail

trust 变更写入独立 `trust_audit` 表，而不是复用 kanban `task_events`。原因很简单：memory trust audit 是合规与溯源边界，保留期、查询方式和访问控制都可能不同；任务事件只描述 Kanban 执行过程，两者职责不应混在一起。

表结构：

```sql
CREATE TABLE trust_audit (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    memory_id TEXT NOT NULL,
    action TEXT NOT NULL,
    old_trust TEXT,
    new_trust TEXT,
    old_reputation REAL,
    new_reputation REAL,
    actor TEXT,
    reason TEXT,
    at TEXT NOT NULL
);
```

当前已写入的触发点：

- `promote_trust()`：`action='promote'`，记录 `old_trust`、`new_trust`、`actor`、`reason`、`at`。

预留触发点：

- reputation 更新：`action='feedback-bump'` / `auto-decay`，记录 `old_reputation` / `new_reputation`。
- agent trust 批量治理：`action='agent-bulk-promote'` 等批量动作，每条 memory 记录一行。

查看单条 memory 的 trust 历史：

```bash
deep-memory trust audit .deep-memory/deep-memory.db <record-id>
```

查看最近 N 天全部 trust 变化：

```bash
deep-memory trust audit .deep-memory/deep-memory.db --recent 7
```

## Rollback / cleanup

如果发现 memory poisoning 或错误候选：

1. 用 `deep-memory trust list <db>` 找到低信任、`untrusted` 或 candidate 记录。
2. 如果只是软删除，使用已有 lifecycle/deprecate 路径把记录标记为 `deprecated`。
3. 如果必须彻底移除，使用：

```bash
deep-memory hard-delete <db> <record-id>
```

4. 如果低信任记录应被接受，先 review，再用 `deep-memory trust promote` 提升为 `verified` / `user`。

## Design boundary

这不是完整的安全系统，只是 memory 层的最小防线：

- 它降低低信任内容在检索中的影响。
- 它阻止明显冲突的低信任写入直接进入 active recall。
- 它保留旧数据兼容性。
- 它把自动判定规则和人工提升路径写清楚，减少调用方隐式猜测。

它不替代隐私过滤、权限控制、签名验证或人审流程。真正重要的是：让 source 不再只是字符串，而成为可计算、可审计、可降权的安全边界。
