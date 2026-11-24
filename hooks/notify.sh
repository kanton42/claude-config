#!/usr/bin/env bash
# Notification hook: desktop notification when Claude Code needs permission
# or input. Windows: toast via notify.ps1 (shown as VS Code). Linux/macOS:
# generic notify-send / osascript fallback. Never fails the hook.
here="${0%/*}"
input="$(cat)"

if command -v powershell.exe >/dev/null 2>&1; then
  ps1="$here/notify.ps1"
  command -v cygpath >/dev/null 2>&1 && ps1="$(cygpath -w "$ps1")"
  printf '%s' "$input" | powershell.exe -NoProfile -NonInteractive \
    -ExecutionPolicy Bypass -File "$ps1" >/dev/null 2>&1
elif command -v notify-send >/dev/null 2>&1; then
  notify-send "Claude Code" "Claude Code needs your attention"
elif command -v osascript >/dev/null 2>&1; then
  osascript -e 'display notification "Claude Code needs your attention" with title "Claude Code"'
fi
exit 0
