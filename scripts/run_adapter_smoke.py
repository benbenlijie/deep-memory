from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

from typer.testing import CliRunner

from deep_memory import DeepMemory
from deep_memory.cli import app
from deep_memory.mcp_server import add_memory, memory_stats, search_memory


def smoke_cli_baseline(tmp: Path) -> dict[str, object]:
    db = tmp / "cli-baseline.db"
    runner = CliRunner()

    init = runner.invoke(app, ["init", str(db)])
    if init.exit_code != 0:
        raise RuntimeError(init.output)

    added = runner.invoke(
        app,
        [
            "add",
            str(db),
            "Project convention: run adapter smoke tests with a temporary SQLite database",
            "--kind",
            "procedural",
            "--source",
            "smoke:cli-baseline",
        ],
    )
    if added.exit_code != 0:
        raise RuntimeError(added.output)

    search = runner.invoke(app, ["search", str(db), "adapter smoke", "--limit", "2"])
    if search.exit_code != 0:
        raise RuntimeError(search.output)
    if "smoke:cli-baseline" not in search.output or "SQLite database" not in search.output:
        raise AssertionError(search.output)

    return {
        "name": "CLI baseline",
        "command": "uv run python scripts/run_adapter_smoke.py",
        "db": str(db),
        "summary": "init/add/search succeeded; search returned the smoke procedure",
    }


def smoke_mcp_functions(tmp: Path) -> dict[str, object]:
    db = tmp / "mcp.db"
    added = add_memory(
        db_path=str(db),
        content="User preference: Chinese first, English only for technical terms",
        kind="semantic",
        importance=0.8,
        confidence=0.9,
        source="smoke:mcp",
    )
    results = search_memory(db_path=str(db), query="Chinese first", limit=3)
    stats = memory_stats(db_path=str(db))

    if not results or results[0]["record"]["id"] != added["id"]:
        raise AssertionError(json.dumps(results, ensure_ascii=False))
    if stats["total"] != 1:
        raise AssertionError(json.dumps(stats, ensure_ascii=False))

    return {
        "name": "MCP server tool surface",
        "command": "uv run python - <<'PY' ... add_memory/search_memory/memory_stats ... PY",
        "db": str(db),
        "summary": "MCP-backed add/search/stats functions shared one temporary DB",
    }


def smoke_codex_wrapper(tmp: Path) -> dict[str, object]:
    db = tmp / "codex-wrapper.db"
    mem = DeepMemory(db)
    mem.add(
        "Project convention: adapter wrappers must import only explicit JSONL facts",
        kind="procedural",
        importance=0.9,
        source="smoke:seed",
    )
    mem.close()

    child = tmp / "codex_child.py"
    facts = tmp / "codex-facts.jsonl"
    prompt_capture = tmp / "codex-prompt.txt"
    child.write_text(
        """
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

Path(sys.argv[1]).write_text(os.environ.get("DEEP_MEMORY_CONTEXT", ""), encoding="utf-8")
Path(sys.argv[2]).write_text(json.dumps({
    "facts": [{
        "content": "Adapter smoke: Codex wrapper imported an explicit post-run fact",
        "kind": "procedural",
        "importance": 0.7,
        "confidence": 0.9,
        "evidence": {"type": "command", "summary": "scripts/run_adapter_smoke.py passed"}
    }]
}, ensure_ascii=False) + "\\n", encoding="utf-8")
""".strip(),
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "codex-run",
            "--db",
            str(db),
            "--task",
            "adapter smoke transcript",
            "--facts-out",
            str(facts),
            "--limit",
            "1",
            "--",
            sys.executable,
            str(child),
            str(prompt_capture),
            str(facts),
        ],
    )
    if result.exit_code != 0:
        raise RuntimeError(result.output)
    if "Relevant durable memories" not in prompt_capture.read_text(encoding="utf-8"):
        raise AssertionError("wrapper did not inject bounded recall")

    reopened = DeepMemory(db)
    try:
        rows = reopened.search("explicit post-run fact", limit=5)
        if not rows:
            raise AssertionError("wrapper did not import explicit fact")
    finally:
        reopened.close()

    return {
        "name": "Codex/OpenCode-style wrapper prototype",
        "command": "uv run deep-memory codex-run --db <tmp>/codex-wrapper.db --task 'adapter smoke transcript' --facts-out <tmp>/codex-facts.jsonl -- python <tmp>/codex_child.py <tmp>/codex-prompt.txt <tmp>/codex-facts.jsonl",
        "db": str(db),
        "summary": "bounded recall injected; explicit JSONL fact imported after child success",
    }


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="deep-memory-smoke-") as tmp_dir:
        tmp = Path(tmp_dir)
        results = [smoke_cli_baseline(tmp), smoke_mcp_functions(tmp), smoke_codex_wrapper(tmp)]
        print(json.dumps({"status": "passed", "smokes": results}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
