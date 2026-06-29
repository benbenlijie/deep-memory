from __future__ import annotations

import argparse
import builtins
import hashlib
import importlib.util
import json
import platform
import statistics
import struct
import sys
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from deep_memory import DeepMemory

SCHEMA_VERSION = 1
DEFAULT_SIZES = (1_000, 10_000, 50_000)
DEFAULT_DIMENSIONS = 512
DEFAULT_ITERATIONS = 20


@dataclass(frozen=True)
class EvalConfig:
    sizes: tuple[int, ...] = DEFAULT_SIZES
    dimensions: int = DEFAULT_DIMENSIONS
    latency_iterations: int = DEFAULT_ITERATIONS
    output_json: Path | None = None
    output_markdown: Path | None = None


class PrelaunchEmbeddingBackend:
    model_name = "prelaunch-deterministic"
    model_version = 1

    def __init__(self, dimensions: int) -> None:
        self.dimensions = dimensions

    def embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        normalized = text.lower()
        groups = [
            (0, ("target", "testing", "playbook", "unique-anchor", "测试", "流程")),
            (1, ("workspace-a", "alpha")),
            (2, ("workspace-b", "beta")),
            (3, ("deprecated", "superseded", "archived")),
            (4, ("deploy", "部署", "release", "shipping")),
            (5, ("config", "settings", "配置")),
        ]
        matched = False
        for index, terms in groups:
            if index < self.dimensions and any(term in normalized for term in terms):
                vector[index] = 1.0
                matched = True
        if not matched:
            digest = hashlib.sha256(normalized.encode("utf-8")).digest()
            stable_hash = int.from_bytes(digest[:8], "big")
            index = (stable_hash % max(1, self.dimensions - 8)) + min(8, self.dimensions - 1)
            vector[index % self.dimensions] = 1.0
        return vector

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self.embed(text) for text in texts]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _stats(samples_ms: list[float]) -> dict[str, float]:
    ordered = sorted(samples_ms)
    if not ordered:
        return {"p50_ms": 0.0, "p95_ms": 0.0, "p99_ms": 0.0, "mean_ms": 0.0}

    def percentile(p: float) -> float:
        index = round((len(ordered) - 1) * p)
        return ordered[max(0, min(len(ordered) - 1, index))]

    return {
        "p50_ms": round(percentile(0.50), 3),
        "p95_ms": round(percentile(0.95), 3),
        "p99_ms": round(percentile(0.99), 3),
        "mean_ms": round(statistics.fmean(ordered), 3),
    }


def _environment() -> dict[str, Any]:
    return {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "numpy_available": importlib.util.find_spec("numpy") is not None,
        "sentence_transformers_available": importlib.util.find_spec("sentence_transformers") is not None,
    }


def _memory_tuple(
    memory_id: str,
    content: str,
    *,
    kind: str = "semantic",
    importance: float = 0.5,
    confidence: float = 0.8,
    conflict_status: str = "active",
    scope: str = "global",
    workspace: str | None = None,
    model_name: str | None = None,
    model_version: int | None = None,
) -> tuple[Any, ...]:
    now = _now()
    return (
        memory_id, content, kind, importance, confidence, "prelaunch-eval",
        now, now, now, now, None, None, conflict_status, None, None,
        scope, workspace, None, None, None, None, model_name, model_version,
        0.5, 1.0, now,
    )


