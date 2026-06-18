# Safety and Privacy Model

`deep-memory` exists because long-lived agents need durable, inspectable memory. Stepping back, the root problem is not whether an agent can remember more — it is whether users can understand, control, correct, export, and delete what is remembered.

This document defines the default safety and privacy boundary for serious adoption. It is intentionally conservative: store less by default, make memory writes explicit, keep local-first control, and require stronger review before any memory changes future agent behavior.

## Design principles

1. Local-first by default
   - The default storage target is a user- or project-controlled local SQLite database.
   - Cloud sync, team sharing, hosted inference, or remote analytics must be explicit opt-in features, not hidden defaults.
   - Users should be able to inspect the database with normal local tools and the `deep-memory` CLI/WebUI.

2. Explicit durable facts, not raw transcript hoarding
   - The safe default is to store compact, user-relevant records that were intentionally selected as durable.
   - Raw conversations, full logs, screenshots, files, emails, browser histories, and arbitrary tool outputs are not memory by default.
   - Adapters should prefer an explicit facts contract, such as `facts` JSONL entries, rather than scraping entire sessions silently.

3. User control over the lifecycle
   - Users must be able to see what is stored, edit incorrect records, soft-delete records, export their data, and request hard deletion where supported.
   - Memory should include source and timestamps so users can understand where a record came from.
   - Contradictions should be surfaced as candidates for review, not silently resolved in ways the user cannot inspect.

4. Least privilege and least retention
   - Store only what is useful for future agent performance.
   - Use expiration, decay, confidence, importance, and deprecation states to avoid turning temporary context into permanent state.
   - Default write paths should reject or redact obvious secrets and high-risk data.

5. Memory should improve agency, not manipulate users
   - Personalization should help the user achieve their goals.
   - The system should not use memory for covert persuasion, dark patterns, behavioral exploitation, or hidden profiling.

## Threat model

A persistent memory layer changes the risk profile of an agent. The main hazards are:

- PII accumulation: small records can gradually become a sensitive profile.
- Secret leakage: API keys, passwords, cookies, recovery codes, private URLs, or credentials may be copied into memory.
- Consent drift: a user may share something in one context that should not become global memory.
- Wrong persistence: temporary status, stale decisions, or unverified model guesses may be recalled later as if they were durable facts.
- Cross-context leakage: memories from one project, tenant, client, or personal context may influence another.
- Over-recall: irrelevant memories can bias the agent or expose private data unnecessarily.
- Dual-use misuse: persistent memory can make agents more capable at surveillance, phishing, social engineering, or unauthorized profiling.

The safe model is therefore not “remember everything and filter later.” It is “select narrowly, store transparently, retrieve minimally, and keep the user in control.”

## What is never stored by default

The default policy is deny-by-default for high-risk categories. The following data must not be stored by default, even if it appears in a conversation, tool output, file, or web page:

1. Secrets and credentials
   - Passwords, passphrases, API keys, OAuth tokens, session cookies, SSH private keys, recovery codes, signing keys, database credentials, `.env` values, cloud credentials, payment secrets.
   - Authentication workarounds, bypass instructions, or reusable access tokens.

2. Raw sensitive personal data
   - Government IDs, passport numbers, driver license numbers, national ID numbers, tax IDs.
   - Bank account numbers, full payment card data, private wallet seed phrases.
   - Precise home addresses, private phone numbers, personal email addresses, unless the user explicitly asks to save them for a bounded purpose.

3. Health, biometric, and intimate data
   - Medical diagnoses, medications, genetic data, biometric identifiers, mental health notes, sexual or intimate information, family/relationship secrets.
   - These require explicit consent, narrow scope, and preferably a specialized application policy.

4. Children’s data and third-party private data
   - Information about minors.
   - Private facts about people who did not consent to being profiled by the memory system.

5. Raw communications and files
   - Full chat transcripts, emails, DMs, call transcripts, documents, browser history, clipboard contents, screenshots, audio/video recordings, source files, or tool logs.
   - A short derived durable fact may be stored only if it passes the consent and minimization policy.

6. Temporary operational state
   - One-off task status, issue numbers, PR numbers, commit SHAs, transient plans, temporary errors, current todo state, short-lived experiment outputs, rate-limit state.
   - These belong in logs, Kanban, GitHub, or session history, not durable memory.

7. Unverified model speculation
   - Guesses about user identity, beliefs, relationships, health, finances, political views, or intent.
   - Inferred sensitive attributes should not be stored as facts.

8. Content that enables harm
   - Instructions, target profiles, credentials, or operational details for phishing, malware, unauthorized access, stalking, surveillance, fraud, or evasion.

If an application needs any item above, it should implement an explicit consent flow, a specific retention policy, and domain-appropriate safeguards before writing it.

## PII policy

PII should be treated as a special-case exception, not a normal memory category.

Allowed by default:

