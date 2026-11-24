#!/usr/bin/env python3
"""PreToolUse guard for delete commands in Bash/PowerShell.

Covers rm, rmdir, unlink (Bash) and Remove-Item with its aliases
rm, ri, rd, rmdir, del, erase (PowerShell).

The command is split at unquoted ; & && | || and newlines, and each delete
segment is judged on its own targets (tracking `cd` between segments).

- Every target resolves strictly inside the project or a temp dir
  ($TMPDIR/$TEMP/$TMP, system temp, Claude scratchpad)          -> allow
- Any target outside, unresolvable variable, subshell, command
  substitution, piped/xargs/find-fed delete, no explicit target,
  or anything unparseable                                        -> ask
- No delete command at all                                       -> no opinion
"""

import json
import os
import re
import shlex
import sys
import tempfile

IS_WIN = os.name == "nt"
GIT_BASH_DRIVE = re.compile(r"^/([a-zA-Z])(?=/|$)")
BASH_VAR = re.compile(r"\$(?:\{([A-Za-z_][A-Za-z0-9_]*)\}|([A-Za-z_][A-Za-z0-9_]*))")
PS_ENV_VAR = re.compile(r"\$env:([A-Za-z_][A-Za-z0-9_]*)", re.IGNORECASE)
PS_PATH_FLAG = re.compile(r"^-(?:path|literalpath|pspath|lp):(.+)$", re.IGNORECASE)
REDIRECT = re.compile(r"^\d*(?:>>?|<|&>)")
CD_CMDS = {"cd", "chdir", "pushd", "set-location", "sl"}
WRAPPERS = {"sudo", "command", "env", "nohup", "time", "exec"}
DELETE_CMDS = {"rm", "rmdir", "unlink", "remove-item", "ri", "rd", "del", "erase"}
DELETE_WORD = re.compile(
    r"\b(?:" + "|".join(sorted(DELETE_CMDS, key=len, reverse=True)) + r")\b",
    re.IGNORECASE,
)
# Segments that have their own `ask` rules in settings.json; never emit
# `allow` for a command containing them, so those rules still apply.
SENSITIVE = re.compile(r"^git\s+reset\s+--hard\b", re.IGNORECASE)
TEMP_VARS = ("TMPDIR", "TEMP", "TMP")


class Ask(Exception):
    pass


def decide(decision, reason):
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": decision,
                    "permissionDecisionReason": f"rm_guard: {reason}",
                }
            }
        )
    )
    sys.exit(0)


def to_native(path):
    """Map Git Bash /c/... -> C:/... and /tmp -> system temp on Windows."""
    if IS_WIN:
        if path == "/tmp" or path.startswith("/tmp/"):
            path = tempfile.gettempdir() + path[4:]
        path = GIT_BASH_DRIVE.sub(lambda m: m.group(1) + ":", path)
    return path


def resolve(path, base):
    path = to_native(os.path.expanduser(path))
    return os.path.normcase(os.path.realpath(os.path.join(base, path)))


PS_LOCAL_VAR = re.compile(r"\$([A-Za-z_][A-Za-z0-9_]*)")
BASH_ASSIGN = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)=(.*)$")


def lookup(name, assigned, use_env=True):
    """Variable assigned earlier in this command, else (optionally) env."""
    if name in assigned:
        if assigned[name] is None:
            raise Ask(f"variable ${name} has an unresolvable value")
        return assigned[name]
    val = os.environ.get(name) if use_env else None
    if not val and use_env and name.upper() in TEMP_VARS:
        val = tempfile.gettempdir()
    if not val:
        raise Ask(f"variable ${name} is not set")
    return val


def expand(token, shell, v):
    """Expand plain variables; anything else with `$` is unresolvable -> ask.

    `v` holds variables assigned earlier in the same command:
    v["env"] for Bash vars / PowerShell $env:, v["ps"] for PowerShell $vars.
    """
    if shell == "PowerShell":
        token = PS_ENV_VAR.sub(lambda m: lookup(m.group(1), v["env"]), token)
        token = PS_LOCAL_VAR.sub(lambda m: lookup(m.group(1), v["ps"], False), token)
    else:
        token = BASH_VAR.sub(lambda m: lookup(m.group(1) or m.group(2), v["env"]), token)
    if "$" in token:
        raise Ask(f"cannot resolve {token!r}")
    return token


