#!/usr/bin/env python3
import json, os, shlex, sys

data = json.load(sys.stdin)
cmd = data.get("tool_input", {}).get("command", "")
cwd = data.get("cwd", os.getcwd())
project = os.path.realpath(os.environ.get("CLAUDE_PROJECT_DIR", cwd))

def decide(decision, reason):
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": decision,
        "permissionDecisionReason": reason}}))
    sys.exit(0)

try:
    parts = shlex.split(cmd)
except ValueError:
    sys.exit(0)
if not parts or parts[0] != "rm":
    sys.exit(0)                      # not rm: normal permission rules apply
if any(c in cmd for c in ";&|`$<>\n"):
    decide("ask", "chained/complex rm command")

paths = [p for p in parts[1:] if not p.startswith("-")]
if not paths:
    sys.exit(0)
for p in paths:
    full = os.path.realpath(os.path.join(cwd, os.path.expanduser(p)))
    if not full.startswith(project + os.sep):
        decide("ask", f"{p} is outside the project")
decide("allow", "rm inside project")