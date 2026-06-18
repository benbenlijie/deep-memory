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

The current local-first backend should be recorded when running the command. In this pass the default `local` path is `passed=55/55` (`accuracy=1.0`) on the fixture, compared with the earlier plain SQLite FTS baseline of `passed=24/55` (`accuracy=0.436`), a `+31/55` absolute lift.

## Harder v2 slice and ranking metrics

`evals/data/zh_memory_retrieval_v2.jsonl` adds 20 deterministic multi-memory cases. Every case has at least three memories, an explicit `is_target: true` label, and realistic distractors such as stale preferences, near-duplicate project facts, obsolete commands, and mixed Chinese/English technical terms.

Run it with ranking output:

```bash
uv run python evals/chinese_retrieval_eval.py --data evals/data/zh_memory_retrieval_v2.jsonl --backend local --json
```

Current checked-in baseline:

- top-k keyword containment: `passed=20/20`, `accuracy=1.0`;
- top-1 accuracy: `top1_passed=20/20`, `top1_accuracy=1.0`;
- mean reciprocal rank: `mrr=1.0`.

This v2 slice is still synthetic and intentionally small. It is useful as a cheap CI regression for ranking and distractor robustness, not as proof that the retriever is production-grade across open-domain Chinese memory workloads.

Phase 2 also adds an optional tokenizer backend:

```bash
uv sync --extra retrieval
uv run python evals/chinese_retrieval_eval.py --data evals/data/zh_memory_retrieval.jsonl --backend jieba
uv run python evals/chinese_retrieval_eval.py --data evals/data/zh_memory_retrieval.jsonl --backend jieba --json
```

The eval also accepts `--limit` for top-k sensitivity checks, for example:

```bash
uv run python evals/chinese_retrieval_eval.py --data evals/data/zh_memory_retrieval.jsonl --limit 3
```

The `jieba` backend preserves the same ASCII/Chinese-run/bigram tokens as `local`, then supplements them with jieba Chinese word segmentation. This keeps the base install lightweight: `jieba` is only installed through the `retrieval` extra, while the default backend has no new dependency. In this pass `--backend jieba` also reaches `passed=55/55` (`accuracy=1.0`) on v1, so it is a documented optional retrieval seam rather than a claimed lift over the already-strong local baseline.

If a future tokenizer or embedding path changes ranking, this file should remain a regression suite: improve labels only when the schema or retrieval objective changes intentionally.

## Why this matters

Stepping back, the bottleneck for Chinese memory retrieval is not just “do you have a vector DB”. The harder question is whether the system can reliably recover the right context across Chinese short text, high-density facts, relative time expressions, names and organizations, mixed Chinese/English terms, and old-versus-new contradictions. This dataset is the first executable measuring device for that.
