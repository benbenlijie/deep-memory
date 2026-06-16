# Architecture

## System model

```text
agent event stream
  -> memory extractor
  -> memory engine
  -> SQLite / vector / graph stores
  -> retrieval planner
  -> agent context injector
```

## Core entities

- `MemoryRecord`: durable unit with content, layer, importance, confidence, source and timestamps.
- `SearchResult`: recalled memory with ranking score.
- `MemoryEngine`: future home for extraction, decay, contradiction detection, compression and skill generation.

## Why SQLite first

The root bottleneck is representation and lifecycle, not distributed storage. SQLite gives a transparent local baseline: easy install, inspectable state, deterministic tests, and a clean path to FTS/vector extensions later.
