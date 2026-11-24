"""Regression tests for rm_guard. Run: ~/miniconda3/python.exe ~/.claude/hooks/tests/test_rm_guard.py"""
import json, os, subprocess, sys, tempfile

HOOK = os.path.expanduser("~/.claude/hooks/rm_guard.sh")
P = r"C:\Users\AntonKlimek\proj"
TMP = tempfile.gettempdir()
B, PS = "Bash", "PowerShell"
CASES = [
    # in project (any depth)
    (B, "rm -rf build", "allow"),
    (B, "rm -rf src/a/b/c/deep.txt", "allow"),
    (B, 'rm -rf ./data/tmp "out dir"', "allow"),
    (B, "rm -rf /c/Users/AntonKlimek/proj/sub", "allow"),
    (B, "rm -rf ../proj/src", "allow"),
    (PS, r"rm -Recurse -Force src\old", "allow"),
    # temp dirs + variables
    (B, "rm -f $TMPDIR/render/Rueckgang_2026_Kurzfassung* && cp x.pptx $TMPDIR/render/ && bash ../DPD_slides/tools/render_pptx.sh $TMPDIR/render/x.pptx 100 >/dev/null 2>&1; ls $TMPDIR/render | grep Kurz", "allow"),
    (B, "rm -rf ${TEMP}/foo /tmp/bar", "allow"),
    (PS, r"rm -Recurse $env:TEMP\foo", "allow"),
    (B, "rm -rf $TMPDIR", "ask"),
    (B, "rm -rf $HOME", "ask"),
    (B, "rm -rf $NOT_SET_VAR/x", "ask"),
    (PS, r"rm $TEMP\x", "ask"),
    # chaining + cd tracking
    (B, "cd src && rm -rf x", "allow"),
    (B, "cd .. && rm -rf x", "ask"),
    (B, "cd /c/Users && rm -rf AntonKlimek/proj/x", "allow"),
    (B, "echo hi; rm x", "allow"),
    (B, "rm x && rm /c/Windows/x", "ask"),
    (B, "rm x && git reset --hard", "none"),
    (B, "(cd src && rm x)", "allow"),
    (B, "rm $(cat list)", "ask"),
    (B, "ls | xargs rm", "ask"),
    # outside / odd
    (B, r"rm C:\Users\x\file", "ask"),
    (B, "rm -rf /c/Users/other", "ask"),
    (B, "rm -rf ..", "ask"),
    (B, "rm -rf ~", "ask"),
    (B, "rm -rf .", "ask"),
    (PS, r"rm -Recurse -Force C:\Windows", "ask"),
    (PS, r"rm -Path:C:\Windows\x", "ask"),
    (B, r"rm my\ file", "ask"),
    (B, "rm -- -weird", "allow"),
    # PowerShell Remove-Item + aliases
    (PS, r"Remove-Item -Recurse -Force .\build", "allow"),
    (PS, r"remove-item -Path src\a,src\b", "allow"),
    (PS, r'Remove-Item -LiteralPath "out dir\x.txt"', "allow"),
    (PS, r"Remove-Item -Recurse $env:TEMP\render\*", "allow"),
    (PS, r"del .\x.txt; ri tmp -Recurse; erase y; rd -Recurse z", "allow"),
    (PS, r"Set-Location src; Remove-Item old -Recurse", "allow"),
    (PS, r"Remove-Item C:\Windows\System32\x", "ask"),
    (PS, r'Remove-Item -Path "src\a","C:\Users\other"', "ask"),
    (PS, r"del C:\Users\AntonKlimek\Documents\x", "ask"),
    (PS, r"rd -Recurse ..\other", "ask"),
    (PS, r"Get-ChildItem *.log | Remove-Item", "ask"),
    (PS, r"Remove-Item -Path:C:\Windows\x", "ask"),
    (PS, r"Remove-Item .", "ask"),
    # Bash rmdir / unlink
    (B, "rmdir build/empty", "allow"),
    (B, "unlink /c/Users/other/x", "ask"),
    (B, "find . -name '*.pyc' | xargs unlink", "ask"),
    # commit messages / quoted text mentioning deletes
    (B, "git commit -q -F - <<'EOF'\nTreat rm, del (e.g. Remove-Item) alike\n\n- rm -rf / (no)\nEOF\ngit push -q origin main", "none"),
    (B, "git commit -m \"drop rm rules (now in hook)\" && git push", "none"),
    (B, "git commit -m 'use `rm` and $(x) (literal)'", "none"),
    (B, "cat <<EOF > notes.txt\nrm everything (joke)\nEOF\nrm -rf build", "allow"),
    (B, "cat <<'EOF'\nx\nEOF\nrm -rf /c/Windows", "ask"),
    (B, "echo \"$(rm -rf x)\"", "ask"),
    (B, "git commit -m \"fix `rm` call\"", "ask"),
    (PS, "git commit -F - @'\nTreat rm, del (e.g. Remove-Item) alike\n'@", "none"),
    (PS, "git commit -m \"drop del rules (now in hook)\"; git push", "none"),
    (B, "rm \"file (1).txt\"", "allow"),
    # variables assigned in the same command
    (B, "S=" + TMP.replace("\\", "/") + "/x\ncd $S && python - <<'EOF'\nprint(1)\nEOF\nrm -rf /c/Users/AntonKlimek/proj/out/memprobe", "allow"),
    (B, "S=/c/Users/AntonKlimek/proj/out; rm -rf $S/a ${S}/b", "allow"),
    (B, "export S=/c/Windows; rm -rf $S/x", "ask"),
    (B, "D=build && cd $D && rm -rf tmp", "allow"),
    (B, "S=$UNSET_X/a; rm -rf $S", "ask"),
    (B, "cd $UNSET_X && rm -rf /c/Users/AntonKlimek/proj/a", "allow"),
    (B, "cd $UNSET_X && rm -rf a", "ask"),
    (B, "cd - && rm -rf a", "ask"),
    (PS, "$d = 'C:\\Users\\AntonKlimek\\proj\\out'; Remove-Item -Recurse $d\\x", "allow"),
    (PS, "$d = 'C:\\Windows'; Remove-Item -Recurse $d\\x", "ask"),
    (PS, "$env:FOO = 'C:\\Users\\AntonKlimek\\proj'; rm $env:FOO\\x", "allow"),
    (PS, "rm $undefined\\x", "ask"),
    # path-qualified / alias-bypass deletes, newline-separated commands
    (B, "/usr/bin/rm -rf /c/Windows/x", "ask"),
    (B, r"\rm -rf build", "allow"),
    (B, r"\rm -rf /c/Windows/x", "ask"),
    (PS, r"C:\Windows\System32\rm.exe C:\Windows\x", "ask"),
    (B, "ls\nrm -rf /c/Windows/x", "ask"),
    (B, "ls\n\trm -rf /c/Windows/x", "ask"),
    (B, "RM -rf /c/Windows/x", "ask"),  # Windows resolves RM -> rm.exe
    (PS, r"REMOVE-ITEM C:\Windows\x", "ask"),
    # parentheses / blocks / substitutions (PowerShell)
    (PS, "$out = \"C:\\Users\\AntonKlimek\\proj\\outputs\\render\"\nRemove-Item \"$out\\*.png\" -ErrorAction SilentlyContinue\n$ppt = New-Object -ComObject PowerPoint.Application\nforeach ($d in \"A_x\",\"B_y\") {\n  $pres = $ppt.Presentations.Open(\"C:\\Users\\AntonKlimek\\proj\\$d.pptx\", $true, $false, $false)\n  $i = 1; foreach ($s in $pres.Slides) { $s.Export(\"$out\\$($d.Split('_')[1])_$i.png\", \"PNG\", 1600, 900); $i++ }\n  $pres.Close()\n}\n$ppt.Quit()", "allow"),
    (PS, "$x.Close(); Remove-Item out\\x.png -ErrorAction SilentlyContinue", "allow"),
    (PS, "Write-Host \"$($env:TEMP)\"; Remove-Item build -Recurse", "allow"),
    (PS, "if (Test-Path build) { Remove-Item build -Recurse -Force }", "allow"),
    (PS, "Remove-Item -Path out -Include *.png -Recurse", "allow"),
    (PS, "if (Test-Path C:\\Windows\\x) { Remove-Item C:\\Windows\\x }", "ask"),
    (PS, "foreach ($f in \"a\",\"b\") { Remove-Item $f }", "ask"),
    (PS, "Get-ChildItem *.tmp | ForEach-Object { Remove-Item $_.FullName }", "ask"),
    (PS, "Remove-Item @(\"C:\\Windows\\x\")", "ask"),
    (PS, "Remove-Item (Join-Path $env:TEMP \"x\")", "ask"),
    (PS, "Write-Host \"$(Remove-Item C:\\x)\"", "ask"),
    (PS, "$p = (Join-Path a b); Remove-Item $p", "ask"),
    (PS, "Set-Location (Get-Item x).Parent; Remove-Item y", "ask"),
    # parentheses / blocks / substitutions (Bash)
    (B, "(cd /c/Windows && rm x)", "ask"),
    (B, "(cd /c/Windows); rm -rf x", "allow"),
    (B, "python -c \"print(1)\" && rm -rf build", "allow"),
    (B, "ls $(pwd) && rm -rf build", "allow"),
    (B, "rm -rf $(pwd)/build", "ask"),
    (B, "{ rm -rf build; }", "allow"),
    (B, "rm -rf proj/{a,b}", "ask"),
    (B, "for f in a b; do rm $f; done", "ask"),
    (B, "for TEMP in /c/Windows; do rm -rf $TEMP/x; done", "ask"),
    (B, "if true; then rm -rf build; else rm -rf /c/Windows/x; fi", "ask"),
    (B, "if [ -d build ]; then rm -rf build; fi", "allow"),
    (B, "rm `cat list`", "ask"),
    (B, "cd $(git rev-parse --show-toplevel) && rm -rf x", "ask"),
    # no rm
    (PS, r"Get-Content delivery.txt", "none"),
    (B, "git rm file", "none"),
    (B, "ls -la", "none"),
    (B, "echo rm", "none"),
]
env = {**os.environ, "CLAUDE_PROJECT_DIR": P, "TMPDIR": TMP}
env.pop("NOT_SET_VAR", None)
bad = 0
for tool, cmd, want in CASES:
    inp = json.dumps({"cwd": P, "tool_name": tool, "tool_input": {"command": cmd}})
    r = subprocess.run(["bash", HOOK], input=inp, capture_output=True, text=True, env=env, timeout=10)
    out = r.stdout
    if out.strip():
        h = json.loads(out)["hookSpecificOutput"]
        got, why = h["permissionDecision"], h["permissionDecisionReason"]
    else:
        got, why = "none", r.stderr.strip()[-120:]
    ok = got == want
    bad += not ok
    print(f"{'OK ' if ok else 'BAD'} [{tool[:2]}] {cmd[:60]:60} -> {got:5} {why}")
print(f"{len(CASES) - bad}/{len(CASES)} passed")
sys.exit(bad)