def record_assignment(toks, shell, v):
    """Remember `S=...` / `export S=...` (Bash) or `$S = '...'` (PowerShell).

    Returns True if the segment was a pure assignment.
    """
    def value(raw):
        try:
            return expand(raw.strip("\"'"), shell, v)
        except Ask:
            return None  # known name, unknown value -> later use asks

    if shell == "PowerShell":
        if len(toks) >= 2 and toks[0].startswith("$") and toks[1] == "=":
            name = toks[0][1:]
            val = value(toks[2]) if len(toks) == 3 else None
            if name.lower().startswith("env:"):
                v["env"][name[4:]] = val
            else:
                v["ps"][name] = val
            return True
        return False
    body = toks[1:] if toks[0] == "export" else toks
    matches = [BASH_ASSIGN.match(t) for t in body]
    if not body or not all(matches):
        return False
    for m in matches:
        v["env"][m.group(1)] = value(m.group(2))
    return True


def is_absolute(path):
    path = to_native(os.path.expanduser(path))
    if IS_WIN:
        return bool(os.path.splitdrive(path)[0]) and os.path.isabs(path)
    return os.path.isabs(path)


HEREDOC = re.compile(r"<<(-?)\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\2")


def strip_heredocs(cmd):
    """Blank heredoc bodies (e.g. commit messages): they are data, not code.

    Approximation: an unquoted-delimiter body could still run $(...); that
    exotic case is accepted.
    """
    out, pending = [], []
    for line in cmd.split("\n"):
        if pending:
            delim, dash = pending[0]
            check = line.lstrip("\t") if dash else line
            if check.rstrip("\r") == delim:
                pending.pop(0)
            out.append("")
            continue
        pending.extend((m.group(3), bool(m.group(1))) for m in HEREDOC.finditer(line))
        out.append(line)
    return "\n".join(out)


def blank_quotes(cmd, quotes, shell):
    """Replace the contents of the given quote types with spaces."""
    out, q, i = [], None, 0
    bash = shell != "PowerShell"
    while i < len(cmd):
        ch = cmd[i]
        if bash and ch == "\\" and q != "'" and i + 1 < len(cmd):
            pair = cmd[i : i + 2]
            out.append("  " if q and q in quotes else pair)
            i += 2
            continue
        if q:
            if ch == q:
                q = None
                out.append(ch)
            else:
                out.append(" " if q in quotes else ch)
        else:
            if ch in "'\"":
                q = ch
            out.append(ch)
        i += 1
    return "".join(out)


def split_segments(cmd):
    """Split at unquoted ; & | and newlines (keeping 2>&1 / &> intact)."""
    segs, cur, quote = [], [], None
    for i, ch in enumerate(cmd):
        if quote:
            cur.append(ch)
            if ch == quote:
                quote = None
            continue
        if ch in "'\"":
            quote = ch
            cur.append(ch)
            continue
        if ch == "&":
            prev = cmd[i - 1] if i else ""
            nxt = cmd[i + 1] if i + 1 < len(cmd) else ""
            if prev in "<>" or nxt == ">":
                cur.append(ch)
                continue
        if ch in ";&|\n":
            segs.append("".join(cur))
            cur = []
            continue
        cur.append(ch)
    if quote:
        raise Ask("unbalanced quotes")
    segs.append("".join(cur))
    return [s.strip() for s in segs if s.strip()]


def tokenize(seg):
    # posix=False keeps Windows backslashes intact; strip quotes ourselves.
    try:
        toks = shlex.split(seg, posix=False)
    except ValueError:
        raise Ask("unparseable command")
    out, skip = [], False
    for t in toks:
        if skip:
            skip = False
            continue
        if REDIRECT.match(t):
            # bare `>` / `2>` takes the next token as its target
            skip = re.fullmatch(r"\d*(?:>>?|<|&>)", t) is not None
            continue
        out.append(t.strip("\"'"))
    return out


