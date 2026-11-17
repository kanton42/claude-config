#!/usr/bin/env bash
# Run rm_guard.py with a real Python; fail closed (ask) if none is usable.
# Avoids the Windows Store "python" stub, which exits non-zero and would
# silently disable the guard.
here="$(dirname "$0")"
for py in "$HOME/miniconda3/python.exe" "$HOME/miniconda3/bin/python" python3 python; do
  if "$py" -c 'import sys; sys.exit(0)' >/dev/null 2>&1; then
    exec "$py" "$here/rm_guard.py"
  fi
done
if grep -Eq '(^|[^[:alnum:]_-])rm([^[:alnum:]_-]|$)'; then
  echo '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"ask","permissionDecisionReason":"rm_guard: no Python found"}}'
fi
exit 0
