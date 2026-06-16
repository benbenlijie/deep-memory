# Memory benchmark v0

This benchmark asks a narrow question: does persistent memory retrieval solve tasks that a no-memory agent cannot answer from the current prompt alone?

It is not a general reasoning benchmark. It is a retrieval-value benchmark: the query is under-specified unless the agent can recover prior user/project facts from memory.

## Fixture

`benchmarks/fixtures/memory_benchmark_v0.json` contains 20 bilingual tasks:

- 10 Chinese tasks
- 10 English tasks

Each task has:

- `query`: the user question
- `memories`: records inserted into a fresh `DeepMemory` database
- `expected_keywords`: facts that must appear in the answer
- `language`: `zh` or `en`

The fixture intentionally mixes user preferences, project decisions, product direction, and repository facts because those are the common bottlenecks for cross-session agents.

## Compared systems

The scoring script compares two conditions:

1. `baseline`: a no-memory baseline that cannot inspect prior sessions and therefore returns a generic insufficient-context answer.
2. `deep_memory`: a fresh SQLite/FTS5 `DeepMemory` database populated from the fixture memories, then queried with each task query.

## Metric

The metric is `answer_contains_all_expected_keywords`.

A task passes if the produced answer contains every expected keyword after case-folding and whitespace normalization. This is deliberately simple and inspectable. It measures whether the retrieval layer surfaced the necessary fact, not whether a model can paraphrase it.

Reported metrics:

- task count and language split
- baseline pass count and accuracy
- deep-memory pass count and accuracy
- absolute accuracy lift
- additional tasks solved by memory

## Reproduce

From the repository root:

```bash
uv sync --extra dev
uv run python benchmarks/memory_benchmark.py
```

Machine-readable report:

```bash
uv run python benchmarks/memory_benchmark.py --json
```

Use an explicit temporary database path:

```bash
uv run python benchmarks/memory_benchmark.py \
  --fixture benchmarks/fixtures/memory_benchmark_v0.json \
  --db /tmp/deep-memory-benchmark.db \
  --json
```

Run the regression tests:

```bash
uv run pytest tests/test_benchmark.py -q
uv run pytest -q
```

## Current v0 result

On the checked-in fixture, the benchmark should show:

- 20 total tasks
- bilingual coverage: 10 zh, 10 en
- baseline accuracy: 0/20
- deep-memory accuracy: at least 16/20 in tests, typically 20/20 with the default retrieval limit
- positive absolute lift over baseline

The default retrieval limit is intentionally set to 8 because the current MVP uses simple lexical retrieval. If a future tokenizer or embedding retriever improves ranking, this benchmark should become stricter by lowering the limit and adding harder near-miss distractors.

## Interpretation

If you退后一步看，这个 benchmark 不是在证明“memory 让模型更聪明”。它证明的是一个更底层的东西：当任务依赖跨会话状态时，没有可检索的长期表征，系统连正确问题空间都进不去。

That is the value this v0 harness tries to isolate.
