# deep-memory demo storyboard

Use this as the shot-by-shot plan for a 2-minute recorded demo.

## Scene 1 — 0:00–0:10 Hook

On screen:
- Split screen or fast cut between two terminal sessions.
- Left: a fresh agent session.
- Right: a second agent session.

Voiceover:
- “Every AI agent forgets. Claude Code learns one repo convention. Codex starts fresh. OpenCode has to ask again.”
- “What if memory were local, inspectable, and shared across agents?”

Key visual moment:
- The word “forgets” should land immediately.
- Keep the split screen simple and high contrast.

## Scene 2 — 0:10–0:30 Problem

On screen:
- Terminal showing the same question asked twice.
- Optional quick cut to a note or README line that says the convention.

Voiceover:
- “The cost is repetition: setup, preferences, verification rules.”
- “The agent looks smart in one session, then becomes a beginner again in the next one.”

Key visual moment:
- Show the same instruction being repeated.
- Make the waste obvious, not abstract.

## Scene 3 — 0:30–1:00 Solution

On screen:
- Terminal with `deep-memory init`.
- Add one memory record.
- Search for that record in a new session.
- Optional small WebUI panel showing the same record.

Voiceover:
- “deep-memory is a local-first memory layer for AI agents.”
- “It stores explicit facts and procedures in a project-local SQLite file.”
- “Now I add one memory, then search it in a new session.”

Key visual moment:
- The search result returning instantly is the proof.
- If possible, show the same memory being retrieved after the session context is cleared.

## Scene 4 — 1:00–1:30 Features montage

On screen:
- WebUI graph view.
- Timeline or edit panel.
- Search result with Chinese text and English technical terms.
- A second workspace or scope indicator.

Voiceover:
- “This is not just storage.”
- “It is inspectable, with trust, provenance, graph and timeline views, Chinese retrieval, and workspace scope isolation.”

Key visual moment:
- Make the inspect/edit/delete affordance visible.
- Show that this is user-controlled state, not hidden behavior.

## Scene 5 — 1:30–2:00 CTA

On screen:
- GitHub repo page.
- README quickstart section.
- Optional one-line text overlay: “local-first • cross-agent • Chinese-first”.

Voiceover:
- “The point is simple: local-first, cross-agent, Chinese-first, and user-controlled.”
- “If your agents should remember project conventions, preferences, and reusable procedures, try deep-memory.”
- “The repo is open source, the database is yours, and the goal is to make agent memory something you can inspect and trust.”

Key visual moment:
- End on the GitHub URL and a clean, readable logo/title frame.

## Recording notes by shot

- Keep terminal font large enough to read on mobile.
- Cut out pauses and wait times.
- Prefer 1 idea per shot.
- Do not over-explain the architecture; the demo should feel like a sequence of proofs.
