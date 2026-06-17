from __future__ import annotations

from html import escape
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from .core import DeepMemory, MemoryKind, MemoryRecord, _clamp01, _row_to_record, utcnow

EDITABLE_KINDS: tuple[MemoryKind, ...] = ("working", "episodic", "semantic", "procedural")


def list_records(
    db: str | Path,
    *,
    query: str = "",
    kind: str | None = None,
    include_deleted: bool = False,
    limit: int = 100,
) -> list[MemoryRecord]:
    """Return memory records for the local inspector."""
    mem = DeepMemory(db)
    where: list[str] = []
    params: list[Any] = []
    if not include_deleted:
        where.append("conflict_status != 'deprecated'")
    if kind:
        where.append("kind = ?")
        params.append(kind)
    if query.strip():
        terms = [term for term in query.strip().split() if term]
        if terms:
            where.append("(" + " OR ".join("content LIKE ?" for _ in terms) + ")")
            params.extend(f"%{term}%" for term in terms)
    sql = "SELECT * FROM memories"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY updated_at DESC LIMIT ?"
    params.append(limit)
    rows = mem.conn.execute(sql, params).fetchall()
    try:
        return [_row_to_record(row) for row in rows]
    finally:
        mem.close()


def update_memory(
    db: str | Path,
    record_id: str,
    *,
    content: str,
    kind: str,
    importance: float,
    confidence: float,
    source: str | None = None,
) -> MemoryRecord:
    """Update one memory record from the local inspector."""
    if kind not in EDITABLE_KINDS:
        raise ValueError(f"unsupported memory kind: {kind}")
    if not content.strip():
        raise ValueError("memory content cannot be empty")
    mem = DeepMemory(db)
    now = utcnow()
    mem.conn.execute(
        """
        UPDATE memories
        SET content = ?, kind = ?, importance = ?, confidence = ?, source = ?, updated_at = ?
        WHERE id = ?
        """,
        (content.strip(), kind, _clamp01(importance), _clamp01(confidence), source, now, record_id),
    )
    mem.conn.commit()
    try:
        return mem.get(record_id)
    finally:
        mem.close()


def delete_memory(db: str | Path, record_id: str, *, reason: str | None = None) -> MemoryRecord:
    """Soft-delete one memory record by marking it deprecated."""
    mem = DeepMemory(db)
    note = "webui:delete"
    if reason:
        note += f" reason={reason}"
    try:
        return mem.deprecate(record_id, source=note)
    finally:
        mem.close()


