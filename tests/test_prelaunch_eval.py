from __future__ import annotations

from evals.prelaunch_eval import EvalConfig, run_eval


def test_prelaunch_eval_outputs_required_gate_sections(tmp_path):
    output_json = tmp_path / "prelaunch-eval.json"
    output_markdown = tmp_path / "PRELAUNCH_EVAL_REPORT.md"

    result = run_eval(
        EvalConfig(
            sizes=(100,),
            dimensions=32,
            latency_iterations=2,
            output_json=output_json,
            output_markdown=output_markdown,
        )
    )

    assert result["schema_version"] == 1
    assert result["environment"]["python"]
    assert "numpy_available" in result["environment"]
    assert result["config"]["sizes"] == [100]

    size_result = result["sizes"]["100"]
    assert set(size_result) >= {
        "latency",
        "correctness",
        "backfill",
        "memory_usage",
        "reproducibility",
        "fallback",
    }
    assert set(size_result["latency"]) >= {"fts5", "vector", "hybrid"}
    assert set(size_result["latency"]["hybrid"]) >= {"cold_ms", "warm"}
    assert set(size_result["latency"]["hybrid"]["warm"]) >= {"p50_ms", "p95_ms", "p99_ms", "mean_ms"}

    correctness = size_result["correctness"]
    assert correctness["known_target_top1"]["passed"] is True
    assert correctness["known_target_top5"]["passed"] is True
    assert correctness["scope_isolation"]["passed"] is True
    assert correctness["lifecycle_filtering"]["passed"] is True
    assert correctness["mixed_language_hybrid"]["passed"] is True

    assert size_result["backfill"]["rows_per_second"] > 0
    assert size_result["memory_usage"]["db_bytes"] > 0
    assert size_result["fallback"]["no_numpy_functional"]["passed"] is True
    assert len(size_result["reproducibility"]["runs"]) == 2
    assert size_result["reproducibility"]["stable_top1"] is True

    assert output_json.exists()
    assert output_markdown.exists()
    report = output_markdown.read_text(encoding="utf-8")
    assert "# Pre-launch eval report" in report
    assert "Launch-safe claims" in report
