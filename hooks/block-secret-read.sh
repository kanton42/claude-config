#!/usr/bin/env bash
# block-secret-read (PreToolUse/Bash|PowerShell): permission deny rules like Read(~/.ssh/**) only cover the
# Read tool, so `cat ~/.ssh/id_rsa` or `Get-Content $HOME\.aws\credentials` would bypass them. This hook asks
# for confirmation when a shell command references a known secret location. Text match only: it stops
# accidental reads, not a deliberately obfuscated path.
input=$(cat)
cmd=$(printf '%s' "$input" | jq -r '.tool_input.command // empty' 2>/dev/null)
[ -z "$cmd" ] && exit 0
# ignore committed env templates
cmd=$(printf '%s' "$cmd" | sed -E 's/\.env\.(example|sample|template|dist)//g')

# Secret dirs (.ssh .aws .azure .kube .docker .gnupg), private keys, .env files, credential/secret stores.
pattern='(^|[^A-Za-z0-9_])\.(ssh|aws|azure|kube|docker|gnupg)([/\\"'"'"'[:space:]]|$)'
pattern+='|id_(rsa|ed25519|ecdsa|dsa)'

# key-file rule: require a filename before the dot and a path terminator after it
pattern+='|[A-Za-z0-9_-]\.(pem|pfx|p12|key)(["'"'"'[:space:];|&>)]|$)'

pattern+='|(^|[^A-Za-z0-9_])\.env([^A-Za-z0-9_]|$)'
pattern+='|\.netrc|\.pgpass|credentials|(^|[/\\])secrets([/\\]|$)'
# pattern+='|\.(pem|pfx|p12|key)([^A-Za-z0-9_]|$)'

if printf '%s' "$cmd" | grep -Eiq -- "$pattern"; then
  printf '%s' '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"ask","permissionDecisionReason":"block-secret-read: this shell command references a secret location (.ssh/.aws/.azure/.env/credentials/keys). Read-deny rules do not cover shell commands — confirm this access is intended."}}'
fi
exit 0
