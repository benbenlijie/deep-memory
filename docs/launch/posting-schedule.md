# Launch posting schedule recommendation

Timezone baseline: Asia/Shanghai, with US windows converted where useful.

## Recommended launch order

1. Twitter/X thread first, to create a canonical short narrative and media anchor.
2. Hacker News next, once the repo README, benchmark doc, and quickstart links are stable.
3. Reddit posts after HN, with the community-specific framing and benchmark table.
4. Chinese platforms after the English launch window, using the natural Chinese version and README.zh-CN.md link.

## Suggested days and times

| Platform | Best window | Asia/Shanghai equivalent | Why |
| --- | --- | --- | --- |
| Twitter/X | Tue-Thu, 8:00-10:00 US Pacific | Tue-Fri, 23:00-01:00 CST | Good overlap for US dev audience; thread can gather early signals before HN/Reddit. |
| Hacker News | Tue-Thu, 7:00-9:00 US Pacific | Tue-Fri, 22:00-00:00 CST | Catches US morning and Europe afternoon; avoid Friday/weekend unless intentionally lower-noise. |
| Reddit r/LocalLLaMA | Tue-Thu, 9:00-11:00 US Eastern | Tue-Fri, 21:00-23:00 CST | Community is active during US workday; technical posts need comments answered quickly. |
| Reddit r/MachineLearning | Mon-Wed, 9:00-11:00 US Eastern | Mon-Wed, 21:00-23:00 CST | Discussion posts do better when framed as eval/design feedback rather than launch marketing. |
| V2EX | Tue-Thu, 09:30-11:30 CST | Same | Domestic dev traffic is strong before lunch; comment response matters. |
| 掘金 | Tue-Thu, 10:00-12:00 CST or 19:30-21:30 CST | Same | Technical article discovery works during work breaks and evening reading. |

## Concrete 2-day plan

Day 1:

- 22:30 CST: publish Twitter/X thread.
- 23:00 CST: submit Hacker News post.
- 23:15-01:00 CST: stay online to answer HN/Twitter comments with technical details, not hype.

Day 2:

- 21:30 CST: post r/LocalLLaMA.
- 22:00 CST: post r/MachineLearning discussion version.
- Next morning 10:00 CST: post V2EX.
- Same day 19:30 CST: post 掘金 article.

## Launch checklist

- GitHub repo: https://github.com/benbenlijie/deep-memory
- Benchmark doc: https://github.com/benbenlijie/deep-memory/blob/main/docs/COMPETITIVE_BENCHMARK.md
- Quickstart: https://github.com/benbenlijie/deep-memory#quickstart
- Chinese README: https://github.com/benbenlijie/deep-memory/blob/main/README.zh-CN.md
- 30s demo media: record quickstart + WebUI inspect/search flow before posting the Twitter/X thread.
- Comment posture: technical, humble, concrete. Avoid “solves memory” language; say “small regression checks” and “controlled preview”.
