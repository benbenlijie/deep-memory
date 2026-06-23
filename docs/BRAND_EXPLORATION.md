# deep-memory Brand Exploration

## Decision

Recommendation: **minimal logo now; full visual identity later**.

If you退后一步看，`deep-memory` 现在真正需要的不是一套完整品牌系统，而是一个很轻的识别锚点：在 GitHub README、docs、demo video、social launch 里让人一眼记住“这是那个 local-first、inspectable agent memory 项目”。

不要现在做重品牌。这个阶段的信任主要来自：清晰定位、可运行 quickstart、可检查 SQLite artifact、eval evidence、治理边界。Logo 只能辅助这些信任信号，不能替代它们。

## Why a minimal logo is useful now

`deep-memory` 已经不是一个纯代码片段，它有：

- README homepage framing: “Local-first memory for AI agents. Inspect what they remember. Decide what they keep.”
- 架构图与 docs launch assets
- GitHub/social launch material
- cross-agent / MCP / WebUI / Memory → Skill 的生态叙事

这类项目受益于一个轻量视觉标识，原因不是“更像公司”，而是：

1. **Reduce cognitive load**
   - 读者第一次打开 README 时，项目名 + tagline + 一个简单图形，可以更快形成 mental model。

2. **Signal category without hype**
   - memory infra 很容易被误解成“又一个 vector DB”或“自动记住一切”。一个克制的本地 artifact / inspectable memory 图形，可以把注意力拉回真正机制。

3. **Reusable launch asset**
   - GitHub README、docs favicon、demo thumbnail、X/Reddit/HN social card 都需要一个 consistent anchor。

4. **Trust boundary**
   - 对 memory 工具来说，品牌不能太 magical。它应该暗示：local, governed, inspectable, explicit, boring-in-a-good-way。

## What not to do now

不要做 full visual identity 现在。

不建议现在投入：

- complicated mascot
- glossy AI brain imagery
- cyberpunk neon identity
- overly anthropomorphic memory character
- heavy brand book / marketing design system
- “AGI memory OS” 这类过度宏大的视觉语言

这些会把项目推向 hype。`deep-memory` 的信任来自可验证机制，不来自神秘感。

## Brand principles

The visual system should feel:

1. **Calm infra**
   - 像 SQLite / DuckDB / OpenTelemetry 这类可依赖基础设施，而不是消费级 AI app。

2. **Local-first**
   - 图形最好暗示 file / database / local artifact，而不是云端网络。

3. **Inspectable memory**
   - Memory 不是黑箱。应该有 layer、window、record、trace、grid、index 这些可检查感。

4. **Governed state**
   - 不是“记住一切”，而是 explicit durable facts + lifecycle + review boundary。

5. **Small-team credible**
   - 不要过度设计。一个好 SVG、2–3 个颜色 token、README usage rules 足够。

## Recommended first identity shape

Use **simple glyph + optional wordmark**.

- GitHub README top: glyph + `deep-memory` wordmark optional
- GitHub social preview / docs favicon: glyph only
- README body and docs: mostly text-first; logo should not dominate
- CLI/package context: text-only `deep-memory` remains primary

Why not text-only?
- Text-only is acceptable, but it gives less recall for social/demo assets.

Why not full icon + mascot?
- Too much personality too early; wrong trust signal for memory governance infra.

Why not complex wordmark?
- Hard to maintain and less useful in small sizes.

## Three lightweight directions

### Direction A — Local Memory Cell

Shape:
- Rounded square container
- Small database/file stack inside
- A few visible record lines or dots
- A subtle “inspection window” cutout

Rationale:
- Best fit for local-first infra.
- Feels calm, portable, inspectable.
- Works at small sizes.

Potential risk:
- May feel generic if not paired with a strong wordmark/tagline.

Best use:
- Default GitHub/social/docs icon.

### Direction B — Memory Trace / Recall Loop

