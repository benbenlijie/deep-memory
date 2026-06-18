from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

from .core import DeepMemory, MemoryKind

DEFAULT_DB_PATH = "deep-memory.db"


def add_memory(
    content: str,
    *,
    db_path: str = DEFAULT_DB_PATH,
    kind: MemoryKind = "semantic",
    importance: float = 0.5,
    confidence: float = 0.8,
    source: str | None = None,
    expires_at: str | None = None,
    scope: str = "workspace",
    workspace: str | None = None,
    tenant: str | None = None,
    user_id: str | None = None,
) -> dict[str, Any]:
    """Add one memory record and return an MCP-friendly JSON object."""
    mem = DeepMemory(Path(db_path))
    try:
        record = mem.add(
            content,
            kind=kind,
            importance=importance,
            confidence=confidence,
            source=source,
            expires_at=expires_at,
            scope=scope,  # type: ignore[arg-type]
            workspace=workspace,
            tenant=tenant,
            user_id=user_id,
        )
        return asdict(record)
    finally:
        mem.close()


def search_memory(
    query: str,
    *,
    db_path: str = DEFAULT_DB_PATH,
    limit: int = 5,
    kind: MemoryKind | None = None,
    workspace: str | None = None,
    include_global: bool = True,
    cross_workspace: bool = False,
) -> list[dict[str, Any]]:
    """Search memories and return scored records as plain JSON objects."""
    mem = DeepMemory(Path(db_path))
    try:
        return [
            {"score": result.score, "record": asdict(result.record)}
            for result in mem.search(
                query,
                limit=limit,
                kind=kind,
                workspace=workspace,
                include_global=include_global,
                cross_workspace=cross_workspace,
                caller="mcp",
            )
        ]
    finally:
        mem.close()


def memory_feedback(
    memory_id: str,
    helpful: bool,
    note: str | None = None,
    *,
    db_path: str = DEFAULT_DB_PATH,
) -> dict[str, Any]:
    """Record whether a retrieved memory helped the caller."""
    mem = DeepMemory(Path(db_path))
    try:
        return asdict(mem.add_feedback(memory_id, helpful=helpful, note=note))
    finally:
        mem.close()


def memory_stats(*, db_path: str = DEFAULT_DB_PATH) -> dict[str, int]:
    """Return memory counts by layer."""
    mem = DeepMemory(Path(db_path))
    try:
        return mem.stats()
    finally:
        mem.close()


def resolve_memory_conflict(
    content: str,
    *,
    db_path: str = DEFAULT_DB_PATH,
    supersedes: list[str],
    source: str | None = None,
    confirmed_by_user: bool = False,
) -> dict[str, Any]:
    """Resolve or stage a semantic-memory contradiction with source trail metadata."""
    mem = DeepMemory(Path(db_path))
    try:
        resolution = mem.resolve_conflict(
            content,
            supersedes=supersedes,
            source=source,
            confirmed_by_user=confirmed_by_user,
        )
        return asdict(resolution)
    finally:
        mem.close()


def list_memory_conflicts(
    *, db_path: str = DEFAULT_DB_PATH, include_superseded: bool = False
) -> list[dict[str, Any]]:
    """Return memories carrying explicit conflict lifecycle state."""
    mem = DeepMemory(Path(db_path))
    try:
        return [
            {"score": result.score, "record": asdict(result.record)}
            for result in mem.conflicts(include_superseded=include_superseded)
        ]
    finally:
        mem.close()


def create_mcp_server():
    """Create a FastMCP server exposing deep-memory tools.

    The import is intentionally lazy so the SDK/CLI remains usable without
    installing the optional MCP dependency. Install with `uv sync --extra mcp`.
    """
    try:
        from mcp.server.fastmcp import FastMCP
    except ModuleNotFoundError as exc:  # pragma: no cover - depends on optional extra
        raise RuntimeError(
            "MCP support requires the optional dependency: uv sync --extra mcp"
        ) from exc

    server = FastMCP("deep-memory")

    @server.tool(name="add")
    def _add(
        content: str,
        db_path: str = DEFAULT_DB_PATH,
        kind: MemoryKind = "semantic",
        importance: float = 0.5,
        confidence: float = 0.8,
        source: str | None = None,
        expires_at: str | None = None,
        scope: str = "workspace",
        workspace: str | None = None,
        tenant: str | None = None,
        user_id: str | None = None,
    ) -> dict[str, Any]:
        """Add one memory record to a deep-memory SQLite database."""
        return add_memory(
            db_path=db_path,
            content=content,
            kind=kind,
            importance=importance,
            confidence=confidence,
            source=source,
            expires_at=expires_at,
            scope=scope,
            workspace=workspace,
            tenant=tenant,
            user_id=user_id,
        )

    @server.tool(name="search")
    def _search(
        query: str,
        db_path: str = DEFAULT_DB_PATH,
        limit: int = 5,
        kind: MemoryKind | None = None,
        workspace: str | None = None,
        include_global: bool = True,
        cross_workspace: bool = False,
    ) -> list[dict[str, Any]]:
        """Search memory records by query, optionally filtered by kind and scope."""
        return search_memory(
            db_path=db_path,
            query=query,
            limit=limit,
            kind=kind,
            workspace=workspace,
            include_global=include_global,
            cross_workspace=cross_workspace,
        )

    @server.tool(name="memory_feedback")
    def _memory_feedback(
        memory_id: str,
        helpful: bool,
        note: str | None = None,
        db_path: str = DEFAULT_DB_PATH,
    ) -> dict[str, Any]:
        """Record whether a retrieved memory was helpful."""
        return memory_feedback(memory_id, helpful, note, db_path=db_path)

    @server.tool(name="stats")
    def _stats(db_path: str = DEFAULT_DB_PATH) -> dict[str, int]:
        """Return counts for working, episodic, semantic, procedural and total records."""
        return memory_stats(db_path=db_path)

    @server.tool(name="resolve_conflict")
    def _resolve_conflict(
        content: str,
        db_path: str = DEFAULT_DB_PATH,
        supersedes: list[str] | None = None,
        source: str | None = None,
        confirmed_by_user: bool = False,
    ) -> dict[str, Any]:
        """Resolve or stage a semantic-memory contradiction."""
        return resolve_memory_conflict(
            content,
            db_path=db_path,
            supersedes=supersedes or [],
            source=source,
            confirmed_by_user=confirmed_by_user,
        )

    @server.tool(name="conflicts")
    def _conflicts(
        db_path: str = DEFAULT_DB_PATH, include_superseded: bool = False
    ) -> list[dict[str, Any]]:
        """List memories with explicit conflict lifecycle state."""
        return list_memory_conflicts(db_path=db_path, include_superseded=include_superseded)

    return server


def main() -> None:
    """Run the deep-memory MCP server over stdio."""
    create_mcp_server().run()


if __name__ == "__main__":
    main()
