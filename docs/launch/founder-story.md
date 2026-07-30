# Founder story (canonical)

<!-- STATUS: Real story, collected from founder. Ready to use.
     Source: founder interview (OpenCode → Codex benchmark relay pain + @doc workaround failure).
     These are real experiences, not templated claims. Use as-is or lightly polish.
-->

## English version (for HN / Reddit / Twitter)

### Pain origin

I was running OpenCode, Codex, and Hermes against the same project. OpenCode would investigate benchmark submission details — the format, the constraints, the evaluation criteria. Then I'd switch to Codex to prepare the submission materials and run model inference on the server. Codex had no idea what OpenCode had figured out. I had to manually relay everything: the submission standards, the format requirements, the validation steps.

After a few rounds of this, it felt stupid. Multiple agents on the same machine, zero shared memory. I was acting as the memory layer between my own tools.

### Why existing options weren't enough

I tried the obvious workaround: save shared context as local docs, then @-mention them in each session. It works for a week. Then you're the one remembering which doc has which convention, which file is still current, which agent saw which version.

During multi-task parallel work, it falls apart. Your brain becomes the memory layer — remembering doc locations, tracking which is stale, manually piping context between agents. That's exactly the burden agents were supposed to offload.

### The conviction

Agent memory is too important to be my job. Every agent on this machine should share it, automatically, without me relaying context by hand. But it also can't just be a pile of everything — it has to hit the right things, stay organized, and not balloon into noise.

That's why I built `deep-memory`.

### One-liner

> All the agents on my machine should share memory. I shouldn't have to repeat myself to every single one.

---

## 中文版（for 知乎 / V2EX / 掘金）

### 痛点起源

我之前同时用 OpenCode、Codex、Hermes 做一个项目。OpenCode 负责调研某个 benchmark 的提交细节——格式、约束、评估标准。然后我切到 Codex，让它在服务器上准备提交材料、跑模型推理。Codex 完全不知道 OpenCode 查到了什么。我得手动把 OpenCode 的结果一条条转告给 Codex。

这样来几次之后就感觉特别蠢。同一台机器上的多个 agent，零共享记忆。我变成了自己工具之间的"人肉记忆层"。

### 现有方案为什么不够

我试过最直接的 workaround：把要共享的内容存成本地文档，对话的时候 @ 对应的文件。能用一周。然后就是你来记住哪个文档放了什么内容、哪个文件还是最新的、哪个 agent 看过哪个版本。

多任务并行的时候直接崩溃——你的脑子变成了记忆层，要记文档位置、判断哪些过期、手动在不同 agent 之间搬运上下文。这恰恰是 agent 本来应该帮你卸掉的负担。

### 信念

我本地机器的所有 agent 都应该能共享记忆，不要让我额外地重复说一遍又一遍。但记忆也不能是一坨无限膨胀的东西——它得准确命中、清晰组织、能更新能遗忘。

所以我做了 `deep-memory`。

---

## Insertion guide

### HN (hacker-news.md)
Founder story replaces the generic hook paragraph. Flow: [pain origin + workaround failure] → [product] → [comparison] → [features] → [eval] → [CTA]

### Reddit r/LocalLLaMA (reddit.md)
Condensed story (3-4 sentences) inserted between hook and product description.

### Twitter (twitter-thread.md)
"Why I built this" as tweet 2, between the cross-agent hook and the product intro.

### 知乎 (zhihu-memory-story.md)
The 船队故事 IS the narrative version. The CTA already references cross-agent pain. No insert needed — the real story lives here in founder-story.md as reference.

### V2EX / 掘金 (chinese-platforms.md)
Optional: add 1-2 sentences of personal pain after the cross-agent hook. The 中文版 pain origin above is ready to condense.
