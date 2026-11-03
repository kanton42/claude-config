#!/usr/bin/env bash
# config-protection: PreToolUse(Edit|Write) — if an edit to a lint/type/CI/settings config
# appears to WEAKEN a rule, ask for confirmation. Otherwise allow silently. Never blocks code edits.
# Adapted from ECC (affaan-m/ECC, MIT) config-protection pattern.
input=$(cat)
f=$(printf '%s' "$input" | jq -r '.tool_input.file_path // empty' 2>/dev/null)
case "$f" in
  *eslint*|*tsconfig*|*.prettierrc*|*ruff*|*.flake8|*pyproject.toml|*/.github/workflows/*|*settings.json|*.pre-commit-config.yaml|*.eslintrc*|*.mypy.ini|*setup.cfg)
    new=$(printf '%s' "$input" | jq -r '(.tool_input.new_string // .tool_input.content) // empty' 2>/dev/null)
    if printf '%s' "$new" | grep -Eiq 'eslint-disable|@ts-ignore|@ts-nocheck|"strict"[[:space:]]*:[[:space:]]*false|noImplicitAny"[[:space:]]*:[[:space:]]*false|skipLibCheck"[[:space:]]*:[[:space:]]*true|continue-on-error[[:space:]]*:[[:space:]]*true|ignore_errors[[:space:]]*=[[:space:]]*True'; then
      printf '%s' '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"ask","permissionDecisionReason":"config-protection: this edit appears to weaken a lint/type/CI rule — confirm it is intentional (not silently disabling a guardrail)."}}'
    fi ;;
esac
exit 0
