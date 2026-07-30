Output "docs/launch/demo-terminal.gif"

Set FontFamily "JetBrains Mono"
Set FontSize "16"
Set Width 1200
Set Height 700
Set Padding 20
Set Theme "Dracula"

Hide

Type "cd /home/ben/open-source/deep-memory"
Enter

Type "rm -f .tmp/dm.db && uv run deep-memory init .tmp/dm.db"
Enter
Sleep 3s

Show

Type "opencode run 'Use the deep-memory CLI tool to save a memory to .tmp/dm.db. The memory content is: Project convention - run uv run pytest -q before code review. Use --kind procedural and --importance 0.8'"
Enter
Sleep 30s

Type "echo"
Enter
Sleep 1s

Type "codex exec 'Use the deep-memory CLI tool to search .tmp/dm.db for testing conventions. Run the search command and report what you find.'"
Enter
Sleep 30s
