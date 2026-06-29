# Pre-launch eval report

This report checks whether `deep-memory` is fast, correct, stable, and reproducible at launch-relevant corpus sizes.

## Environment

- Python: `3.11.15`
- Platform: `Linux-6.17.0-35-generic-x86_64-with-glibc2.39`
- NumPy available: `True`
- sentence-transformers available: `False`

## Search latency

| Size | Mode | Cold ms | Warm p50 | Warm p95 | Warm p99 | Warm mean |
| ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 1000 | fts5 | 45.177 | 38.930 | 53.794 | 53.794 | 41.418 |
| 1000 | vector | 143.919 | 36.782 | 53.865 | 53.865 | 35.245 |
| 1000 | hybrid | 24.465 | 24.394 | 75.923 | 75.923 | 31.109 |
| 10000 | fts5 | 54.869 | 54.425 | 58.536 | 58.536 | 55.014 |
| 10000 | vector | 299.066 | 28.813 | 37.147 | 37.147 | 29.916 |
| 10000 | hybrid | 31.204 | 38.599 | 46.193 | 46.193 | 37.839 |
| 50000 | fts5 | 131.709 | 125.811 | 133.989 | 133.989 | 126.457 |
| 50000 | vector | 1580.330 | 51.748 | 103.397 | 103.397 | 59.835 |
| 50000 | hybrid | 49.101 | 48.980 | 87.618 | 87.618 | 54.500 |

## Correctness gate

| Size | Check | Pass | Evidence |
| ---: | --- | --- | --- |
| 1000 | known_target_top1 | `True` | `{"passed": true, "top_ids": ["known-target", "mixed-language", "mem-000327", "mem-000329", "mem-000330"]}` |
| 1000 | known_target_top5 | `True` | `{"passed": true, "top_ids": ["known-target", "mixed-language", "mem-000327", "mem-000329", "mem-000330"]}` |
| 1000 | scope_isolation | `True` | `{"passed": true, "workspace_a_top_ids": ["workspace-a"], "workspace_b_top_ids": ["workspace-b"]}` |
| 1000 | lifecycle_filtering | `True` | `{"passed": true, "top_ids": ["mixed-language", "known-target", "mem-000327", "mem-000329", "mem-000330", "mem-000331", "mem-000332", "mem-000333", "mem-000334", "mem-000335"]}` |
| 1000 | mixed_language_hybrid | `True` | `{"passed": true, "top_ids": ["mixed-language", "workspace-a", "workspace-b", "mem-000329", "mem-000330"]}` |
| 10000 | known_target_top1 | `True` | `{"passed": true, "top_ids": ["known-target", "mixed-language", "mem-003338", "mem-003336", "mem-003335"]}` |
| 10000 | known_target_top5 | `True` | `{"passed": true, "top_ids": ["known-target", "mixed-language", "mem-003338", "mem-003336", "mem-003335"]}` |
| 10000 | scope_isolation | `True` | `{"passed": true, "workspace_a_top_ids": ["workspace-a"], "workspace_b_top_ids": ["workspace-b"]}` |
| 10000 | lifecycle_filtering | `True` | `{"passed": true, "top_ids": ["mixed-language", "known-target", "mem-003338", "mem-003336", "mem-003335", "mem-003334", "mem-003333", "mem-003332", "mem-003331", "mem-003330"]}` |
| 10000 | mixed_language_hybrid | `True` | `{"passed": true, "top_ids": ["mixed-language", "workspace-b", "workspace-a", "mem-003337", "mem-003336"]}` |
| 50000 | known_target_top1 | `True` | `{"passed": true, "top_ids": ["known-target", "mixed-language", "mem-016672", "mem-016671", "mem-016670"]}` |
| 50000 | known_target_top5 | `True` | `{"passed": true, "top_ids": ["known-target", "mixed-language", "mem-016672", "mem-016671", "mem-016670"]}` |
| 50000 | scope_isolation | `True` | `{"passed": true, "workspace_a_top_ids": ["workspace-a"], "workspace_b_top_ids": ["workspace-b"]}` |
| 50000 | lifecycle_filtering | `True` | `{"passed": true, "top_ids": ["mixed-language", "known-target", "mem-016672", "mem-016671", "mem-016670", "mem-016669", "mem-016668", "mem-016667", "mem-016666", "mem-016665"]}` |
| 50000 | mixed_language_hybrid | `True` | `{"passed": true, "top_ids": ["mixed-language", "workspace-b", "workspace-a", "mem-016672", "mem-016670"]}` |

## Backfill and memory usage

| Size | Seed rows/s | Backfill rows/s | DB bytes | Embedding rows | Embedding blob bytes |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 1000 | 12830.594 | 16001.377 | 4751360 | 1000 | 2048000 |
| 10000 | 17452.730 | 15792.896 | 46284800 | 10000 | 20480000 |
| 50000 | 16866.010 | 15404.873 | 231116800 | 50000 | 102400000 |

## Stability and fallback

| Size | Stable top1 | Fallback functional |
| ---: | --- | --- |
| 1000 | `True` | `True` |
| 10000 | `True` | `True` |
| 50000 | `True` | `True` |

## Launch-safe claims

- The deterministic pre-launch gate covers 1k/10k/50k corpus sizes with FTS5, vector, and hybrid retrieval.
- Correctness checks cover known-target retrieval, scope isolation, lifecycle filtering, mixed-language hybrid retrieval, reproducibility, and fallback behavior.
- This is a deterministic local eval, not a replacement for real-user corpus evaluation or hosted production load testing.
