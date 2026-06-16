"""Two-minute deep-memory quickstart.

Run from the repository root:

    uv run python examples/quickstart.py

The example writes to a temporary SQLite database, adds a few memories, and
recalls the user's style preference across the same agent-like flow.
"""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from deep_memory import DeepMemory


def main() -> None:
    with TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "agent.db"
        mem = DeepMemory(db_path)

        mem.add("用户偏好：中文为主，技术术语用英文", kind="semantic", importance=0.9)
        mem.add("2026-06-16: discussed deep-memory GitHub launch", kind="episodic")
        mem.add("成功的 agent 流程应该沉淀为 reusable skills", kind="procedural")

        print(f"database: {db_path}")
        print(f"stats: {mem.stats()}")
        print("\nRecall: 用户喜欢什么回答风格？")

        for result in mem.search("用户喜欢什么回答风格？", limit=3):
            print(f"- {result.score:.4f} [{result.record.kind}] {result.record.content}")


if __name__ == "__main__":
    main()
