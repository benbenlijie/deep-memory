---
name: deep-memory-agent
description: Use when an AI agent has deep-memory installed and needs to decide when to search memory, when to write durable semantic/procedural memory, and when not to remember transient, private, or unverified material.
version: 0.1.0
author: deep-memory contributors
license: MIT
metadata:
  deep_memory:
    auto_install: false
    install_boundary: review_required
    default_db: ~/.deep-memory/deep-memory.db
  hermes:
    tags: [memory, agent-memory, deep-memory, safety, skills]
    related_skills: []
---

# deep-memory-agent

Auto-install: no — review required before installing this candidate into any active agent skill directory.

## Overview

Use this candidate skill as the first-party operating guide for agents that have access to `deep-memory`. The root problem is not “remember more”. It is deciding which prior context is worth retrieving, which new facts or procedures are durable enough to store, and which information should deliberately stay out of memory.

`deep-memory` is a local, inspectable memory layer for AI agents. The default database path is `~/.deep-memory/deep-memory.db`. Records are governed by `kind`, `scope`, `scope_id`, confidence, importance, provenance, and deletion/rollback tools.

## When to use

Search memory before starting work when any of these are true:

- The task is large, multi-step, risky, or likely to depend on prior user preferences or project conventions.
- The user references “last time”, “previously”, “our usual way”, a project name, a workflow, or a past decision.
- You are entering a known workspace and need repo-specific commands, constraints, architecture decisions, or safety boundaries.
- You are about to make a persistent change: code, config, docs, credentials setup, deployment, automation, or agent behavior.
- You are unsure whether a relevant convention already exists and a short search could prevent rework.

Write memory only after verification when the information is durable and useful across future sessions:

- Semantic memory: stable user preferences, project conventions, architecture decisions, tool quirks, environment facts, or domain constraints.
- Procedural memory: repeated workflows, troubleshooting playbooks, verification loops, install sequences, or review checklists that worked and are likely to recur.
- Evidence-backed lessons: a failure mode plus the verified fix, when it is not merely a one-off status update.

## When not to use

Do not write memory for:

- Temporary task state, progress notes, stale task IDs, PR numbers, issue numbers, commit SHAs, run IDs, or “phase done” updates.
- Secrets, API keys, cookies, passwords, private tokens, recovery codes, or authentication bypass details.
- Raw transcript dumps, unredacted logs, raw PII, private customer/user data, or sensitive personal information.
- Unverified speculation, guesses, model impressions, or hypotheses that have not survived a real check.
- One-off commands that should be fixed in docs/tests instead of preserved as agent behavior.
- Anything that would be unsafe or embarrassing if exported into a shared skill, public repo, or multi-agent memory store.

Do not search memory when the answer must come from current system state, current time/date, live web facts, file contents, git state, or command output. Use the appropriate live tool first, then optionally write a durable lesson if the result is stable and reusable.

## Commands

Set the database explicitly in scripts so agents and humans inspect the same store:

```bash
MEMORY_DB=${MEMORY_DB:-~/.deep-memory/deep-memory.db}
```

Search before a substantial task:

```bash
deep-memory search "$MEMORY_DB" "project conventions and relevant prior decisions" \
  --scope project \
  --scope-id <project-or-workspace-id> \
  --limit 5
```

Search user-level preferences:

```bash
deep-memory search "$MEMORY_DB" "user communication preferences and durable constraints" \
  --scope user \
  --scope-id <user-id> \
  --limit 5
```

Search across scopes only when the task genuinely needs broad recall:

```bash
deep-memory search "$MEMORY_DB" "reusable workflow for this failure mode" \
  --all-scopes \
  --limit 10
```

Add a verified semantic memory:

```bash
deep-memory add "$MEMORY_DB" \
  "Project X uses uv and requires uv run pytest -q plus uv run ruff check . before review." \
  --kind semantic \
  --scope project \
  --scope-id project-x \
  --importance 0.8 \
  --confidence 0.9 \
  --source "verified:repo-docs-and-test-run"
```

Add a verified procedural memory:

```bash
deep-memory add "$MEMORY_DB" \
  "Workflow: before changing Project X, search project memory, run the targeted test first, implement the minimal change, then run uv run pytest -q and uv run ruff check . before handoff." \
  --kind procedural \
  --scope project \
  --scope-id project-x \
  --importance 0.85 \
  --confidence 0.9 \
  --source "verified:successful-change-loop"
```

Inspect and edit memory through the local WebUI:

