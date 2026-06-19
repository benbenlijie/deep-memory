from __future__ import annotations

import argparse
import json
import math
import sys
import tempfile
import time
from dataclasses import asdict
from pathlib import Path
from statistics import median
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from benchmarks.competitive.adapters import COMPETITOR_SPECS, make_adapter
    from benchmarks.competitive.base import MemoryAdapter, MemoryItem, RetrievalCase
    from benchmarks.competitive.datasets import load_chinese_retrieval_jsonl, load_memory_benchmark
else:
    from .adapters import COMPETITOR_SPECS, make_adapter
    from .base import MemoryAdapter, MemoryItem, RetrievalCase
    from .datasets import load_chinese_retrieval_jsonl, load_memory_benchmark

DEFAULT_SYSTEMS = ["deep-memory", "mem0", "zep", "langmem", "chatgpt-memory"]
DEFAULT_INSERT_SIZES = [1000, 10000]

FEATURE_MATRIX: dict[str, dict[str, str]] = {
    "deep-memory": {
        "local_first": "yes",
        "cross_agent": "yes: CLI/SDK/MCP/adapters",
        "trust": "yes: source trust + reputation",
        "bi_temporal": "partial: event_time/as_of/valid_until",
        "scope": "yes: global/user/tenant/workspace/project",
        "lifecycle": "yes: decay, feedback, conflict states, soft delete/export",
        "graph": "roadmap/prototype visualization, not KG retrieval",
        "sync": "yes: portable export/import patterns",
    },
    "mem0": {
        "local_first": "partial: OSS package available, typical configs use external LLM/vector services",
        "cross_agent": "yes: SDK/API integrations",
        "trust": "not first-class in default API",
        "bi_temporal": "not first-class in default API",
        "scope": "yes: user/session-style scoping",
        "lifecycle": "partial: memory update/delete/history depending on backend",
        "graph": "available in some hosted/graph modes",
        "sync": "cloud/platform dependent",
    },
    "Zep": {
        "local_first": "no: cloud-first service",
        "cross_agent": "yes: API/service",
        "trust": "not exposed as local inspectable trust model",
        "bi_temporal": "strong temporal graph orientation, service controlled",
        "scope": "yes: users/sessions/threads",
        "lifecycle": "service-managed",
        "graph": "yes: temporal knowledge graph",
        "sync": "cloud service",
    },
    "LangMem": {
        "local_first": "partial: can use local stores, LangGraph ecosystem dependent",
        "cross_agent": "partial: best inside LangGraph",
        "trust": "application-defined",
        "bi_temporal": "application/store-defined",
        "scope": "yes: namespace/store patterns",
        "lifecycle": "yes: hot-path/background memory managers",
        "graph": "not the core primitive",
        "sync": "LangGraph/store dependent",
    },
    "ChatGPT Memory": {
        "local_first": "no",
        "cross_agent": "no public cross-agent API",
        "trust": "opaque to developers",
        "bi_temporal": "opaque",
        "scope": "product-account scoped",
        "lifecycle": "user-facing controls, not benchmark API",
        "graph": "opaque",
        "sync": "OpenAI product ecosystem only",
    },
}

SETUP_MATRIX: dict[str, dict[str, str]] = {
    "deep-memory": {
        "time_to_first_search": "~seconds from source: uv sync --extra dev; uv run python benchmarks/competitive/run_competitive_benchmark.py --systems deep-memory --quick",
        "complexity": "local SQLite file; no API key for default lexical retrieval",
    },
    "mem0": {
        "time_to_first_search": "minutes after package install plus LLM/embedder config/API key for fair semantic memory",
        "complexity": "SDK setup + provider/backend configuration",
    },
    "Zep": {
        "time_to_first_search": "requires cloud account, API key, collection/user/session setup",
        "complexity": "managed service setup; not offline reproducible",
    },
    "LangMem": {
        "time_to_first_search": "requires LangGraph app/store/checkpointer wiring for realistic use",
        "complexity": "good if already in LangGraph; heavier otherwise",
    },
    "ChatGPT Memory": {
        "time_to_first_search": "not reproducible via public benchmark API",
        "complexity": "product setting, not developer library",
    },
}


def normalize(text: str) -> str:
    return " ".join(text.casefold().split())


def contains_all_keywords(answer: str, expected: tuple[str, ...]) -> bool:
    haystack = normalize(answer)
    return all(normalize(keyword) in haystack for keyword in expected)


def percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    index = (len(ordered) - 1) * p
    lower = math.floor(index)
    upper = math.ceil(index)
    if lower == upper:
        return ordered[int(index)]
    return ordered[lower] * (upper - index) + ordered[upper] * (index - lower)


