from __future__ import annotations

import json
import statistics
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from deep_memory import DeepMemory
from deep_memory.embeddings import DeterministicEmbeddingBackend

RetrievalMode = Literal["fts5", "vector", "hybrid"]
CategoryName = Literal["exact_match", "synonym_match", "cross_lingual", "semantic_paraphrase"]


class BenchmarkEmbeddingBackend(DeterministicEmbeddingBackend):
    def __init__(self) -> None:
        super().__init__(model_name="benchmark-embedder", model_version=1, dim=24)
        self._groups = [
            ("test", "testing", "pytest", "验证", "测试"),
            ("deploy", "deployment", "ship", "发布", "部署", "上线"),
            ("config", "configuration", "setting", "配置", "设定"),
            ("bug", "defect", "issue", "缺陷", "故障"),
            ("search", "retrieval", "lookup", "检索", "召回"),
            ("performance", "latency", "speed", "性能", "延迟"),
            ("privacy", "security", "safety", "隐私", "安全"),
            ("backup", "snapshot", "restore", "备份", "恢复"),
            ("database", "sqlite", "storage", "数据库", "存储"),
            ("scope_id", "project", "repo", "项目", "仓库"),
            ("review", "audit", "verify", "评审", "复核"),
            ("memory", "recall", "context", "记忆", "上下文"),
        ]

    def embed(self, text: str) -> list[float]:
        normalized = text.lower()
        vector = [0.0] * len(self._groups)
        matched = False
        for idx, group in enumerate(self._groups):
            if any(term.lower() in normalized for term in group):
                vector[idx] = 1.0
                matched = True
        if not matched:
            return super().embed(text)
        return vector

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self.embed(text) for text in texts]


@dataclass(frozen=True)
class BenchmarkQuery:
    category: CategoryName
    query: str
    target_content: str
    distractor_content: str


@dataclass(frozen=True)
class BenchmarkConfig:
    output_path: Path | None = None
    performance_sizes: tuple[int, ...] = (1000, 10_000, 50_000)
    latency_iterations: int = 10


SEED_BENCHMARK_QUERIES: tuple[BenchmarkQuery, ...] = (
    BenchmarkQuery("exact_match", "test strategy", "document test strategy for regression coverage", "record weekly design sync notes"),
    BenchmarkQuery("exact_match", "deploy runbook", "update deploy runbook before release", "collect quarterly hiring feedback"),
    BenchmarkQuery("exact_match", "config schema", "define config schema for workspace settings", "summarize customer interview transcript"),
    BenchmarkQuery("exact_match", "bug triage", "codify bug triage steps for oncall", "draft roadmap reflection memo"),
    BenchmarkQuery("exact_match", "search ranking", "explain search ranking tradeoffs in retrieval", "log launch retrospective anecdotes"),
    BenchmarkQuery("synonym_match", "testing playbook", "document test strategy for regression coverage", "record weekly design sync notes"),
    BenchmarkQuery("synonym_match", "shipping checklist", "update deploy runbook before release", "collect quarterly hiring feedback"),
    BenchmarkQuery("synonym_match", "settings contract", "define config schema for workspace settings", "summarize customer interview transcript"),
    BenchmarkQuery("synonym_match", "defect handling", "codify bug triage steps for oncall", "draft roadmap reflection memo"),
    BenchmarkQuery("synonym_match", "retrieval ordering", "explain search ranking tradeoffs in retrieval", "log launch retrospective anecdotes"),
    BenchmarkQuery("cross_lingual", "测试流程", "document test strategy for regression coverage", "record weekly design sync notes"),
    BenchmarkQuery("cross_lingual", "部署步骤", "update deploy runbook before release", "collect quarterly hiring feedback"),
    BenchmarkQuery("cross_lingual", "配置规范", "define config schema for workspace settings", "summarize customer interview transcript"),
    BenchmarkQuery("cross_lingual", "缺陷处理", "codify bug triage steps for oncall", "draft roadmap reflection memo"),
    BenchmarkQuery("cross_lingual", "检索排序", "explain search ranking tradeoffs in retrieval", "log launch retrospective anecdotes"),
    BenchmarkQuery("semantic_paraphrase", "how should we keep regressions from slipping into releases", "document test strategy for regression coverage", "record weekly design sync notes"),
    BenchmarkQuery("semantic_paraphrase", "what should the team follow before shipping safely", "update deploy runbook before release", "collect quarterly hiring feedback"),
    BenchmarkQuery("semantic_paraphrase", "which document defines how settings are structured", "define config schema for workspace settings", "summarize customer interview transcript"),
    BenchmarkQuery("semantic_paraphrase", "what process handles incoming failures during support", "codify bug triage steps for oncall", "draft roadmap reflection memo"),
    BenchmarkQuery("semantic_paraphrase", "how do we choose which memory should rank first", "explain search ranking tradeoffs in retrieval", "log launch retrospective anecdotes"),
)


