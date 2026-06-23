#!/usr/bin/env python3
from __future__ import annotations

import tempfile
from pathlib import Path

from deep_memory import DeepMemory
from deep_memory.embeddings import DeterministicEmbeddingBackend


class SynonymEmbeddingBackend(DeterministicEmbeddingBackend):
    def __init__(self) -> None:
        super().__init__(model_name="synonym-eval", model_version=1, dim=20)
        self._groups = [
            ("test", "pytest", "测试"),
            ("deploy", "部署", "deployment"),
            ("release", "发布", "ship"),
            ("bug", "defect", "缺陷"),
            ("docs", "documentation", "文档"),
            ("cache", "缓存", "memoize"),
            ("auth", "login", "登录"),
            ("database", "sqlite", "数据库"),
            ("backup", "备份", "snapshot"),
            ("config", "configuration", "配置"),
            ("search", "retrieval", "检索"),
            ("latency", "performance", "性能"),
            ("privacy", "安全", "security"),
            ("memory", "记忆", "recall"),
            ("agent", "助手", "assistant"),
            ("cli", "command", "命令"),
            ("vector", "embedding", "向量"),
            ("review", "复核", "audit"),
            ("migration", "schema", "迁移"),
            ("workspace", "project", "项目"),
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


PAIRS = [
    ("test", "store pytest regression workflow"),
    ("部署", "document deploy runbook"),
    ("发布", "release checklist is ready"),
    ("defect", "bug triage policy"),
    ("文档", "docs update before launch"),
    ("缓存", "cache invalidation note"),
    ("登录", "auth token handling"),
    ("数据库", "sqlite backup location"),
    ("备份", "backup retention policy"),
    ("配置", "config file schema"),
    ("检索", "search ranking formula"),
    ("性能", "latency budget"),
    ("security", "privacy boundary"),
    ("记忆", "memory consolidation"),
    ("助手", "agent routing rule"),
    ("命令", "cli invocation"),
    ("向量", "embedding model version"),
    ("复核", "review gate"),
    ("迁移", "schema migration"),
    ("项目", "workspace scope"),
]


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        mem = DeepMemory(Path(tmp) / "memory.db", embedding_backend=SynonymEmbeddingBackend())
        expected_ids: dict[str, str] = {}
        for query, content in PAIRS:
            expected_ids[query] = mem.add(content, kind="semantic", importance=0.9).id
        passed = 0
        for query, _content in PAIRS:
            results = mem.search(query, limit=1, retrieval_mode="hybrid", cross_workspace=True)
            ok = bool(results and results[0].record.id == expected_ids[query])
            passed += int(ok)
            print(f"{query}: {'PASS' if ok else 'FAIL'}")
        rate = passed / len(PAIRS)
        print(f"pass_rate={rate:.0%} ({passed}/{len(PAIRS)})")
        if rate < 0.8:
            raise SystemExit(1)


if __name__ == "__main__":
    main()
