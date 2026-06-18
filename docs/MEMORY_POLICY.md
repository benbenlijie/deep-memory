# Memory Write Policy

`deep-memory` is not designed to remember everything. The useful boundary is narrower: store compact, durable, inspectable facts that improve future agent work, and refuse or pause on data that would make the memory database unsafe or misleading.

This document defines the minimal memory-write policy layer used before durable writes through SDK, CLI, MCP, Hermes import, WebUI edit paths, and adapter wrappers.

## Policy decisions

Every candidate memory is classified into one of three outcomes:

| Decision | Meaning | Default behavior |
| --- | --- | --- |
| `allow` | Safe enough for normal durable memory if it is useful and scoped correctly. | Write may proceed. |
| `deny` | Too risky, stale, raw, or misleading to store as memory by default. | Refuse the write. |
| `requires_confirmation` | Potentially legitimate, but needs explicit user approval and narrow scope. | Refuse automatic writes; allow only with a consent-aware path. |

The implementation entry point is `deep_memory.privacy.evaluate_memory_write_policy(content)`. The hard guard used by write paths is `ensure_memory_content_allowed(content)`.

## Default allow

Allowed memories should be compact derived facts, not raw context. Good default examples:

- User preferences that the user clearly wants reused: language, tone, accessibility preference, preferred tools.
- Project or workspace conventions: build commands, coding style, architecture choices, review expectations.
- Verified procedural facts: a workflow that succeeded, a command sequence validated by tests, a reusable debugging or deployment procedure.
- Stable, non-sensitive domain facts needed for future work.
- Scoped team/project facts that do not profile private individuals.

Prefer records shaped like:

```text
Project convention: run uv run pytest -q and uv run ruff check . before review.
```

Avoid imperative global rules unless the user explicitly wants them. Prefer `source`, `confidence`, `importance`, `kind`, `scope`, `workspace`, `tenant`, and `expires_at` where available.

## Default deny

These categories are refused before storage by default:

1. Secrets and credentials
   - Passwords, API keys, OAuth tokens, session cookies, private keys, seed phrases, recovery codes, cloud credentials, `.env` values.
   - If it normally belongs in a password manager, keychain, SSH agent, cloud secret manager, or CI secret store, it is not memory.

2. Raw transcript or raw communication dumps
   - Full chat transcripts, emails, DMs, call transcripts, tool logs, browser history, screenshots, copied files, or arbitrary raw session output.
   - A short derived fact may be allowed if it passes the rest of this policy.

3. Temporary task status
   - PR numbers, issue numbers, commit SHAs, task IDs, “phase N done”, transient plans, current todo state, temporary failures, short-lived experiment output.
   - These belong in Kanban, Git, issue trackers, logs, or session history, not durable memory.

4. Harmful operational content
   - Credential replay, phishing, malware, stalking, surveillance, doxxing, evasion, unauthorized-access instructions or target profiles.

5. Unverified sensitive speculation
   - Guesses about identity, health, finances, political views, relationships, intent, or other sensitive attributes.

## Requires confirmation

These may be legitimate in some applications, but automatic writes must pause:

- Third-party private data, especially private contact details, medical, salary, family, relationship, or legal information.
- Raw personal contact details such as personal email addresses and phone numbers.
- Sensitive user data such as home address, legal identifiers, employment/financial history, health or biometric information.
- Any memory intended for team sharing, cloud sync, cross-device sync, or cross-agent sharing beyond the current local database.

A consent-aware path should capture: who approved it, scope, retention, source, and how to delete/export it. The current minimal guard exposes `confirmed_by_user` at the Python helper level for future consent-aware flows; CLI/MCP automatic writes should remain conservative.

## Covered write paths

The current implementation routes the following through the shared guard:

- Python SDK: `DeepMemory.add(...)`
- CLI: `deep-memory add ...`
- MCP: `add_memory(...)` and the MCP `add` tool, via `DeepMemory.add(...)`
- Hermes JSONL import: `write_hermes_session_facts(...)`, via `DeepMemory.add(...)`
- Codex wrapper facts import, via Hermes-style explicit facts import

WebUI edits are direct SQL updates for inspector usability. They should keep using the same policy boundary before editing content; this is the next place to tighten if WebUI becomes more than a local trusted inspector.

## Test plan

Regression tests should cover:

- secrets/credentials are refused from SDK, CLI, MCP, and Hermes import paths;
- raw transcript-shaped content is refused;
- temporary task status is refused;
- third-party private data returns `requires_confirmation`;
- verified procedural facts are allowed;
- normal dated facts such as `2026-06-16 ...` are not misclassified as phone numbers;
- README keeps only a short safety boundary and links here.

Current commands:

```bash
uv run pytest -q
uv run ruff check .
```

## Next implementation card

If this policy becomes stricter, create a follow-up implementation card for:

- consent-aware CLI/MCP options for `requires_confirmation` writes;
- WebUI edit validation with clear error banners;
- structured policy result objects exposed in MCP for preview/review flows;
- configurable allowlists by workspace or tenant;
- redaction utilities for converting raw context into minimal durable facts.
