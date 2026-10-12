#!/usr/bin/env bash
# Fast Rust gate for Stop hooks: fmt + clippy, only for workspaces with uncommitted .rs changes.
# Tests, coverage and mutants stay in /aw-ship-review.
# Usage: gate-check.sh claude|agy      Prints hook JSON; always exits 0.
# Claude: checks the session cwd from the hook input (the worktree when in one), not $CLAUDE_PROJECT_DIR.
# Antigravity: checks every workspacePaths entry; which one is active is undocumented (unverified).
mode=${1:-claude}; in=$(cat); export NO_COLOR=1 CARGO_TERM_COLOR=never
pass() { [ "$mode" = agy ] && echo '{}'; exit 0; }
if [ "$mode" = claude ]; then
  [ "$(jq -r '.stop_hook_active // false' <<<"$in")" = true ] && exit 0   # already blocked once: let it stop
  dirs=$(jq -r '.cwd // empty' <<<"$in"); [ -n "$dirs" ] || dirs=${CLAUDE_PROJECT_DIR:-$PWD}
else
  [ "$(jq -r '.executionNum // 0' <<<"$in")" -gt 3 ] && pass               # (unverified) retry cap
  dirs=$(jq -r '.workspacePaths[]? // empty' <<<"$in"); [ -n "$dirs" ] || dirs=$PWD
fi
fail=""
while IFS= read -r d; do
  [ -d "$d" ] || continue
  manifest=$(cd "$d" && cargo locate-project --workspace --message-format plain 2>/dev/null) || continue
  root=$(dirname "$manifest")
  [ -n "$(git -C "$root" status --porcelain -- '*.rs' 2>/dev/null)" ] || continue   # no Rust changes
  out=$( (cd "$root" && cargo fmt --all --check -- --color never && cargo clippy --workspace --all-targets --quiet -- -D warnings) 2>&1 ) \
    || fail+="$root:"$'\n'"$(tail -n 40 <<<"$out")"$'\n'
done <<<"$dirs"
[ -z "$fail" ] && pass
r="fmt/clippy failed. Fix before stopping:"$'\n'"$fail"
if [ "$mode" = claude ]; then jq -n --arg r "$r" '{decision:"block",reason:$r}'; else jq -n --arg r "$r" '{decision:"continue",reason:$r}'; fi
exit 0
