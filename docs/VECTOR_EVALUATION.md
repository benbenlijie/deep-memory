# Vector / embedding model evaluation

This document records the M+14 B1 decision for local embeddings in deep-memory.

## Goal

Pick a default local embedding backend for Chinese + English coding memory that improves semantic recall without making deep-memory heavy for users who only want SQLite + FTS5.

## Candidates

| Candidate | Dim | Approx. package/model impact | Strength | Weakness |
|---|---:|---:|---|---|
| `BAAI/bge-small-zh-v1.5` | 512 | ~95 MB model, `sentence-transformers` optional extra | Strong Chinese retrieval, acceptable multilingual/coding synonyms, small enough for local OSS use | Requires first model download/load; not as multilingual as bge-m3 |
| `BAAI/bge-m3` | 1024 | ~2.2 GB model | Best broad multilingual retrieval and long-context embedding quality | Too large and slow for default local memory; cold start is poor for CLI/agent workflows |
| Model2Vec/static embeddings | model-dependent | very small/fast | Lowest latency and memory footprint | Lower semantic quality, weaker Chinese/cross-language synonym behavior |

## Evaluation criteria

1. Chinese retrieval accuracy: `evals/data/zh_memory_retrieval_v2.jsonl` is the standing fixture for Chinese memory retrieval.
2. English synonym recall: coding-memory pairs such as `test` ↔ `pytest`, `deploy` ↔ `release`, `bug` ↔ `regression`, `docs` ↔ `documentation`.
3. Package size impact: base install must remain lightweight; vector dependencies are optional.
4. First-load latency: model loading must be lazy, not import-time.
5. Memory usage per inference: default should fit ordinary laptops/dev boxes.

## Decision

Default vector backend: `BAAI/bge-small-zh-v1.5` through `sentence-transformers`, behind the optional `vector` extra.

Why this wins:

- It is the best bottleneck match for deep-memory's current problem: Chinese-first semantic recall with acceptable English coding-memory behavior.
- It keeps the base package small because `sentence-transformers` is only installed with `uv sync --extra vector` / `deep-memory[vector]`.
- Its 512-dimensional vectors are modest enough for local SQLite BLOB storage.
- Cold-start cost is isolated by lazy loading: importing `deep_memory` does not import or instantiate the model.
- It gives a cleaner upgrade path: B2/B3 can add vector search/reranking while FTS5 remains the graceful fallback.

## Why not bge-m3 as default

`bge-m3` is likely the quality winner for broad multilingual retrieval, but its size and cold-start cost make it a poor default for an OSS agent-memory package. It is better as a future opt-in backend for users who explicitly prefer quality over footprint.

## Why not Model2Vec as default

Model2Vec/static embeddings are attractive for latency, but this stage is about making embeddings real for Chinese + English coding memory. The quality risk is higher than the performance benefit for the default path. It remains a possible future `fast-vector` backend.

## Implementation notes

- New optional extra: `vector = ["sentence-transformers>=3.0.0"]`.
- New module: `src/deep_memory/embeddings.py` with an `EmbeddingBackend` protocol.
- New table: `memory_embeddings(memory_id, embedding BLOB, model_name, model_version, dim, created_at)`.
- `DeepMemory.add()` attempts to generate/store an embedding when a vector backend is available.
- Without the vector extra, `add()` silently skips embeddings and FTS5 search still works.
- Embedding metadata is mirrored on `memories.embedding_model` and `memories.embedding_version` for schema compatibility with M+13.

## Minimal validation performed

The implementation includes tests for:

- float vector BLOB round-trip;
- embedding row insertion with model name/version/dim;
- graceful degradation without `sentence-transformers`;
- migration creating `memory_embeddings` for legacy databases;
- lazy backend/model loading;
- selected default model/version constants.

Full task validation should pass:

```bash
uv run pytest -q
uv run ruff check .
```
