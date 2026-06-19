from __future__ import annotations

import importlib.util
import os
from importlib import metadata
from pathlib import Path
from time import perf_counter

from deep_memory import DeepMemory

from .base import AdapterSpec, AdapterStats, BaseAdapter, MemoryItem, SearchHit


class DeepMemoryAdapter(BaseAdapter):
    name = "deep-memory"

    def __init__(self, workdir: Path) -> None:
        super().__init__(workdir)
        self.db_path = self.workdir / "deep-memory.db"
        self.mem: DeepMemory | None = None
        self.reset()

    def reset(self) -> None:
        if self.mem is not None:
            self.mem.close()
        if self.db_path.exists():
            self.db_path.unlink()
        self.mem = DeepMemory(self.db_path, embedding_backend=None)
        self.mem._embedding_backend_resolved = True

    def add(self, item: MemoryItem) -> None:
        assert self.mem is not None
        kind = item.kind if item.kind in {"working", "episodic", "semantic", "procedural"} else "semantic"
        self.mem.add(
            item.content,
            kind=kind,  # type: ignore[arg-type]
            importance=item.importance,
            source={"agent": "competitive-benchmark", "origin_type": "explicit", "trust_level": "user"},
            scope="global",
        )

    def search(self, query: str, *, limit: int = 5) -> list[SearchHit]:
        assert self.mem is not None
        return [
            SearchHit(content=hit.record.content, score=hit.score, metadata={"id": hit.record.id})
            for hit in self.mem.search(query, limit=limit, cross_workspace=True)
        ]

    def stats(self) -> AdapterStats:
        assert self.mem is not None
        row = self.mem.conn.execute("SELECT COUNT(*) AS n FROM memories").fetchone()
        return AdapterStats(
            record_count=int(row["n"]),
            disk_bytes=_path_size(self.db_path),
            ram_bytes=_rss_bytes(),
            package_count=_package_count(),
            install_bytes=_package_install_size("deep_memory"),
        )

    def close(self) -> None:
        if self.mem is not None:
            self.mem.close()
            self.mem = None


class ImportOnlyAdapter(BaseAdapter):
    """Adapter for competitors that are installable but not runnable offline without API setup.

    It intentionally does not fake retrieval. The benchmark records environment readiness,
    setup time, package/dependency weight, and the exact blocker.
    """

    def __init__(self, workdir: Path, spec: AdapterSpec) -> None:
        self.spec = spec
        self._records: list[MemoryItem] = []
        self.import_available = False
        self.import_error: str | None = None
        self.init_seconds = 0.0
        super().__init__(workdir)
        self.reset()

    @property
    def name(self) -> str:  # type: ignore[override]
        return self.spec.name

    def reset(self) -> None:
        self._records.clear()
        start = perf_counter()
        if self.spec.import_name:
            self.import_available = importlib.util.find_spec(self.spec.import_name) is not None
            if not self.import_available:
                self.import_error = f"Python import not found: {self.spec.import_name}"
            elif self.spec.requires_api_key and self.spec.api_key_env and not os.getenv(self.spec.api_key_env):
                self.import_error = f"requires {self.spec.api_key_env} for live retrieval benchmark"
            else:
                self.import_error = "no offline adapter implemented for this package/API"
        else:
            self.import_error = "no Python package probe configured"
        self.init_seconds = perf_counter() - start

    def add(self, item: MemoryItem) -> None:
        self._records.append(item)

    def search(self, query: str, *, limit: int = 5) -> list[SearchHit]:
        raise RuntimeError(self.import_error or f"{self.name} cannot be benchmarked in offline mode")

    def stats(self) -> AdapterStats:
        return AdapterStats(
            record_count=len(self._records),
            ram_bytes=_rss_bytes(),
            package_count=_package_count(self.spec.package_name) if self.spec.package_name else None,
            install_bytes=_distribution_size(self.spec.package_name),
            extra={
                "import_available": self.import_available,
                "init_seconds": round(self.init_seconds, 6),
                "blocker": self.import_error,
                "notes": self.spec.notes,
            },
        )


COMPETITOR_SPECS = {
    "mem0": AdapterSpec(
        name="mem0",
        import_name="mem0",
        package_name="mem0ai",
        requires_api_key=True,
        api_key_env="OPENAI_API_KEY",
        supports_offline_benchmark=False,
        notes="mem0 OSS package is installable, but default semantic extraction/retrieval paths typically require an LLM/embedder configuration.",
    ),
    "zep": AdapterSpec(
        name="Zep",
        import_name="zep_cloud",
        package_name="zep-cloud",
        requires_api_key=True,
        api_key_env="ZEP_API_KEY",
        supports_offline_benchmark=False,
        notes="Zep is a cloud context-engineering service; live benchmarking requires an account/API key and network access.",
    ),
    "langmem": AdapterSpec(
        name="LangMem",
        import_name="langmem",
        package_name="langmem",
        requires_api_key=False,
        supports_offline_benchmark=False,
        notes="LangMem is LangGraph-native tooling; a fair run needs a configured LangGraph store/checkpointer and optional model-backed background manager.",
    ),
    "chatgpt-memory": AdapterSpec(
        name="ChatGPT Memory",
        import_name=None,
        package_name=None,
        requires_api_key=False,
        supports_offline_benchmark=False,
        notes="ChatGPT Memory has no public local benchmark API; include as feature/setup comparison only.",
    ),
}


def make_adapter(name: str, workdir: Path) -> BaseAdapter:
    normalized = name.lower()
    if normalized in {"deep-memory", "deep_memory", "deepmemory"}:
        return DeepMemoryAdapter(workdir)
    if normalized in COMPETITOR_SPECS:
        return ImportOnlyAdapter(workdir, COMPETITOR_SPECS[normalized])
    raise ValueError(f"unknown competitive adapter: {name}")


def _rss_bytes() -> int | None:
    try:
        import resource

        rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    except Exception:
        return None
    # resource.ru_maxrss is KiB on Linux. This project benchmark is Linux/CI oriented.
    return int(rss * 1024)


def _path_size(path: Path) -> int:
    if not path.exists():
        return 0
    if path.is_file():
        return path.stat().st_size
    total = 0
    for child in path.rglob("*"):
        if child.is_file():
            total += child.stat().st_size
    return total


def _package_count(package_name: str | None = None) -> int | None:
    try:
        distributions = list(metadata.distributions())
    except Exception:
        return None
    if package_name is None:
        return len(distributions)
    normalized_target = package_name.lower().replace("_", "-")
    installed = any(
        (dist.metadata["Name"] or "").lower().replace("_", "-") == normalized_target
        for dist in distributions
    )
    return len(distributions) if installed else None


def _distribution_size(package_name: str | None) -> int | None:
    if not package_name:
        return None
    try:
        dist = metadata.distribution(package_name)
    except metadata.PackageNotFoundError:
        return None
    total = 0
    for file in dist.files or []:
        try:
            path = Path(str(dist.locate_file(file)))
            if path.exists() and path.is_file():
                total += path.stat().st_size
        except OSError:
            continue
    return total


def _package_install_size(import_name: str) -> int | None:
    spec = importlib.util.find_spec(import_name)
    if spec is None or spec.origin is None:
        return None
    path = Path(spec.origin)
    root = path.parent if path.name != "__init__.py" else path.parent
    return _path_size(root)
