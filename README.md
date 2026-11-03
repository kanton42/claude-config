# claude-config

Global (user-level) Claude Code configuration, versioned directly in `~/.claude`.
Project-specific settings live in each project's own `CLAUDE.md` / `.claude/` and are not part of this repo.

## Contents

| Path | What |
|------|------|
| `CLAUDE.md` | Standing instructions for every project |
| `settings.json` | Permissions, hook wiring, model settings |
| `hooks/` | `secret-scan`, `config-protection`, `block-no-verify`, `precompact-carryover` (bash; need `jq`) |
| `commands/` | Slash commands (`/cost-report`, `/harness-audit`) |
| `skills/` | Custom skills + Anthropic document skills (`document-skills/`, see their `LICENSE.txt`) |

`.gitignore` ignores everything in `~/.claude` except the paths above, so credentials, transcripts,
per-project memory, sessions, caches and backups are never tracked. Add new top-level items by
allowlisting them there.

## Install on another machine

```bash
curl -fsSL -H "Authorization: token $(gh auth token)" \
  https://raw.githubusercontent.com/kanton42/claude-config/main/install.sh | bash
# or: gh repo clone kanton42/claude-config /tmp/cc && bash /tmp/cc/install.sh
```

Existing files that the repo would overwrite are backed up to `~/.claude/backups/pre-config-<timestamp>/`.
Requires `git`, `bash` and `jq` (hooks).

## Update

Edit in place in `~/.claude`, then `git -C ~/.claude commit -am "..." && git -C ~/.claude push`.
Elsewhere: `git -C ~/.claude pull`.
