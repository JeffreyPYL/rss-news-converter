#!/usr/bin/env bash
set -euo pipefail

# scripts/aw-agent-exec.sh
# Provider-agnostic execution wrapper for headless AI CLI runners (agy, claude, cursor)
# Supports prompt execution and session resumption.

STAGE="${1:-}"
PROMPT="${2:-}"
SESSION_ID="${3:-}"

if [[ -z "$STAGE" || -z "$PROMPT" ]]; then
    echo "Usage: $0 <stage> <prompt> [session_id]" >&2
    exit 1
fi

PROVIDER="${AW_AGENT_PROVIDER:-agy}"

echo "[aw-agent-exec] Executing stage: $STAGE using provider: $PROVIDER"

case "$PROVIDER" in
    agy)
        CMD=("agy" "-p" "$PROMPT" "--dangerously-skip-permissions")
        if [[ -n "$SESSION_ID" ]]; then
            CMD+=("--conversation" "$SESSION_ID")
        fi
        ;;
    claude)
        CMD=("claude" "-p" "$PROMPT" "--dangerously-skip-permissions" "--output-format" "json")
        if [[ -n "$SESSION_ID" ]]; then
            CMD+=("--resume" "$SESSION_ID")
        fi
        ;;
    cursor)
        CMD=("cursor" "agent" "--prompt" "$PROMPT")
        if [[ -n "$SESSION_ID" ]]; then
            CMD+=("--session" "$SESSION_ID")
        fi
        ;;
    mock)
        # Mock provider for testing pipelines without running LLMs
        echo "[mock] Ran stage: $STAGE with session: $SESSION_ID"
        echo "[mock] Prompt: $PROMPT"
        exit 0
        ;;
    *)
        echo "Error: Unknown AW_AGENT_PROVIDER: $PROVIDER (must be agy, claude, cursor, or mock)" >&2
        exit 1
        ;;
esac

echo "[aw-agent-exec] Command: ${CMD[*]}"
"${CMD[@]}"
