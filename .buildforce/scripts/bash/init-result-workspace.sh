#!/usr/bin/env bash
# Initialize a strategy result workspace from canonical templates.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

JSON_MODE=false
FORCE_MODE=false
STRATEGY_PATH=""

print_help() {
    cat <<'EOF'
Usage: bash .buildforce/scripts/bash/init-result-workspace.sh --strategy-path algorithms/<strategy> [--json] [--force]
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

if [[ -z "$STRATEGY_PATH" ]]; then
    echo "ERROR: --strategy-path is required." >&2
    print_help >&2
    exit 2
fi

if ! command -v python3 >/dev/null 2>&1; then
    echo "ERROR: python3 is required for result workspace tooling. Install dependencies with \`pip install -r requirements.txt\`." >&2
    exit 2
fi

BUILDFORCE_ROOT="$(get_buildforce_root)" || exit 1
PYTHON_SCRIPT="$BUILDFORCE_ROOT/.buildforce/scripts/python/result_workspace.py"

CMD=(python3 "$PYTHON_SCRIPT" init --buildforce-root "$BUILDFORCE_ROOT" --strategy-path "$STRATEGY_PATH")
if $JSON_MODE; then
    CMD+=(--json)
fi
if $FORCE_MODE; then
    CMD+=(--force)
fi

"${CMD[@]}"
