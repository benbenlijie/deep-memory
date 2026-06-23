from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

import typer
from rich.console import Console
from rich.progress import BarColumn, Progress, TaskProgressColumn, TextColumn, TimeElapsedColumn
from rich.table import Table

from .adapters.agent_wrapper import run_codex_wrapper
from .adapters.hermes import write_hermes_session_facts
from .core import DeepMemory
from .portable import diff_databases, export_portable, import_portable
from .privacy import ensure_memory_content_allowed
from .webui import run_server

app = typer.Typer(help="Persistent memory for AI agents")
trust_app = typer.Typer(help="Inspect memory source trust levels")
agent_app = typer.Typer(help="Inspect and override source agent trust")
scope_app = typer.Typer(help="Inspect and promote memory retrieval scopes")
app.add_typer(trust_app, name="trust")
app.add_typer(agent_app, name="agent")
app.add_typer(scope_app, name="scope")
console = Console()


def _record_payload(record) -> dict[str, object]:
    payload = asdict(record)
    payload["source_info"] = asdict(record.source_info)
    return payload


def _trust_audit_payload(entry) -> dict[str, object]:
    return asdict(entry)


@trust_app.command("list")
def trust_list(
    db: Path,
    limit: int = typer.Option(50, "--limit", help="Show top N memories by trust factor"),
    suspicious: bool = typer.Option(False, "--suspicious", help="Show only low-trust memories"),
    all_records: bool = typer.Option(False, "--all", help="Show all matching memories"),
    by_agent: str | None = typer.Option(None, "--by-agent", help="Filter by source agent"),
    by_trust: str | None = typer.Option(None, "--by-trust", help="Filter by trust level"),
) -> None:
    """List memories ordered by source trust level."""
    mem = DeepMemory(db)
    try:
        if by_trust is not None and by_trust not in {"user", "verified", "agent-high", "agent-auto", "external", "untrusted"}:
            raise typer.BadParameter("--by-trust must be one of user, verified, agent-high, agent-auto, external, or untrusted")
        records = mem.trust_records(
            limit=None if all_records else limit,
            suspicious=suspicious,
            agent=by_agent,
            trust_level=by_trust,  # type: ignore[arg-type]
        )
        total = mem.trust_records_count(
            suspicious=suspicious,
            agent=by_agent,
            trust_level=by_trust,  # type: ignore[arg-type]
        )
    finally:
        mem.close()
    console.print(f"showing {len(records)} of {total}")
    for record in records:
        info = record.source_info
        console.print(
            " | ".join(
                [
                    record.id,
                    info.trust_level,
                    f"{info.trust_factor:.2f}",
                    info.origin_type,
                    info.agent or "",
                    record.conflict_status,
                    record.kind,
                    record.content,
                ]
            )
        )


@trust_app.command("promote")
def trust_promote(
    db: Path,
    record_id: str,
    to: str = typer.Option(..., "--to", help="Promotion target: verified or user"),
    by: str = typer.Option("reviewer", "--by", help="Reviewer or actor promoting this memory"),
    reason: str | None = typer.Option(None, "--reason", help="Optional audit reason"),
) -> None:
    """Promote a memory source trust level after manual review."""

    if to not in {"verified", "user"}:
        raise typer.BadParameter("--to must be verified or user")
    mem = DeepMemory(db)
    try:
        record = mem.promote_trust(record_id, to=to, promoted_by=by, reason=reason)  # type: ignore[arg-type]
    except KeyError as exc:
        raise typer.BadParameter(f"unknown memory id: {record_id}") from exc
    finally:
        mem.close()
    console.print_json(json.dumps(_record_payload(record), ensure_ascii=False))


@trust_app.command("audit")
def trust_audit(
    db: Path,
    record_id: str | None = typer.Argument(None, help="Memory id to inspect"),
    recent: int | None = typer.Option(None, "--recent", help="Show trust changes from the last N days"),
) -> None:
    """Show trust change history for one memory or a recent admin window."""

    if record_id is None and recent is None:
        raise typer.BadParameter("provide a memory id or --recent N")
    mem = DeepMemory(db)
    try:
        entries = mem.trust_audit(record_id, recent_days=recent)
    finally:
        mem.close()
    console.print_json(json.dumps([_trust_audit_payload(entry) for entry in entries], ensure_ascii=False))


@agent_app.command("list")
def agent_list(db: Path = typer.Argument(Path(".deep-memory/deep-memory.db"), help="SQLite database path")) -> None:
    """List registered source agents and memory counts."""
    mem = DeepMemory(db)
    try:
        rows = mem.agent_list()
    finally:
        mem.close()
    table = Table("agent", "trust", "memories", "first_seen", "last_seen", "note")
    for row in rows:
        table.add_row(
            str(row["agent"]),
            "trusted" if row["trusted"] else "known",
            str(row["memory_count"]),
            str(row["first_seen_at"]),
            str(row["last_seen_at"]),
            str(row["note"] or ""),
        )
    console.print(table)


