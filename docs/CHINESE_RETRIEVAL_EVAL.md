# Chinese Retrieval Evaluation v1

This dataset turns the project’s “Chinese-first memory retrieval” claim into something we can run, inspect, and improve.

## Data file

`evals/data/zh_memory_retrieval.jsonl`

Current v1 contains 55 synthetic-but-realistic Chinese-first query-memory cases. The data intentionally includes mixed technical terms such as `MCP`, `Hermes`, `adapter`, `JSONL`, `source of truth`, `Kanban`, and `Loop Engineering`, because real agent-memory records in this project are bilingual.

## Coverage

The dataset covers the required Phase 2 dimensions:

- time expressions: absolute dates, relative dates, month-end references, and future milestones
- preferences: answer language/style, executable-code preference, `/goal` workflow, artifact location, channel preference
- project facts: storage, memory layers, growth target, Chinese-first evaluation, integrations, provenance/governance
- names / people: Ben, `demis-research`, `default profile`, reviewer and contributor roles
- organizations / systems: Hermes Agent, GitHub, Teambition, Hermes Kanban, QQ/NapCatQQ/OneBot
- contradictions: old/new preferences, confirmed supersession, candidate updates, superseded facts

It also includes procedural, technical-stack, channel, and business-context cases so the benchmark is not only an entity lookup test.

## JSONL schema

Each line is a standalone evaluation case:

```json
{
  "id": "zh_001_preference",
  "category": "preference",
  "query": "用户偏好是什么？",
  "memories": [
    {
      "content": "用户偏好：中文为主，技术术语保留英文",
      "kind": "semantic",
      "importance": 0.8,
      "source": "optional-source"
    }
  ],
  "expected_keywords": ["中文", "技术术语"],
  "notes": "labeling rationale"
}
```

### Fields

- `id`: stable case id, prefixed with `zh_` and a zero-padded ordinal.
- `category`: coarse scenario label for aggregate analysis.
- `query`: user-style retrieval query, usually natural Chinese rather than exact keyword copies.
- `memories`: records inserted into a fresh temporary `DeepMemory` database for the case.
  - `content`: stored memory text.
  - `kind`: one of `working`, `episodic`, `semantic`, or `procedural`.
  - `importance`: float in `[0, 1]`, used by current ranking.
  - `source`: optional provenance string, useful for adapter and contradiction cases.
- `expected_keywords`: minimal substrings that must appear in the retrieved context for the case to pass.
- `notes`: labeling rationale or special assumption.

## Labeling assumptions

V1 uses keyword containment rather than human preference ranking. That is deliberate: it catches gross Chinese retrieval regressions cheaply before we introduce heavier embedding models, rerankers, or human-labeled relevance judgments.

Assumptions:

1. A case passes when all `expected_keywords` appear anywhere in the concatenated top-k retrieved memory contents.
2. Keywords are minimal fact anchors, not full natural-language answers.
3. Contradiction cases label the freshest, confirmed, or candidate memory depending on the scenario; they do not require the retriever to perform full conflict resolution by itself.
4. Some cases include distractor memories so retrieval must prefer the relevant record, while remaining deterministic enough for local CI.
5. Mixed Chinese/English tokens are part of the task because project records contain terms like `Hermes`, `MCP`, `adapter`, `JSONL`, `Kanban`, and `source of truth`.

## How to run

```bash
uv run python evals/chinese_retrieval_eval.py --data evals/data/zh_memory_retrieval.jsonl
uv run python evals/chinese_retrieval_eval.py --data evals/data/zh_memory_retrieval.jsonl --json
```

Current baseline on the local FTS5/bigram implementation should be recorded when running the command. In this pass the baseline is `passed=24/55` (`accuracy=0.436`), while the current local-first Chinese retrieval path reaches `passed=55/55` (`accuracy=1.0`) on the same fixture, a `+31/55` absolute lift. The implementation stays local-first: no jieba/pkuseg/BGE install is required for the default path, but the design leaves a clear seam for an optional tokenizer or embedding backend later.

If a future tokenizer or embedding path changes ranking, this file should remain a regression suite: improve labels only when the schema or retrieval objective changes intentionally.

## Why this matters

If you退后一步看，中文记忆检索的 bottleneck 不只是“有没有向量库”。真正有趣的问题是：系统能否在中文短文本、高密度事实、相对时间、名字/组织、中英混排和新旧矛盾中稳定找回正确上下文。这个数据集是第一版可执行的测量装置。