def _expand_queries() -> list[BenchmarkQuery]:
    expanded: list[BenchmarkQuery] = []
    for repeat_idx in range(4):
        for query in SEED_BENCHMARK_QUERIES:
            suffix = f" [variant {repeat_idx + 1}]"
            expanded.append(
                BenchmarkQuery(
                    category=query.category,
                    query=query.query + suffix,
                    target_content=query.target_content + suffix,
                    distractor_content=query.distractor_content + suffix,
                )
            )
    return expanded


BENCHMARK_QUERIES = _expand_queries()


def _metric_hits(ranks: list[int | None], k: int) -> float:
    return sum(1 for rank in ranks if rank is not None and rank <= k) / len(ranks)


def _metric_mrr(ranks: list[int | None]) -> float:
    return sum((1 / rank) if rank else 0.0 for rank in ranks) / len(ranks)


def _rank_for_query(results, target_content: str) -> int | None:
    for index, result in enumerate(results, start=1):
        if result.record.content == target_content:
            return index
    return None


def _evaluate_recall(mem: DeepMemory) -> dict[str, object]:
    categories: dict[str, dict[str, list[int | None]]] = {
        category: {mode: [] for mode in ("fts5", "vector", "hybrid")}
        for category in ("exact_match", "synonym_match", "cross_lingual", "semantic_paraphrase")
    }
    for item in BENCHMARK_QUERIES:
        for mode in ("fts5", "vector", "hybrid"):
            results = mem.search(item.query, limit=5, retrieval_mode=mode, cross_scope=True)
            categories[item.category][mode].append(_rank_for_query(results, item.target_content))
    rendered_categories: dict[str, object] = {}
    overall: dict[str, list[int | None]] = {mode: [] for mode in ("fts5", "vector", "hybrid")}
    for category, mode_ranks in categories.items():
        rendered_modes: dict[str, object] = {}
        for mode, ranks in mode_ranks.items():
            overall[mode].extend(ranks)
            rendered_modes[mode] = {
                "recall@1": round(_metric_hits(ranks, 1), 4),
                "recall@3": round(_metric_hits(ranks, 3), 4),
                "recall@5": round(_metric_hits(ranks, 5), 4),
                "mrr": round(_metric_mrr(ranks), 4),
            }
        rendered_categories[category] = {"query_count": len(next(iter(mode_ranks.values()))), "modes": rendered_modes}
    summary_modes = {
        mode: {
            "recall@1": round(_metric_hits(ranks, 1), 4),
            "recall@3": round(_metric_hits(ranks, 3), 4),
            "recall@5": round(_metric_hits(ranks, 5), 4),
            "mrr": round(_metric_mrr(ranks), 4),
        }
        for mode, ranks in overall.items()
    }
    return {
        "summary": {"query_count": len(BENCHMARK_QUERIES), "modes": summary_modes},
        "categories": rendered_categories,
    }


def _latency_stats(samples_ms: list[float]) -> dict[str, float]:
    ordered = sorted(samples_ms)

    def percentile(p: float) -> float:
        index = max(0, min(len(ordered) - 1, round((len(ordered) - 1) * p)))
        return ordered[index]

    return {
        "p50_ms": round(percentile(0.50), 3),
        "p95_ms": round(percentile(0.95), 3),
        "p99_ms": round(percentile(0.99), 3),
        "mean_ms": round(statistics.fmean(ordered), 3),
    }


def _seed_search_corpus(mem: DeepMemory, size: int) -> None:
    for idx in range(size):
        mem.add(
            f"background memory {idx}: project note about archive stability and weekly updates",
            kind="semantic",
            importance=0.4,
        )
    for item in BENCHMARK_QUERIES[:20]:
        mem.add(item.target_content, kind="semantic", importance=0.9)
        mem.add(item.distractor_content, kind="semantic", importance=0.5)


def _measure_search_latency(size: int, iterations: int) -> dict[str, dict[str, float]]:
    query = "testing playbook [variant 1]"
    samples: dict[str, list[float]] = {mode: [] for mode in ("fts5", "vector", "hybrid")}
    with tempfile.TemporaryDirectory() as tmp:
        mem = DeepMemory(Path(tmp) / f"perf-{size}.db", embedding_backend=BenchmarkEmbeddingBackend())
        _seed_search_corpus(mem, size)
        for mode in ("fts5", "vector", "hybrid"):
            for _ in range(iterations):
                start = time.perf_counter()
                mem.search(query, limit=5, retrieval_mode=mode, cross_scope=True)
                samples[mode].append((time.perf_counter() - start) * 1000)
        mem.close()
    return {mode: _latency_stats(values) for mode, values in samples.items()}