- Low-risk preferences that the user clearly wants reused, such as language, tone, accessibility preference, preferred tools, or stable project conventions.
- Project-scoped facts that do not identify private individuals beyond necessary professional context.

Requires explicit consent:

- Contact details, addresses, legal identifiers, employment/financial/personal history, or any sensitive profile attribute.
- Durable facts about third parties.
- Any memory that will be shared across devices, team members, cloud services, or agents.

Recommended representation:

- Prefer abstracted preferences over raw details.
  - Better: “User prefers Chinese answers with English technical terms.”
  - Worse: raw copied paragraphs from a private conversation.
- Include scope when needed.
  - “Project X convention: ...” is safer than a global rule.
- Include source and confidence.
  - A memory should be traceable and correctable.

## Secrets policy

Secrets should never become memory records. The system should treat them as toxic data.

Minimum safeguards:

- Redact common secret patterns before storage.
- Warn and refuse obvious credential-looking writes.
- Current implementation: the core `DeepMemory.add` path rejects obvious credential labels, GitHub/OpenAI/AWS-style tokens, private key blocks, seed phrase labels, and raw email addresses. Because CLI `add`, Hermes import, MCP add, WebUI edit flows, and adapter wrappers all write through `DeepMemory.add`, this is a shared default guardrail rather than a CLI-only check.
- Do not include secrets in skill candidates, exports, issue reports, logs, or evaluation fixtures.
- Keep memory databases out of public repositories unless they contain only sanitized demo data.
- If a secret is accidentally stored, rotate the secret and hard-delete or rewrite the affected database backup chain where feasible.

A useful implementation rule: if the value would normally live in a password manager, `.env`, SSH agent, keychain, cloud secret manager, or CI secret store, `deep-memory` should not store it.

## Consent and write modes

`deep-memory` should support different write modes as the product matures:

1. Manual write
   - The user or developer explicitly calls `add`.
   - Safest default for SDK, CLI, WebUI, and MCP.

2. Proposed write
   - The agent proposes candidate memories for approval.
   - The user or reviewer accepts, edits, rejects, scopes, or expires each candidate.

3. Policy-gated automatic write
   - Only for low-risk, well-defined categories.
   - Must use allowlists, redaction, confidence thresholds, source tracking, and user-visible audit logs.

4. Prohibited automatic write
   - Secrets, sensitive PII, third-party private data, raw transcripts, and harmful operational content.

For early adoption, the recommended default is manual write or proposed write. Automatic memory should be introduced only after strong evaluation and clear user controls.

## Deletion model

Users need two kinds of deletion because memory systems also need auditability and undo.

1. Soft deletion
   - Mark a record as `deprecated`, hidden from normal retrieval, but retained for audit/recovery.
   - Useful for mistakes, contradictions, and reversible cleanup.
   - Current WebUI behavior uses this pattern for delete actions.

2. Hard deletion
   - Physically remove the record from the active database.
   - Required for privacy requests, accidental secret ingestion, or data minimization commitments.
   - Should be accompanied by guidance about backups, replicas, exports, and downstream copies.

Deletion requirements:

- Deleted records must not be returned by default search.
- Superseded records are treated like deleted records for default recall and export: they remain available in conflict/audit views, but `search` and `export` hide them unless the operator explicitly requests deprecated records for audit/backup.
- Search should make the active/deprecated boundary explicit for admin or audit views.
- If a record has been exported to another system, the user should be told that deletion in `deep-memory` may not erase external copies.
- Hard deletion should be available through CLI/API, even if soft deletion remains the safer UI default. Current CLI: `uv run deep-memory hard-delete <db> <memory-id>` physically removes one record from the active SQLite database; operators must still handle backups or external exports separately.

## Export and portability

User trust improves when memory is portable.

Export should support:

- JSONL for machine-readable backups and migration. Current CLI: `uv run deep-memory export <db>` exports active records only; add `--include-deprecated` only for explicit audit or backup workflows.
- Markdown or table views for human review.
- Filters by kind, source, time range, project, tenant, confidence, importance, and status.
- Clear separation between active and deprecated records.

Export should not silently include secrets, deprecated records, or cross-tenant data. For team or cloud contexts, export should be access-controlled and logged.

## Local-first defaults

The default deployment model should be:

- SQLite database controlled by the user or project.
- No network access required for core add/search/stats.
- Retrieval telemetry is on by default but stored only in the local SQLite database (queries, hit memory ids, scores, caller type). Disable with `DEEP_MEMORY_TELEMETRY=off`; hash-only mode with `DEEP_MEMORY_TELEMETRY_QUERY=hash`. See [`docs/TELEMETRY.md`](TELEMETRY.md).
- No remote model call required to inspect, edit, delete, or export memory.
- Optional integrations, such as MCP or hosted agents, configured explicitly by the user.

This matters because memory is not just application state. It is a long-lived representation of a person, project, organization, or workflow. Local-first defaults make the representation inspectable and reversible.

