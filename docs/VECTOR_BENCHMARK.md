# Vector retrieval benchmark

This document records the current retrieval benchmark and latency snapshot for the vector retrieval lane.

## Recall benchmark

| Category | Mode | Recall@1 | Recall@3 | Recall@5 | MRR |
| --- | --- | ---: | ---: | ---: | ---: |
| exact_match | fts5 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| exact_match | vector | 0.2500 | 0.2500 | 0.5000 | 0.3000 |
| exact_match | hybrid | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| synonym_match | fts5 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| synonym_match | vector | 0.2500 | 0.2500 | 0.5000 | 0.3000 |
| synonym_match | hybrid | 0.6000 | 0.6000 | 0.6000 | 0.6000 |
| cross_lingual | fts5 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| cross_lingual | vector | 0.2500 | 0.2500 | 0.5000 | 0.3000 |
| cross_lingual | hybrid | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| semantic_paraphrase | fts5 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| semantic_paraphrase | vector | 0.1000 | 0.1000 | 0.2500 | 0.1300 |
| semantic_paraphrase | hybrid | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

## Performance benchmark

### Search latency

| Corpus size | Mode | p50 ms | p95 ms | p99 ms | mean ms |
| --- | --- | ---: | ---: | ---: | ---: |
| 1000 | fts5 | 9.703 | 10.354 | 10.354 | 9.777 |
| 1000 | vector | 21.803 | 23.964 | 23.964 | 22.065 |
| 1000 | hybrid | 22.818 | 25.595 | 25.595 | 23.176 |
| 10000 | fts5 | 20.003 | 24.057 | 24.057 | 20.475 |
| 10000 | vector | 149.366 | 174.344 | 174.344 | 152.298 |
| 10000 | hybrid | 147.919 | 152.940 | 152.940 | 148.563 |
| 50000 | fts5 | 19.993 | 25.239 | 25.239 | 20.568 |
| 50000 | vector | 699.030 | 722.315 | 722.315 | 700.802 |
| 50000 | hybrid | 702.513 | 715.739 | 715.739 | 703.278 |

### Embedding latency

- per text: 0.045 ms
- batch of 64: 0.400 ms
- batch per text: 0.006 ms

### Memory usage

| Corpus size | DB bytes | Embedding rows | Embedding blob bytes | Vector overhead bytes |
| --- | ---: | ---: | ---: | ---: |
| 1000 | 819200 | 1000 | 48000 | 48000 |
| 10000 | 7294976 | 10000 | 480000 | 480000 |
| 50000 | 35889152 | 50000 | 2400000 | 2400000 |