def _insert_memories(mem: DeepMemory, rows: Iterable[tuple[Any, ...]]) -> None:
    mem.conn.executemany(
        """
        INSERT INTO memories (
            id, content, kind, importance, confidence, source,
            created_at, updated_at, learned_at, event_time, valid_until, expires_at,
            conflict_status, supersedes_id, superseded_by_id, scope, workspace, tenant,
            user_id, agent, idempotency_key, embedding_model, embedding_version,
            baseline_trust, reputation, reputation_updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        list(rows),
    )


def _insert_embeddings(mem: DeepMemory, backend: PrelaunchEmbeddingBackend, rows: Iterable[tuple[str, str]]) -> None:
    now = _now()
    embedding_rows = [
        (
            memory_id,
            struct.pack(f"<{backend.dimensions}f", *backend.embed(content)),
            backend.model_name,
            backend.model_version,
            backend.dimensions,
            now,
        )
        for memory_id, content in rows
    ]
    mem.conn.executemany(
        """
        INSERT INTO memory_embeddings (memory_id, embedding, model_name, model_version, dim, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        embedding_rows,
    )
    mem.conn.commit()


def _seed_eval_db(mem: DeepMemory, backend: PrelaunchEmbeddingBackend, size: int) -> None:
    special_rows = [
        ("known-target", "target testing playbook unique-anchor memory for regression verification", "active", "global", None),
        ("workspace-a", "workspace-a alpha deployment runbook", "active", "workspace", "workspace-a"),
        ("workspace-b", "workspace-b beta deployment runbook", "active", "workspace", "workspace-b"),
        ("deprecated-old", "deprecated testing playbook old memory", "deprecated", "global", None),
        ("superseded-old", "superseded testing playbook old memory", "superseded", "global", None),
        ("archived-old", "archived testing playbook old memory", "archived", "global", None),
        ("mixed-language", "部署 release playbook for mixed Chinese English query", "active", "global", None),
    ]
    rows: list[tuple[Any, ...]] = []
    embedding_inputs: list[tuple[str, str]] = []
    for idx in range(max(0, size - len(special_rows))):
        memory_id = f"mem-{idx:06d}"
        content = f"background memory {idx}: project note about docs config storage"
        rows.append(_memory_tuple(memory_id, content, model_name=backend.model_name, model_version=backend.model_version))
        embedding_inputs.append((memory_id, content))
    for memory_id, content, status, scope, workspace in special_rows:
        rows.append(_memory_tuple(memory_id, content, importance=0.95, conflict_status=status, scope=scope, workspace=workspace, model_name=backend.model_name, model_version=backend.model_version))
        embedding_inputs.append((memory_id, content))
    _insert_memories(mem, rows)
    _insert_embeddings(mem, backend, embedding_inputs)


def _ids(results: list[Any]) -> list[str]:
    return [result.record.id for result in results]


def _measure_latency(mem: DeepMemory, iterations: int) -> dict[str, Any]:
    query = "target testing playbook"
    latency: dict[str, Any] = {}
    for mode in ("fts5", "vector", "hybrid"):
        start = time.perf_counter()
        mem.search(query, limit=5, retrieval_mode=mode, cross_workspace=True)
        cold_ms = (time.perf_counter() - start) * 1000
        warm_samples = []
        for _ in range(iterations):
            start = time.perf_counter()
            mem.search(query, limit=5, retrieval_mode=mode, cross_workspace=True)
            warm_samples.append((time.perf_counter() - start) * 1000)
        latency[mode] = {"cold_ms": round(cold_ms, 3), "warm": _stats(warm_samples)}
    return latency


def _evaluate_correctness(mem: DeepMemory) -> dict[str, Any]:
    known = mem.search("unique-anchor", limit=5, retrieval_mode="hybrid", cross_workspace=True)
    workspace_a = mem.search("deployment runbook", limit=5, retrieval_mode="hybrid", workspace="workspace-a", include_global=False)
    workspace_b = mem.search("deployment runbook", limit=5, retrieval_mode="hybrid", workspace="workspace-b", include_global=False)
    lifecycle = mem.search("deprecated superseded archived testing playbook", limit=10, retrieval_mode="hybrid", cross_workspace=True)
    mixed = mem.search("部署 shipping checklist", limit=5, retrieval_mode="hybrid", cross_workspace=True)
    lifecycle_ids = set(_ids(lifecycle))
    return {
        "known_target_top1": {"passed": bool(known and known[0].record.id == "known-target"), "top_ids": _ids(known)},
        "known_target_top5": {"passed": "known-target" in _ids(known), "top_ids": _ids(known)},
        "scope_isolation": {
            "passed": bool(workspace_a and workspace_b and workspace_a[0].record.id == "workspace-a" and workspace_b[0].record.id == "workspace-b"),
            "workspace_a_top_ids": _ids(workspace_a),
            "workspace_b_top_ids": _ids(workspace_b),
        },
        "lifecycle_filtering": {
            "passed": not {"deprecated-old", "superseded-old", "archived-old"} & lifecycle_ids,
            "top_ids": _ids(lifecycle),
        },
        "mixed_language_hybrid": {"passed": "mixed-language" in _ids(mixed), "top_ids": _ids(mixed)},
    }


def _measure_backfill(size: int, dimensions: int) -> dict[str, float | int]:
    backend = PrelaunchEmbeddingBackend(dimensions)
    with tempfile.TemporaryDirectory() as tmp:
        mem = DeepMemory(Path(tmp) / "backfill.db", embedding_backend=backend)
        rows = [
            _memory_tuple(f"backfill-{idx:06d}", f"backfill memory {idx} config", model_name=None, model_version=None)
            for idx in range(size)
        ]
        _insert_memories(mem, rows)
        mem.conn.commit()
        start = time.perf_counter()
        result = mem.backfill_embeddings(batch_size=1000)
        elapsed = time.perf_counter() - start
        mem.close()
    return {
        "seconds": round(elapsed, 3),
        "rows_per_second": round(size / elapsed, 3) if elapsed else float(size),
        "scanned": result.scanned,
        "backfilled": result.backfilled,
        "skipped": result.skipped,
    }


def _memory_usage(mem: DeepMemory, db_path: Path) -> dict[str, int]:
    row = mem.conn.execute("SELECT COUNT(*), COALESCE(SUM(LENGTH(embedding)), 0) FROM memory_embeddings").fetchone()
    return {
        "db_bytes": db_path.stat().st_size,
        "embedding_rows": int(row[0]),
        "embedding_blob_bytes": int(row[1]),
    }


def _evaluate_reproducibility(mem: DeepMemory) -> dict[str, Any]:
    runs = [
        _ids(mem.search("target testing playbook", limit=5, retrieval_mode="hybrid", cross_workspace=True))
        for _ in range(2)
    ]
    return {"runs": runs, "stable_top1": bool(runs[0] and runs[1] and runs[0][0] == runs[1][0])}


def _evaluate_fallback(mem: DeepMemory) -> dict[str, Any]:
    original_import = builtins.__import__

    def guarded_import(name: str, *args: Any, **kwargs: Any) -> Any:
        if name == "numpy":
            raise ImportError("simulated missing numpy")
        return original_import(name, *args, **kwargs)

    mem._invalidate_vector_search_cache()
    builtins.__import__ = guarded_import
    try:
        cached = mem._build_vector_search_cache([])
        results = mem.search("target testing playbook", limit=5, retrieval_mode="auto", cross_workspace=True)
    finally:
        builtins.__import__ = original_import
        mem._invalidate_vector_search_cache()
    return {
        "no_numpy_functional": {"passed": bool(results), "top_ids": _ids(results)},
        "empty_cache_shape": [len(cached[0]), cached[1], cached[2]],
    }


def _evaluate_size(size: int, config: EvalConfig) -> dict[str, Any]:
    backend = PrelaunchEmbeddingBackend(config.dimensions)
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / f"prelaunch-{size}.db"
        mem = DeepMemory(db_path, embedding_backend=backend)
        seed_start = time.perf_counter()
        _seed_eval_db(mem, backend, size)
        seed_seconds = time.perf_counter() - seed_start
        result = {
            "seed": {"seconds": round(seed_seconds, 3), "rows_per_second": round(size / seed_seconds, 3) if seed_seconds else float(size)},
            "latency": _measure_latency(mem, config.latency_iterations),
            "correctness": _evaluate_correctness(mem),
            "backfill": _measure_backfill(size, config.dimensions),
            "memory_usage": _memory_usage(mem, db_path),
            "reproducibility": _evaluate_reproducibility(mem),
            "fallback": _evaluate_fallback(mem),
        }
        mem.close()
    return result


def build_markdown_report(result: dict[str, Any]) -> str:
    lines = [
        "# Pre-launch eval report",
        "",
        "This report checks whether `deep-memory` is fast, correct, stable, and reproducible at launch-relevant corpus sizes.",
        "",
        "## Environment",
        "",
    ]
    env = result["environment"]
    lines.extend([
        f"- Python: `{env['python']}`",
        f"- Platform: `{env['platform']}`",
        f"- NumPy available: `{env['numpy_available']}`",
        f"- sentence-transformers available: `{env['sentence_transformers_available']}`",
        "",
        "## Search latency",
        "",
        "| Size | Mode | Cold ms | Warm p50 | Warm p95 | Warm p99 | Warm mean |",
        "| ---: | --- | ---: | ---: | ---: | ---: | ---: |",
    ])
    for size, payload in result["sizes"].items():
        for mode, stats in payload["latency"].items():
            warm = stats["warm"]
            lines.append(f"| {size} | {mode} | {stats['cold_ms']:.3f} | {warm['p50_ms']:.3f} | {warm['p95_ms']:.3f} | {warm['p99_ms']:.3f} | {warm['mean_ms']:.3f} |")
    lines.extend(["", "## Correctness gate", "", "| Size | Check | Pass | Evidence |", "| ---: | --- | --- | --- |"])
    for size, payload in result["sizes"].items():
        for check, evidence in payload["correctness"].items():
            lines.append(f"| {size} | {check} | `{evidence['passed']}` | `{json.dumps(evidence, ensure_ascii=False)}` |")
    lines.extend(["", "## Backfill and memory usage", "", "| Size | Seed rows/s | Backfill rows/s | DB bytes | Embedding rows | Embedding blob bytes |", "| ---: | ---: | ---: | ---: | ---: | ---: |"])
    for size, payload in result["sizes"].items():
        lines.append(f"| {size} | {payload['seed']['rows_per_second']:.3f} | {payload['backfill']['rows_per_second']:.3f} | {payload['memory_usage']['db_bytes']} | {payload['memory_usage']['embedding_rows']} | {payload['memory_usage']['embedding_blob_bytes']} |")
    lines.extend(["", "## Stability and fallback", "", "| Size | Stable top1 | Fallback functional |", "| ---: | --- | --- |"])
    for size, payload in result["sizes"].items():
        lines.append(f"| {size} | `{payload['reproducibility']['stable_top1']}` | `{payload['fallback']['no_numpy_functional']['passed']}` |")
    lines.extend([
        "",
        "## Launch-safe claims",
        "",
        "- The deterministic pre-launch gate covers 1k/10k/50k corpus sizes with FTS5, vector, and hybrid retrieval.",
        "- Correctness checks cover known-target retrieval, scope isolation, lifecycle filtering, mixed-language hybrid retrieval, reproducibility, and fallback behavior.",
        "- This is a deterministic local eval, not a replacement for real-user corpus evaluation or hosted production load testing.",
    ])
    return "\n".join(lines) + "\n"


def run_eval(config: EvalConfig | None = None) -> dict[str, Any]:
    config = config or EvalConfig()
    result: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "environment": _environment(),
        "config": {"sizes": list(config.sizes), "dimensions": config.dimensions, "latency_iterations": config.latency_iterations},
        "sizes": {},
    }
    for size in config.sizes:
        result["sizes"][str(size)] = _evaluate_size(size, config)
    if config.output_json is not None:
        config.output_json.parent.mkdir(parents=True, exist_ok=True)
        config.output_json.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    if config.output_markdown is not None:
        config.output_markdown.parent.mkdir(parents=True, exist_ok=True)
        config.output_markdown.write_text(build_markdown_report(result), encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Run deep-memory pre-launch large-scale eval gate.")
    parser.add_argument("--sizes", default="1000,10000,50000")
    parser.add_argument("--dimensions", type=int, default=DEFAULT_DIMENSIONS)
    parser.add_argument("--iterations", type=int, default=DEFAULT_ITERATIONS)
    parser.add_argument("--json", type=Path, default=Path("docs/prelaunch_eval_results.json"))
    parser.add_argument("--markdown", type=Path, default=Path("docs/PRELAUNCH_EVAL_REPORT.md"))
    args = parser.parse_args()
    sizes = tuple(int(part.strip()) for part in args.sizes.split(",") if part.strip())
    result = run_eval(EvalConfig(sizes=sizes, dimensions=args.dimensions, latency_iterations=args.iterations, output_json=args.json, output_markdown=args.markdown))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
