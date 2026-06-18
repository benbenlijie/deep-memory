from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path
from typing import Literal

from deep_memory import DeepMemory

EvalBackend = Literal["local", "jieba"]


def run_eval(path: Path, *, backend: EvalBackend = "local", limit: int = 5) -> dict:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    passed = 0
    top1_passed = 0
    reciprocal_rank_sum = 0.0
    details = []
    with tempfile.TemporaryDirectory() as td:
        for row in rows:
            mem = DeepMemory(Path(td) / f"{row['id']}.db")
            target_contents = {
                item["content"] for item in row["memories"] if item.get("is_target") is True
            }
            for item in row["memories"]:
                mem.add(item["content"], kind=item.get("kind", "semantic"), importance=item.get("importance", 0.8))
            results = mem.search(row["query"], limit=limit, backend=backend)
            answer = "\n".join(r.record.content for r in results)
            ok = all(k in answer for k in row["expected_keywords"])
            rank = None
            for idx, result in enumerate(results, start=1):
                content = result.record.content
                is_target = content in target_contents or all(k in content for k in row["expected_keywords"])
                if is_target:
                    rank = idx
                    break
            top1_ok = rank == 1
            passed += int(ok)
            top1_passed += int(top1_ok)
            reciprocal_rank_sum += 1 / rank if rank else 0
            details.append(
                {
                    "id": row["id"],
                    "category": row["category"],
                    "pass": ok,
                    "rank": rank,
                    "top1_pass": top1_ok,
                }
            )
    return {
        "backend": backend,
        "limit": limit,
        "task_count": len(rows),
        "passed": passed,
        "accuracy": passed / len(rows) if rows else 0,
        "top1_passed": top1_passed,
        "top1_accuracy": top1_passed / len(rows) if rows else 0,
        "mrr": reciprocal_rank_sum / len(rows) if rows else 0,
        "details": details,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="evals/data/zh_memory_retrieval.jsonl")
    parser.add_argument("--backend", default="local", choices=["local", "jieba"])
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    backend: EvalBackend = args.backend
    result = run_eval(Path(args.data), backend=backend, limit=args.limit)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(
            f"backend={result['backend']} "
            f"limit={result['limit']} "
            f"accuracy={result['accuracy']:.3f} passed={result['passed']}/{result['task_count']}"
        )


if __name__ == "__main__":
    main()
