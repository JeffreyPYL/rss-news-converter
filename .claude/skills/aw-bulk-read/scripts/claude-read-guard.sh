#!/usr/bin/env bash
# Claude Code PreToolUse hook (matcher: Read). Denies whole-file reads of large text files.
# Images, PDFs and notebooks pass: Read handles them specially and `limit` does not apply.
# Env: AW_READ_MAX_BYTES (default 200000).
in=$(cat); max=${AW_READ_MAX_BYTES:-200000}
f=$(jq -r '.tool_input.file_path // empty' <<<"$in"); lim=$(jq -r '.tool_input.limit // empty' <<<"$in")
shopt -s nocasematch
case "$f" in *.png|*.jpg|*.jpeg|*.gif|*.webp|*.bmp|*.ico|*.tif|*.tiff|*.heic|*.pdf|*.ipynb) exit 0;; esac
[ -n "$f" ] && [ -z "$lim" ] && [ -f "$f" ] && [ "$(wc -c <"$f")" -gt "$max" ] && jq -n --arg r "File is over $max bytes. Use the bulk-reader subagent (/aw-bulk-read) or Read with offset and limit." \
  '{hookSpecificOutput:{hookEventName:"PreToolUse",permissionDecision:"deny",permissionDecisionReason:$r}}'
exit 0
