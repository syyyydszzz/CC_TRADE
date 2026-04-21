#!/usr/bin/env bash
# Validate a strategy result workspace against the repository contract.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

JSON_MODE=false
STRATEGY_PATH=""

print_help() {
    cat <<'EOF'
Usage: bash scripts/check-result-workspace.sh [--strategy-path algorithms/<strategy>] [--json]

If --strategy-path is omitted, the repo root must already be a single-strategy workspace.
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --strategy-path)
            STRATEGY_PATH="${2:-}"
            shift 2
            ;;
        --json)
            JSON_MODE=true
            shift
            ;;
        --help|-h)
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

REPO_ROOT="$(get_repo_root)" || exit 1
PYTHON_BIN="$(resolve_repo_python "$REPO_ROOT")" || exit 2
PYTHON_SCRIPT="$REPO_ROOT/scripts/python/result_workspace.py"

CMD=("$PYTHON_BIN" "$PYTHON_SCRIPT" check --repo-root "$REPO_ROOT")
if [[ -n "$STRATEGY_PATH" ]]; then
    CMD+=(--strategy-path "$STRATEGY_PATH")
fi
if $JSON_MODE; then
    CMD+=(--json)
fi

"${CMD[@]}"
