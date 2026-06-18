# Vector Retrieval Roadmap

`deep-memory` stays SQLite + FTS5-first until there is clear evidence that lexical retrieval is the bottleneck. This document defines the readiness path for embeddings without implementing vector storage or adding dependencies today.

## Scope

Current state:

- FTS5 remains the default retrieval path.
- No vector store, embedding runtime, background worker, or API dependency is introduced in this phase.
- The schema reserves nullable metadata fields on each `MemoryRecord`: `embedding_model` and `embedding_version`.
- The placeholder config is explicit: `embedding.enabled = false`.

Non-goals for this phase:

- no vector index implementation;
- no embedding generation;
- no hosted sync;
- no automatic upload of memory contents to third-party APIs.

## Trigger conditions

Enable vector work only when at least one of these conditions is true:

| Trigger | Default threshold | Why it matters | Evidence required |
| --- | ---: | --- | --- |
| Record volume | >= 50k active records | FTS5 and fallback retrieval can become noisy for power users. | Local benchmark showing latency or top-k quality degradation. |
| User opt-in | explicit opt-in | Embeddings may introduce model download, GPU/CPU cost, or API privacy tradeoffs. | User-visible setting and safety copy. |
| FTS recall gap | below project recall threshold | Semantic near-matches and synonyms can fail lexical retrieval (`test` vs `pytest`). | Checked-in eval fixture with failing lexical cases and improved hybrid result. |

The default `N` for the volume trigger is 50k records. It should remain configurable because a single-user project database and a team memory database have different cost and latency profiles.

## Placeholder configuration

The default configuration surface should be equivalent to:

```toml
[embedding]
enabled = false
model = null
version = null
provider = null
```

Rules:

- `embedding.enabled = false` is the only supported runtime behavior today.
- `embedding_model` records the exact model/provider identifier used to produce an embedding once embeddings exist.
- `embedding_version` is an integer schema/index generation marker, not a semantic model version string.
- Any future writer that produces embeddings must stamp both fields so backfills and cutovers are auditable.

## Candidate models

| Option | Strengths | Costs / risks | Best fit |
| --- | --- | --- | --- |
| Local `bge-small-zh-v1.5` | Small, local, good Chinese/English mixed baseline, privacy-preserving. | Lower multilingual breadth and semantic ceiling than larger models; local CPU cost still exists. | Default local opt-in for Chinese-first personal/project memory. |
| Local `bge-m3` | Strong multilingual retrieval, better cross-lingual and mixed-language coverage. | Larger model, higher disk/RAM/latency cost, more complex local deployment. | Power users and teams with multilingual memory and acceptable local resource cost. |
| API embeddings (OpenAI / voyage) | Strong managed quality, no local model install, fast iteration. | Third-party data exposure, recurring cost, network dependency, regional/compliance questions. | Explicit opt-in users who value quality/convenience over local-only privacy. |

Selection principle: start with a local model for privacy-preserving evals, then compare API providers only behind explicit opt-in and documented data-handling boundaries.

## Hybrid retrieval design

Vector retrieval should augment, not replace, the lexical baseline.

Proposed scoring:

```text
final_score = alpha * bm25_score + beta * vector_score + gamma * metadata_score
```

Initial tunables:

- `alpha`: lexical/BM25 weight;
- `beta`: vector similarity weight;
- `gamma`: existing memory metadata weight (`importance`, `confidence`, freshness/decay);
- `top_k_lexical` and `top_k_vector`: candidate pool sizes before fusion;
- `min_vector_score`: guardrail to avoid weak semantic drift.

Design constraints:

- BM25/FTS5 remains available even when embeddings fail.
- Fusion parameters must be observable in eval output.
- Hybrid retrieval must support exact-match wins for names, IDs, commands, and file paths.
- The WebUI/export path must remain inspectable; embeddings must not become the only view of memory.

## Migration path: shadow column pattern

Use a reversible shadow-index rollout:

1. Add an `embedding_v2` storage path or index side table while keeping existing FTS5 reads unchanged.
2. Run background backfill in batches, stamping `embedding_model` and `embedding_version` for each completed record.
3. Add a feature flag for hybrid retrieval, default off.
4. Run dual-read validation: FTS-only and hybrid both execute, eval logs compare top-k, latency, and disagreement cases.
5. Cut over only when evals pass and privacy copy is reviewed.
6. Keep the old index for 2 weeks after cutover.
7. Remove or compact old embedding storage only after rollback risk is low.

Operational requirements:

- Backfill must be resumable and idempotent.
- Partial backfills must not hide records from search.
- Failed embedding generation should leave the record searchable through FTS5.
- Embedding version changes should be treated as a new generation, not in-place mutation without auditability.

## Rollback

Rollback should be a single feature-flag change:

```toml
[embedding]
enabled = false
```

Rollback behavior:

- all reads return to FTS5/local fallback;
- existing embedding metadata remains for audit/backfill resume;
- no memory records are deleted;
- old FTS5 index remains available during and after rollback.

## Evaluation gates

Before vector retrieval becomes default for any user segment, require:

- a checked-in eval fixture containing synonym/semantic-near cases where FTS5 fails;
- recall/MRR comparison for FTS-only vs vector-only vs hybrid;
- latency and memory/disk footprint measurements at 50k, 100k, and 1M records or realistic synthetic equivalents;
- privacy review for API-backed models;
- rollback drill showing `embedding.enabled = false` restores lexical retrieval.

## Open questions

- Should vector storage live in SQLite extensions, a sidecar index, or a separate local service?
- What is the minimum fixture size that catches semantic wins without overfitting to demos?
- Should team memory support different embedding providers per tenant/workspace?
- How should embeddings interact with deletion/export guarantees?
