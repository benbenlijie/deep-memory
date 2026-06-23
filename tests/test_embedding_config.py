import os
from contextlib import contextmanager

from deep_memory import DeepMemory
from deep_memory.embeddings import DeterministicEmbeddingBackend


class KeywordEmbeddingBackend(DeterministicEmbeddingBackend):
    def __init__(self) -> None:
        super().__init__(model_name="keyword-test", model_version=1, dim=6)


@contextmanager
def chdir(path):
    previous = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(previous)


def write_embedding_config(path, enabled):
    path.write_text(
        f"""
[tool.deep-memory.embedding]
enabled = {str(enabled).lower()}
""".lstrip(),
        encoding="utf-8",
    )


def test_pyproject_embedding_enabled_activates_backend(tmp_path, monkeypatch):
    write_embedding_config(tmp_path / "pyproject.toml", True)
    monkeypatch.delenv("DEEP_MEMORY_EMBEDDING", raising=False)
    monkeypatch.setattr("deep_memory.core.get_default_embedding_backend", KeywordEmbeddingBackend)

    with chdir(tmp_path):
        mem = DeepMemory(tmp_path / "memory.db")
        backend = mem._resolve_embedding_backend()

    assert isinstance(backend, KeywordEmbeddingBackend)


def test_pyproject_embedding_false_env_on_activates_backend(tmp_path, monkeypatch):
    write_embedding_config(tmp_path / "pyproject.toml", False)
    monkeypatch.setenv("DEEP_MEMORY_EMBEDDING", "on")
    monkeypatch.setattr("deep_memory.core.get_default_embedding_backend", KeywordEmbeddingBackend)

    with chdir(tmp_path):
        mem = DeepMemory(tmp_path / "memory.db")
        backend = mem._resolve_embedding_backend()

    assert isinstance(backend, KeywordEmbeddingBackend)


def test_pyproject_embedding_true_env_off_deactivates_backend(tmp_path, monkeypatch):
    write_embedding_config(tmp_path / "pyproject.toml", True)
    monkeypatch.setenv("DEEP_MEMORY_EMBEDDING", "off")
    monkeypatch.setattr("deep_memory.core.get_default_embedding_backend", KeywordEmbeddingBackend)

    with chdir(tmp_path):
        mem = DeepMemory(tmp_path / "memory.db")
        backend = mem._resolve_embedding_backend()

    assert backend is None


def test_no_pyproject_and_no_env_keeps_embedding_off(tmp_path, monkeypatch):
    monkeypatch.delenv("DEEP_MEMORY_EMBEDDING", raising=False)
    monkeypatch.setattr("deep_memory.core.get_default_embedding_backend", KeywordEmbeddingBackend)

    with chdir(tmp_path):
        mem = DeepMemory(tmp_path / "memory.db")
        backend = mem._resolve_embedding_backend()

    assert backend is None


def test_pyproject_embedding_enabled_is_discovered_from_parent_directory(tmp_path, monkeypatch):
    write_embedding_config(tmp_path / "pyproject.toml", True)
    nested = tmp_path / "one" / "two"
    nested.mkdir(parents=True)
    monkeypatch.delenv("DEEP_MEMORY_EMBEDDING", raising=False)
    monkeypatch.setattr("deep_memory.core.get_default_embedding_backend", KeywordEmbeddingBackend)

    with chdir(nested):
        mem = DeepMemory(tmp_path / "memory.db")
        backend = mem._resolve_embedding_backend()

    assert isinstance(backend, KeywordEmbeddingBackend)