def render_index(
    db: str | Path,
    *,
    query: str = "",
    kind: str = "",
    include_deleted: bool = False,
    message: str = "",
) -> str:
    records = list_records(
        db,
        query=query,
        kind=kind or None,
        include_deleted=include_deleted,
    )
    stats = _stats(db)
    rows = "\n".join(_render_row(record) for record in records)
    kind_options = "\n".join(
        f'<option value="{escape(k)}" {"selected" if kind == k else ""}>{escape(k)}</option>'
        for k in EDITABLE_KINDS
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>deep-memory Memory Inspector</title>
  <style>
    :root {{ color-scheme: light dark; font-family: ui-sans-serif, system-ui, sans-serif; }}
    body {{ margin: 2rem; line-height: 1.45; }}
    header {{ display: flex; justify-content: space-between; gap: 1rem; align-items: baseline; }}
    .muted {{ color: #777; }}
    form, table {{ margin-top: 1rem; }}
    input, select, textarea, button {{ font: inherit; padding: .45rem; }}
    textarea {{ width: min(62rem, 100%); min-height: 4rem; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ border-top: 1px solid #9995; padding: .65rem; vertical-align: top; text-align: left; }}
    tr:focus-within {{ outline: 3px solid #4c8bf5; outline-offset: 2px; }}
    .content {{ min-width: 22rem; }}
    .actions {{ display: flex; gap: .5rem; flex-wrap: wrap; }}
    .banner {{ padding: .75rem; background: #e7f2ff; color: #123; border-radius: .5rem; }}
  </style>
</head>
<body>
  <header>
    <div>
      <h1>Memory Inspector</h1>
      <p class="muted">Local database: <code>{escape(str(db))}</code></p>
    </div>
    <p class="muted">Total {stats.get("total", 0)} · semantic {stats.get("semantic", 0)} · episodic {stats.get("episodic", 0)} · procedural {stats.get("procedural", 0)}</p>
  </header>
  {f'<p class="banner" role="status">{escape(message)}</p>' if message else ''}
  <form method="get" action="/" role="search">
    <label>Search <input aria-label="Search memories" name="q" value="{escape(query)}"></label>
    <label>Kind <select name="kind"><option value="">all</option>{kind_options}</select></label>
    <label><input type="checkbox" name="include_deleted" value="1" {'checked' if include_deleted else ''}> include deprecated</label>
    <button type="submit">Filter</button>
  </form>
  <table aria-label="Memory records">
    <thead><tr><th>Content</th><th>Metadata</th><th>Edit</th><th>Delete</th></tr></thead>
    <tbody>{rows or '<tr><td colspan="4">No records found.</td></tr>'}</tbody>
  </table>
</body>
</html>"""


def run_server(db: str | Path, *, host: str = "127.0.0.1", port: int = 8765) -> None:
    db_path = Path(db)

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            params = parse_qs(urlparse(self.path).query)
            self._send_html(
                render_index(
                    db_path,
                    query=params.get("q", [""])[0],
                    kind=params.get("kind", [""])[0],
                    include_deleted=params.get("include_deleted", [""])[0] == "1",
                    message=params.get("message", [""])[0],
                )
            )

        def do_POST(self) -> None:  # noqa: N802
            length = int(self.headers.get("Content-Length", "0"))
            fields = parse_qs(self.rfile.read(length).decode("utf-8"))
            action = fields.get("action", [""])[0]
            record_id = fields.get("id", [""])[0]
            try:
                if action == "update":
                    update_memory(
                        db_path,
                        record_id,
                        content=fields.get("content", [""])[0],
                        kind=fields.get("kind", ["semantic"])[0],
                        importance=float(fields.get("importance", ["0.5"])[0]),
                        confidence=float(fields.get("confidence", ["0.8"])[0]),
                        source=fields.get("source", [""])[0] or None,
                    )
                    message = "updated"
                elif action == "delete":
                    delete_memory(db_path, record_id, reason=fields.get("reason", [""])[0] or None)
                    message = "deleted"
                else:
                    raise ValueError(f"unsupported action: {action}")
            except Exception as exc:  # pragma: no cover - manual UI path
                message = f"error: {exc}"
            self.send_response(HTTPStatus.SEE_OTHER)
            self.send_header("Location", f"/?message={message}")
            self.end_headers()

        def _send_html(self, html: str) -> None:
            body = html.encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    print(f"deep-memory WebUI: http://{host}:{port}  db={db_path}")
    ThreadingHTTPServer((host, port), Handler).serve_forever()


def _render_row(record: MemoryRecord) -> str:
    options = "".join(
        f'<option value="{escape(k)}" {"selected" if record.kind == k else ""}>{escape(k)}</option>'
        for k in EDITABLE_KINDS
    )
    source = record.source or ""
    return f"""
<tr>
  <td class="content"><textarea name="content" form="edit-{escape(record.id)}">{escape(record.content)}</textarea></td>
  <td>
    <strong>{escape(record.kind)}</strong> · {escape(record.conflict_status)}<br>
    confidence {record.confidence:.2f} · importance {record.importance:.2f}<br>
    <span class="muted">source: {escape(source)}</span><br>
    <span class="muted">updated: {escape(record.updated_at)}</span>
  </td>
  <td>
    <form id="edit-{escape(record.id)}" method="post" action="/" class="actions">
      <input type="hidden" name="action" value="update">
      <input type="hidden" name="id" value="{escape(record.id)}">
      <label>kind <select name="kind">{options}</select></label>
      <label>importance <input name="importance" type="number" min="0" max="1" step="0.05" value="{record.importance:.2f}"></label>
      <label>confidence <input name="confidence" type="number" min="0" max="1" step="0.05" value="{record.confidence:.2f}"></label>
      <label>source <input name="source" value="{escape(source)}"></label>
      <button type="submit">Save</button>
    </form>
  </td>
  <td>
    <form method="post" action="/" class="actions">
      <input type="hidden" name="action" value="delete">
      <input type="hidden" name="id" value="{escape(record.id)}">
      <label>reason <input name="reason" aria-label="Delete reason for {escape(record.id)}"></label>
      <button type="submit">Soft delete</button>
    </form>
  </td>
</tr>"""


def _stats(db: str | Path) -> dict[str, int]:
    mem = DeepMemory(db)
    try:
        return mem.stats()
    finally:
        mem.close()
