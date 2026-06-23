from __future__ import annotations

import json
from html import escape
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from .core import DeepMemory, MemoryKind, MemoryRecord, TelemetryReport, _clamp01, _row_to_record, utcnow

EDITABLE_KINDS: tuple[MemoryKind, ...] = ("working", "episodic", "semantic", "procedural")
ASSET_DIR = Path(__file__).resolve().parents[2] / "docs" / "assets"
FAVICON_FILES = {
    "/favicon.svg": ("favicon.svg", "image/svg+xml"),
    "/favicon.ico": ("favicon.ico", "image/x-icon"),
}
KIND_COLORS: dict[str, str] = {
    "working": "#1c7ed6",
    "episodic": "#f08c00",
    "semantic": "#2fb344",
    "procedural": "#9c36b5",
}
EDGE_STYLES: dict[str, dict[str, object]] = {
    "supersedes": {"color": "#e03131", "arrows": "to", "width": 2},
    "conflict": {"color": "#f59f00", "dashes": True, "arrows": "to", "width": 2},
    "same-source": {"color": "#868e96", "width": 1},
    "temporal-adjacent": {"color": "#74c0fc", "width": 1},
}
AGGREGATION_THRESHOLD = 200


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


def all_records(db: str | Path, *, include_deleted: bool = True) -> list[MemoryRecord]:
    mem = DeepMemory(db)
    sql = "SELECT * FROM memories"
    params: list[object] = []
    if not include_deleted:
        sql += " WHERE conflict_status != 'deprecated'"
    sql += " ORDER BY event_time ASC, created_at ASC"
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


def build_graph_payload(db: str | Path, *, aggregation_threshold: int = AGGREGATION_THRESHOLD) -> dict[str, object]:
    """Build vis.js-compatible nodes and edges for memory relationship visualization."""
    records = all_records(db)
    if not records:
        return {"nodes": [], "edges": [], "aggregated": False, "record_count": 0}
    if len(records) > aggregation_threshold:
        return _build_aggregated_graph(records)
    return {
        "nodes": [_record_node(record) for record in records],
        "edges": _relationship_edges(records),
        "aggregated": False,
        "record_count": len(records),
    }


def build_timeline_payload(db: str | Path) -> dict[str, object]:
    records = all_records(db)
    return {
        "items": [
            {
                "id": record.id,
                "content": record.content,
                "snippet": _snippet(record.content, 180),
                "kind": record.kind,
                "source": _source_label(record.source),
                "time": record.event_time or record.created_at,
                "created_at": record.created_at,
                "status": record.conflict_status,
                "url": f"/edit?id={record.id}",
            }
            for record in records
        ]
    }


