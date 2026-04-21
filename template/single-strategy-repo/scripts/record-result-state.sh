#!/usr/bin/env bash
# Record the machine-readable state summary for a strategy result workspace.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

REPO_ROOT="$(get_repo_root)" || exit 1
PYTHON_BIN="$(resolve_repo_python "$REPO_ROOT")" || exit 2
PYTHON_SCRIPT="$REPO_ROOT/scripts/python/result_workspace.py"

"$PYTHON_BIN" "$PYTHON_SCRIPT" record-state --repo-root "$REPO_ROOT" "$@"
