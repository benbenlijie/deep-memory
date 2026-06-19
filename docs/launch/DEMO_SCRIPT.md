# deep-memory 2-minute demo script

Audience: AI agent builders and developers who want their tools to remember useful state across sessions.

Goal: show the value in the first 10 seconds, then prove the product in under 2 minutes.

Estimated spoken length: about 280–310 words.

## 0:00–0:10 Hook

Every AI agent forgets.
Claude Code learns one repo convention.
Codex starts fresh.
OpenCode has to ask again.

What if memory were local, inspectable, and shared across agents?

## 0:10–0:30 Problem

Here is the real cost of forgetting: you repeat the same setup, the same preferences, and the same verification rules.
The agent looks smart in one session, then becomes a beginner again in the next one.

## 0:30–1:00 Solution

This is deep-memory: a local-first memory layer for AI agents.
It stores explicit facts and procedures in a project-local SQLite file.

Watch this.
I add one memory: “Chinese first, technical terms in English, keep replies concise.”
Then I search for it in a new session.
The answer comes back immediately.

Now I switch agents.
Same database.
Same recall.
That means Claude Code and Codex can share the same durable context without a cloud memory service.

## 1:00–1:30 Features

deep-memory is not just storage.
It is inspectable.
It has trust and provenance.
It can show graph and timeline views.
It supports Chinese retrieval.
And it keeps workspace scope separate so one project does not leak into another.

## 1:30–2:00 CTA

The point is simple: local-first, cross-agent, Chinese-first, and user-controlled.
If your agents should remember project conventions, preferences, and reusable procedures, try deep-memory.
The repo is open source, the database is yours, and the goal is to make agent memory something you can inspect and trust.

GitHub: https://github.com/benbenlijie/deep-memory