## Retrieval and context-injection safety

Safe storage is not enough. Recall can also leak or distort.

Retrieval should be bounded:

- Use task-specific queries and small limits.
- Do not inject the entire memory database into an agent prompt.
- Respect kind, source, project, tenant, and status filters.
- Prefer active, high-confidence, relevant records.
- Avoid recalling sensitive records unless the current task truly requires them.

Context injection should label recalled memory as memory, not as fresh user instruction. If a recalled record conflicts with the current user message, the current user message should normally win, and the contradiction should be surfaced for review.

## Multi-tenant and team use

Team adoption requires stricter boundaries than personal local use.

Recommended controls:

- Tenant or project namespace on every record.
- Access control for read, write, export, delete, and admin/audit views.
- Default no cross-tenant retrieval.
- Review workflow for shared procedural memories and skill candidates.
- Separate personal user preferences from organization/project conventions.
- Audit logs for writes, edits, deletes, exports, and policy overrides.

A personal memory system can be permissive with user-approved preferences. A team memory system should assume cross-context leakage is the main failure mode.

## Memory → Skill safety

Procedural memory is powerful because it can change future behavior. A skill is stronger than a recalled fact.

Safety requirements:

- Only L4 procedural memories are eligible for skill export.
- Skill candidates must include evidence, source trail, trigger reasons, and safety boundaries.
- Auto-install should remain disabled by default.
- Human or reviewer approval is required before promotion.
- Skill candidates must remove stale task IDs, private paths, secrets, raw PII, credentials, and one-off status.
- Skills must not encode bypasses around human approval, access controls, or safety policy.

The right threshold is: if the procedure would be unsafe in a shared repository or shared agent profile, it should not become a skill without redaction and scope narrowing.

## Dual-use risks

Persistent memory can make helpful agents more useful, but it can also make harmful agents more persistent.

High-risk misuse includes:

- Long-term profiling of people without consent.
- Social engineering based on remembered vulnerabilities or relationships.
- Phishing personalization.
- Stalking, surveillance, or doxxing.
- Credential harvesting or replay.
- Cross-session planning for unauthorized access or evasion.

Mitigations:

- Refuse to store harmful operational details.
- Avoid third-party private profiling by default.
- Keep consent and provenance visible.
- Add policy gates around shared, cloud, or automated writes.
- Make deletion/export practical, not theoretical.
- Evaluate retrieval for privacy leakage, not only relevance.

## Developer checklist

Before adding a new memory write path, answer:

- What exact data will be stored?
- Who consented to this storage?
- Is it a durable fact, or merely temporary context?
- Does it include PII, secrets, third-party private data, or harmful operational detail?
- What is the source, confidence, importance, kind, scope, and retention behavior?
- How can the user inspect, edit, delete, and export it?
- Could this memory leak across projects, tenants, users, or agents?
- What tests prove the write path rejects or redacts unsafe data?

Before adding a new retrieval path, answer:

- Why does this task need memory?
- What filters limit retrieval scope?
- How many records can be injected?
- Are deprecated or sensitive records excluded?
- How are conflicts with current user instructions handled?
- What evidence shows retrieval improves the task without leaking unrelated data?

## Current implementation and remaining governance gaps

The current MVP already has local SQLite storage, explicit Hermes fact import, MCP add/search/stats, WebUI inspection/edit/soft-delete, Memory → Skill candidate export, JSONL export, hard-delete, and shared secret/PII write-path refusal for obvious high-risk patterns.

Implemented guardrails:

1. `export` CLI/API emits active records by default and excludes deprecated or superseded records unless the operator explicitly opts into audit/backup scope.
2. `hard-delete` CLI/API physically removes one record from the active SQLite database.
3. `DeepMemory.add` rejects obvious credential labels, common token formats, private key blocks, seed phrase labels, and raw email addresses before persistence; CLI add and Hermes import surface this as a user-visible validation error.
4. Default `search` excludes deprecated and superseded records across FTS, LIKE fallback, and supplement ranking.
5. Regression tests cover export default behavior, explicit deprecated export, hard-delete, superseded export exclusion, CLI secret refusal, and Hermes import secret refusal.

Remaining gaps before multi-agent/team memory sharing:

1. Record scoping fields for project/tenant/user context.
2. Access control and audit logs for read, write, export, delete, and policy overrides.
3. More complete sensitive-data detection/redaction beyond obvious regex patterns, especially phone numbers, addresses, government IDs, and locale-specific identifiers.
4. Proposed-write review workflow for automatic extraction.
5. Backup/replica deletion workflow and external export revocation guidance.
6. Scoped retrieval filters that default to active, tenant-bounded, non-sensitive records.

The interesting question is not whether memory can become larger, but whether it can become governable. A memory layer that users can inspect, constrain, correct, and delete is much more likely to become trusted infrastructure.
