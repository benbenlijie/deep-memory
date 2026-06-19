from __future__ import annotations

import json
import subprocess
import sys


def test_competitive_benchmark_quick_run_writes_report(tmp_path):
    output_json = tmp_path / "competitive.json"
    output_md = tmp_path / "competitive.md"
    result = subprocess.run(
        [
            sys.executable,
            "benchmarks/competitive/run_competitive_benchmark.py",
            "--quick",
            "--systems",
            "deep-memory",
            "mem0",
            "zep",
            "langmem",
            "--output-json",
            str(output_json),
            "--output-md",
            str(output_md),
        ],
        text=True,
        capture_output=True,
        check=True,
    )

    assert "deep-memory" in result.stdout
    report = json.loads(output_json.read_text(encoding="utf-8"))
    systems = {item["system"]: item for item in report["systems"]}
    assert systems["deep-memory"]["status"] == "benchmarked"
    assert systems["deep-memory"]["search_accuracy"]["passed"] >= 16
    assert systems["deep-memory"]["chinese_retrieval"]["top1_passed"] == 20
    assert systems["mem0"]["status"] == "not_benchmarked"
    assert systems["Zep"]["status"] == "not_benchmarked"
    assert systems["LangMem"]["status"] == "not_benchmarked"

    markdown = output_md.read_text(encoding="utf-8")
    assert "Summary table across the 7 benchmark dimensions" in markdown
    assert "Where competitors may win" in markdown
    assert "Full feature matrix" in markdown
