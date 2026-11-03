#!/usr/bin/env bash
# Install this global Claude Code config into ~/.claude (Linux, macOS, Git Bash on Windows).
# Usage: bash install.sh [repo-url]
# Files in ~/.claude that the repo also tracks are backed up to ~/.claude/backups/pre-config-<timestamp>/.
# Everything else in ~/.claude (credentials, sessions, projects) is left untouched.
set -euo pipefail

repo="${1:-https://github.com/kanton42/claude-config.git}"
dest="$HOME/.claude"
mkdir -p "$dest"
cd "$dest"

if [ -d .git ]; then
  git pull --ff-only
  exit 0
fi

git init -q -b main
git remote add origin "$repo"
git fetch -q origin main

backup="backups/pre-config-$(date +%Y%m%d-%H%M%S)"
git ls-tree -r --name-only origin/main | while IFS= read -r f; do
  if [ -e "$f" ]; then
    mkdir -p "$backup/$(dirname "$f")"
    cp -p "$f" "$backup/$f"
  fi
done

git checkout -q -f -B main origin/main
chmod +x hooks/*.sh

command -v jq >/dev/null || echo "WARNING: jq not found; the hooks in hooks/ need it to parse tool input." >&2
echo "Installed Claude config into $dest"