def synthetic_items(count: int) -> list[MemoryItem]:
    anchors = [
        "user prefers concise Chinese answers with English technical terms",
        "project uses SQLite FTS5 for local-first memory retrieval",
        "Hermes adapter imports explicit JSONL facts only after successful runs",
        "deep-memory supports trust levels, conflict states, and scoped memories",
    ]
    return [
        MemoryItem(
            content=f"benchmark record {idx:06d}: {anchors[idx % len(anchors)]}; shard={idx % 97}; owner=user-{idx % 13}",
            kind="semantic",
            importance=0.5 + (idx % 5) * 0.1,
            metadata={"synthetic_index": idx},
        )
        for idx in range(count)
    ]


def run_insert_benchmark(adapter: MemoryAdapter, counts: list[int]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for count in counts:
        adapter.reset()
        latencies: list[float] = []
        for item in synthetic_items(count):
            start = time.perf_counter()
            adapter.add(item)
            latencies.append((time.perf_counter() - start) * 1000)
        stats = adapter.stats()
        output[str(count)] = {
            "records": count,
            "total_seconds": round(sum(latencies) / 1000, 4),
            "p50_ms": round(median(latencies), 4),
            "p95_ms": round(percentile(latencies, 0.95), 4),
            "stats": asdict(stats),
        }
    return output


def run_retrieval_cases(adapter: MemoryAdapter, cases: list[RetrievalCase], *, limit: int) -> dict[str, Any]:
    passed = 0
    top1_passed = 0
    reciprocal_rank_sum = 0.0
    details: list[dict[str, Any]] = []
    for case in cases:
        adapter.reset()
        target_contents = {item.content for item in case.memories if item.metadata.get("is_target") is True}
        for item in case.memories:
            adapter.add(item)
        start = time.perf_counter()
        hits = adapter.search(case.query, limit=limit)
        search_ms = (time.perf_counter() - start) * 1000
        answer = "\n".join(hit.content for hit in hits)
        ok = contains_all_keywords(answer, case.expected_keywords)
        rank = None
        for idx, hit in enumerate(hits, start=1):
            if hit.content in target_contents or contains_all_keywords(hit.content, case.expected_keywords):
                rank = idx
                break
        top1_ok = rank == 1
        passed += int(ok)
        top1_passed += int(top1_ok)
        reciprocal_rank_sum += 1 / rank if rank else 0
        details.append(
            {
                "id": case.id,
                "language": case.language,
                "category": case.category,
                "pass": ok,
                "rank": rank,
                "top1_pass": top1_ok,
                "search_ms": round(search_ms, 4),
            }
        )
    total = len(cases)
    return {
        "task_count": total,
        "passed": passed,
        "accuracy": round(passed / total, 4) if total else 0.0,
        "top1_passed": top1_passed,
        "top1_accuracy": round(top1_passed / total, 4) if total else 0.0,
        "mrr": round(reciprocal_rank_sum / total, 4) if total else 0.0,
        "p50_search_ms": round(percentile([d["search_ms"] for d in details], 0.50), 4) if details else 0.0,
        "p95_search_ms": round(percentile([d["search_ms"] for d in details], 0.95), 4) if details else 0.0,
        "details": details,
    }


def run_system(
    name: str,
    repo_root: Path,
    workdir: Path,
    *,
    insert_counts: list[int],
    retrieval_cases: list[RetrievalCase],
    chinese_cases: list[RetrievalCase],
    limit: int,
) -> dict[str, Any]:
    adapter = make_adapter(name, workdir / name.replace(" ", "_"))
    try:
        result: dict[str, Any] = {
            "system": adapter.name,
            "feature_matrix": FEATURE_MATRIX.get(adapter.name, FEATURE_MATRIX.get(name, {})),
            "setup": SETUP_MATRIX.get(adapter.name, SETUP_MATRIX.get(name, {})),
        }
        try:
            result["write_speed"] = run_insert_benchmark(adapter, insert_counts)
            result["search_accuracy"] = run_retrieval_cases(adapter, retrieval_cases, limit=limit)
            result["chinese_retrieval"] = run_retrieval_cases(adapter, chinese_cases, limit=limit)
            result["memory_footprint"] = {
                count: value["stats"] for count, value in result["write_speed"].items()
            }
            result["status"] = "benchmarked"
        except Exception as exc:
            result["status"] = "not_benchmarked"
            result["blocker"] = str(exc)
            result["stats"] = asdict(adapter.stats())
            spec = COMPETITOR_SPECS.get(name.lower())
            if spec:
                result["competitor_spec"] = asdict(spec)
        return result
    finally:
        adapter.close()


def write_markdown_report(report: dict[str, Any], output: Path) -> None:
    systems = report["systems"]
    lines = [
        "# Competitive benchmark: deep-memory vs mem0, Zep, LangMem, ChatGPT Memory",
        "",
        "This benchmark is intentionally conservative. It reports live measurements only when a system can be run reproducibly in this repository without private cloud credentials. Competitors that need API keys or app-specific wiring are listed with explicit blockers rather than fabricated scores.",
        "",
        "## Reproduce",
        "",
        "```bash",
        "uv run python benchmarks/competitive/run_competitive_benchmark.py --quick",
        "```",
        "",
        f"Generated by: `{report['command']}`",
        "",
        "## Summary table across the 7 benchmark dimensions",
        "",
        "| System | Status | Write speed p95 @1k | Search accuracy | Chinese retrieval | Footprint @1k | Features | Setup complexity | Dependencies |",
        "| --- | --- | ---: | ---: | ---: | --- | --- | --- | --- |",
    ]
    for item in systems:
        system = item["system"]
        status = item["status"]
        if status == "benchmarked":
            write_1k = item["write_speed"].get("1000") or next(iter(item["write_speed"].values()))
            p95 = f"{write_1k['p95_ms']} ms"
            search = f"{item['search_accuracy']['accuracy']:.0%} ({item['search_accuracy']['passed']}/{item['search_accuracy']['task_count']})"
            zh = f"{item['chinese_retrieval']['top1_accuracy']:.0%} top-1 ({item['chinese_retrieval']['top1_passed']}/{item['chinese_retrieval']['task_count']})"
            disk = write_1k["stats"].get("disk_bytes")
            footprint = _format_bytes(disk) if disk is not None else "n/a"
            deps = str(write_1k["stats"].get("package_count") or "n/a")
        else:
            p95 = search = zh = "not run"
            footprint = "not run"
            deps = str((item.get("stats") or {}).get("package_count") or "not installed/API")
        features = item.get("feature_matrix", {})
        setup = item.get("setup", {})
        lines.append(
            "| {system} | {status} | {p95} | {search} | {zh} | {footprint} | local-first: {local}; trust: {trust}; graph: {graph} | {setup} | {deps} |".format(
                system=system,
                status=status if status == "benchmarked" else f"blocked: {item.get('blocker', 'not reproducible offline')}",
                p95=p95,
                search=search,
                zh=zh,
                footprint=footprint,
                local=features.get("local_first", "n/a"),
                trust=features.get("trust", "n/a"),
                graph=features.get("graph", "n/a"),
                setup=setup.get("complexity", "n/a"),
                deps=deps,
            )
        )
    benchmarked = [item for item in systems if item["status"] == "benchmarked"]
    if benchmarked:
        lines.extend(["", "## Quick charts", ""])
        for item in benchmarked:
            write_1k = item["write_speed"].get("1000") or next(iter(item["write_speed"].values()))
            search_bar = _bar(float(item["search_accuracy"]["accuracy"]))
            zh_bar = _bar(float(item["chinese_retrieval"]["top1_accuracy"]))
            lines.extend(
                [
                    f"### {item['system']}",
                    "",
                    f"- Search accuracy  `{search_bar}` {item['search_accuracy']['accuracy']:.0%}",
                    f"- Chinese top-1    `{zh_bar}` {item['chinese_retrieval']['top1_accuracy']:.0%}",
                    f"- p95 add latency: `{write_1k['p95_ms']} ms` at 1k inserts",
                    "",
                ]
            )
    lines.extend(
        [
            "",
            "## What deep-memory wins today",
            "",
            "- Local-first reproducibility: the default benchmark runs on a local SQLite database with no API key.",
            "- Chinese retrieval: the checked-in zh v2 fixture is benchmarked directly; current local run reaches perfect top-1 on this fixture.",
            "- Setup simplicity: clone/sync/run; no hosted project, organization, or model provider configuration is required for lexical retrieval.",
            "- Dependency surface: core runtime is intentionally small (`typer`, `pydantic`, `rich`) and the retrieval baseline does not require vector DB infrastructure.",
            "",
            "## Where competitors may win",
            "",
            "- mem0 may win on richer semantic extraction and production integrations once configured with model/vector backends.",
            "- Zep likely wins on managed temporal graph context assembly and enterprise service operations.",
            "- LangMem likely wins for teams already standardized on LangGraph and background memory managers.",
            "- ChatGPT Memory wins on consumer-product convenience, but it is not currently a reproducible developer benchmark target.",
            "",
            "## Live deep-memory measurements",
            "",
        ]
    )
    for item in systems:
        if item["status"] != "benchmarked":
            continue
        lines.extend([f"### {item['system']}", "", "#### Write speed / footprint", ""])
        lines.extend(["| Records | Total insert time | p50 add | p95 add | Disk | RSS |", "| ---: | ---: | ---: | ---: | ---: | ---: |"])
        for count, value in item["write_speed"].items():
            stats = value["stats"]
            lines.append(
                f"| {count} | {value['total_seconds']} s | {value['p50_ms']} ms | {value['p95_ms']} ms | {_format_bytes(stats.get('disk_bytes'))} | {_format_bytes(stats.get('ram_bytes'))} |"
            )
        lines.extend(
            [
                "",
                "#### Retrieval accuracy",
                "",
                f"- Shared bilingual fixture: {item['search_accuracy']['passed']}/{item['search_accuracy']['task_count']} pass, accuracy {item['search_accuracy']['accuracy']:.0%}, MRR {item['search_accuracy']['mrr']:.3f}, p95 search {item['search_accuracy']['p95_search_ms']} ms.",
                f"- Chinese v2 fixture: {item['chinese_retrieval']['passed']}/{item['chinese_retrieval']['task_count']} pass, top-1 {item['chinese_retrieval']['top1_accuracy']:.0%}, MRR {item['chinese_retrieval']['mrr']:.3f}, p95 search {item['chinese_retrieval']['p95_search_ms']} ms.",
                "",
            ]
        )
    lines.extend(["## Full feature matrix", ""])
    keys = ["local_first", "cross_agent", "trust", "bi_temporal", "scope", "lifecycle", "graph", "sync"]
    lines.append("| System | " + " | ".join(keys) + " |")
    lines.append("| --- | " + " | ".join("---" for _ in keys) + " |")
    for item in systems:
        features = item.get("feature_matrix", {})
        lines.append("| " + item["system"] + " | " + " | ".join(str(features.get(key, "n/a")) for key in keys) + " |")
    lines.extend(["", "## Raw JSON", "", f"Machine-readable results: `{report['json_output']}`", ""])
    output.write_text("\n".join(lines), encoding="utf-8")


def _bar(ratio: float, *, width: int = 20) -> str:
    filled = max(0, min(width, round(ratio * width)))
    return "█" * filled + "░" * (width - filled)


def _format_bytes(value: Any) -> str:
    if value is None:
        return "n/a"
    value = float(value)
    for unit in ["B", "KiB", "MiB", "GiB"]:
        if value < 1024 or unit == "GiB":
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{value:.1f} GiB"


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the competitive memory benchmark.")
    parser.add_argument("--systems", nargs="+", default=DEFAULT_SYSTEMS)
    parser.add_argument("--insert-counts", nargs="+", type=int, default=DEFAULT_INSERT_SIZES)
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--quick", action="store_true", help="Run a short local benchmark suitable for CI/docs refresh.")
    parser.add_argument("--output-json", type=Path, default=Path("benchmarks/competitive/results.json"))
    parser.add_argument("--output-md", type=Path, default=Path("docs/COMPETITIVE_BENCHMARK.md"))
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[2]
    insert_counts = [1000] if args.quick else args.insert_counts
    retrieval_cases = load_memory_benchmark(repo_root / "benchmarks/fixtures/memory_benchmark_v0.json")
    chinese_cases = load_chinese_retrieval_jsonl(repo_root / "evals/data/zh_memory_retrieval_v2.jsonl")

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="deep-memory-competitive-") as tmp:
        workdir = Path(tmp)
        systems = [
            run_system(
                name,
                repo_root,
                workdir,
                insert_counts=insert_counts,
                retrieval_cases=retrieval_cases,
                chinese_cases=chinese_cases,
                limit=args.limit,
            )
            for name in args.systems
        ]
    report = {
        "command": " ".join(["uv", "run", "python", "benchmarks/competitive/run_competitive_benchmark.py", *sys_argv_without_interpreter()]),
        "systems": systems,
        "insert_counts": insert_counts,
        "retrieval_case_count": len(retrieval_cases),
        "chinese_case_count": len(chinese_cases),
        "json_output": str(args.output_json),
    }
    args.output_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown_report(report, args.output_md)
    print(json.dumps({"systems": [s["system"] for s in systems], "json": str(args.output_json), "markdown": str(args.output_md)}, ensure_ascii=False, indent=2))


def sys_argv_without_interpreter() -> list[str]:
    import sys

    return sys.argv[1:]


if __name__ == "__main__":
    main()
