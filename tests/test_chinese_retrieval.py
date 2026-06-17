from __future__ import annotations

from deep_memory import DeepMemory
from deep_memory.core import _query_tokens


def test_query_tokens_preserve_mixed_chinese_english_terms():
    tokens = list(_query_tokens("Hermes adapter 读取显式 facts JSONL 并导入 deep-memory"))

    assert "Hermes" in tokens
    assert "adapter" in tokens
    assert "facts" in tokens
    assert "JSONL" in tokens
    assert "deep-memory" in tokens
    assert "读取显式" in tokens
    assert "读取" in tokens
    assert "导入" in tokens


def test_chinese_search_recalls_mixed_ascii_memory_from_generic_query(tmp_path):
    mem = DeepMemory(tmp_path / "memory.db")
    mem.add("Hermes adapter 读取显式 facts JSONL 并导入 deep-memory", importance=0.8)

    answer = "\n".join(result.record.content for result in mem.search("相关技术实现是什么？", limit=5))

    assert "Hermes" in answer
    assert "adapter" in answer
    assert "读取显式" in answer
