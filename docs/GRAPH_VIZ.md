# Memory Graph Visualization

`deep-memory webui` exposes two relationship-oriented views in addition to the editable memory list:

- `/graph` renders a force-directed graph of memory records.
- `/graph.json` returns the graph data as JSON for tests, integrations, or custom clients.
- `/timeline` renders records in event-time order.
- `/timeline.json` returns the timeline data as JSON.

## Nodes

Each node is one memory record when the database has 200 records or fewer. The node title contains a content snippet and compact metadata, and clicking a node opens `/edit?id=<memory_id>` in the local editor.

Node colors follow memory `kind`:

| kind | color | meaning |
| --- | --- | --- |
| `working` | blue | short-lived task context |
| `episodic` | orange | session/event memory |
| `semantic` | green | durable facts/preferences |
| `procedural` | purple | reusable workflows or skills |

## Edge types

The graph makes four relationship classes visible:

| edge | style | meaning |
| --- | --- | --- |
| `supersedes` | red arrow | source record explicitly supersedes the target via `supersedes_id` or `superseded_by_id`. |
| `conflict` | yellow dashed arrow | source record is a conflict candidate pointing at the record it may replace. |
| `same-source` | thin gray line | adjacent records from the same `source`, useful for spotting import/session clusters. |
| `temporal-adjacent` | light blue line | adjacent records in `event_time, created_at` order, useful for seeing chronology. |

`conflict` is intentionally separated from `supersedes`: a candidate relation should be reviewed before being treated as a resolved replacement.

## Aggregation rule

When the database has more than 200 records, `/graph` automatically collapses records by `(kind, source)`.

A group node has this id shape:

```text
group:<kind>:<source>
```

The node label includes the group size, for example:

```text
semantic · agent:a (201)
```

Edges between groups are counted and labelled with the edge type plus count. Edges inside a group are omitted in aggregated mode to keep the visualization readable.

## Timeline

`/timeline` orders memories by `event_time`, falling back to `created_at`. This gives a useful view today and becomes more meaningful as bi-temporal memory semantics mature.

## Performance limits

The force-directed view is designed as a local demo and inspector, not a large-scale graph database UI.

Recommended limits:

- best experience: fewer than 200 records, unaggregated;
- acceptable: fewer than 1,000 records, aggregated by `(kind, source)`;
- above 1,000 records: prefer filtering/exporting JSON and using a dedicated graph tool.

The WebUI remains local-first and binds to `127.0.0.1` by default; the graph view does not add telemetry or remote sync.
