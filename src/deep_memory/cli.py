from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from .adapters.hermes import write_hermes_session_facts
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


@app.command("resolve-conflict")
def resolve_conflict(
    db: Path,
    content: str,
    supersedes: list[str] = typer.Option(..., "--supersedes", help="Memory id to supersede"),
    source: str | None = typer.Option(None),
    confirmed_by_user: bool = typer.Option(False, "--confirmed-by-user"),
) -> None:
    """Resolve or stage a semantic contradiction."""
    mem = DeepMemory(db)
    resolution = mem.resolve_conflict(
        content,
        supersedes=supersedes,
        source=source,
        confirmed_by_user=confirmed_by_user,
    )
    console.print_json(json.dumps(resolution.__dict__, default=lambda obj: obj.__dict__, ensure_ascii=False))


@app.command()
def conflicts(
    db: Path,
    include_superseded: bool = typer.Option(False, "--include-superseded"),
) -> None:
    """Print memories with explicit conflict lifecycle state."""
    mem = DeepMemory(db)
    table = Table("score", "status", "content", "source", "supersedes", "superseded_by")
    for result in mem.conflicts(include_superseded=include_superseded):
        record = result.record
        table.add_row(
            str(result.score),
            record.conflict_status,
            record.content,
            record.source or "",
            record.supersedes_id or "",
            record.superseded_by_id or "",
        )
    console.print(table)


@app.command("hermes-import")
def hermes_import(
    db: Path,
    session_jsonl: Path,
) -> None:
    """Import explicit facts from a Hermes JSONL session export."""
    records = write_hermes_session_facts(db, session_jsonl)
    suffix = "" if len(records) == 1 else "s"
    console.print(f"imported {len(records)} Hermes fact{suffix} into [bold]{db}[/bold]")


@app.command()
def stats(db: Path) -> None:
    """Print memory counts by layer."""
    mem = DeepMemory(db)
    console.print_json(json.dumps(mem.stats(), ensure_ascii=False))


if __name__ == "__main__":
    app()
