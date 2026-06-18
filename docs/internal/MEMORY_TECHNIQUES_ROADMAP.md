# 记忆技术 × deep-memory 长期优化规划

> 将人类记忆技术的信息论本质（而非神经科学隐喻）落地到 deep-memory 的工程路线图。
>
> 状态：规划草案 | 创建：2026-06-17 | 维护：deep-memory team

---

## 目录

1. [核心洞察：记忆技术的五个信息论本质](#1-核心洞察)
2. [deep-memory 现状诊断](#2-现状诊断)
3. [与 AI 记忆 SOTA 的差距分析](#3-sota-差距)
4. [长期规划：Phase 0 → Phase 4](#4-长期规划)
5. [优先级矩阵与里程碑](#5-优先级矩阵)
6. [评估体系](#6-评估体系)
7. [非目标与边界](#7-非目标)

---

## 1. 核心洞察

### 记忆技术不是"技巧"，而是信息论规律

记忆宫殿、PAO、间隔重复——这些技术之所以有效，不是因为模拟了大脑结构，而是利用了**信息存储和检索的通用规律**。这些规律适用于任何信息系统，包括 AI 记忆——但必须以信息论形式落地，而非神经科学隐喻。

### 五个本质原理

| # | 原理 | 一句话 | 人类技术实例 | 神经科学基础 |
|---|------|--------|-------------|-------------|
| **P1** | **编码丰富度** | 存的时候绑定的关联维度越多，检索越容易命中 | 记忆宫殿（空间+场景+动作）、Major System（视觉+言语双编码） | Dual Coding Theory (Paivio 1971); 海马体-新皮层连接组重组 (Dresler 2017) |
| **P2** | **结构化脚手架** | 预建独立的寻址层，把 O(n) 检索变成 O(1) 定位 | 记忆宫殿的 100+ 空间位置、Peg System 的数字锚点 | 认知地图理论 (O'Keefe); CA3 自联想网络 |
| **P3** | **压缩** | 重新编码成更紧凑的单元，不丢信息但减少 chunk 数 | PAO（6位数字→1个场景）、Chain/Story（孤立项→因果链） | Cowan 容量限制 ~4 chunks; 递归压缩 (Planton 2020) |
| **P4** | **检索即编码** | 每次检索本身就是一次再编码，强化记忆痕迹 | 间隔重复（SM-2, FSRS）、主动回忆（测试效应） | 重巩固 (reconsolidation); 测试效应 g=0.50 (Rowland 2014) |
| **P5** | **离线巩固** | 快速写入 + 慢速重组，从碎片情景记忆提炼为语义知识 | 睡眠巩固、NREM/REM 循环 | 系统巩固 (Wang & Morris 2017); 互补学习系统 (McClelland) |

### 关键证据

- **记忆运动员的脑不是天生不同**：Dresler et al. (2017, *Neuron*) — 记忆运动员的工作记忆容量与常人无异，优势完全来自策略。训练 6 周后普通人的脑网络**收敛到运动员模式**，4 个月后仍保持。
- **测试效应是最强的编码事件**：Roediger & Karpicke (2006) — 测试组一周后回忆 61%，重读组仅 40%。但学生**不知道**测试更有效——元认知盲区。
- **AI 中的空间隐喻没有计算价值**：MemPalace 批判性分析 (2026) — "Wing→Room→Drawer" 层次结构有用，但"空间宫殿"隐喻本身不产生额外检索价值。**结构有用，隐喻没用。**

---

## 2. 现状诊断

### deep-memory 的记忆模型

```
写入: content (文本) + kind + importance + confidence + source
存储: SQLite 扁平表 + FTS5 虚拟表
检索: BM25 词法匹配 + 重要性/置信度/衰减加权打分
生命周期: candidate → active → superseded/deprecated
遗忘: exp(-age / (1 + 30 × importance))  # 被动指数衰减
```

### 原理覆盖度评估

| 原理 | 覆盖度 | 现状 | 差距 |
|------|--------|------|------|
| **P1 编码丰富度** | 🔴 20% | 仅存 `content` 文本 + 元数据标签 | **严重缺失**。无上下文绑定、无关联编码、无检索线索预存。记忆是"裸文本"，检索路径单一 |
| **P2 结构化脚手架** | 🔴 10% | 扁平表 + scope 分区 | **缺失**。无图结构、无层次索引。检索是全表 FTS5——O(n) 扫描 |
| **P3 压缩** | 🔴 0% | 无 | **完全缺失**。记忆从不被合并、压缩、重组。1000 条相似记忆 = 1000 条独立记录 |
| **P4 检索即编码** | 🔴 0% | 搜索是只读操作 | **完全缺失**。检索不改变记忆。无间隔重复、无访问追踪、无重巩固 |
| **P5 离线巩固** | 🟡 15% | 仅有遗忘衰减 + 冲突生命周期 | **几乎缺失**。只有被动衰减，无主动巩固。无情景→语义转换 |

### 已借用的认知科学原理 ✅

- 记忆类型分类（working / episodic / semantic / procedural）
- 艾宾浩斯遗忘曲线（简化版）
- 重要性加权

---

## 3. SOTA 差距

### AI 记忆 SOTA 的三个层次

| 层次 | 代表项目 | 特征 | deep-memory 对标 |
|------|---------|------|-----------------|
| **L1 检索系统** | Pinecone, Chroma, 朴素 RAG | 找文档，不是记忆。无状态、无时间、无冲突 | deep-memory 已超越此层（有生命周期+冲突+衰减） |
| **L2 记忆系统** | Mem0, A-MEM, Graphiti, Zep | 提取+存储+检索事实。有冲突处理。 | deep-memory 处于此层（有冲突+提取+技能导出） |
| **L3 认知架构** | zenbrain, SCM, SleepGate, Auto-Dreamer | 模拟认知过程：遗忘曲线、巩固、编码特异性 | **deep-memory 目标**：选择性达到此层 |

### 关键 SOTA 教训

1. **"RAG is not memory"**（三篇独立分析收敛）— 向量检索 ≠ 记忆。deep-memory 用 FTS5 反而更诚实。
2. **MemPalace 的空间隐喻没有计算价值** — 性能来自元数据过滤，不是"空间导航"。**不要在 AI 里复制神经隐喻。**
3. **A-MEM 的 Zettelkasten 链接是有效信息论机制** — 原子笔记 + 显式关联 = 更多检索路径。值得借鉴。
4. **FSRS 比 SM-2 好 30%** — 学习型遗忘参数优于固定启发式。
5. **SleepGate/SCM/Auto-Dreamer 的"巩固"本质是批量合并+压缩** — 不需要睡眠隐喻。

### deep-memory 不应做的事

- ❌ 引入向量数据库作为核心（roadmap 已标注"later, if justified"）
- ❌ 复制神经科学隐喻（"海马体模块""NREM 阶段"）
- ❌ 试图在 AI 中实现"真正的"记忆宫殿
- ❌ 牺牲可检查性来换取黑盒智能

---

## 4. 长期规划

### 总体路线

```
Phase 0: 数据模型基础       ← 让记忆"可连接、可追踪、可上下文化"
    ↓
Phase 1: 核心记忆原理       ← P1+P2+P4+P5 的最小可用实现
    ↓
Phase 2: 高级编码           ← P1 的深化 + P3 压缩
    ↓
Phase 3: 认知记忆           ← P4 完整实现 + 元记忆
    ↓
Phase 4: 生态集成           ← MCP/Adapter/WebUI 全面适配
```

---

### Phase 0 — 数据模型基础

> **目标**：为所有后续 Phase 铺设数据层。不加功能，只加结构。

| ID | 任务 | 改动 | 对应原理 |
|----|------|------|---------|
| 0.1 | **memory_links 关联表** | 新增表：`(source_id, target_id, relation_type, weight, created_at)`。relation_type ∈ {supports, contradicts, elaborates, related_to, derived_from} | P1 编码丰富度 + P2 脚手架 |
| 0.2 | **访问追踪字段** | memories 表新增 `access_count INT DEFAULT 0`, `last_accessed_at TEXT`, `last_access_query TEXT` | P4 检索即编码 |
| 0.3 | **编码上下文字段** | memories 表新增 `encoding_context TEXT`（JSON：`{task, files, session_topic, related_queries}`） | P1 编码丰富度 |
| 0.4 | **巩固状态字段** | memories 表新增 `consolidation_level INT DEFAULT 0`（0=原始, 1=合并, 2=抽象, 3=核心知识） | P3 压缩 + P5 巩固 |
| 0.5 | **迁移脚本 + 向后兼容** | ALTER TABLE 增量迁移；旧数据 consolidation_level=0, access_count=0 | — |

**验收标准**：
- [ ] 所有新字段在旧数据库上迁移成功，数据无丢失
- [ ] `memory_links` 表 CRUD 操作通过单元测试
- [ ] `lsp_diagnostics` / `pytest -q` 全绿
- [ ] 现有 eval（中文检索 v1/v2, memory benchmark）不退化

**依赖**：无
**预计规模**：~500 行代码 + 测试

---

### Phase 1 — 核心记忆原理

> **目标**：实现 P1（关联）+ P2（图检索扩展）+ P4（访问重巩固）+ P5（批量巩固）的最小可用版本。

#### 1.1 记忆关联图（P1 + P2）

**原理**：给记忆建立显式关联边，让检索沿图遍历而非全表扫描。

**功能**：
- `link(memory_id_a, memory_id_b, relation_type, weight)` — 显式创建关联
- `auto_link(memory_id)` — 写入时自动检测关联候选（基于 token 重叠 + kind 一致性），创建 `related_to` 边
- 检索扩展：FTS5 命中后，沿 `memory_links` 扩展 1-2 跳，提升召回

**检索流程变更**：
```
当前: query → FTS5 BM25 → 打分排序 → 返回 top-N
新增: query → FTS5 BM25 → top-K 候选 → 沿图扩展 1-2 跳 → 去重重排 → 返回 top-N
```

**实现要点**：
- 图扩展用 SQLite 递归 CTE（`WITH RECURSIVE`），不需要图数据库
- 扩展结果打分：原始命中分 × 0.7 + 关联传播分 × 0.3
- 只扩展 `relation_type` 为 `supports`/`elaborates`/`related_to` 的边（不扩展 `contradicts`）

**验收标准**：
- [ ] 中文检索 v2 从 20/20 → 维持 20/20，且对"需要关联推理"的新测试用例提升 ≥30%
- [ ] 图扩展的延迟 < 10ms（1000 条记忆规模）
- [ ] `memory_links` 表可通过 CLI/WebUI 查看和管理

#### 1.2 访问重巩固衰减（P4）

**原理**：被检索到的记忆应该被强化（模拟重巩固），未被检索的更快衰减。

**衰减公式变更**：
```python
# 当前
decay = exp(-age_days / (1 + 30 * importance))

# 新增访问因子
access_boost = 1 + log(1 + access_count) * 0.15  # 访问越多，half_life 越长
half_life = (1 + 30 * importance) * access_boost
decay = exp(-age_days / half_life)
```

**检索时副作用**：
- 每次搜索命中的记忆：`access_count += 1`, `last_accessed_at = now`, `last_access_query = query`
- 这个副作用是**可选的**（`track_access=True` 参数），保持向后兼容

**验收标准**：
- [ ] 被检索 10 次的记忆，衰减速度比新记忆慢 ≥2x
- [ ] 访问追踪可关闭（`track_access=False`），行为与旧版一致
- [ ] 现有 eval 不退化

#### 1.3 批量巩固命令（P5）

**原理**：编码和巩固分离——快速写入 + 慢速重组。

**功能**：
```bash
deep-memory consolidate <db> --scope project --kind semantic --dry-run
```
- 输入：一组同 scope/kind 的活跃记忆
- 过程：LLM（可选）或规则引擎合并相似记忆 → 生成更高层抽象
- 输出：新记忆 `supersedes` 旧的（利用现有冲突生命周期）
- `consolidation_level` 标记：原始(0) → 合并(1) → 抽象(2) → 核心知识(3)

**巩固策略（分阶段实现）**：
1. **v1 规则巩固**（不需要 LLM）：
   - 完全重复 → 保留 importance 最高的
   - 高 token 重叠（>80%）→ 合并内容，importance 取 max
   - 逻辑矛盾 → 标记 `candidate` 冲突
2. **v2 LLM 巩固**（可选）：
   - 调用 LLM 合并语义相似的记忆
   - 生成抽象总结（从 episodic → semantic）
   - 识别隐含关联并创建 `memory_links`

**验收标准**：
- [ ] `consolidate --dry-run` 输出合并计划，不修改数据
- [ ] 合并后旧记忆变为 `superseded`，新记忆携带 `supersedes_id` 链
- [ ] 合并后的记忆检索不退化（eval 回归通过）
- [ ] WebUI 可可视化巩固前后的记忆变化

**依赖**：Phase 0 全部完成
**预计规模**：~2000 行代码 + 测试 + eval

---

### Phase 2 — 高级编码

> **目标**：深化 P1（编码上下文）+ 实现 P3（压缩/chunking）+ 升级冲突检测（模式分离）。

#### 2.1 编码上下文检索（P1 深化）

**原理**：编码特异性（Tulving）——检索成功的前提是编码上下文与检索上下文匹配。

**功能**：
- 写入时：调用方可传 `encoding_context={"task": "...", "files": [...], "session_topic": "..."}`
- 检索时：query 与 `encoding_context` 做轻量匹配（token overlap on context fields），作为额外打分信号
- 打分权重调整：`lexical × 0.45 + importance × 0.20 + context_match × 0.20 + confidence × 0.10 + decay × 0.05`

**验收标准**：
- [ ] 带 `encoding_context` 的记忆，在"上下文匹配"查询中排名提升
- [ ] 不带 context 的旧记忆行为不变
- [ ] 新 eval：上下文匹配准确率 > 70%

#### 2.2 记忆压缩与 Chunking（P3）

**原理**：把零散记忆重组为更紧凑的知识单元。

**功能**：
- `chunk(memory_ids, chunk_title)` — 将多条记忆合并为一个"chunk 记忆"，原记忆变为 `superseded`
- Chunk 记忆的 `content` 是压缩摘要，`encoding_context` 保留原始 ID 列表
- 检索时：chunk 记忆的 `consolidation_level=2`，打分加权更高

**与 1.3 巩固的区别**：
- 巩固是**自动批量**合并相似记忆
- Chunking 是**用户/agent 显式**组织记忆为知识单元

**验收标准**：
- [ ] 10 条零散记忆可 chunk 为 1 条摘要记忆
- [ ] Chunk 记忆检索时能"展开"显示原始记忆
- [ ] WebUI 支持 chunk 可视化

#### 2.3 模式分离升级（冲突检测增强）

**原理**：模式分离（DG）——相似但不相同的记忆应该被区分。

**当前问题**：`conflict_candidates()` 只看 token 重叠，无法区分"补充信息"和"信息矛盾"。

**升级方案**：
- 冲突检测两阶段：
  1. **候选发现**：token 重叠 > 60% → 候选对
  2. **矛盾判定**：对候选对调用轻量规则（或可选 LLM）判定是 `supports` / `contradicts` / `elaborates`
- 自动创建 `memory_links` 边，relation_type 由判定结果决定

**验收标准**：
- [ ] 对"用户喜欢简洁回答" vs "用户喜欢详细回答"能标记为 `contradicts`
- [ ] 对"用户喜欢简洁回答" vs "用户偏好简短输出"能标记为 `supports`
- [ ] 误报率 < 15%

**依赖**：Phase 1.1（memory_links）完成
**预计规模**：~1500 行代码 + eval 扩展

---

### Phase 3 — 认知记忆

> **目标**：完整实现 P4（间隔重复）+ 元记忆（知道"自己不知道什么"）。

#### 3.1 间隔重复复习队列（P4 完整）

**原理**：FSRS 启发的稳定性/可检索性双参数模型。

**注意**：AI 记忆和人类记忆有根本差异——AI 不"遗忘"，它只是"检索不到"。间隔重复在 AI 中的真正含义是：**定期把重要记忆重新注入 agent 上下文窗口**，而非"防止遗忘"。

**功能**：
- 每条记忆维护 `stability`（存储强度）和 `retrievability`（可检索性）
- `retrievability(t) = (1 + FACTOR × t / stability) ^ DECAY`（FSRS 公式）
- 新命令：`deep-memory review-queue <db>` — 返回 `retrievability < 0.85` 的记忆列表
- MCP/Adapter 集成：agent 启动时自动拉取"待复习"记忆注入上下文

**与 1.2 访问追踪的关系**：
- 1.2 是被动追踪（检索时记录）
- 3.1 是主动调度（预测哪些记忆需要重新曝光）

**验收标准**：
- [ ] `review-queue` 在 1000 条记忆上 < 50ms
- [ ] 重要且长期未访问的记忆出现在队列顶部
- [ ] 可与 MCP server 集成，agent 启动时自动获取

#### 3.2 元记忆与覆盖度评估

**原理**：人类知道"自己不知道什么"（metamemory）。AI 记忆系统普遍缺失。

**功能**：
- `coverage_map(scope, domain)` — 返回某领域/scope 的记忆覆盖度评估
- 基于 `kind`/`consolidation_level`/`access_count` 分布计算覆盖度分数
- 检索结果附带置信度："我找到了 3 条相关记忆，但这个领域整体覆盖度只有 40%"
- 覆盖度低时主动建议 agent "你可能需要在这个领域记录更多"

**实现**：
- 维护 `domain_index`（从记忆内容提取领域标签）
- 按 domain 聚合统计：记忆数量、consolidation_level 分布、最后更新时间
- 输出覆盖度热图（WebUI 可视化）

**验收标准**：
- [ ] `coverage_map` 能识别"空领域"和"饱和领域"
- [ ] 检索结果附带覆盖度信号
- [ ] WebUI 展示覆盖度热图

**依赖**：Phase 1 + Phase 2 完成
**预计规模**：~2000 行代码 + eval + WebUI 扩展

---

### Phase 4 — 生态集成

> **目标**：把新能力通过 MCP/Adapter/WebUI 暴露给所有 agent。

#### 4.1 MCP 工具扩展

新增 MCP 工具：
- `deep_memory_link` — 创建记忆关联
- `deep_memory_consolidate` — 触发巩固
- `deep_memory_review_queue` — 获取复习队列
- `deep_memory_coverage` — 查询覆盖度

#### 4.2 WebUI 记忆图可视化

- 力导向图展示 `memory_links` 关联网络
- 巩固前后的 diff 视图
- 覆盖度热图面板
- 访问频率/衰减曲线图表

#### 4.3 Adapter 更新

- 所有 adapter（Hermes, Codex, Claude Code, OpenCode）支持 encoding_context 传入
- Agent 安装指南更新：推荐"搜索前注入复习队列"工作流

**验收标准**：
- [ ] MCP 新工具通过所有 agent 的 smoke test
- [ ] WebUI 图可视化在 500 节点规模下流畅渲染
- [ ] 至少 2 个 adapter 实测 encoding_context 传递

**依赖**：Phase 1-3 完成
**预计规模**：~1500 行代码 + 文档

---

## 5. 优先级矩阵

### 价值 × 投入矩阵

| 任务 | 价值 | 投入 | 比率 | 优先级 |
|------|------|------|------|--------|
| **1.1 记忆关联图** | 🔴 高 | 🟡 中 | **★★★★★** | **P0 — 核心差距** |
| **1.2 访问重巩固** | 🔴 高 | 🟢 低 | **★★★★★** | **P0 — 最小改动最大效果** |
| **1.3 批量巩固** | 🔴 高 | 🟡 中 | **★★★★☆** | **P0 — 记忆从碎片变知识** |
| **2.1 编码上下文** | 🟡 中 | 🟡 中 | **★★★☆☆** | P1 |
| **2.3 模式分离升级** | 🟡 中 | 🟡 中 | **★★★☆☆** | P1 |
| **2.2 显式 Chunking** | 🟡 中 | 🟡 中 | **★★☆☆☆** | P2 |
| **3.1 间隔重复** | 🟡 中 | 🔴 高 | **★★☆☆☆** | P2 |
| **3.2 元记忆** | 🟢 低 | 🔴 高 | **★☆☆☆☆** | P3 |

### 建议里程碑

| 里程碑 | 内容 | 预计时间 | 核心交付物 |
|--------|------|---------|-----------|
| **M1: 可连接的记忆** | Phase 0 + 1.1 + 1.2 | 2-3 周 | 记忆不再孤立，检索沿图扩展 |
| **M2: 自我演化的记忆** | Phase 1.3 + Phase 2.1 | 2-3 周 | 记忆可批量巩固，编码带上下文 |
| **M3: 知识压缩** | Phase 2.2 + 2.3 | 2-3 周 | 记忆可 chunk/压缩，冲突智能检测 |
| **M4: 认知级记忆** | Phase 3 | 3-4 周 | 间隔重复 + 覆盖度评估 |
| **M5: 生态就绪** | Phase 4 | 2 周 | MCP/WebUI/Adapter 全面适配 |

---

## 6. 评估体系

### 新增 Eval 维度

| Eval | 衡量什么 | 目标 |
|------|---------|------|
| **关联召回 eval** | 图扩展是否提升了需要关联推理的查询 | 比 baseline 提升 ≥30% |
| **巩固质量 eval** | 合并后的记忆是否保持信息完整性 | 人工审核准确率 >90% |
| **编码特异性 eval** | 带上下文的记忆在上下文匹配查询中是否排名更高 | top-1 准确率 >70% |
| **冲突检测 eval** | contradicts/supports/elaborates 分类准确率 | 误报率 <15% |
| **复习队列 eval** | 长期未访问的重要记忆是否出现在队列顶部 | Recall@10 >80% |
| **覆盖度评估 eval** | 能否正确识别"空领域" | 准确率 >85% |

### 回归 Eval（不退化）

- 中文检索 v1：55/55
- 中文检索 v2：20/20
- Memory benchmark v0：≥16/20

### 性能基准

- 检索延迟（1000 条记忆）：< 50ms（含图扩展）
- 巩固延迟（100 条记忆批量）：< 5s
- 复习队列计算：< 50ms

---

## 7. 非目标与边界

### 不做的事

- ❌ **引入向量数据库作为核心** — Roadmap 已标注"later, if justified"。FTS5 + 图扩展 + 上下文匹配的信息论组合已足够。
- ❌ **复制神经科学隐喻** — 不建"海马体模块""NREM 阶段"。只落地信息论原理。
- ❌ **在 AI 中实现"真正的"记忆宫殿** — 空间隐喻没有计算价值（MemPalace 批判性分析, 2026）。
- ❌ **牺牲可检查性** — 所有新结构（links, context, consolidation_level）必须是 SQLite 中可查询、可导出的。
- ❌ **自动写入巩固结果** — 巩固必须可审查（`--dry-run`），重要合并需确认。

### 与现有架构的一致性

- SQLite boring on purpose → 所有新功能用 SQLite 原生能力（递归 CTE、JSON 函数）
- Local-first → 不引入外部服务依赖
- Inspectable → 所有新字段可通过 CLI/WebUI 查看
- Explicit writes → 巩固和 chunking 是显式操作，不自动执行

---

## 附录 A：原理 → 人类技术 → AI 实现的完整映射

| 信息论原理 | 人类记忆技术 | 神经科学基础 | deep-memory 对应实现 |
|-----------|------------|------------|---------------------|
| **P1 编码丰富度** | 记忆宫殿、Major System（双编码） | Dual Coding Theory, 海马-新皮层连接 | encoding_context 字段 + memory_links 关联 |
| **P2 结构化脚手架** | 记忆宫殿空间位置、Peg System 锚点 | 认知地图理论, CA3 自联想 | memory_links 图 + 检索时图扩展 |
| **P3 压缩** | PAO、Chain/Story | Cowan 容量限制, 递归压缩 | chunk() 命令 + consolidation_level |
| **P4 检索即编码** | 间隔重复（FSRS）、测试效应 | 重巩固, LTP-like 变化 | access_count 追踪 + review-queue + 重巩固衰减 |
| **P5 离线巩固** | 睡眠巩固、NREM/REM | 系统巩固, 互补学习系统 | consolidate 命令 + superseded 生命周期 |

## 附录 B：参考文献

### 记忆技术

1. Dresler et al. (2017), *Neuron* — Mnemonic training reshapes brain networks
2. Dresler et al. (2017), *Science Advances* — Durable memories through MoL training
3. Roediger & Karpicke (2006), *Psychological Science* — Test-enhanced learning
4. Rowland (2014), *Psychological Bulletin* — Meta-analysis of testing effect (g=0.50)
5. Cepeda et al. (2006/2008), *Psychological Bulletin/Science* — Spacing effect meta-analysis
6. Cowan (2001), *BBS* — The magical number 4
7. Wang & Morris (2017), *Annual Review of Psychology* — Hippocampal-neocortical consolidation
8. Sherman (2024), *Perspectives on Psychological Science* — Memory systems framework
9. Planton et al. (2020), *PLOS Comp Biol* — Working memory as compression

### AI 记忆系统

10. MemGPT (2023) — OS-inspired virtual memory for LLMs
11. A-MEM (NeurIPS 2025) — Zettelkasten-based agentic memory
12. SYNAPSE (2026) — Spreading activation for memory retrieval
13. Graphiti / Zep — Temporal context graphs
14. FSRS — Free Spaced Repetition Scheduler
15. SleepGate (2026) — Sleep-inspired KV cache consolidation
16. SCM (2026) — Sleep-consolidated memory with NREM/REM
17. Auto-Dreamer (2026) — Learned offline consolidation
18. MemPalace critical analysis (2026) — Why spatial metaphors don't add computational value
19. "Why RAG isn't Memory" (2026) — Three independent analyses

---

*本文档是内部规划文档，不构成对用户的公开承诺。所有 Phase 的时间和范围需根据实际资源评估调整。*
