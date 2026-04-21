#!/usr/bin/env bash
# Extract a stable metric summary from a QuantConnect backtest artifact.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

JSON_MODE=false
ARTIFACT_PATH=""

print_help() {
    cat <<'EOF'
Usage: bash scripts/extract-qc-backtest-metrics.sh --artifact-path <path-to-backtest.json> [--json]
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --artifact-path)
            ARTIFACT_PATH="${2:-}"
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

if [[ -z "$ARTIFACT_PATH" ]]; then
    echo "ERROR: --artifact-path is required." >&2
    print_help >&2
    exit 2
fi

REPO_ROOT="$(get_repo_root)" || exit 1
PYTHON_BIN="$(resolve_repo_python "$REPO_ROOT")" || exit 2
PYTHON_SCRIPT="$REPO_ROOT/scripts/python/extract_qc_backtest_metrics.py"

CMD=("$PYTHON_BIN" "$PYTHON_SCRIPT" --repo-root "$REPO_ROOT" --artifact-path "$ARTIFACT_PATH")
if $JSON_MODE; then
    CMD+=(--json)
fi

"${CMD[@]}"