def rm_targets(toks, shell):
    """Return delete-target list, or None if the segment isn't a delete."""
    while toks and toks[0].lower() in WRAPPERS:
        toks = toks[1:]
    if not toks:
        return None
    lowered = [t.lower() for t in toks]
    if lowered[0] not in DELETE_CMDS:
        if lowered[0] in {"xargs", "find"} and DELETE_CMDS.intersection(lowered):
            raise Ask(f"delete fed by {lowered[0]}")
        return None
    targets, opts_done = [], False
    for t in toks[1:]:
        if not opts_done and t == "--":
            opts_done = True
            continue
        if not opts_done and t.startswith("-"):
            m = PS_PATH_FLAG.match(t)
            if m:
                targets.append(m.group(1))
            continue
        targets.append(t)
    if shell == "PowerShell":
        # Remove-Item -Path a,b  /  "a","b"
        targets = [p.strip("\"' ") for t in targets for p in t.split(",")]
        targets = [t for t in targets if t]
    if not targets:
        raise Ask(f"{toks[0]} without explicit target (piped input?)")
    return targets


def safe_roots(project):
    roots = {project}
    for name in TEMP_VARS:
        if os.environ.get(name):
            roots.add(resolve(os.environ[name], project))
    roots.add(resolve(tempfile.gettempdir(), project))
    return roots


def main():
    data = json.load(sys.stdin)
    shell = data.get("tool_name", "Bash")
    cmd = strip_heredocs(data.get("tool_input", {}).get("command", ""))
    # `live`: single-quoted text removed (literal in Bash and PowerShell);
    # double-quoted text stays because $(...) still runs inside it.
    # `bare`: all quoted text removed, for parens that only matter unquoted.
    live = blank_quotes(cmd, "'", shell)
    bare = blank_quotes(cmd, "'\"", shell)
    if not DELETE_WORD.search(live):
        sys.exit(0)

    cwd = resolve(to_native(data.get("cwd") or os.getcwd()), "/")
    project = resolve(os.environ.get("CLAUDE_PROJECT_DIR") or cwd, cwd)
    roots = safe_roots(project)

    try:
        backtick_subst = shell != "PowerShell" and "`" in live
        if backtick_subst or "$(" in live or re.search(r"[()]", bare):
            raise Ask("subshell or command substitution")
        segs = split_segments(cmd)
        saw_rm = sensitive = False
        assigned = {"env": {}, "ps": {}}
        for seg in segs:
            if SENSITIVE.match(seg):
                sensitive = True
            toks = tokenize(seg)
            if not toks:
                continue
            if record_assignment(toks, shell, assigned):
                continue
            if toks[0].lower() in CD_CMDS:
                args = [t for t in toks[1:] if not t.startswith("-")]
                if toks[1:] == ["-"]:
                    cwd = None  # previous dir: unknown
                elif not args:
                    cwd = resolve("~", "/")
                else:
                    try:
                        target = expand(args[0], shell, assigned)
                        cwd = resolve(target, cwd) if cwd or is_absolute(target) else None
                    except Ask:
                        cwd = None  # only matters for later relative targets
                continue
            if toks[0].lower() == "popd":
                cwd = None
                continue
            targets = rm_targets(toks, shell)
            if targets is None:
                continue
            saw_rm = True
            for raw in targets:
                if raw.endswith("\\") and shell != "PowerShell":
                    raise Ask(f"ambiguous path {raw!r}")
                path = expand(raw, shell, assigned)
                if cwd is None and not is_absolute(path):
                    raise Ask(f"{raw}: working directory unknown after cd")
                full = resolve(path, cwd or "/")
                if not any(full.startswith(r + os.sep) for r in roots):
                    raise Ask(f"{raw} is outside the project and temp dirs")
    except Ask as e:
        decide("ask", str(e))

    if saw_rm and not sensitive:
        decide("allow", "rm targets inside project/temp")
    sys.exit(0)


if __name__ == "__main__":
    main()
