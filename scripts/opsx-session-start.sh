#!/usr/bin/env bash
# Start an optional thin runtime loop session bound to an existing OpenSpec change.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SESSIONS_DIR="$REPO_ROOT/.claude/runtime/opsx-sessions"
CHANGE_ID=""
GOAL=""
MAX_ITERATIONS=20
COMPLETION_PROMISE="OPSX_COMPLETE"

print_help() {
    cat <<'EOF'
Usage: bash scripts/opsx-session-start.sh --change-id <change-id> [OPTIONS]

Options:
  --goal <text>                 Optional goal summary for the loop
  --max-iterations <n>          Maximum loop iterations (default: 20)
  --completion-promise <text>   Promise text that closes the loop (default: OPSX_COMPLETE)
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --change-id)
            CHANGE_ID="${2:-}"
            shift 2
            ;;
        --goal)
            GOAL="${2:-}"
            shift 2
            ;;
        --max-iterations)
            MAX_ITERATIONS="${2:-}"
            shift 2
            ;;
        --completion-promise)
            COMPLETION_PROMISE="${2:-}"
            shift 2
            ;;
        -h|--help)
            print_help
            exit 0
            ;;
        *)
            echo "ERROR: Unknown argument: $1" >&2
            print_help >&2
            exit 2
            ;;
    esac
done

if [[ -z "$CHANGE_ID" ]]; then
    echo "ERROR: --change-id is required." >&2
    exit 2
fi

if [[ ! -d "$REPO_ROOT/openspec/changes/$CHANGE_ID" ]]; then
    echo "ERROR: OpenSpec change not found: openspec/changes/$CHANGE_ID" >&2
    exit 2
fi

SESSION_ID="$(head -c 3 /dev/urandom | xxd -p)"
SESSION_DIR="$SESSIONS_DIR/$SESSION_ID"
INDEX_FILE="$SESSIONS_DIR/index.yaml"

mkdir -p "$SESSION_DIR"

cat > "$SESSION_DIR/state.yaml" <<EOF
change_id: "$CHANGE_ID"
goal: "${GOAL:-Review and close OpenSpec change $CHANGE_ID}"
session_id: "$SESSION_ID"
status: active
iteration: 1
started_at: "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
last_gate: null
attempts: []
EOF

cat > "$SESSION_DIR/loop.md" <<EOF
---
active: true
iteration: 1
max_iterations: $MAX_ITERATIONS
completion_promise: "$COMPLETION_PROMISE"
started_at: "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
---

Use OpenSpec change \`$CHANGE_ID\` as the only planning authority.
Validate against \`openspec/changes/$CHANGE_ID/tasks.md\`.
Do not create or update planning artifacts outside \`openspec/changes/$CHANGE_ID/\`.
EOF

if [[ ! -f "$INDEX_FILE" ]]; then
    cat > "$INDEX_FILE" <<EOF
active_session: "$SESSION_ID"
sessions:
  - id: "$SESSION_ID"
    change_id: "$CHANGE_ID"
    status: active
    created_at: "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
EOF
else
    python3 - "$INDEX_FILE" "$SESSION_ID" "$CHANGE_ID" <<'PY'
from __future__ import annotations
import sys
from pathlib import Path
import yaml

index_path = Path(sys.argv[1])
session_id = sys.argv[2]
change_id = sys.argv[3]
payload = yaml.safe_load(index_path.read_text(encoding="utf-8")) or {}
payload["active_session"] = session_id
sessions = payload.setdefault("sessions", [])
sessions.append(
    {
        "id": session_id,
        "change_id": change_id,
        "status": "active",
        "created_at": __import__("datetime").datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
)
index_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
PY
fi

echo "OPSX_SESSION: $SESSION_ID"
echo "Change: $CHANGE_ID"
echo "State: $SESSION_DIR/state.yaml"
echo "Loop: $SESSION_DIR/loop.md"
