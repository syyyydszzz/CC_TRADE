#!/usr/bin/env bash
# Initialize a strategy result workspace from canonical templates.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

JSON_MODE=false
FORCE_MODE=false

print_help() {
    cat <<'EOF'
Usage: bash scripts/init-result-workspace.sh [--json] [--force]
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --json)
            JSON_MODE=true
            shift
            ;;
        --force)
            FORCE_MODE=true
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

CMD=("$PYTHON_BIN" "$PYTHON_SCRIPT" init --repo-root "$REPO_ROOT")
if $JSON_MODE; then
    CMD+=(--json)
fi
if $FORCE_MODE; then
    CMD+=(--force)
fi

"${CMD[@]}"