```bash
deep-memory webui "$MEMORY_DB" --host 127.0.0.1 --port 8765
```

## Scope policy

Use the narrowest scope that will still help the future agent.

| Scope | Use for | Example `scope_id` |
| --- | --- | --- |
| `global` | Rare conventions that should apply everywhere on this machine. | `default` |
| `user` | Stable user preferences and personal working style. | `ben` |
| `workspace` | A local workspace, monorepo, or machine-specific setup. | `open-source` |
| `project` | Repository/product-specific conventions and decisions. | `deep-memory` |
| `tenant` | Team, customer, environment, or organization isolation. | `acme-prod` |

Rules:

1. Prefer `project` for repo-specific commands, architecture, and workflows.
2. Prefer `user` for durable preferences that should follow the user across projects.
3. Prefer `workspace` for machine-local paths or toolchain details.
4. Use `global` sparingly; it creates the highest risk of irrelevant recall.
5. Always set `scope_id` for non-global records. A scope without a precise `scope_id` is usually too broad.
6. When in doubt, write narrower now and promote later after repeated evidence.

## Search loop

1. Define the task and likely namespaces.
2. Run one or two targeted `deep-memory search` queries.
3. Read only the relevant results; ignore stale or low-confidence material.
4. Treat memory as context, not proof. Verify against live files, commands, docs, or user-provided facts before acting.
5. If memory conflicts with current evidence, trust current evidence and consider adding a corrected memory after verification.

## Write loop

1. Ask whether the information will still matter in future sessions.
2. Classify it as `semantic` or `procedural`; avoid writing vague mixed records.
3. Require evidence: command output, test result, file/document check, successful workflow, or explicit user correction.
4. Remove secrets, raw transcript text, stale task IDs, temporary status, and one-off paths unless the path is itself a durable workspace fact.
5. Choose the narrowest `scope` and precise `scope_id`.
6. Write one compact declarative record.
7. Search for the record immediately to verify it is retrievable.
8. If the memory is wrong or unsafe, remove or correct it instead of leaving hidden drift.

## Verification

Before claiming deep-memory is working for an agent, run a temporary smoke test against an explicit database:

```bash
TMP_DB=$(mktemp -t deep-memory-skill-smoke.XXXXXX.db)
deep-memory init "$TMP_DB"
deep-memory add "$TMP_DB" \
  "Workflow: deep-memory smoke test writes and retrieves a scoped procedural memory." \
  --kind procedural \
  --scope project \
  --scope-id deep-memory-skill-smoke \
  --importance 0.8 \
  --confidence 0.9 \
  --source smoke-test
deep-memory search "$TMP_DB" "smoke test scoped procedural memory" \
  --scope project \
  --scope-id deep-memory-skill-smoke \
  --limit 3
deep-memory webui "$TMP_DB" --host 127.0.0.1 --port 8765
```

Expected result: search returns the smoke-test record with `scope=project`, `scope_id=deep-memory-skill-smoke`, and `kind=procedural`. WebUI opens locally and lets the reviewer inspect the same database. Stop the WebUI after inspection.

For normal task use, verify any new durable record with a follow-up search:

```bash
deep-memory search "$MEMORY_DB" "distinctive phrase from the memory" \
  --scope <scope> \
  --scope-id <scope_id> \
  --limit 3
```

## Rollback

If a memory should not have been written:

1. Inspect it in WebUI or search results and identify the exact record.
2. Prefer an explicit correction memory only when future agents need to understand the change.
3. Use the project’s supported delete/soft-delete/hard-delete path for unsafe records. For secrets or raw PII, hard-delete and rotate the exposed secret outside deep-memory.
4. Re-run search to confirm the unsafe or obsolete record is no longer returned.
5. If the bad record came from this skill being too broad, revise this candidate before installation.

## Review checklist

Before installing this candidate as an active Hermes or other agent skill:

- [ ] Frontmatter is valid and description is under 1024 characters.
- [ ] Auto-install is explicitly `no`; installation requires human review.
- [ ] The skill says when to search, when to write, and when not to remember.
- [ ] It names `deep-memory search`, `deep-memory add`, and `deep-memory webui` with the default database path.
- [ ] It defines `global`, `user`, `workspace`, `project`, `tenant`, and `scope_id` policy.
- [ ] It forbids secrets, raw transcript dumps, raw PII, stale task IDs, and unverified speculation.
- [ ] It includes verification and rollback steps.
- [ ] It contains no real credentials, private data, stale task IDs, PR numbers, issue numbers, or commit SHAs.