@agent_app.command("trust")
def agent_trust(
    db: Path,
    name: str,
    to: str = typer.Option(..., "--to", help="Target: trusted, known, or untrusted"),
    note: str | None = typer.Option(None, "--note", help="Optional registry note"),
) -> None:
    """Override one agent's baseline trust and update its existing memories."""
    if to not in {"trusted", "known", "untrusted"}:
        raise typer.BadParameter("--to must be trusted, known, or untrusted")
    mem = DeepMemory(db)
    try:
        result = mem.set_agent_trust(name, to=to, note=note)  # type: ignore[arg-type]
    finally:
        mem.close()
    console.print_json(json.dumps(result, ensure_ascii=False))


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
    scope: str = typer.Option("workspace", help="global|user|tenant|workspace|project"),
    workspace: str | None = typer.Option(None, help="Workspace name; inferred from cwd when omitted for workspace scope"),
    tenant: str | None = typer.Option(None),
    user_id: str | None = typer.Option(None, "--user-id"),
) -> None:
    """Add one memory record."""
    try:
        ensure_memory_content_allowed(content)
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc
    mem = DeepMemory(db)
    record = mem.add(
        content,
        kind=kind,  # type: ignore[arg-type]
        importance=importance,
        confidence=confidence,
        source=source,
        scope=scope,  # type: ignore[arg-type]
        workspace=workspace,
        tenant=tenant,
        user_id=user_id,
    )
    console.print_json(json.dumps(_record_payload(record), ensure_ascii=False))


@app.command()
def search(
    db: Path,
    query: str,
    limit: int = typer.Option(5),
    kind: str | None = typer.Option(None),
    retrieval_mode: str = typer.Option("auto", "--retrieval-mode", help="auto|fts5|vector|hybrid"),
    as_of: str | None = typer.Option(None, "--as-of", help="Only return records valid as of YYYY-MM-DD or ISO timestamp"),
    workspace: str | None = typer.Option(None, help="Workspace name; inferred from cwd when omitted"),
    include_global: bool = typer.Option(True, "--include-global/--no-include-global", help="Include explicitly global memories"),
    cross_workspace: bool = typer.Option(False, "--all-workspaces", help="Search across workspace/project scoped memories"),
    allow_fallback: bool = typer.Option(True, "--fallback/--no-fallback", help="Fill results from lower-trust memories when the high-trust bucket is short"),
    embedding_version: int | None = typer.Option(None, "--embedding-version", help="Restrict vector/hybrid search to a specific embedding generation"),
) -> None:
    """Search memories."""
    if retrieval_mode not in {"auto", "fts5", "vector", "hybrid"}:
        raise typer.BadParameter("--retrieval-mode must be auto, fts5, vector, or hybrid")
    mem = DeepMemory(db)
    rows = mem.search(
        query,
        limit=limit,
        kind=kind,
        retrieval_mode=retrieval_mode,  # type: ignore[arg-type]
        as_of=as_of,
        workspace=workspace,
        include_global=include_global,
        cross_workspace=cross_workspace,
        allow_fallback=allow_fallback,
        embedding_version=embedding_version,
        caller="cli",
    )  # type: ignore[arg-type]
    table = Table("score", "kind", "content", "source")
    for result in rows:
        source = result.record.source
        if not isinstance(source, str):
            source = json.dumps(source, ensure_ascii=False) if source is not None else ""
        table.add_row(str(result.score), result.record.kind, result.record.content, source)
    console.print(table)


@app.command("backfill-embeddings")
def backfill_embeddings(
    db: Path,
    batch_size: int = typer.Option(100, "--batch-size", min=1, help="Number of memories to embed per batch"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview how many memories would be backfilled"),
) -> None:
    """Backfill missing or outdated memory embeddings in resumable batches."""
    mem = DeepMemory(db)
    try:
        backend = mem._resolve_embedding_backend()
        if backend is None:
            raise typer.BadParameter(
                "embedding backfill is unavailable; install deep-memory[vector] or configure an embedding backend"
            )
        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            console=console,
            transient=True,
        ) as progress:
            preview = mem.backfill_embeddings(embedding_backend=backend, batch_size=batch_size, dry_run=True)
            task_id = progress.add_task("backfilling embeddings", total=max(preview.scanned - preview.skipped, 0))
            if dry_run:
                progress.update(task_id, completed=max(preview.scanned - preview.skipped, 0))
                result = preview
            else:
                result = mem.backfill_embeddings(
                    embedding_backend=backend,
                    batch_size=batch_size,
                    dry_run=False,
                    progress_callback=lambda advance: progress.advance(task_id, advance),
                )
    finally:
        mem.close()
    target_count = result.scanned - result.skipped
    if dry_run:
        console.print(
            f"would backfill {target_count} embeddings (scanned={result.scanned}, skipped={result.skipped}, batch_size={batch_size})"
        )
    else:
        console.print(
            f"backfilled {result.backfilled} embeddings (scanned={result.scanned}, skipped={result.skipped}, batch_size={batch_size})"
        )


