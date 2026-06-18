from __future__ import annotations

from deep_memory import DeepMemory
from deep_memory.webui import build_graph_payload, build_timeline_payload, render_graph, render_timeline


def test_graph_payload_returns_nodes_and_relationship_edges(tmp_path):
    db = tmp_path / "memory.db"
    mem = DeepMemory(db)
    old = mem.add("用户偏好：英文回答", kind="semantic", source="profile")
    new = mem.add("用户偏好：中文回答", kind="semantic", source="profile")
    conflict = mem.add("用户偏好：日文回答", kind="semantic", source="profile")
    episode = mem.add("本次会话：讨论 WebUI 图谱", kind="episodic", source="session")
    mem.conn.execute(
        "UPDATE memories SET supersedes_id = ? WHERE id = ?",
        (old.id, new.id),
    )
    mem.conn.execute(
        "UPDATE memories SET supersedes_id = ?, conflict_status = 'candidate' WHERE id = ?",
        (old.id, conflict.id),
    )
    mem.conn.commit()

    payload = build_graph_payload(db)

    assert {node["id"] for node in payload["nodes"]} == {old.id, new.id, conflict.id, episode.id}
    node = next(node for node in payload["nodes"] if node["id"] == new.id)
    assert node["kind"] == "semantic"
    assert node["color"] == "#2fb344"
    assert node["url"] == f"/edit?id={new.id}"
    assert "用户偏好" in node["title"]
    edge_keys = {(edge["from"], edge["to"], edge["type"]) for edge in payload["edges"]}
    assert (new.id, old.id, "supersedes") in edge_keys
    assert (conflict.id, old.id, "conflict") in edge_keys
    assert any(edge["type"] == "same-source" for edge in payload["edges"])
    assert any(edge["type"] == "temporal-adjacent" for edge in payload["edges"])


def test_graph_payload_aggregates_large_graph_by_kind_and_source(tmp_path):
    db = tmp_path / "memory.db"
    mem = DeepMemory(db)
    for idx in range(201):
        mem.add(f"semantic memory {idx}", kind="semantic", source="agent:a")
    mem.add("procedural memory", kind="procedural", source="agent:b")

    payload = build_graph_payload(db)

    assert payload["aggregated"] is True
    assert payload["record_count"] == 202
    group_ids = {node["id"] for node in payload["nodes"]}
    assert "group:semantic:agent:a" in group_ids
    assert "group:procedural:agent:b" in group_ids
    semantic_group = next(node for node in payload["nodes"] if node["id"] == "group:semantic:agent:a")
    assert semantic_group["count"] == 201
    assert semantic_group["label"] == "semantic · agent:a (201)"


def test_graph_payload_handles_empty_database(tmp_path):
    db = tmp_path / "memory.db"
    DeepMemory(db).close()

    payload = build_graph_payload(db)

    assert payload == {"nodes": [], "edges": [], "aggregated": False, "record_count": 0}


def test_timeline_payload_orders_by_event_time_then_created_at(tmp_path):
    db = tmp_path / "memory.db"
    mem = DeepMemory(db)
    late = mem.add("late", kind="working", event_time="2026-01-03T00:00:00+00:00")
    early = mem.add("early", kind="semantic", event_time="2026-01-01T00:00:00+00:00")

    payload = build_timeline_payload(db)

    assert [item["id"] for item in payload["items"]] == [early.id, late.id]
    assert payload["items"][0]["time"] == "2026-01-01T00:00:00+00:00"


def test_graph_and_timeline_pages_render_visualizations(tmp_path):
    db = tmp_path / "memory.db"
    mem = DeepMemory(db)
    mem.add("用户偏好：中文为主", kind="semantic", source="test")

    graph_html = render_graph(db)
    timeline_html = render_timeline(db)

    assert "Memory Graph" in graph_html
    assert "force-directed" in graph_html
    assert "same-source" in graph_html
    assert "Memory Timeline" in timeline_html
    assert "用户偏好：中文为主" in timeline_html
