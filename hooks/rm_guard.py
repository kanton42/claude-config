#!/usr/bin/env python3
"""PreToolUse guard for `rm` in Bash/PowerShell.

- `rm` (incl. -rf) whose targets all resolve inside the project -> allow.
- Any target outside the project, or anything we can't parse safely -> ask.
- Commands without `rm` in command position -> no opinion (normal rules apply).
"""

import json
import os
import re
import shlex
import sys

# `rm` at a command position: start of line or after ; & | ( or newline.
RM_AT_CMD_POS = re.compile(r"(?:^|[;&|(\n])\s*rm(?:\s|$)")
GIT_BASH_DRIVE = re.compile(r"^/([a-zA-Z])(?=/|$)")


def decide(decision, reason):
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": decision,
                    "permissionDecisionReason": reason,
                }
            }
        )
    )
    sys.exit(0)


def to_native(path):
    """Map Git Bash style /c/Users/... to C:/Users/... on Windows."""
    if os.name == "nt":
        path = GIT_BASH_DRIVE.sub(lambda m: m.group(1) + ":", path)
    return path


def resolve(path, base):
    path = to_native(os.path.expanduser(path))
    return os.path.normcase(os.path.realpath(os.path.join(base, path)))


def main():
    data = json.load(sys.stdin)
    cmd = data.get("tool_input", {}).get("command", "")
    if not RM_AT_CMD_POS.search(cmd):
        sys.exit(0)

    cwd = to_native(data.get("cwd") or os.getcwd())
    project = resolve(os.environ.get("CLAUDE_PROJECT_DIR") or cwd, cwd)

    if any(c in cmd for c in ";&|`$<>()\n"):
        decide("ask", "chained/complex rm command")

    # posix=False keeps Windows backslashes intact; strip quotes ourselves.
    try:
        parts = [t.strip("\"'") for t in shlex.split(cmd, posix=False)]
    except ValueError:
        decide("ask", "unparseable rm command")
    if not parts or parts[0] != "rm":
        decide("ask", "rm in unexpected position")

    paths = [p for p in parts[1:] if p and not p.startswith("-")]
    if not paths:
        sys.exit(0)
    for p in paths:
        if p.endswith("\\"):  # bash escaped space, e.g. my\ file
            decide("ask", f"ambiguous path {p!r}")
        full = resolve(p, cwd)
        if not full.startswith(project + os.sep):
            decide("ask", f"{p} is outside the project")
    decide("allow", "rm inside project")


if __name__ == "__main__":
    main()
