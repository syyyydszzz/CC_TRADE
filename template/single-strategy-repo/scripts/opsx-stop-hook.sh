#!/usr/bin/env bash
# Optional stop hook for the thin OpenSpec runtime loop.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SESSIONS_DIR="$REPO_ROOT/.claude/runtime/opsx-sessions"
HOOK_INPUT="$(cat)"
TRANSCRIPT_PATH="$(echo "$HOOK_INPUT" | sed -n 's/.*"transcript_path" *: *"\([^"]*\)".*/\1/p')"

if [[ -z "$TRANSCRIPT_PATH" || ! -f "$TRANSCRIPT_PATH" ]]; then
    exit 0
fi

ACTIVE_SESSION="$(grep -oE 'OPSX_SESSION: [a-f0-9]+' "$TRANSCRIPT_PATH" 2>/dev/null | tail -1 | sed 's/OPSX_SESSION: //' || true)"
if [[ -z "$ACTIVE_SESSION" ]]; then
    exit 0
fi

SESSION_DIR="$SESSIONS_DIR/$ACTIVE_SESSION"
STATE_FILE="$SESSION_DIR/state.yaml"
LOOP_FILE="$SESSION_DIR/loop.md"

if [[ ! -f "$STATE_FILE" || ! -f "$LOOP_FILE" ]]; then
    exit 0
fi

STATUS="$(sed -n 's/^status: *//p' "$STATE_FILE" | head -1 | tr -d '"')"
case "$STATUS" in
    achieved|cancelled|failed|max_iterations_reached)
        exit 0
        ;;
esac

FRONTMATTER="$(sed -n '/^---$/,/^---$/{ /^---$/d; p; }' "$LOOP_FILE")"
ITERATION="$(echo "$FRONTMATTER" | sed -n 's/^iteration: *//p' | head -1)"
MAX_ITERATIONS="$(echo "$FRONTMATTER" | sed -n 's/^max_iterations: *//p' | head -1)"
COMPLETION_PROMISE="$(echo "$FRONTMATTER" | sed -n 's/^completion_promise: *//p' | head -1 | sed 's/^"\(.*\)"$/\1/')"

if [[ "${ITERATION:-}" =~ ^[0-9]+$ && "${MAX_ITERATIONS:-}" =~ ^[0-9]+$ && "$ITERATION" -ge "$MAX_ITERATIONS" ]]; then
    bash "$REPO_ROOT/scripts/opsx-session-update.sh" --session-id "$ACTIVE_SESSION" --status max_iterations_reached >/dev/null
    exit 0
fi

LAST_OUTPUT="$(python3 - "$TRANSCRIPT_PATH" <<'PY'
import json
import sys

last_texts = []
with open(sys.argv[1], "r", encoding="utf-8") as handle:
    for raw_line in handle:
        line = raw_line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if payload.get("role") != "assistant":
            continue
        texts = [item["text"] for item in payload.get("content", []) if item.get("type") == "text" and isinstance(item.get("text"), str)]
        if texts:
            last_texts = texts
if last_texts:
    sys.stdout.write("\n".join(last_texts))
PY
)"

PROMISE_TEXT="$(echo "$LAST_OUTPUT" | perl -0777 -pe 's/.*?<promise>(.*?)<\/promise>.*/$1/s; s/^\s+|\s+$//g; s/\s+/ /g' 2>/dev/null || true)"
if [[ -n "$PROMISE_TEXT" && "$PROMISE_TEXT" == "$COMPLETION_PROMISE" ]]; then
    bash "$REPO_ROOT/scripts/opsx-session-update.sh" --session-id "$ACTIVE_SESSION" --status achieved >/dev/null
    exit 0
fi

NEXT_ITERATION=$((ITERATION + 1))
TEMP_FILE="${LOOP_FILE}.tmp.$$"
sed "s/^iteration: .*/iteration: $NEXT_ITERATION/" "$LOOP_FILE" > "$TEMP_FILE"
mv "$TEMP_FILE" "$LOOP_FILE"
python3 - "$STATE_FILE" "$NEXT_ITERATION" <<'PY'
from __future__ import annotations
import sys
from pathlib import Path
import yaml

state_path = Path(sys.argv[1])
iteration = int(sys.argv[2])
state = yaml.safe_load(state_path.read_text(encoding="utf-8")) or {}
state["iteration"] = iteration
state_path.write_text(yaml.safe_dump(state, sort_keys=False), encoding="utf-8")
PY

PROMPT_TEXT="$(awk '/^---$/{i++; next} i>=2' "$LOOP_FILE")"
SYSTEM_MSG="OPSX [$ACTIVE_SESSION] iteration $NEXT_ITERATION | To complete: <promise>$COMPLETION_PROMISE</promise>"

perl -e '
  my ($prompt, $msg) = @ARGV;
  for my $s (\$prompt, \$msg) {
    $$s =~ s/([\\"])/\\$1/g;
    $$s =~ s/\n/\\n/g;
    $$s =~ s/\r/\\r/g;
    $$s =~ s/\t/\\t/g;
  }
  printf "{\"decision\":\"block\",\"reason\":\"%s\",\"systemMessage\":\"%s\"}\n", $prompt, $msg;
' -- "$PROMPT_TEXT" "$SYSTEM_MSG"
