#!/bin/bash
cd /home/ben/open-source/deep-memory
export PATH="$HOME/.local/bin:$PATH"
opencode run "Run this exact shell command and report the output: uv run deep-memory add .tmp/dm.db 'Project convention: run uv run pytest -q before code review' --kind procedural --importance 0.8"
