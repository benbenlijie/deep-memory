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
| 1000 | fts5 | 10.823 | 12.768 | 12.768 | 11.430 |
| 1000 | vector | 30.854 | 32.131 | 32.131 | 30.604 |
| 1000 | hybrid | 31.018 | 32.623 | 32.623 | 31.386 |
| 10000 | fts5 | 21.056 | 22.817 | 22.817 | 20.613 |
| 10000 | vector | 218.505 | 228.633 | 228.633 | 220.276 |
| 10000 | hybrid | 223.200 | 235.447 | 235.447 | 223.219 |

### Embedding latency

- per text: 0.037 ms
- batch of 64: 0.401 ms
- batch per text: 0.006 ms

### Memory usage

| Corpus size | DB bytes | Embedding rows | Embedding blob bytes | Vector overhead bytes |
| --- | ---: | ---: | ---: | ---: |
| 1000 | 843776 | 1000 | 48000 | 48000 |
| 10000 | 7393280 | 10000 | 480000 | 480000 |
