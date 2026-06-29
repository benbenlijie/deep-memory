from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from evals.retrieval_benchmark import BenchmarkConfig, run_benchmark


def test_retrieval_benchmark_produces_category_metrics_and_hybrid_lifts_semantic_cases(tmp_path):
    output = tmp_path / "retrieval-results.json"

    result = run_benchmark(BenchmarkConfig(output_path=output, performance_sizes=(1000,)))

    assert output.exists()
    saved = json.loads(output.read_text(encoding="utf-8"))
    assert saved["recall"]["summary"]["query_count"] == 80
    assert set(saved["recall"]["categories"]) == {
        "exact_match",
        "synonym_match",
        "cross_lingual",
        "semantic_paraphrase",
    }
    for category in saved["recall"]["categories"].values():
        assert category["query_count"] == 20
        assert set(category["modes"]) == {"fts5", "vector", "hybrid"}
        for metrics in category["modes"].values():
            assert set(metrics) == {"recall@1", "recall@3", "recall@5", "mrr"}
            assert all(0.0 <= value <= 1.0 for value in metrics.values())

    assert result["recall"]["categories"]["synonym_match"]["modes"]["hybrid"]["recall@5"] > result["recall"]["categories"]["synonym_match"]["modes"]["fts5"]["recall@5"]
    assert result["recall"]["categories"]["cross_lingual"]["modes"]["hybrid"]["recall@5"] > result["recall"]["categories"]["cross_lingual"]["modes"]["fts5"]["recall@5"]
    hybrid_p95_ms = result["performance"]["search_latency"]["1000"]["hybrid"]["p95_ms"]
    assert hybrid_p95_ms < 50
    assert result["performance"]["embedding_latency"]["per_text_ms"] >= 0
    assert result["performance"]["memory_usage"]["1000"]["vector_overhead_bytes"] > 0
