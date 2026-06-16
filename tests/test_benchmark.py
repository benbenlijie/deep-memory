from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_memory_benchmark_fixture_set_is_bilingual_and_large_enough():
    fixture_path = Path("benchmarks/fixtures/memory_benchmark_v0.json")
    data = json.loads(fixture_path.read_text(encoding="utf-8"))

    tasks = data["tasks"]
    assert len(tasks) >= 20
    assert any(task["language"] == "zh" for task in tasks)
    assert any(task["language"] == "en" for task in tasks)
    assert all(task["query"].strip() for task in tasks)
    assert all(task["memories"] for task in tasks)
    assert all(task["expected_keywords"] for task in tasks)


def test_memory_benchmark_script_proves_memory_beats_no_memory(tmp_path):
    result = subprocess.run(
        [
            sys.executable,
            "benchmarks/memory_benchmark.py",
            "--fixture",
            "benchmarks/fixtures/memory_benchmark_v0.json",
            "--db",
            str(tmp_path / "benchmark.db"),
            "--json",
        ],
        check=True,
        text=True,
        capture_output=True,
    )
    report = json.loads(result.stdout)

    assert report["task_count"] >= 20
    assert report["baseline"]["accuracy"] < report["deep_memory"]["accuracy"]
    assert report["deep_memory"]["accuracy"] >= 0.8
    assert report["lift"]["absolute_accuracy"] > 0
