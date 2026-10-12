#!/usr/bin/env bash
# Antigravity PreToolUse hook (matcher: view_file). Denies reads of large text files; images, PDFs, notebooks pass.
# (unverified) view_file arg names are undocumented: take the first absolute-path string in toolCall.args.
# Always exit 0 and print JSON: hook exit codes are undocumented.
in=$(cat); max=${AW_READ_MAX_BYTES:-200000}
f=$(jq -r '[.toolCall.args[]? | strings | select(startswith("/"))][0] // empty' <<<"$in")
shopt -s nocasematch
case "$f" in *.png|*.jpg|*.jpeg|*.gif|*.webp|*.bmp|*.ico|*.tif|*.tiff|*.heic|*.pdf|*.ipynb) echo '{"decision":"allow"}'; exit 0;; esac
has_range=$(jq -r 'if (.toolCall.args.StartLine != null or .toolCall.args.EndLine != null or .toolCall.args.ContentOffset != null) then "true" else "false" end' <<<"$in")
if [ "$has_range" = "true" ]; then echo '{"decision":"allow"}'; exit 0; fi
if [ -n "$f" ] && [ -f "$f" ] && [ "$(wc -c <"$f")" -gt "$max" ]; then
  jq -n --arg r "File is over $max bytes. Delegate to the bulk-reader subagent (aw-bulk-read) or view a line range." '{decision:"deny",reason:$r}'
else echo '{"decision":"allow"}'; fi
exit 0
