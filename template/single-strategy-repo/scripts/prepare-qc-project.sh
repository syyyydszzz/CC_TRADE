#!/usr/bin/env bash
# Prepare a QuantConnect project for qc-mcp execution:
# 1) sync repo main.py into the QC workspace project
# 2) if deployment-target is Cloud Platform, push the QC project to QuantConnect with LEAN CLI

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

QC_WORKSPACE="${QC_WORKSPACE_ROOT:-}"
PROJECT_NAME=""
LEAN_BIN="${LEAN_BIN:-}"
JSON_MODE=false
DRY_RUN=false
FORCE_PUSH=false
PYTHON_BIN=""

print_help() {
    cat <<'EOF'
Usage: bash scripts/prepare-qc-project.sh [OPTIONS]

Options:
  --qc-workspace <path>            QuantConnect workspace root. Defaults to --auto-detect, then $QC_WORKSPACE_ROOT
  --project-name <name>            QuantConnect project directory name. Defaults to repo directory name
  --lean-binary <path>             Explicit LEAN CLI binary to use for cloud push
  --force                          Pass --force to lean cloud push
  --json                           Emit machine-readable JSON
  --dry-run                        Show what would happen without writing files
  -h, --help                       Show help

Examples:
  bash scripts/prepare-qc-project.sh --qc-workspace /Users/me/Desktop/QuantConnect_project
EOF
}

json_escape() {
    "$PYTHON_BIN" -c 'import json,sys; print(json.dumps(sys.argv[1], ensure_ascii=False))' "$1"
}

read_qc_field() {
    local config_path="$1"
    local field_name="$2"
    "$PYTHON_BIN" - "$config_path" "$field_name" <<'PY'
import json
import sys

config_path, field_name = sys.argv[1], sys.argv[2]
with open(config_path, "r", encoding="utf-8") as handle:
    data = json.load(handle)
value = data.get(field_name)
print("" if value is None else value)
PY
}

find_lean_bin() {
    local candidate=""
    if [[ -n "$LEAN_BIN" ]]; then
        candidate="$LEAN_BIN"
        if [[ ! -x "$candidate" ]]; then
            echo "ERROR: --lean-binary is not executable: $candidate" >&2
            exit 2
        fi
        echo "$candidate"
        return 0
    fi

    if candidate="$(command -v lean 2>/dev/null)"; then
        echo "$candidate"
        return 0
    fi

    for candidate in \
        "$HOME/anaconda3/bin/lean" \
        "/usr/local/bin/lean" \
        "/opt/homebrew/bin/lean" \
        "$HOME/.local/bin/lean" \
        "$HOME/bin/lean"; do
        if [[ -x "$candidate" ]]; then
            echo "$candidate"
            return 0
        fi
    done

    echo "ERROR: LEAN CLI not found. Install it or pass --lean-binary <path>." >&2
    exit 2
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --qc-workspace)
            QC_WORKSPACE="${2:-}"
            shift 2
            ;;
        --project-name)
            PROJECT_NAME="${2:-}"
            shift 2
            ;;
        --lean-binary)
            LEAN_BIN="${2:-}"
            shift 2
            ;;
        --force)
            FORCE_PUSH=true
            shift
            ;;
        --json)
            JSON_MODE=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
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

REPO_ROOT="$(get_repo_root)" || exit 1
PYTHON_BIN="$(resolve_repo_python "$REPO_ROOT")" || exit 2
PROJECT_DIR="$(resolve_project_dir "$REPO_ROOT" "")" || exit 2

if [[ ! -d "$PROJECT_DIR" ]]; then
    echo "ERROR: Project directory not found: $PROJECT_DIR" >&2
    exit 2
fi

if [[ -z "$PROJECT_NAME" ]]; then
    PROJECT_NAME="$(default_project_name "$REPO_ROOT" "$PROJECT_DIR")"
fi

PROJECT_PATH="$(project_relative_path "$REPO_ROOT" "$PROJECT_DIR")"

resolve_qc_workspace_root "$QC_WORKSPACE" "$PROJECT_NAME" || exit 2
QC_WORKSPACE="$QC_WORKSPACE_RESOLVED"

LOCAL_MAIN="$PROJECT_DIR/main.py"
QC_PROJECT_DIR="$QC_WORKSPACE/$PROJECT_NAME"
QC_MAIN="$QC_PROJECT_DIR/main.py"
QC_CONFIG="$QC_PROJECT_DIR/config.json"
QC_LEAN_CONFIG="$QC_WORKSPACE/lean.json"

if [[ ! -d "$QC_WORKSPACE" ]]; then
    echo "ERROR: QuantConnect workspace not found: $QC_WORKSPACE" >&2
    exit 2
fi

