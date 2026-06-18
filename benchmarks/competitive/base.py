from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol


@dataclass(frozen=True)
class MemoryItem:
    """A single memory entry in a shared benchmark dataset."""

    content: str
    kind: str = "semantic"
    importance: float = 0.8
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RetrievalCase:
    """A retrieval task with expected lexical evidence."""

    id: str
    query: str
    memories: tuple[MemoryItem, ...]
    expected_keywords: tuple[str, ...]
    language: str = "en"
    category: str = "general"


@dataclass(frozen=True)
class SearchHit:
    content: str
    score: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AdapterStats:
    record_count: int | None = None
    disk_bytes: int | None = None
    ram_bytes: int | None = None
    package_count: int | None = None
    install_bytes: int | None = None
    extra: dict[str, Any] = field(default_factory=dict)


class MemoryAdapter(Protocol):
    """Minimal interface every benchmark adapter must expose."""

    name: str

    def reset(self) -> None:
        """Clear adapter state for a fresh run."""
        ...

    def add(self, item: MemoryItem) -> None:
        """Insert one memory."""
        ...

    def search(self, query: str, *, limit: int = 5) -> list[SearchHit]:
        """Return ranked memory hits."""
        ...

    def stats(self) -> AdapterStats:
        """Return resource stats for current adapter state."""
        ...

    def close(self) -> None:
        """Release any resources."""
        ...


@dataclass(frozen=True)
class AdapterSpec:
    name: str
    import_name: str | None
    package_name: str | None
    requires_api_key: bool = False
    api_key_env: str | None = None
    supports_offline_benchmark: bool = True
    notes: str = ""


class BaseAdapter:
    name = "base"

    def __init__(self, workdir: Path) -> None:
        self.workdir = Path(workdir)
        self.workdir.mkdir(parents=True, exist_ok=True)

    def reset(self) -> None:
        raise NotImplementedError

    def add(self, item: MemoryItem) -> None:
        raise NotImplementedError

    def search(self, query: str, *, limit: int = 5) -> list[SearchHit]:
        raise NotImplementedError

    def stats(self) -> AdapterStats:
        return AdapterStats()

    def close(self) -> None:
        return None
