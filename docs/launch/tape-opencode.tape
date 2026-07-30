Output "docs/launch/terminal-opencode.gif"

Set FontFamily "JetBrains Mono"
Set FontSize "14"
Set Width "1200"
Set Height "700"
Set Padding 16
Set Theme "Dracula"

Hide

Type "cd /home/ben/open-source/deep-memory"
Enter

Type "rm -f deep-memory.db && uv run deep-memory init deep-memory.db && uv run deep-memory add deep-memory.db 'This project requires running uv run pytest -q before code review.' --kind procedural --importance 0.8"
Enter
Sleep 4s

Show

Type "opencode"
Enter
Sleep 8s

Type "Save this to deep-memory: this project requires running uv run pytest -q before code review"
Enter
Sleep 30s

Ctrl+C
Sleep 2s