def render_index(
    db: str | Path,
    *,
    query: str = "",
    kind: str = "",
    include_deleted: bool = False,
    message: str = "",
    view: str = "memories",
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
    memory_body = f"""
  <form method="get" action="/" role="search">
    <input type="hidden" name="view" value="memories">
    <label>Search <input aria-label="Search memories" name="q" value="{escape(query)}"></label>
    <label>Kind <select name="kind"><option value="">all</option>{kind_options}</select></label>
    <label><input type="checkbox" name="include_deleted" value="1" {'checked' if include_deleted else ''}> include deprecated</label>
    <button type="submit">Filter</button>
  </form>
  <table aria-label="Memory records">
    <thead><tr><th>Content</th><th>Metadata</th><th>Edit</th><th>Delete</th></tr></thead>
    <tbody>{rows or '<tr><td colspan="4">No records found.</td></tr>'}</tbody>
  </table>"""
    body = _render_insights(telemetry_insights(db)) if view == "insights" else memory_body
    return _page(
        db,
        "deep-memory Memory Inspector",
        "Memory Inspector",
        stats,
        body,
        message=message,
    )


def render_graph(db: str | Path, *, message: str = "") -> str:
    stats = _stats(db)
    payload = build_graph_payload(db)
    data_json = json.dumps(payload, ensure_ascii=False)
    edge_styles_json = json.dumps(EDGE_STYLES, ensure_ascii=False)
    body = f"""
  <section aria-label="Memory graph">
    <h2>Memory Graph</h2>
    <p class="muted">force-directed relationship graph. Click a node to open <code>/edit?id=...</code>.</p>
    <p class="legend">
      <span class="dot working"></span> working
      <span class="dot episodic"></span> episodic
      <span class="dot semantic"></span> semantic
      <span class="dot procedural"></span> procedural
      · edges: supersedes / conflict / same-source / temporal-adjacent
    </p>
    <div id="graph" role="img" aria-label="Force-directed memory graph"></div>
    <pre id="graph-empty" class="muted"></pre>
  </section>
  <script src="https://unpkg.com/vis-network@9.1.9/standalone/umd/vis-network.min.js"></script>
  <script>
    const graphPayload = {data_json};
    const edgeStyles = {edge_styles_json};
    const container = document.getElementById('graph');
    const empty = document.getElementById('graph-empty');
    if (!graphPayload.nodes.length) {{
      empty.textContent = 'No memory records yet.';
    }} else if (window.vis) {{
      const nodes = new vis.DataSet(graphPayload.nodes);
      const edges = new vis.DataSet(graphPayload.edges.map(edge => Object.assign({{}}, edgeStyles[edge.type] || {{}}, edge)));
      const network = new vis.Network(container, {{nodes, edges}}, {{
        layout: {{ improvedLayout: true }},
        physics: {{ solver: 'forceAtlas2Based', stabilization: {{ iterations: 140 }} }},
        interaction: {{ hover: true, tooltipDelay: 120, navigationButtons: true }}
      }});
      network.on('click', params => {{
        if (params.nodes.length) {{
          const node = nodes.get(params.nodes[0]);
          if (node && node.url) window.location.href = node.url;
        }}
      }});
    }} else {{
      empty.textContent = JSON.stringify(graphPayload, null, 2);
    }}
  </script>"""
    return _page(db, "deep-memory Memory Graph", "Memory Graph", stats, body, message=message)


def render_timeline(db: str | Path, *, message: str = "") -> str:
    stats = _stats(db)
    payload = build_timeline_payload(db)
    timeline_items = payload["items"]
    assert isinstance(timeline_items, list)
    items = "\n".join(
        f"""
      <li>
        <time>{escape(str(item['time']))}</time>
        <a href="{escape(str(item['url']))}">{escape(str(item['snippet']))}</a><br>
        <span class="muted">{escape(str(item['kind']))} · {escape(str(item['status']))} · source: {escape(str(item['source'] or ''))}</span>
      </li>"""
        for item in timeline_items
        if isinstance(item, dict)
    )
    body = f"""
  <section aria-label="Memory timeline">
    <h2>Memory Timeline</h2>
    <p class="muted">Ordered by <code>event_time</code>, falling back to <code>created_at</code>.</p>
    <ol class="timeline">{items or '<li class="muted">No memory records yet.</li>'}</ol>
  </section>"""
    return _page(db, "deep-memory Memory Timeline", "Memory Timeline", stats, body, message=message)


def run_server(db: str | Path, *, host: str = "127.0.0.1", port: int = 8765) -> None:
    db_path = Path(db)

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            params = parse_qs(parsed.query)
            if parsed.path in FAVICON_FILES:
                name, content_type = FAVICON_FILES[parsed.path]
                self._send_file(ASSET_DIR / name, content_type)
                return
            if parsed.path == "/graph.json":
                self._send_json(build_graph_payload(db_path))
                return
            if parsed.path == "/timeline.json":
                self._send_json(build_timeline_payload(db_path))
                return
            if parsed.path == "/graph":
                self._send_html(render_graph(db_path, message=params.get("message", [""])[0]))
                return
            if parsed.path == "/timeline":
                self._send_html(render_timeline(db_path, message=params.get("message", [""])[0]))
                return
            if parsed.path == "/edit":
                self._send_html(
                    render_index(
                        db_path,
                        query=params.get("id", [""])[0],
                        include_deleted=True,
                        message=params.get("message", [""])[0],
                    )
                )
                return
            self._send_html(
                render_index(
                    db_path,
                    query=params.get("q", [""])[0],
                    kind=params.get("kind", [""])[0],
                    include_deleted=params.get("include_deleted", [""])[0] == "1",
                    message=params.get("message", [""])[0],
                    view=params.get("view", ["memories"])[0],
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

        def _send_json(self, payload: dict[str, object]) -> None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _send_file(self, path: Path, content_type: str) -> None:
            if not path.exists():
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            body = path.read_bytes()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    print(f"deep-memory WebUI: http://{host}:{port}  db={db_path}")
    ThreadingHTTPServer((host, port), Handler).serve_forever()


def _record_node(record: MemoryRecord) -> dict[str, object]:
    source = _source_label(record.source)
    meta = [
        f"kind={record.kind}",
        f"status={record.conflict_status}",
        f"importance={record.importance:.2f}",
        f"confidence={record.confidence:.2f}",
    ]
    if source:
        meta.append(f"source={source}")
    return {
        "id": record.id,
        "label": _snippet(record.content, 36),
        "title": escape(_snippet(record.content, 240) + "\n" + " · ".join(meta)),
        "kind": record.kind,
        "group": record.kind,
        "color": KIND_COLORS.get(record.kind, "#868e96"),
        "url": f"/edit?id={record.id}",
        "source": source,
        "status": record.conflict_status,
        "created_at": record.created_at,
        "event_time": record.event_time,
    }


def _relationship_edges(records: list[MemoryRecord]) -> list[dict[str, object]]:
    ids = {record.id for record in records}
    edges: list[dict[str, object]] = []
    seen: set[tuple[str, str, str]] = set()

    def add_edge(source: str, target: str, edge_type: str) -> None:
        key = (source, target, edge_type)
        if source != target and source in ids and target in ids and key not in seen:
            seen.add(key)
            edges.append({"from": source, "to": target, "type": edge_type, "label": edge_type})

    for record in records:
        if record.supersedes_id:
            edge_type = "conflict" if record.conflict_status == "candidate" else "supersedes"
            add_edge(record.id, record.supersedes_id, edge_type)
        if record.superseded_by_id:
            add_edge(record.superseded_by_id, record.id, "supersedes")

    by_source: dict[str, list[MemoryRecord]] = {}
    for record in records:
        source = _source_label(record.source)
        if source:
            by_source.setdefault(source, []).append(record)
    for group in by_source.values():
        ordered = sorted(group, key=lambda record: (record.event_time, record.created_at, record.id))[:80]
        for left, right in zip(ordered, ordered[1:]):
            add_edge(left.id, right.id, "same-source")

    ordered_records = sorted(records, key=lambda record: (record.event_time, record.created_at, record.id))
    for left, right in zip(ordered_records, ordered_records[1:]):
        add_edge(left.id, right.id, "temporal-adjacent")
    return edges


def _build_aggregated_graph(records: list[MemoryRecord]) -> dict[str, object]:
    groups: dict[tuple[str, str], list[MemoryRecord]] = {}
    for record in records:
        groups.setdefault((record.kind, _source_label(record.source) or "unknown"), []).append(record)
    nodes = []
    group_for: dict[str, str] = {}
    for (kind, source), group_records in sorted(groups.items()):
        group_id = f"group:{kind}:{source}"
        nodes.append(
            {
                "id": group_id,
                "label": f"{kind} · {source} ({len(group_records)})",
                "title": f"{len(group_records)} records\nkind={kind}\nsource={source}",
                "kind": kind,
                "source": source,
                "count": len(group_records),
                "color": KIND_COLORS.get(kind, "#868e96"),
            }
        )
        for record in group_records:
            group_for[record.id] = group_id
    edge_counts: dict[tuple[str, str, str], int] = {}
    for edge in _relationship_edges(records):
        source = group_for.get(str(edge["from"]))
        target = group_for.get(str(edge["to"]))
        edge_type = str(edge["type"])
        if source and target and source != target:
            edge_counts[(source, target, edge_type)] = edge_counts.get((source, target, edge_type), 0) + 1
    edges = [
        {"from": source, "to": target, "type": edge_type, "label": f"{edge_type} ({count})", "value": count}
        for (source, target, edge_type), count in sorted(edge_counts.items())
    ]
    return {"nodes": nodes, "edges": edges, "aggregated": True, "record_count": len(records)}


def _source_label(source: str | dict[str, str] | None) -> str:
    if source is None:
        return ""
    if isinstance(source, dict):
        agent = source.get("agent") or "agent"
        trust = source.get("trust_level") or "unknown"
        return f"{agent}:{trust}"
    return source


def _snippet(text: str, limit: int) -> str:
    normalized = " ".join(text.split())
    if len(normalized) <= limit:
        return normalized
    return normalized[: max(limit - 1, 0)] + "…"


def _render_row(record: MemoryRecord) -> str:
    options = "".join(
        f'<option value="{escape(k)}" {"selected" if record.kind == k else ""}>{escape(k)}</option>'
        for k in EDITABLE_KINDS
    )
    source = _source_label(record.source)
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


def telemetry_insights(db: str | Path, *, days: int = 7) -> TelemetryReport:
    """Return retrieval-quality telemetry for the WebUI Insights view."""
    mem = DeepMemory(db)
    try:
        return mem.telemetry_report(days=days)
    finally:
        mem.close()


def _render_insights(report: TelemetryReport) -> str:
    growth = "n/a" if report.weekly_growth_rate is None else f"{report.weekly_growth_rate:.1%}"
    buckets = "".join(
        f"<li>{escape(bucket)}: {count}</li>" for bucket, count in report.score_distribution.items()
    )
    candidates = "".join(_render_insight_candidate(candidate) for candidate in report.high_usage_low_feedback)
    if not candidates:
        candidates = '<li class="muted">No high usage / low feedback candidates yet.</li>'
    return f"""
  <section aria-label="Insights">
    <h2>Insights</h2>
    <p class="muted">Last {report.days} days retrieval quality telemetry.</p>
    <ul>
      <li>retrievals: {report.retrieval_count}</li>
      <li>hit rate: {report.hit_rate:.1%}</li>
      <li>feedback: {report.feedback["helpful"]} helpful / {report.feedback["not_helpful"]} not helpful</li>
      <li>weekly growth rate: {growth}</li>
    </ul>
    <h3>Hit score distribution</h3>
    <ul>{buckets}</ul>
    <h3>High usage / low feedback candidates</h3>
    <ul>{candidates}</ul>
  </section>"""


def _render_insight_candidate(candidate: object) -> str:
    helpful_rate = getattr(candidate, "helpful_rate")
    rate = "n/a" if helpful_rate is None else f"{helpful_rate:.1%}"
    return (
        f"<li><code>{escape(getattr(candidate, 'memory_id'))}</code> "
        f"usage={getattr(candidate, 'usage_count')} helpful_rate={rate}<br>"
        f"{escape(getattr(candidate, 'content'))}</li>"
    )


def _page(
    db: str | Path,
    title: str,
    heading: str,
    stats: dict[str, int],
    body: str,
    *,
    message: str = "",
) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)}</title>
  <link rel="icon" href="/favicon.svg" type="image/svg+xml">
  <link rel="alternate icon" href="/favicon.ico" type="image/x-icon">
  <style>
    :root {{ color-scheme: light dark; font-family: ui-sans-serif, system-ui, sans-serif; }}
    body {{ margin: 2rem; line-height: 1.45; }}
    header {{ display: flex; justify-content: space-between; gap: 1rem; align-items: baseline; }}
    nav {{ margin: 1rem 0; }}
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
    #graph {{ height: 72vh; min-height: 32rem; border: 1px solid #9995; border-radius: .75rem; }}
    .legend {{ display: flex; gap: .7rem; flex-wrap: wrap; align-items: center; }}
    .dot {{ width: .8rem; height: .8rem; border-radius: 999px; display: inline-block; }}
    .dot.working {{ background: {KIND_COLORS['working']}; }}
    .dot.episodic {{ background: {KIND_COLORS['episodic']}; }}
    .dot.semantic {{ background: {KIND_COLORS['semantic']}; }}
    .dot.procedural {{ background: {KIND_COLORS['procedural']}; }}
    .timeline {{ max-width: 72rem; }}
    .timeline li {{ margin: 1rem 0; padding-left: .5rem; }}
    .timeline time {{ font-family: ui-monospace, SFMono-Regular, Menlo, monospace; color: #777; }}
  </style>
</head>
<body>
  <header>
    <div>
      <h1>{escape(heading)}</h1>
      <p class="muted">Local database: <code>{escape(str(db))}</code></p>
    </div>
    <p class="muted">Total {stats.get("total", 0)} · semantic {stats.get("semantic", 0)} · episodic {stats.get("episodic", 0)} · procedural {stats.get("procedural", 0)}</p>
  </header>
  <nav><a href="/?view=memories">Memories</a> · <a href="/?view=insights">Insights</a> · <a href="/graph">Graph</a> · <a href="/timeline">Timeline</a></nav>
  {f'<p class="banner" role="status">{escape(message)}</p>' if message else ''}
  {body}
</body>
</html>"""


def _stats(db: str | Path) -> dict[str, int]:
    mem = DeepMemory(db)
    try:
        return mem.stats()
    finally:
        mem.close()