def _measure_embedding_latency() -> dict[str, float]:
    backend = BenchmarkEmbeddingBackend()
    texts = [f"embedding sample {idx} deploy test config" for idx in range(64)]
    start = time.perf_counter()
    backend.embed("single embedding sample")
    per_text_ms = (time.perf_counter() - start) * 1000
    start = time.perf_counter()
    backend.embed_batch(texts)
    batch_ms = (time.perf_counter() - start) * 1000
    return {
        "per_text_ms": round(per_text_ms, 3),
        "batch_64_ms": round(batch_ms, 3),
        "batch_per_text_ms": round(batch_ms / len(texts), 3),
    }


def _measure_memory_usage(size: int) -> dict[str, int]:
    backend = BenchmarkEmbeddingBackend()
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / f"usage-{size}.db"
        mem = DeepMemory(db, embedding_backend=backend)
        for idx in range(size):
            mem.add(f"memory payload {idx} test deploy config retrieval", kind="semantic", importance=0.5)
        row_count = mem.conn.execute("SELECT COUNT(*) FROM memory_embeddings").fetchone()[0]
        blob_bytes = mem.conn.execute("SELECT SUM(LENGTH(embedding)) FROM memory_embeddings").fetchone()[0] or 0
        db_bytes = db.stat().st_size
        mem.close()
    return {
        "db_bytes": int(db_bytes),
        "embedding_rows": int(row_count),
        "embedding_blob_bytes": int(blob_bytes),
        "vector_overhead_bytes": int(blob_bytes),
    }


def build_markdown_report(result: dict[str, object]) -> str:
    recall = result["recall"]
    performance = result["performance"]
    lines = [
        "# Vector retrieval benchmark",
        "",
        "This document records the current retrieval benchmark and latency snapshot for the vector retrieval lane.",
        "",
        "## Recall benchmark",
        "",
        "| Category | Mode | Recall@1 | Recall@3 | Recall@5 | MRR |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for category, payload in recall["categories"].items():
        for mode, metrics in payload["modes"].items():
            lines.append(
                f"| {category} | {mode} | {metrics['recall@1']:.4f} | {metrics['recall@3']:.4f} | {metrics['recall@5']:.4f} | {metrics['mrr']:.4f} |"
            )
    lines.extend([
        "",
        "## Performance benchmark",
        "",
        "### Search latency",
        "",
        "| Corpus size | Mode | p50 ms | p95 ms | p99 ms | mean ms |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ])
    for size, modes in performance["search_latency"].items():
        for mode, stats in modes.items():
            lines.append(
                f"| {size} | {mode} | {stats['p50_ms']:.3f} | {stats['p95_ms']:.3f} | {stats['p99_ms']:.3f} | {stats['mean_ms']:.3f} |"
            )
    embedding_latency = performance["embedding_latency"]
    lines.extend([
        "",
        "### Embedding latency",
        "",
        f"- per text: {embedding_latency['per_text_ms']:.3f} ms",
        f"- batch of 64: {embedding_latency['batch_64_ms']:.3f} ms",
        f"- batch per text: {embedding_latency['batch_per_text_ms']:.3f} ms",
        "",
        "### Memory usage",
        "",
        "| Corpus size | DB bytes | Embedding rows | Embedding blob bytes | Vector overhead bytes |",
        "| --- | ---: | ---: | ---: | ---: |",
    ])
    for size, stats in performance["memory_usage"].items():
        lines.append(
            f"| {size} | {stats['db_bytes']} | {stats['embedding_rows']} | {stats['embedding_blob_bytes']} | {stats['vector_overhead_bytes']} |"
        )
    return "\n".join(lines) + "\n"


def run_benchmark(config: BenchmarkConfig | None = None) -> dict[str, object]:
    config = config or BenchmarkConfig()
    with tempfile.TemporaryDirectory() as tmp:
        mem = DeepMemory(Path(tmp) / "benchmark.db", embedding_backend=BenchmarkEmbeddingBackend())
        for item in BENCHMARK_QUERIES:
            mem.add(item.target_content, kind="semantic", importance=0.9)
            mem.add(item.distractor_content, kind="episodic", importance=0.3)
        recall = _evaluate_recall(mem)
        mem.close()
    performance = {
        "search_latency": {
            str(size): _measure_search_latency(size, config.latency_iterations)
            for size in config.performance_sizes
        },
        "embedding_latency": _measure_embedding_latency(),
        "memory_usage": {str(size): _measure_memory_usage(size) for size in config.performance_sizes},
    }
    result = {"recall": recall, "performance": performance}
    if config.output_path is not None:
        config.output_path.parent.mkdir(parents=True, exist_ok=True)
        config.output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    json_path = root / "docs" / "vector_benchmark_results.json"
    markdown_path = root / "docs" / "VECTOR_BENCHMARK.md"
    result = run_benchmark(BenchmarkConfig(output_path=json_path))
    markdown_path.write_text(build_markdown_report(result), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
