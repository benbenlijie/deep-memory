import importlib
import sqlite3

import pytest

from deep_memory import DeepMemory
from deep_memory.embeddings import (
    DEFAULT_EMBEDDING_MODEL,
    DEFAULT_EMBEDDING_VERSION,
    DeterministicEmbeddingBackend,
    SentenceTransformerEmbeddingBackend,
    _pack_embedding,
    _unpack_embedding,
    get_default_embedding_backend,
)


def test_embedding_blob_round_trip_preserves_float_vector():
    vector = [0.125, -1.5, 3.25]

    blob = _pack_embedding(vector)

    assert isinstance(blob, bytes)
    assert _unpack_embedding(blob) == pytest.approx(vector)


def test_add_stores_embedding_with_model_name_version_and_dim_when_backend_configured(tmp_path):
    backend = DeterministicEmbeddingBackend(model_name="test-embedder", model_version=7, dim=8)
    mem = DeepMemory(tmp_path / "memory.db", embedding_backend=backend)

    record = mem.add("用户偏好：中文为主，技术术语用英文")

    row = mem.conn.execute(
        "SELECT memory_id, model_name, model_version, dim, embedding FROM memory_embeddings WHERE memory_id = ?",
        (record.id,),
    ).fetchone()
    assert record.embedding_model == "test-embedder"
    assert record.embedding_version == 7
    assert row["memory_id"] == record.id
    assert row["model_name"] == "test-embedder"
    assert row["model_version"] == 7
    assert row["dim"] == 8
    assert len(_unpack_embedding(row["embedding"])) == 8


def test_add_without_vector_extra_gracefully_skips_embedding(tmp_path, monkeypatch):
    def unavailable_backend():
        return None

    monkeypatch.setattr("deep_memory.core.get_default_embedding_backend", unavailable_backend)
    mem = DeepMemory(tmp_path / "memory.db")

    record = mem.add("FTS5 should still work without vector dependencies")

    rows = mem.conn.execute("SELECT * FROM memory_embeddings").fetchall()
    assert rows == []
    assert record.embedding_model is None
    assert record.embedding_version is None
    assert mem.search("FTS5", cross_workspace=True)


def test_embedding_schema_migration_adds_memory_embeddings_to_legacy_database(tmp_path):
    db_path = tmp_path / "legacy.db"
    conn = sqlite3.connect(db_path)
    conn.executescript(
        """
        CREATE TABLE memories (
            id TEXT PRIMARY KEY,
            content TEXT NOT NULL,
            kind TEXT NOT NULL,
            importance REAL NOT NULL DEFAULT 0.5,
            confidence REAL NOT NULL DEFAULT 0.8,
            source TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            expires_at TEXT
        );
        CREATE VIRTUAL TABLE memories_fts USING fts5(
            content, kind, source, content='memories', content_rowid='rowid'
        );
        """
    )
    conn.close()

    mem = DeepMemory(db_path)

    columns = {row["name"] for row in mem.conn.execute("PRAGMA table_info(memory_embeddings)")}
    assert {"memory_id", "embedding", "model_name", "model_version", "dim"}.issubset(columns)


def test_default_backend_is_lazy_and_missing_dependency_does_not_raise_on_import(monkeypatch):
    module = importlib.import_module("deep_memory.embeddings")
    monkeypatch.setattr(module.importlib.util, "find_spec", lambda name: None)
    module.reset_default_embedding_backend()

    assert get_default_embedding_backend() is None


def test_sentence_transformer_backend_loads_model_only_on_first_embed(monkeypatch):
    loads = []

    class FakeSentenceTransformer:
        def __init__(self, model_name):
            loads.append(model_name)

        def encode(self, texts, normalize_embeddings=True):
            if isinstance(texts, str):
                return [1.0, 2.0]
            return [[float(idx), float(idx + 1)] for idx, _ in enumerate(texts)]

    monkeypatch.setattr("deep_memory.embeddings.SentenceTransformer", FakeSentenceTransformer)
    backend = SentenceTransformerEmbeddingBackend("fake/model")

    assert loads == []
    assert backend.embed("hello") == [1.0, 2.0]
    assert loads == ["fake/model"]
    assert backend.embed_batch(["a", "b"]) == [[0.0, 1.0], [1.0, 2.0]]
    assert loads == ["fake/model"]
    assert backend.model_name == "fake/model"
    assert backend.model_version == DEFAULT_EMBEDDING_VERSION


def test_default_embedding_constants_tag_selected_model():
    assert DEFAULT_EMBEDDING_MODEL == "BAAI/bge-small-zh-v1.5"
    assert DEFAULT_EMBEDDING_VERSION == 1
