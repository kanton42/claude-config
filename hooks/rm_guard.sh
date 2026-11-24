#!/usr/bin/env bash
# Run rm_guard.py with a real Python; fail closed (ask) if none is usable or
# the guard crashes. Avoids the Windows Store "python" stub, which exits
# non-zero and would silently disable the guard.
here="$(dirname "$0")"
input="$(cat)"  # read once: probes must never consume the hook input

for py in "$HOME/miniconda3/python.exe" "$HOME/miniconda3/bin/python" python3 python; do
  case "$py" in
    /*) [ -x "$py" ] || continue ;;  # known install: no slow startup probe
    *) "$py" -c 'import sys' </dev/null >/dev/null 2>&1 || continue ;;
  esac
  if out="$(printf '%s' "$input" | "$py" "$here/rm_guard.py")"; then
    printf '%s\n' "$out"
    exit 0
  fi
  break  # guard crashed -> fall through to fail-closed check
done

if printf '%s' "$input" | grep -Eiq '(^|[^[:alnum:]_-])(rm|rmdir|unlink|remove-item|ri|rd|del|erase)([^[:alnum:]_-]|$)'; then
  echo '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"ask","permissionDecisionReason":"rm_guard: guard unavailable (no Python or crash)"}}'
fi
exit 0
