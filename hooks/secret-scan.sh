#!/usr/bin/env bash
# secret-scan (UserPromptSubmit, WARN-ONLY): if the submitted prompt looks like it contains a real
# API key / token / private key, surface a warning. Never blocks. Adapted from ECC (affaan-m/ECC, MIT)
# before-submit-prompt.js. Catches accidental paste of live API keys before send.
input=$(cat)
if printf '%s' "$input" | grep -Eq 'sk-or-v1-[A-Za-z0-9]{16,}|sk-[A-Za-z0-9]{20,}|sk-ant-[A-Za-z0-9_-]{20,}|gh[posru]_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|xox[baprs]-[A-Za-z0-9-]{10,}|-----BEGIN [A-Z ]*PRIVATE KEY-----'; then
  printf '%s' '{"systemMessage":"⚠ secret-scan: this prompt looks like it contains an API key / token / private key. Claude never needs secret values — share env-file format and fill it yourself. (warning only — not blocked; rotate the key if it was real.)"}'
fi
exit 0
