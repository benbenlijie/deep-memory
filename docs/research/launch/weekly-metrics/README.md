# Weekly Launch Metrics

Use one file per launch week: `YYYY-WW.md`.

## Template

```md
# deep-memory launch metrics — YYYY-WW

## Summary

- Main launch experiment:
- Biggest bottleneck this week:
- Next bottleneck to attack:

## Metrics

| Layer | Metric | This week | Previous week | Target | Notes |
| --- | ---: | ---: | ---: | ---: | --- |
| Attention | GitHub stars |  |  | 100+ W1 |  |
| Attention | Repo visitors |  |  | 500+ W1 | GitHub traffic |
| Intent | Clone count |  |  | 50+ W1 | GitHub traffic |
| Activation | Quickstart success reports |  |  | 10+ W1 | Issues/comments/manual |
| Activation | CLI/API demo completions |  |  | 10+ W1 | Self-reported initially |
| Feedback | Memory failure cases submitted |  |  | 10+ W1 | Issue template |
| Feedback | Integration requests |  |  | 5+ W1 | Hermes/MCP/Claude/Codex/OpenCode |
| Quality | Blocking bugs/regressions |  |  | <5 W1 | Issues/CI |
| Community | PRs or serious contributors |  |  | 1–3 W1 | GitHub |

## Feedback taxonomy

- Positioning confusion:
- Quickstart friction:
- Retrieval failure:
- Memory governance:
- Integration demand:
- Trust/safety:

## Decisions

- If stars high but clones low → improve quickstart and first command path.
- If clones high but activation low → fix install/demo friction before new features.
- If “just a vector DB” confusion dominates → sharpen memory governance positioning.
- If Chinese retrieval complaints dominate → accelerate tokenizer/eval dataset.
- If integration requests dominate → prioritize Hermes/MCP adapter examples.

## Next launch experiment

- Channel:
- Hypothesis:
- Asset:
- Expected signal:
- Stop/continue rule:
```
