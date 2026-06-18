from __future__ import annotations

import hashlib
import importlib.util
import struct
from functools import cached_property
from typing import Protocol

DEFAULT_EMBEDDING_MODEL = "BAAI/bge-small-zh-v1.5"
DEFAULT_EMBEDDING_VERSION = 1

try:  # pragma: no cover - exercised through monkeypatched tests when installed.
    from sentence_transformers import SentenceTransformer  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover - normal path without vector extra.
    SentenceTransformer = None  # type: ignore[assignment]


class EmbeddingBackend(Protocol):
    @property
    def model_name(self) -> str: ...

    @property
    def model_version(self) -> int: ...

    def embed(self, text: str) -> list[float]: ...

    def embed_batch(self, texts: list[str]) -> list[list[float]]: ...


class SentenceTransformerEmbeddingBackend:
    def __init__(
        self,
        model_name: str = DEFAULT_EMBEDDING_MODEL,
        *,
        model_version: int = DEFAULT_EMBEDDING_VERSION,
    ) -> None:
        self._model_name = model_name
        self._model_version = model_version

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def model_version(self) -> int:
        return self._model_version

    @cached_property
    def _model(self):
        if SentenceTransformer is None:
            raise RuntimeError("sentence-transformers is not installed; install deep-memory[vector]")
        return SentenceTransformer(self._model_name)

    def embed(self, text: str) -> list[float]:
        vector = self._model.encode(text, normalize_embeddings=True)
        return _as_float_list(vector)

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        vectors = self._model.encode(texts, normalize_embeddings=True)
        return [_as_float_list(vector) for vector in vectors]


class DeterministicEmbeddingBackend:
    """Small dependency-free backend for tests and deterministic fixtures."""

    def __init__(self, *, model_name: str = "deterministic-test", model_version: int = 1, dim: int = 16) -> None:
        self._model_name = model_name
        self._model_version = model_version
        self._dim = dim

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def model_version(self) -> int:
        return self._model_version

    def embed(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        values = []
        for idx in range(self._dim):
            byte = digest[idx % len(digest)]
            values.append(round((byte / 127.5) - 1.0, 6))
        return values

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self.embed(text) for text in texts]


_DEFAULT_BACKEND: EmbeddingBackend | None | object = object()


def get_default_embedding_backend() -> EmbeddingBackend | None:
    global _DEFAULT_BACKEND
    if _DEFAULT_BACKEND is not _UNSET:
        return _DEFAULT_BACKEND  # type: ignore[return-value]
    if importlib.util.find_spec("sentence_transformers") is None:
        _DEFAULT_BACKEND = None
    else:
        _DEFAULT_BACKEND = SentenceTransformerEmbeddingBackend()
    return _DEFAULT_BACKEND  # type: ignore[return-value]


def reset_default_embedding_backend() -> None:
    global _DEFAULT_BACKEND
    _DEFAULT_BACKEND = _UNSET


def _pack_embedding(vector: list[float]) -> bytes:
    return struct.pack(f"<{len(vector)}f", *vector)


def _unpack_embedding(blob: bytes) -> list[float]:
    if len(blob) % 4 != 0:
        raise ValueError("embedding blob length must be a multiple of 4")
    return list(struct.unpack(f"<{len(blob) // 4}f", blob))


def _as_float_list(vector) -> list[float]:
    if hasattr(vector, "tolist"):
        vector = vector.tolist()
    return [float(value) for value in vector]


_UNSET = object()
reset_default_embedding_backend()
