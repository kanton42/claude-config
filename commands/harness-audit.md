---
description: Audit your Claude Code harness (~/.claude) — inventory skills/hooks/commands/agents and score coverage of the things that matter, with a prioritized action list. Read-only.
argument-hint: "[skills|hooks|commands|all] (default all)"
allowed-tools: Bash(ls *), Bash(jq *), Bash(wc *), Bash(find *), Bash(cat ~/.claude/settings.json), Read, Grep
---

# Harness Audit

Deterministic, READ-ONLY inventory + scorecard of your personal harness. No external script — self-contained
(this is the lean re-implementation of ECC's `/harness-audit`, which depended on its own repo's JS engine).

Run these read-only probes, then report:

```bash
echo "== skills =="; ls -1 ~/.claude/skills 2>/dev/null | sort; echo "count: $(ls -1 ~/.claude/skills 2>/dev/null | wc -l | tr -d ' ')"
echo "== commands =="; ls -1 ~/.claude/commands 2>/dev/null
echo "== agents =="; ls -1 ~/.claude/agents 2>/dev/null
echo "== hook events =="; jq -r '.hooks | keys[]' ~/.claude/settings.json
echo "== hook commands =="; jq -r '.hooks | to_entries[] | "\(.key): " + ([.value[].hooks[].command] | join(" | "))' ~/.claude/settings.json
echo "== CLAUDE.md size (keep lean) =="; wc -l ~/.claude/CLAUDE.md
echo "== permissions =="; jq '{allow: (.permissions.allow|length), deny: (.permissions.deny|length), defaultMode: .permissions.defaultMode}' ~/.claude/settings.json
```

## Score these dimensions (0–10 each), from the probe output
1. **Tool coverage** — breadth of allowed Bash/MCP; gaps that cause repeated prompts.
2. **Context efficiency** — CLAUDE.md lean (≲120 lines)? skills auto-trigger vs bloat?
3. **Quality gates** — PostToolUse formatter present? a ship/pre-commit gate?
4. **Memory persistence** — SessionStart context load + PreCompact carry-over present?
5. **Security guardrails** — PreToolUse `config-protection` + `block-no-verify`; UserPromptSubmit `secret-scan`; deny-list for destructive cmds.
6. **Cost awareness** — any cost telemetry / `cost-aware-llm-pipeline` skill in use?
7. **Skill hygiene** — duplicates, stubs, stale skills; do descriptions have crisp trigger keywords?

## Output
- `overall: N/70` + per-dimension score with the concrete evidence (which hook/skill/file).
- **Top 3 actions** (highest gap × lowest effort), each with the exact file to touch.
- Note any skill that looks stale/duplicate/stub for pruning.
Be terse and direct; cite real paths. Do not modify anything — this is read-only.
