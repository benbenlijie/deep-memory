from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from .core import DeepMemory

app = typer.Typer(help="Persistent memory for AI agents")
console = Console()


@app.command()
def init(db: Path = typer.Argument(..., help="SQLite database path")) -> None:
    """Initialize a deep-memory database."""
    mem = DeepMemory(db)
    mem.close()
    console.print(f"initialized [bold]{db}[/bold]")


@app.command()
def add(
    db: Path,
    content: str,
    kind: str = typer.Option("semantic", help="working|episodic|semantic|procedural"),
    importance: float = typer.Option(0.5),
    confidence: float = typer.Option(0.8),
    source: str | None = typer.Option(None),
) -> None:
    """Add one memory record."""
    mem = DeepMemory(db)
    record = mem.add(
        content,
        kind=kind,  # type: ignore[arg-type]
        importance=importance,
        confidence=confidence,
        source=source,
    )
    console.print_json(json.dumps(record.__dict__, ensure_ascii=False))


@app.command()
def search(
    db: Path,
    query: str,
    limit: int = typer.Option(5),
    kind: str | None = typer.Option(None),
) -> None:
    """Search memories."""
    mem = DeepMemory(db)
    rows = mem.search(query, limit=limit, kind=kind)  # type: ignore[arg-type]
    table = Table("score", "kind", "content", "source")
    for result in rows:
        table.add_row(str(result.score), result.record.kind, result.record.content, result.record.source or "")
    console.print(table)


@app.command()
def stats(db: Path) -> None:
    """Print memory counts by layer."""
    mem = DeepMemory(db)
    console.print_json(json.dumps(mem.stats(), ensure_ascii=False))


if __name__ == "__main__":
    app()