@scope_app.command("promote")
def scope_promote(
    db: Path,
    record_id: str,
    to: str = typer.Option(..., "--to", help="Promotion target: global, tenant, user, workspace, or project"),
    workspace: str | None = typer.Option(None),
    tenant: str | None = typer.Option(None),
    user_id: str | None = typer.Option(None, "--user-id"),
) -> None:
    """Promote or move one memory record into an explicit retrieval scope."""

    if to not in {"global", "tenant", "user", "workspace", "project"}:
        raise typer.BadParameter("--to must be global, tenant, user, workspace, or project")
    mem = DeepMemory(db)
    try:
        record = mem.promote_scope(
            record_id,
            to=to,  # type: ignore[arg-type]
            workspace=workspace,
            tenant=tenant,
            user_id=user_id,
        )
    except KeyError as exc:
        raise typer.BadParameter(f"unknown memory id: {record_id}") from exc
    finally:
        mem.close()
    console.print_json(json.dumps(_record_payload(record), ensure_ascii=False))


@scope_app.command("demote")
def scope_demote(
    db: Path,
    record_id: str,
    to: str = typer.Option(..., "--to", help="Demotion target: workspace, tenant, or user"),
    workspace: str | None = typer.Option(None),
    tenant: str | None = typer.Option(None),
    user_id: str | None = typer.Option(None, "--user-id"),
) -> None:
    """Demote a memory from global into a narrower retrieval scope."""

    if to not in {"workspace", "tenant", "user"}:
        raise typer.BadParameter("--to must be workspace, tenant, or user")
    mem = DeepMemory(db)
    try:
        record = mem.promote_scope(
            record_id,
            to=to,  # type: ignore[arg-type]
            workspace=workspace,
            tenant=tenant,
            user_id=user_id,
        )
    except KeyError as exc:
        raise typer.BadParameter(f"unknown memory id: {record_id}") from exc
    finally:
        mem.close()
    console.print_json(json.dumps(_record_payload(record), ensure_ascii=False))


@scope_app.command("list")
def scope_list(db: Path) -> None:
    """Print counts grouped by scope and boundary fields."""

    mem = DeepMemory(db)
    try:
        rows = mem.scope_distribution()
    finally:
        mem.close()
    table = Table("scope", "workspace", "tenant", "user_id", "count")
    for row in rows:
        table.add_row(
            str(row["scope"]),
            str(row["workspace"] or ""),
            str(row["tenant"] or ""),
            str(row["user_id"] or ""),
            str(row["count"]),
        )
    console.print(table)


@app.command()
def consolidate(
    db: Path,
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview candidates without modifying DB"),
    threshold: float = typer.Option(0.6, help="Token overlap threshold for candidate groups"),
    max_group_size: int = typer.Option(10, help="Maximum records per consolidation group"),
) -> None:
    """Consolidate similar active records and archive the originals."""

    mem = DeepMemory(db)
    try:
        plan = mem.consolidate(dry_run=dry_run, threshold=threshold, max_group_size=max_group_size)
    except RuntimeError as exc:
        raise typer.BadParameter(str(exc)) from exc
    finally:
        mem.close()
    console.print_json(
        json.dumps(
            {
                "dry_run": plan.dry_run,
                "groups": [group.__dict__ for group in plan.groups],
                "archived_count": plan.archived_count,
                "created_count": plan.created_count,
            },
            ensure_ascii=False,
        )
    )


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
    try:
        records = write_hermes_session_facts(db, session_jsonl)
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc
    suffix = "" if len(records) == 1 else "s"
    console.print(f"imported {len(records)} Hermes fact{suffix} into [bold]{db}[/bold]")


@app.command()
def stats(db: Path) -> None:
    """Print memory counts by layer."""
    mem = DeepMemory(db)
    console.print_json(json.dumps(mem.stats(), ensure_ascii=False))


