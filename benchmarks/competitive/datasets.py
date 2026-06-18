from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .base import MemoryItem, RetrievalCase


def _memory_from_raw(raw: str | dict[str, Any]) -> MemoryItem:
    if isinstance(raw, str):
        return MemoryItem(content=raw)
    metadata = {k: v for k, v in raw.items() if k not in {"content", "kind", "importance"}}
    return MemoryItem(
        content=str(raw["content"]),
        kind=str(raw.get("kind", "semantic")),
        importance=float(raw.get("importance", 0.8)),
        metadata=metadata,
    )


def load_memory_benchmark(path: Path) -> list[RetrievalCase]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    cases: list[RetrievalCase] = []
    for row in payload["tasks"]:
        cases.append(
            RetrievalCase(
                id=str(row["id"]),
                query=str(row["query"]),
                memories=tuple(_memory_from_raw(item) for item in row["memories"]),
                expected_keywords=tuple(str(item) for item in row["expected_keywords"]),
                language=str(row.get("language", "en")),
                category=str(row.get("category", "memory_benchmark_v0")),
            )
        )
    return cases


def load_chinese_retrieval_jsonl(path: Path) -> list[RetrievalCase]:
    cases: list[RetrievalCase] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        cases.append(
            RetrievalCase(
                id=str(row["id"]),
                query=str(row["query"]),
                memories=tuple(_memory_from_raw(item) for item in row["memories"]),
                expected_keywords=tuple(str(item) for item in row["expected_keywords"]),
                language="zh",
                category=str(row.get("category", "zh_memory_retrieval_v2")),
            )
        )
    return cases


def load_default_cases(repo_root: Path) -> list[RetrievalCase]:
    return [
        *load_memory_benchmark(repo_root / "benchmarks/fixtures/memory_benchmark_v0.json"),
        *load_chinese_retrieval_jsonl(repo_root / "evals/data/zh_memory_retrieval_v2.jsonl"),
    ]
