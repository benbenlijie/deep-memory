#!/bin/bash
cd /home/ben/open-source/deep-memory
export PATH="$HOME/.local/bin:$PATH"
codex exec "Run this exact shell command and report the output: uv run deep-memory search .tmp/dm.db 'how do we verify changes'"
