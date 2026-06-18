# Memory Inspector WebUI Spec

## Product thesis

The memory layer only becomes trustworthy when users can inspect, correct, and delete what the agent thinks it knows.
This WebUI is the trust layer for deep-memory: it turns hidden state into reviewable state.

## Goals

- Let users understand what the system remembers and why.
- Let users correct incorrect memory without breaking provenance.
- Make conflicts visible instead of silently merging them away.
- Let procedural memories graduate into skill candidates only after review.
- Keep the UI local-first, fast, and safe by default.

## Non-goals

- No cloud sync in Phase 1.
- No collaborative editing or multi-user permissions model yet.
- No automatic destructive mutation from model output alone.
- No complex graph visualization before the core review flows work.

## Information architecture

The WebUI has four primary screens plus a shared detail drawer:

1. Timeline
2. Semantic facts
3. Conflicts
4. Skill candidates
5. Memory detail / audit drawer

Navigation should be simple and persistent, with the current database path visible in the header.

## Screen 1: Timeline

Purpose: show episodic memory as a chronological narrative.

Primary content:

- session or interaction id
- timestamp range
- event summary
- linked source(s)
- resulting memory records
- whether the event created, updated, superseded, or conflicted

Behavior:

- default sort: newest first
- filter by kind: episodic / semantic / procedural / working
- filter by source: Hermes session, CLI, MCP, imported JSONL, manual edit
- click a timeline item to open the detail drawer
- allow search over event text and source metadata

What users should learn here:

- when a fact entered the system
- what triggered a change
- whether the memory came from a session, manual edit, or import

## Screen 2: Semantic facts

Purpose: inspect durable facts the agent relies on.

Columns:

- content
- kind
- confidence
- importance
- source
- created_at
- updated_at
- status

Status values:

- active
- candidate
- superseded
- deprecated
- deleted_tombstone

Interactions:

- inline edit for content, confidence, importance, and tags
- open detail drawer for source trail and linked records
- bulk select for export, delete, or supersede
- sort by recency, importance, confidence, or status
- search by exact phrase, entity, or source

Trust cues:

- show confidence and importance on every row
- visually distinguish stale or superseded facts
- make the current active fact obvious when multiple versions exist

## Screen 3: Conflicts

Purpose: surface contradictions that need human resolution.

A conflict row should show:

- conflicting values or normalized key
- competing memory records
- why the system thinks they overlap
- recency / confidence comparison
- current resolution state

Resolution actions:

- confirm one record as current
- reject one record
- merge two records into a new canonical fact
- mark as unresolved for later review

Conflict policy:

- do not auto-delete lower-confidence candidates
- keep all source records in the audit trail
- require explicit user action before a conflict becomes a canonical replacement

## Screen 4: Skill candidates

Purpose: show procedural memories that may become reusable skills.

A skill candidate should display:

- short procedural summary
- triggering evidence
- success history
- recurrence likelihood
- safety notes
- promotion status

Actions:

- edit the candidate summary
- mark as not reusable
- export as skill markdown draft
- attach review notes
- approve for skill generation

Promotion rule:

- only procedures with repeated success and no secrets, ephemeral IDs, or one-off status should be promotable
- promotion requires a human review gate

## Screen 5: Memory detail / audit drawer

Purpose: make every visible item explain itself.

The drawer should show:

- full content
- normalized form if applicable
- source trail
- extraction or import metadata
- edits over time
- supersession chain
- deletion state
- related conflicts
- related skill candidates

This is the core trust affordance: users can see not just what the system believes, but how that belief evolved.

## Edit flow

1. User opens a memory row or drawer.
2. User edits content or metadata.
3. UI shows before / after diff.
4. User confirms the change.
5. System writes a new revision and keeps the previous revision in the audit log.
6. Timeline updates with an edit event.

Rules:

- edits are append-only at the audit layer
- the visible current value may change, but the previous value is never lost
- edits must preserve source linkage and timestamps

## Delete flow

1. User selects delete.
2. UI warns about permanence and audit consequences.
3. User confirms.
4. System marks the record deleted and retains a tombstone.
5. Tombstone includes record id, deletion time, actor, and reason.

Delete policy:

- hard delete is reserved for internal maintenance later
- user-facing delete means soft delete with tombstone by default
- deleted items remain visible in audit mode

## Supersede flow

1. User opens a fact that has become outdated.
2. User chooses supersede.
3. User enters the new canonical value.
4. System creates a new active record linked to the old one.
5. The old record becomes superseded, not erased.
6. Conflict list and timeline reflect the transition.

Supersede rules:

- preserve the old source trail
- link old and new records bidirectionally
- do not silently overwrite without a history entry
- the new value should be the explicit canonical replacement

## Audit trail requirements

Every mutation must emit an auditable event.

Minimum audit fields:

- event_id
- actor
- action type
- target record id
- before snapshot
- after snapshot
- timestamp
- reason or user note
- source channel if applicable

Audit invariants:

- append-only event log
- no silent mutation
- all destructive operations record the actor and confirmation path
- imports should be distinguishable from manual edits

## Minimal tech choice

Phase 1 should stay deliberately small:

- frontend: local React or a lightweight server-rendered UI
- backend: existing local Python service or FastAPI endpoint layer
- storage: the existing SQLite database
- auth: local session only, no remote login in Phase 1

Recommended MVP shape:

- FastAPI serves JSON endpoints and static assets
- React or HTMX renders the four screens
- the UI reads from the same SQLite database used by the memory engine

Why this choice:

- local-first and inspectable
- easy to prototype
- matches the current project architecture
- keeps the trust layer close to the data layer

## Accessibility constraints

The UI must be usable without a mouse and readable under stress.

Requirements:

- full keyboard navigation for tables, dialogs, filters, and drawers
- visible focus states
- sufficient color contrast for status states
- text labels for icons and action buttons
- confirmation dialogs that are screen-reader friendly
- no meaning conveyed by color alone
- row selection and destructive actions must be reachable from the keyboard
- readable density: avoid cramped tables and tiny metadata text

## Trust principles

- Show the source before asking the user to trust the memory.
- Make conflicts explicit instead of hiding them.
- Never delete evidence just because a canonical fact exists.
- Prefer reversible operations with clear audit history.
- Let users inspect and control the system before any automation is expanded.

## Open implementation questions

- Should the first version be server-rendered or SPA-style?
- Do we need pagination now, or is filtered local search enough for the MVP dataset?
- Should skill candidate promotion happen in the UI or via a separate export workflow?
- Do we want tombstones visible by default or only in audit mode?

## Success criteria for this phase

- Users can inspect timeline, semantic facts, conflicts, and skill candidates.
- Users can edit, delete, and supersede memories with an audit trail.
- The interface clearly exposes source, confidence, and status.
- The UI remains local-first and keyboard accessible.
