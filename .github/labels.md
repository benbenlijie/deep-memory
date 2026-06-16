# GitHub labels proposal

This file is a proposal for repository labels. Apply manually in GitHub settings or through `gh label create/edit` after review.

## Type

| Label | Color | Description |
| --- | --- | --- |
| `type:bug` | `d73a4a` | Code behavior is wrong or broken. |
| `type:docs` | `0075ca` | Documentation, examples, tutorials, or release notes. |
| `type:eval` | `5319e7` | Datasets, metrics, benchmarks, or failure taxonomy. |
| `type:feature` | `a2eeef` | New product capability. |
| `type:adapter` | `0e8a16` | Agent runtime, protocol, or memory backend integration. |
| `type:research` | `fbca04` | Design exploration that needs evidence before implementation. |

## Lane

| Label | Color | Description |
| --- | --- | --- |
| `lane:retrieval` | `1d76db` | Query parsing, FTS5, Chinese retrieval, embeddings, hybrid retrieval. |
| `lane:adapters` | `0e8a16` | Hermes, MCP, Claude Code, Codex, OpenCode, backends, protocols. |
| `lane:ui` | `c5def5` | CLI inspector, web editor, graph/timeline visualizer, correction UX. |
| `lane:evals` | `5319e7` | Memory failure cases, benchmark fixtures, metrics, leaderboard. |
| `lane:docs` | `0075ca` | README, architecture, guides, examples, troubleshooting. |

## Difficulty / workflow

| Label | Color | Description |
| --- | --- | --- |
| `good first issue` | `7057ff` | Small, well-scoped, no architecture decision required. |
| `help wanted` | `008672` | Useful contribution, may require some project familiarity. |
| `needs design` | `fbca04` | Discuss design/contract before implementation. |
| `blocked` | `b60205` | Waiting on another issue, decision, or external dependency. |

## Memory quality

| Label | Color | Description |
| --- | --- | --- |
| `memory-case` | `bfd4f2` | Concrete memory failure report. |
| `privacy-boundary` | `d4c5f9` | Should-not-remember, redaction, deletion, or data minimization. |
| `conflict-resolution` | `f9d0c4` | Contradictory, stale, superseded, or deprecated memory behavior. |
| `chinese-retrieval` | `fef2c0` | Chinese or mixed-language retrieval quality. |
| `memory-skill` | `c2e0c6` | Memory × Skill compounding path. |

## Priority

| Label | Color | Description |
| --- | --- | --- |
| `p0-launch` | `b60205` | Blocks launch credibility or first-screen conversion. |
| `p1-core` | `d93f0b` | Important for the near-term memory governance loop. |
| `p2-ecosystem` | `fbca04` | Useful for broader ecosystem growth. |
