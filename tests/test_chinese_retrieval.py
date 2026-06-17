from __future__ import annotations

import pytest

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


def test_jieba_query_tokens_include_segmented_terms_when_available():
    pytest.importorskip("jieba")

    tokens = list(_query_tokens("中文检索需要分词召回", backend="jieba"))

    assert "中文" in tokens
    assert "检索" in tokens
    assert "分词" in tokens
    assert "召回" in tokens


def test_search_accepts_optional_jieba_backend(tmp_path):
    pytest.importorskip("jieba")
    mem = DeepMemory(tmp_path / "memory.db")
    mem.add("中文检索需要分词召回，同时保持 SQLite FTS 轻量基线", importance=0.9)

    answer = "\n".join(
        result.record.content for result in mem.search("分词召回方案", limit=3, backend="jieba")
    )

    assert "中文检索" in answer
    assert "分词召回" in answer


def test_unknown_retrieval_backend_is_rejected(tmp_path):
    mem = DeepMemory(tmp_path / "memory.db")
    mem.add("中文检索需要清晰的 backend 边界")

    with pytest.raises(ValueError, match="unknown retrieval backend"):
        mem.search("检索", backend="does-not-exist")
