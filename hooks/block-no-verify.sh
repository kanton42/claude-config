#!/usr/bin/env bash
# block-no-verify (PreToolUse/Bash): if a git command tries to skip hooks via --no-verify, ask to confirm.
# Enforces the pre-commit gate (lint+types+tests before commit) mechanically. Adapted from ECC (MIT).
input=$(cat)
cmd=$(printf '%s' "$input" | jq -r '.tool_input.command // empty' 2>/dev/null)
case "$cmd" in
  *git*--no-verify*|*"git commit -n"*|*"git push --no-verify"*)
    printf '%s' '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"ask","permissionDecisionReason":"--no-verify bypasses the pre-commit gate (lint/types/tests). CLAUDE.md says failures should never reach main — confirm you really intend to skip the hooks."}}' ;;
esac
exit 0
