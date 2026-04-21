#!/usr/bin/env bash
# Update the optional OpenSpec runtime loop session state.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SESSIONS_DIR="$REPO_ROOT/.claude/runtime/opsx-sessions"
SESSION_ID=""
STATUS=""
LAST_GATE=""
ATTEMPT_RESULT=""
ATTEMPT_DETAILS=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --session-id)
            SESSION_ID="${2:-}"
            shift 2
            ;;
        --status)
            STATUS="${2:-}"
            shift 2
            ;;
        --last-gate)
            LAST_GATE="${2:-}"
            shift 2
            ;;
        --attempt-result)
            ATTEMPT_RESULT="${2:-}"
            shift 2
            ;;
        --attempt-details)
            ATTEMPT_DETAILS="${2:-}"
            shift 2
            ;;
        *)
            echo "ERROR: Unknown argument: $1" >&2
            exit 2
            ;;
    esac
done

if [[ -z "$SESSION_ID" ]]; then
    echo "ERROR: --session-id is required." >&2
    exit 2
fi

STATE_FILE="$SESSIONS_DIR/$SESSION_ID/state.yaml"
LOOP_FILE="$SESSIONS_DIR/$SESSION_ID/loop.md"

if [[ ! -f "$STATE_FILE" ]]; then
    echo "ERROR: Session state file not found: $STATE_FILE" >&2
    exit 2
fi

python3 - "$STATE_FILE" "$LOOP_FILE" "$STATUS" "$LAST_GATE" "$ATTEMPT_RESULT" "$ATTEMPT_DETAILS" <<'PY'
from __future__ import annotations
import sys
from pathlib import Path
import yaml

state_path = Path(sys.argv[1])
loop_path = Path(sys.argv[2])
status = sys.argv[3]
last_gate = sys.argv[4]
attempt_result = sys.argv[5]
attempt_details = sys.argv[6]

state = yaml.safe_load(state_path.read_text(encoding="utf-8")) or {}
if status:
    state["status"] = status
    if status in {"achieved", "cancelled", "failed", "max_iterations_reached"}:
        state["completed_at"] = __import__("datetime").datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
if last_gate:
    state["last_gate"] = last_gate
if attempt_result or attempt_details:
    attempts = state.setdefault("attempts", [])
    iteration = 1
    if loop_path.exists():
        text = loop_path.read_text(encoding="utf-8")
        for line in text.splitlines():
            if line.startswith("iteration:"):
                iteration = int(line.split(":", 1)[1].strip())
                break
    state["iteration"] = iteration
    attempts.append(
        {
            "iteration": iteration,
            "result": attempt_result or "info",
            "details": attempt_details or "",
        }
    )
state_path.write_text(yaml.safe_dump(state, sort_keys=False), encoding="utf-8")
PY