if [[ ! -d "$QC_PROJECT_DIR" ]]; then
    echo "ERROR: QuantConnect project directory not found: $QC_PROJECT_DIR" >&2
    exit 2
fi

if [[ ! -f "$QC_CONFIG" ]]; then
    echo "ERROR: QuantConnect project metadata not found: $QC_CONFIG" >&2
    exit 2
fi

if [[ ! -f "$QC_LEAN_CONFIG" ]]; then
    cat >&2 <<EOF
ERROR: LEAN workspace config not found: $QC_LEAN_CONFIG

QuantConnect cloud push requires lean.json at the QC workspace root.
EOF
    exit 2
fi

if [[ ! -f "$LOCAL_MAIN" ]]; then
    echo "ERROR: Source file not found: $LOCAL_MAIN" >&2
    exit 2
fi

if [[ -n "$QC_WORKSPACE_NOTE" ]]; then
    echo "Note: $QC_WORKSPACE_NOTE" >&2
fi

DEPLOYMENT_TARGET="$(read_qc_field "$QC_CONFIG" "deployment-target")"
CLOUD_ID="$(read_qc_field "$QC_CONFIG" "cloud-id")"

SYNC_STATUS="updated"
if [[ -f "$QC_MAIN" ]] && cmp -s "$LOCAL_MAIN" "$QC_MAIN"; then
    SYNC_STATUS="in_sync"
fi

if ! $DRY_RUN && [[ "$SYNC_STATUS" == "updated" ]]; then
    cp "$LOCAL_MAIN" "$QC_MAIN"
fi

PUSH_STATUS="not_required"
LEAN_BIN_USED=""

if [[ "$DEPLOYMENT_TARGET" == "Cloud Platform" ]]; then
    LEAN_BIN_USED="$(find_lean_bin)"
    if $DRY_RUN; then
        PUSH_STATUS="would_push"
    else
        PUSH_STATUS="pushed"
        PUSH_CMD=("$LEAN_BIN_USED" cloud push --project "$PROJECT_NAME")
        if $FORCE_PUSH; then
            PUSH_CMD+=(--force)
        fi
        (
            cd "$QC_WORKSPACE"
            "${PUSH_CMD[@]}"
        )
    fi
fi

if $JSON_MODE; then
    printf '{\n'
    printf '  "action": %s,\n' "$(json_escape "$([[ "$PUSH_STATUS" == "not_required" ]] && echo sync_only || echo prepare_execution)")"
    printf '  "project_path": %s,\n' "$(json_escape "$PROJECT_PATH")"
    printf '  "strategy_path": %s,\n' "$(json_escape "$PROJECT_PATH")"
    printf '  "project_name": %s,\n' "$(json_escape "$PROJECT_NAME")"
    printf '  "qc_workspace": %s,\n' "$(json_escape "$QC_WORKSPACE")"
    printf '  "qc_workspace_source": %s,\n' "$(json_escape "$QC_WORKSPACE_SOURCE")"
    printf '  "qc_project_dir": %s,\n' "$(json_escape "$QC_PROJECT_DIR")"
    printf '  "deployment_target": %s,\n' "$(json_escape "$DEPLOYMENT_TARGET")"
    printf '  "cloud_id": %s,\n' "$(json_escape "$CLOUD_ID")"
    printf '  "sync_status": %s,\n' "$(json_escape "$SYNC_STATUS")"
    printf '  "push_status": %s,\n' "$(json_escape "$PUSH_STATUS")"
    printf '  "lean_binary": %s\n' "$(json_escape "$LEAN_BIN_USED")"
    printf '}\n'
    exit 0
fi

if $DRY_RUN; then
    if [[ "$SYNC_STATUS" == "in_sync" ]]; then
        echo "Dry run: repo and QC workspace already match: $LOCAL_MAIN -> $QC_MAIN"
    else
        echo "Dry run: would sync $LOCAL_MAIN -> $QC_MAIN"
    fi
else
    if [[ "$SYNC_STATUS" == "in_sync" ]]; then
        echo "Repo and QC workspace already match: $LOCAL_MAIN -> $QC_MAIN"
    else
        echo "Synced $LOCAL_MAIN -> $QC_MAIN"
    fi
fi

if [[ "$QC_WORKSPACE_SOURCE" != "argument" ]]; then
    echo "Using QC workspace: $QC_WORKSPACE ($QC_WORKSPACE_SOURCE)"
fi

if [[ "$DEPLOYMENT_TARGET" == "Cloud Platform" ]]; then
    if $DRY_RUN; then
        echo "Dry run: would push $QC_PROJECT_DIR to QuantConnect cloud with $LEAN_BIN_USED"
    else
        echo "Pushed $QC_PROJECT_DIR to QuantConnect cloud with $LEAN_BIN_USED"
    fi
else
    echo "No cloud push required: deployment-target is $DEPLOYMENT_TARGET"
fi
