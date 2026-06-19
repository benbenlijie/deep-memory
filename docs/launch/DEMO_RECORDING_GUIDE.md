# deep-memory demo recording guide

This guide is for recording the 2-minute launch demo.

## 1. Recommended recording setup

### Terminal recording

Best default: asciinema.

Why:
- easy to record clean terminal sessions;
- lightweight;
- good for quick edits and subtitles later.

Alternative: terminalizer.

Use terminalizer if you want a more polished rendered video from a recorded terminal session, but expect a bit more setup.

### Screen recording for WebUI

Use OBS Studio if you want to capture terminal + browser + microphone in one pass.

Tips:
- set a simple scene with terminal on the left and browser on the right;
- use a fixed window size so the layout does not jump;
- zoom the browser enough that the search result and graph are readable;
- disable notifications.

## 2. Voiceover tips

- Speak slower than normal conversation.
- Leave a tiny pause after the hook line.
- Aim for clean, declarative sentences.
- Avoid long digressions about implementation details.
- If you miss a line, stop and rerecord the shot instead of improvising.

Practical pacing target:
- about 140–160 words per minute;
- keep the whole script near 300 words.

## 3. Recording flow

Suggested order:
1. record the terminal proof first;
2. record WebUI or graph shots second;
3. record the voiceover last, or record live if you are comfortable;
4. assemble clips in a simple editor.

## 4. Editing tool recommendation

Good default: DaVinci Resolve.

Why:
- strong enough for clean cuts, zooms, and captions;
- free version is usually enough;
- good if you want a polished final launch video.

If you want something lighter and faster, CapCut is fine for a short social clip.

## 5. Demo commands to verify before recording

These commands were tested in this workspace and are safe candidates for the demo flow:

```bash
uv run deep-memory init .tmp/demo-video/demo-agent.db
uv run deep-memory add .tmp/demo-video/demo-agent.db "用户偏好：中文为主，技术术语用英文；回答要简洁" --kind semantic --importance 0.9
uv run deep-memory add .tmp/demo-video/demo-agent.db "Project convention: run uv run pytest -q before review" --kind procedural --importance 0.8
uv run deep-memory search .tmp/demo-video/demo-agent.db "用户喜欢什么风格？"
uv run deep-memory search .tmp/demo-video/demo-agent.db "how do we verify changes?"
uv run deep-memory stats .tmp/demo-video/demo-agent.db
```

The repository also exposes these entry points that were checked via `--help`:

```bash
uv run deep-memory webui --help
uv run deep-memory codex-run --help
uv run deep-memory trust --help
uv run deep-memory scope --help
```

For the recorded video, keep the visible demo itself focused on the shortest proof path:
- init a DB;
- add one memory;
- search it back;
- open the WebUI;
- show the same DB across agents or sessions.

## 6. What to avoid

- Avoid typing too much on screen.
- Avoid scrolling long outputs.
- Avoid showing untested commands.
- Avoid overclaiming that memory is solved.
- Avoid cluttered desktop backgrounds or notifications.

## 7. Final sanity check

Before exporting the final video, confirm:
- the hook lands in the first 10 seconds;
- the memory retrieval is visible and readable;
- the WebUI shot does not feel like a separate product;
- the CTA is clean and short.
