from __future__ import annotations

import sys
from pathlib import Path

from typer.testing import CliRunner

from deep_memory import DeepMemory
from deep_memory.cli import app


def _python_command(script: Path, *args: str) -> list[str]:
    return [sys.executable, str(script), *args]


def test_codex_run_injects_bounded_pre_task_recall_and_imports_explicit_facts(tmp_path):
    db = tmp_path / "memory.db"
    mem = DeepMemory(db)
    mem.add("Project convention: use uv run pytest -q before review", kind="procedural", importance=0.9)
    mem.add("Project convention: keep adapter prompts bounded", kind="semantic", importance=0.8)
    mem.add("Unrelated preference: coffee beans", kind="semantic", importance=0.1)
    mem.close()

    facts = tmp_path / "facts.jsonl"
    child = tmp_path / "child.py"
    child.write_text(
        """
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

prompt = os.environ.get("DEEP_MEMORY_CONTEXT", "") + "\\n" + " ".join(sys.argv[1:])
Path(sys.argv[1]).write_text(prompt, encoding="utf-8")
Path(sys.argv[2]).write_text(json.dumps({
    "facts": [{
        "content": "Project convention: adapter wrapper imports only explicit JSONL facts",
        "kind": "procedural",
        "importance": 0.8,
        "confidence": 0.9,
        "evidence": {"type": "tests", "summary": "wrapper smoke passed"},
    }]
}, ensure_ascii=False) + "\\n", encoding="utf-8")
""".strip(),
        encoding="utf-8",
    )
    captured_prompt = tmp_path / "prompt.txt"

    result = CliRunner().invoke(
        app,
        [
            "codex-run",
            "--db",
            str(db),
            "--task",
            "adapter verification workflow",
            "--facts-out",
            str(facts),
            "--limit",
            "2",
            "--",
            *_python_command(child, captured_prompt, facts),
        ],
    )

    assert result.exit_code == 0, result.output
    injected = captured_prompt.read_text(encoding="utf-8")
    assert "Relevant durable memories" in injected
    assert "use uv run pytest -q before review" in injected
    assert "keep adapter prompts bounded" in injected
    assert "coffee beans" not in injected
    reopened = DeepMemory(db)
    try:
        rows = reopened.search("explicit JSONL facts", limit=5)
        assert any("imports only explicit JSONL facts" in row.record.content for row in rows)
        assert any(row.record.source and row.record.source.startswith("codex:") for row in rows)
    finally:
        reopened.close()


def test_codex_run_failed_child_does_not_import_facts(tmp_path):
    db = tmp_path / "memory.db"
    DeepMemory(db).close()
    facts = tmp_path / "facts.jsonl"
    child = tmp_path / "fail_after_fact.py"
    child.write_text(
        """
from pathlib import Path
import sys
Path(sys.argv[1]).write_text('{"facts":[{"content":"Do not persist from failed run","kind":"semantic"}]}\\n', encoding="utf-8")
raise SystemExit(7)
""".strip(),
        encoding="utf-8",
    )

    result = CliRunner().invoke(
        app,
        ["codex-run", "--db", str(db), "--task", "failing task", "--facts-out", str(facts), "--", *_python_command(child, facts)],
    )

    assert result.exit_code == 7
    reopened = DeepMemory(db)
    try:
        assert reopened.search("failed run", limit=5) == []
    finally:
        reopened.close()


def test_codex_run_missing_facts_file_is_partial_and_does_not_write_memory(tmp_path):
    db = tmp_path / "memory.db"
    DeepMemory(db).close()
    child = tmp_path / "success_without_facts.py"
    child.write_text("raise SystemExit(0)\n", encoding="utf-8")
    missing_facts = tmp_path / "missing.jsonl"

    result = CliRunner().invoke(
        app,
        [
            "codex-run",
            "--db",
            str(db),
            "--task",
            "partial task",
            "--facts-out",
            str(missing_facts),
            "--",
            *_python_command(child),
        ],
    )

    assert result.exit_code == 0
    assert "imported 0 Codex facts" in result.output
    reopened = DeepMemory(db)
    try:
        assert reopened.search("partial task", limit=5) == []
    finally:
        reopened.close()
