from __future__ import annotations

import argparse
import json
import re
import tempfile
from pathlib import Path
from typing import Any

from deep_memory import DeepMemory


def load_fixture(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.casefold()).strip()


def answer_contains_all_expected_keywords(answer: str, expected_keywords: list[str]) -> bool:
    normalized_answer = normalize(answer)
    return all(normalize(keyword) in normalized_answer for keyword in expected_keywords)


def no_memory_baseline_answer(task: dict[str, Any]) -> str:
    return "I do not have enough persistent memory to answer this from prior sessions."


def deep_memory_answer(mem: DeepMemory, task: dict[str, Any], *, limit: int) -> str:
    results = mem.search(task["query"], limit=limit)
    return "\n".join(result.record.content for result in results)


def evaluate_task(mem: DeepMemory, task: dict[str, Any], *, limit: int) -> dict[str, Any]:
    baseline_answer = no_memory_baseline_answer(task)
    memory_answer = deep_memory_answer(mem, task, limit=limit)
    expected = list(task["expected_keywords"])
    return {
        "id": task["id"],
        "language": task["language"],
        "expected_keywords": expected,
        "baseline_pass": answer_contains_all_expected_keywords(baseline_answer, expected),
        "deep_memory_pass": answer_contains_all_expected_keywords(memory_answer, expected),
        "retrieved_answer": memory_answer,
    }


def build_memory_db(db_path: Path, tasks: list[dict[str, Any]]) -> DeepMemory:
    if db_path.exists():
        db_path.unlink()
    mem = DeepMemory(db_path)
    for task in tasks:
        for memory in task["memories"]:
            mem.add(memory, kind="semantic", importance=0.9, confidence=0.95, source=task["id"])
    return mem


def summarize(task_results: list[dict[str, Any]]) -> dict[str, Any]:
    task_count = len(task_results)
    baseline_passes = sum(1 for item in task_results if item["baseline_pass"])
    memory_passes = sum(1 for item in task_results if item["deep_memory_pass"])
    language_counts: dict[str, int] = {}
    for item in task_results:
        language_counts[item["language"]] = language_counts.get(item["language"], 0) + 1
    return {
        "task_count": task_count,
        "languages": language_counts,
        "metric": "answer_contains_all_expected_keywords",
        "baseline": {
            "passed": baseline_passes,
            "accuracy": round(baseline_passes / task_count, 4) if task_count else 0.0,
        },
        "deep_memory": {
            "passed": memory_passes,
            "accuracy": round(memory_passes / task_count, 4) if task_count else 0.0,
        },
        "lift": {
            "absolute_accuracy": round((memory_passes - baseline_passes) / task_count, 4)
            if task_count
            else 0.0,
            "additional_tasks_solved": memory_passes - baseline_passes,
        },
        "tasks": task_results,
    }


def run_benchmark(fixture_path: Path, db_path: Path, *, limit: int) -> dict[str, Any]:
    fixture = load_fixture(fixture_path)
    tasks = list(fixture["tasks"])
    mem = build_memory_db(db_path, tasks)
    try:
        task_results = [evaluate_task(mem, task, limit=limit) for task in tasks]
    finally:
        mem.close()
    report = summarize(task_results)
    report["fixture"] = str(fixture_path)
    report["db"] = str(db_path)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare no-memory baseline vs deep-memory retrieval.")
    parser.add_argument(
        "--fixture",
        type=Path,
        default=Path("benchmarks/fixtures/memory_benchmark_v0.json"),
        help="Path to benchmark fixture JSON.",
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=None,
        help="SQLite db path for the benchmark run. Defaults to a temporary file.",
    )
    parser.add_argument("--limit", type=int, default=8, help="Retrieval limit per task.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON report.")
    args = parser.parse_args()

    if args.db is None:
        tmp = tempfile.NamedTemporaryFile(prefix="deep-memory-benchmark-", suffix=".db", delete=False)
        tmp.close()
        db_path = Path(tmp.name)
    else:
        db_path = args.db

    report = run_benchmark(args.fixture, db_path, limit=args.limit)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"tasks: {report['task_count']} languages: {report['languages']}")
        print(
            "baseline accuracy: "
            f"{report['baseline']['accuracy']:.2%} "
            f"({report['baseline']['passed']}/{report['task_count']})"
        )
        print(
            "deep-memory accuracy: "
            f"{report['deep_memory']['accuracy']:.2%} "
            f"({report['deep_memory']['passed']}/{report['task_count']})"
        )
        print(
            "absolute lift: "
            f"{report['lift']['absolute_accuracy']:.2%} "
            f"(+{report['lift']['additional_tasks_solved']} tasks)"
        )


if __name__ == "__main__":
    main()
