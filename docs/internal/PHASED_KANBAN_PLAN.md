# Phased Kanban Plan: deep-memory → 100k-star OSS

## Root model

如果你退后一步看，100k star 不是一个单纯的增长目标，而是一个复合系统：

```text
root problem clarity → working artifact → trust evidence → integrations → community flywheel
```

所以 Kanban 不按“功能列表”拆，而按每一阶段必须证明的 bottleneck 拆。

## Existing top-level cards

- `t_a0b52e69` — P0 repo launch polish and first-screen conversion
- `t_2ab070e0` — P0 Hermes plugin MVP for deep-memory
- `t_fff43acf` — P0 memory benchmark v0
- `t_21867a44` — P0 Chinese retrieval baseline
- `t_30241c38` — P1 conflict resolution loop
- `t_f39ef073` — P1 MCP server adapter
- `t_363c0c08` — P0 launch assets and growth loop

## New phased cards

| Phase | Card | ID | Depends on |
| --- | --- | --- | --- |
| P0-A | Phase 0: define 100k-star north-star metrics and loop dashboard | `t_fde213bf` | t_a0b52e69 |
| P0-B | Phase 0: product positioning and competitor truth table | `t_08f0d29d` | t_a0b52e69 |
| P1-A | Phase 1: package release readiness and PyPI dry run | `t_f2e95675` | t_a0b52e69 |
| P1-B | Phase 1: quickstart examples and demo fixture | `t_93d8c99a` | t_a0b52e69 |
| P1-C | Phase 1: memory extraction API contract | `t_64f2f75b` | t_a0b52e69 |
| P2-A | Phase 2: Claude Code / Codex / OpenCode adapter specs | `t_4a901835` | t_2ab070e0, t_f39ef073 |
| P2-B | Phase 2: Chinese retrieval evaluation dataset v1 | `t_d9c2acac` | t_fff43acf |
| P2-C | Phase 2: Chinese retrieval implementation loop | `t_43a555be` | t_21867a44, t_d9c2acac |
| P3-A | Phase 3: memory inspector WebUI product spec | `t_0a2aff00` | t_30241c38 |
| P3-B | Phase 3: local WebUI MVP | `t_f3db9ee6` | t_0a2aff00 |
| P4-A | Phase 4: Memory-to-Skill generation design and prototype | `t_dbdcd456` | t_30241c38, t_f39ef073 |
| P4-B | Phase 4: MCP server hardening and agent interoperability test | `t_88879221` | t_f39ef073, t_4a901835 |
| P5-A | Phase 5: governance, privacy, and memory safety model | `t_a497f594` | t_f3db9ee6, t_88879221 |
| P5-B | Phase 5: community contribution architecture | `t_d504712c` | t_fde213bf, t_08f0d29d |
| P5-C | Phase 5: 100k-star launch/relaunch calendar | `t_fcdda293` | t_363c0c08, t_fde213bf, t_08f0d29d |
| R1 | Review gate: M+1 MVP credibility go/no-go | `t_5c275b1a` | t_fde213bf, t_08f0d29d, t_f2e95675, t_93d8c99a, t_64f2f75b, t_2ab070e0, t_fff43acf |
| R2 | Review gate: M+3 trust and retrieval credibility | `t_dcd77cd4` | t_43a555be, t_f3db9ee6, t_30241c38 |
| R3 | Review gate: M+6 ecosystem readiness | `t_11d7a978` | t_dbdcd456, t_88879221, t_a497f594 |

## Review gates

- R1 M+1 MVP credibility: repo + examples + package + extraction + plugin + benchmark.
- R2 M+3 trust/retrieval credibility: Chinese eval + retrieval delta + conflict loop + WebUI.
- R3 M+6 ecosystem readiness: MCP + adapters + Memory-to-Skill + safety model.

## Loop rule per card

Each card must close the same loop:

1. Define target and acceptance.
2. Produce artifact.
3. Collect evidence: test output, docs path, demo command, benchmark result.
4. Evaluate pass/partial/fail.
5. If fail, create a fix card rather than silently editing the goal.
6. Deposit durable knowledge into docs/tests/evals/skills.
