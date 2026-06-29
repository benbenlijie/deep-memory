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
| 1000 | fts5 | 39.927 | 39.034 | 53.772 | 53.772 | 40.748 |
| 1000 | vector | 124.675 | 26.706 | 46.553 | 46.553 | 29.800 |
| 1000 | hybrid | 33.902 | 31.414 | 39.187 | 39.187 | 32.387 |
| 10000 | fts5 | 59.571 | 55.839 | 56.389 | 56.389 | 55.832 |
| 10000 | vector | 306.056 | 28.993 | 32.185 | 32.185 | 29.452 |
| 10000 | hybrid | 30.272 | 29.973 | 36.620 | 36.620 | 31.201 |
| 50000 | fts5 | 126.355 | 124.744 | 125.300 | 125.300 | 124.803 |
| 50000 | vector | 1561.805 | 52.822 | 68.618 | 68.618 | 54.873 |
| 50000 | hybrid | 51.156 | 55.933 | 96.920 | 96.920 | 60.522 |

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
| 1000 | 15784.061 | 15532.926 | 4751360 | 1000 | 2048000 |
| 10000 | 17602.021 | 16194.728 | 46284800 | 10000 | 20480000 |
| 50000 | 16970.452 | 15129.237 | 231116800 | 50000 | 102400000 |

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