@app.command()
def export(
    db: Path,
    include_deprecated: bool = typer.Option(
        False,
        "--include-deprecated",
        help="Include deprecated soft-deleted records. Off by default for privacy.",
    ),
    as_of: str | None = typer.Option(None, "--as-of", help="Only export records valid as of YYYY-MM-DD or ISO timestamp"),
    portable: bool = typer.Option(False, "--portable", help="Write portable JSONL + manifest bundle."),
    output: Path | None = typer.Option(None, "--output", "-o", help="Output directory for --portable."),
) -> None:
    """Export memory records as JSONL or as a portable sync bundle."""
    if portable:
        if output is None:
            raise typer.BadParameter("--output is required with --portable")
        manifest = export_portable(db, output, include_deprecated=include_deprecated, as_of=as_of)
        console.print_json(json.dumps(manifest, ensure_ascii=False))
        return
    mem = DeepMemory(db)
    try:
        for record in mem.export_records(include_deprecated=include_deprecated, as_of=as_of):
            typer.echo(json.dumps(_record_payload(record), ensure_ascii=False))
    finally:
        mem.close()


@app.command("import")
def import_(
    db: Path,
    portable_path: Path,
    merge: bool = typer.Option(False, "--merge", help="Deduplicate and merge portable JSONL records."),
) -> None:
    """Import a portable JSONL bundle into a local database."""
    try:
        result = import_portable(db, portable_path, merge=merge)
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc
    console.print_json(json.dumps(result, ensure_ascii=False))


@app.command("diff")
def diff_(db1: Path, db2: Path) -> None:
    """Compare two deep-memory databases."""
    console.print_json(json.dumps(diff_databases(db1, db2), ensure_ascii=False))


@app.command("hard-delete")
def hard_delete(db: Path, record_id: str) -> None:
    """Physically delete one memory record from the local database."""
    mem = DeepMemory(db)
    try:
        deleted = mem.hard_delete(record_id)
    except RuntimeError as exc:
        raise typer.BadParameter(str(exc)) from exc
    finally:
        mem.close()
    console.print(f"hard-deleted {deleted} memory from [bold]{db}[/bold]")


@app.command("prune-backups")
def prune_backups(
    db: Path = typer.Argument(Path(".deep-memory/deep-memory.db"), help="SQLite database path"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview expired backups without deleting them"),
    retention_days: int | None = typer.Option(None, "--retention-days", help="Override backup retention TTL in days"),
) -> None:
    """Delete auto-backups older than the configured retention TTL."""
    mem = DeepMemory(db, lazy_prune=False)
    try:
        result = mem.prune_backups(retention_days=retention_days, dry_run=dry_run)
    finally:
        mem.close()
    console.print_json(json.dumps(result, ensure_ascii=False))


@app.command("codex-run", context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
def codex_run(
    ctx: typer.Context,
    db: Path = typer.Option(..., "--db", help="Explicit deep-memory SQLite database path"),
    task: str = typer.Option(..., "--task", help="Task description used for pre-run recall"),
    facts_out: Path | None = typer.Option(
        None,
        "--facts-out",
        help="Explicit post-run JSONL facts file to import only after child success",
    ),
    limit: int = typer.Option(5, "--limit", min=0, help="Maximum recalled memories to inject"),
) -> None:
    """Run a Codex-style command with bounded recall and explicit facts import."""

    command = list(ctx.args)
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        raise typer.BadParameter("child command is required after --")

    result = run_codex_wrapper(db=db, task=task, command=command, facts_out=facts_out, limit=limit)
    suffix = "" if len(result.imported) == 1 else "s"
    console.print(f"imported {len(result.imported)} Codex fact{suffix} into [bold]{db}[/bold]")
    if result.returncode != 0:
        raise typer.Exit(result.returncode)


@app.command()
def feedback(
    db: Path,
    memory_id: str,
    helpful: bool = typer.Option(False, "--helpful", help="Mark the retrieved memory as helpful."),
    not_helpful: bool = typer.Option(
        False, "--not-helpful", help="Mark the retrieved memory as not helpful."
    ),
    note: str | None = typer.Option(None, help="Optional feedback note."),
) -> None:
    """Record retrieval feedback for one memory."""
    if helpful == not_helpful:
        raise typer.BadParameter("choose exactly one of --helpful or --not-helpful")
    mem = DeepMemory(db)
    try:
        entry = mem.add_feedback(memory_id, helpful=helpful, note=note)
    finally:
        mem.close()
    console.print_json(json.dumps(entry.__dict__, ensure_ascii=False))


@app.command()
def report(db: Path = typer.Argument(Path(".deep-memory/deep-memory.db")), days: int = typer.Option(7)) -> None:
    """Print a markdown telemetry report for recent retrieval quality."""
    mem = DeepMemory(db)
    try:
        typer.echo(mem.telemetry_report_markdown(days=days))
    finally:
        mem.close()


@app.command()
def webui(
    db: Path,
    host: str = typer.Option("127.0.0.1", help="Bind host for the local-only WebUI"),
    port: int = typer.Option(8765, help="Bind port for the local WebUI"),
) -> None:
    """Serve the local memory inspector/editor WebUI."""
    run_server(db, host=host, port=port)


if __name__ == "__main__":
    app()