Shape:
- A small loop or path connecting records
- One highlighted recall node
- Optional square boundary showing “local scope”

Rationale:
- Captures `what to remember → when to recall → when to decay/forget`.
- More dynamic and research-flavored.
- Good for diagrams and docs.

Potential risk:
- Could drift into generic graph/agent imagery.

Best use:
- Secondary docs motif, architecture diagrams, slides.

### Direction C — DM Monogram as Database Layers

Shape:
- Minimal `d/m` monogram built from stacked layers or terminal-like strokes
- Could sit in a rounded square

Rationale:
- Strongest as a project identity mark.
- More ownable than generic database icon.
- Useful for favicon/social avatar.

Potential risk:
- Monograms often become clever but less semantically clear.

Best use:
- Later refinement if the project gains traction.

## Recommended color system

Use a narrow, calm palette aligned with current architecture SVG.

Core tokens:

```text
--dm-bg:        #020617  /* slate-950 */
--dm-surface:   #0f172a  /* slate-900 */
--dm-text:      #e2e8f0  /* slate-200 */
--dm-muted:     #94a3b8  /* slate-400 */
--dm-cyan:      #38bdf8  /* recall / retrieval */
--dm-green:     #34d399  /* explicit writes / governed memory */
--dm-purple:    #a78bfa  /* SQLite / storage layer */
--dm-amber:     #fbbf24  /* eval / audit signal */
```

Default logo color:
- dark background: slate + cyan + green
- light background: dark slate outline + cyan/green accents

Avoid:
- red-heavy palette unless indicating safety warnings
- black-box AI gradients
- overly bright neon
- too many colors in the logo itself

## Usage rules

1. **README top**
   - Keep the existing H1 `# deep-memory`.
   - Optional: add centered logo above the tagline only if it does not push quickstart too far down.
   - Better first step: use the icon in social preview/docs assets, not necessarily above the fold.

2. **GitHub social preview**
   - Use icon + tagline:
     - `deep-memory`
     - `Local-first memory for AI agents`
     - `Inspect what they remember. Decide what they keep.`

3. **Docs / demo**
   - Use the glyph as a small navigation mark or slide corner.
   - Do not use it as a huge hero unless the page has enough proof below it.

4. **CLI / package**
   - Keep text-first. The terminal experience should remain boring and clear.

5. **Do not imply hosted service**
   - Avoid cloud shapes unless clearly marked as non-core roadmap.
   - The mark should feel like a local artifact, not SaaS memory cloud.

## First SVG draft

Created draft:

- `docs/assets/deep-memory-logo.svg`

This implements Direction A: **Local Memory Cell**.

It is intentionally simple:

- rounded square = local bounded scope
- stacked bars = SQLite/file-backed durable records
- cyan inspection window = inspectability / retrieval
- green dot = explicit accepted memory write
- no brain, no cloud, no mascot

## README/social recommendation

For now, do **not** immediately insert the logo into the README H1 until launch copy is settled. Use it first as:

1. GitHub social preview base asset
2. docs/favicon or docs header mark
3. demo video corner / thumbnail
4. optional small README centered image after the language switch if it visually improves scanability

Suggested README insertion if later approved:

```html
<p align="center">
  <img src="docs/assets/deep-memory-logo.svg" alt="deep-memory logo" width="120">
</p>
```

Keep width between `96` and `140`. Larger than that risks making the repo feel more like a marketing site than infra.

## Final recommendation

Decision: **minimal logo now**.

Use Direction A as v0. Treat it as a lightweight identity anchor, not a brand campaign. Revisit full visual identity only after one of these becomes true:

- the repo has meaningful external contributors
- docs site exists beyond README
- social/demo launch needs repeated visual templates
- users start recognizing the project and consistency becomes valuable

The root bottleneck is still trust and verification, not visual polish. The logo should quietly reinforce the trust model: local artifact, explicit memory, inspectable state.
