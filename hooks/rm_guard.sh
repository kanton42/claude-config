#!/usr/bin/env bash
# Fast pre-filter + launcher for rm_guard.py.
#
# Most shell commands contain no delete word; for those we exit using only
# bash builtins (no subprocess), so the hook costs ~nothing. Otherwise run
# rm_guard.py with a real Python; fail closed (ask) if none is usable or the
# guard crashes. Avoids the Windows Store "python" stub, which exits non-zero
# and would silently disable the guard.

# Must be a superset of DELETE_WORD in rm_guard.py. The input is raw JSON, so
# a command on a new line appears as `\nrm`: accept \n \r \t escapes as a
# word boundary too.
DEL_RE='(^|[^[:alnum:]_]|\\[nrt])(rm|rmdir|unlink|remove-item|ri|rd|del|erase)([^[:alnum:]_]|$)'

IFS= read -r -d '' input  # read hook input once (builtin, no fork)
shopt -s nocasematch
[[ $input =~ $DEL_RE ]] || exit 0

here="${0%/*}"
for py in "$HOME/miniconda3/python.exe" "$HOME/miniconda3/bin/python" python3 python; do
  case "$py" in
    /*) [ -x "$py" ] || continue ;;  # known install: no slow startup probe
    *) "$py" -c 'import sys' </dev/null >/dev/null 2>&1 || continue ;;
  esac
  if out="$(printf '%s' "$input" | "$py" "$here/rm_guard.py")"; then
    printf '%s\n' "$out"
    exit 0
  fi
  break  # guard crashed -> fall through to fail-closed answer
done

echo '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"ask","permissionDecisionReason":"rm_guard: guard unavailable (no Python or crash)"}}'
exit 0
