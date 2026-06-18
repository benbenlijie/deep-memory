from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from evals.chinese_retrieval_eval import run_eval


def test_chinese_retrieval_v2_reports_ranking_metrics():
    result = run_eval(Path("evals/data/zh_memory_retrieval_v2.jsonl"), backend="local", limit=5)

    assert result["task_count"] >= 20
    assert result["top1_passed"] <= result["passed"]
    assert 0 <= result["top1_accuracy"] <= 1
    assert 0 <= result["mrr"] <= 1
    assert all("rank" in detail for detail in result["details"])
    assert all("top1_pass" in detail for detail in result["details"])


def test_chinese_retrieval_v2_contains_multi_memory_distractors():
    fixture = Path("evals/data/zh_memory_retrieval_v2.jsonl")
    rows = [line for line in fixture.read_text(encoding="utf-8").splitlines() if line.strip()]

    assert len(rows) >= 20
    assert all('"is_target":true' in row for row in rows)
    assert all(row.count('"content"') >= 3 for row in rows)
    assert any("stale" in row or "过期" in row or "旧" in row for row in rows)
    assert any("MCP" in row or "JSONL" in row or "adapter" in row for row in rows)
