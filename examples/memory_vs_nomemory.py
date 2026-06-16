"""Compare an agent without memory to one using deep-memory.

Run from the repository root:

    uv run python examples/memory_vs_nomemory.py

This is deliberately small and deterministic: the "agent" is a tiny function
that can only personalize its answer if relevant memories are retrieved.
"""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from deep_memory import DeepMemory


def answer_without_memory(question: str) -> str:
    return f"Q: {question}\nA: I do not have prior user context in this session."


def answer_with_memory(mem: DeepMemory, question: str) -> str:
    recalls = mem.search(question, limit=2)
    if not recalls:
        return f"Q: {question}\nA: I could not find relevant long-term memory."

    context = "; ".join(result.record.content for result in recalls)
    return f"Q: {question}\nA: Based on memory: {context}"


def main() -> None:
    question = "How should I answer this user? 用户喜欢什么风格？"

    with TemporaryDirectory() as tmpdir:
        mem = DeepMemory(Path(tmpdir) / "agent.db")
        mem.add("用户偏好：中文为主，技术术语用英文", kind="semantic", importance=0.9)
        mem.add("用户偏好：简洁、有深度，不要废话", kind="semantic", importance=0.95)

        print("=== Without memory ===")
        print(answer_without_memory(question))
        print("\n=== With deep-memory ===")
        print(answer_with_memory(mem, question))


if __name__ == "__main__":
    main()
