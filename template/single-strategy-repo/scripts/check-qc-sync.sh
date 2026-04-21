#!/usr/bin/env bash
# Check whether the local repo strategy source matches the QuantConnect workspace project.
# This checker validates the repo contract source file (`main.py`) and QC project metadata.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

QC_WORKSPACE="${QC_WORKSPACE_ROOT:-}"
PROJECT_NAME=""
JSON_MODE=false
SHOW_DIFF=false
PYTHON_BIN=""

print_help() {
    cat <<'EOF'
Usage: bash scripts/check-qc-sync.sh [OPTIONS]

Options:
  --qc-workspace <path>            QuantConnect workspace root. Defaults to --auto-detect, then $QC_WORKSPACE_ROOT
  --project-name <name>            QuantConnect project directory name. Defaults to repo directory name
  --json                           Emit machine-readable JSON
  --show-diff                      Print unified diff when repo and QC main.py differ
  -h, --help                       Show help

Notes:
  - This checker compares the current contract source file: main.py
  - It also validates whether the QC project is Cloud Platform-bound for qc-mcp workflows
  - It does not prove that the currently open project in QuantConnect Local Platform matches;
    use qc-mcp read_open_project for that gate
EOF
}

json_escape() {
    "$PYTHON_BIN" -c 'import json,sys; print(json.dumps(sys.argv[1], ensure_ascii=False))' "$1"
}

sha256_file() {
    local file_path="$1"
    "$PYTHON_BIN" - "$file_path" <<'PY'
import hashlib
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
if not path.exists():
    sys.exit(0)

hasher = hashlib.sha256()
with path.open("rb") as handle:
    for chunk in iter(lambda: handle.read(1024 * 1024), b""):
        hasher.update(chunk)
print(hasher.hexdigest())
PY
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
        --json)
            JSON_MODE=true
            shift
            ;;
        --show-diff)
            SHOW_DIFF=true
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

resolve_qc_workspace_root "$QC_WORKSPACE" "" || exit 2
QC_WORKSPACE="$QC_WORKSPACE_RESOLVED"

LOCAL_MAIN="$PROJECT_DIR/main.py"
QC_PROJECT_DIR="$QC_WORKSPACE/$PROJECT_NAME"
QC_MAIN="$QC_PROJECT_DIR/main.py"
QC_CONFIG="$QC_PROJECT_DIR/config.json"

PROJECT_EXISTS=false
CONFIG_EXISTS=false
LOCAL_MAIN_EXISTS=false
QC_MAIN_EXISTS=false
DEPLOYMENT_TARGET=""
CLOUD_ID=""
FILE_SYNC_STATUS="unknown"
CLOUD_STATUS="unknown"
OVERALL_STATUS="blocked"
READY_FOR_QC_MCP=false
RECOMMENDED_COMMAND=""
RECOMMENDED_ACTION=""
LOCAL_HASH=""
QC_HASH=""

if [[ -d "$QC_PROJECT_DIR" ]]; then
    PROJECT_EXISTS=true
fi

if [[ -f "$QC_CONFIG" ]]; then
    CONFIG_EXISTS=true
    DEPLOYMENT_TARGET="$(read_qc_field "$QC_CONFIG" "deployment-target")"
    CLOUD_ID="$(read_qc_field "$QC_CONFIG" "cloud-id")"
fi

if [[ -f "$LOCAL_MAIN" ]]; then
    LOCAL_MAIN_EXISTS=true
    LOCAL_HASH="$(sha256_file "$LOCAL_MAIN")"
fi

if [[ -f "$QC_MAIN" ]]; then
    QC_MAIN_EXISTS=true
    QC_HASH="$(sha256_file "$QC_MAIN")"
fi

if ! $PROJECT_EXISTS; then
    FILE_SYNC_STATUS="project_missing"
    CLOUD_STATUS="project_missing"
    RECOMMENDED_ACTION="Create or open the QC project named $PROJECT_NAME in QuantConnect Local Platform."
elif ! $CONFIG_EXISTS; then
    FILE_SYNC_STATUS="config_missing"
    CLOUD_STATUS="config_missing"
    RECOMMENDED_ACTION="Open the project through QuantConnect Local Platform so config.json is created."
elif ! $LOCAL_MAIN_EXISTS; then
    FILE_SYNC_STATUS="local_main_missing"
    CLOUD_STATUS="not_evaluated"
    RECOMMENDED_ACTION="Restore the local strategy source at $LOCAL_MAIN."
elif ! $QC_MAIN_EXISTS; then
    FILE_SYNC_STATUS="qc_main_missing"
    RECOMMENDED_ACTION="Sync the local strategy into the QC workspace with prepare-qc-project.sh."
else
    if cmp -s "$LOCAL_MAIN" "$QC_MAIN"; then
        FILE_SYNC_STATUS="in_sync"
    else
        FILE_SYNC_STATUS="out_of_sync"
    fi
fi

if $CONFIG_EXISTS; then
    if [[ "$DEPLOYMENT_TARGET" != "Cloud Platform" ]]; then
        CLOUD_STATUS="local_only"
        RECOMMENDED_ACTION="Switch or recreate $PROJECT_NAME as a Cloud Platform project before qc-mcp execution."
    elif [[ -z "$CLOUD_ID" ]]; then
        CLOUD_STATUS="missing_cloud_id"
        RECOMMENDED_ACTION="Reopen or recreate $PROJECT_NAME as a valid Cloud Platform project so cloud-id is assigned."
    else
        CLOUD_STATUS="cloud_ready"
    fi
fi

if [[ "$FILE_SYNC_STATUS" == "in_sync" && "$CLOUD_STATUS" == "cloud_ready" ]]; then
    OVERALL_STATUS="ready"
    READY_FOR_QC_MCP=true
    RECOMMENDED_ACTION="No file sync needed. You can run read_open_project next to verify the active QC project."
elif [[ "$PROJECT_EXISTS" == true && "$CONFIG_EXISTS" == true && "$FILE_SYNC_STATUS" != "project_missing" && "$FILE_SYNC_STATUS" != "config_missing" && "$FILE_SYNC_STATUS" != "local_main_missing" && "$CLOUD_STATUS" == "cloud_ready" ]]; then
    OVERALL_STATUS="sync_required"
    RECOMMENDED_ACTION="Run prepare-qc-project.sh to sync repo main.py into QC and push cloud code."
fi

if [[ "$PROJECT_EXISTS" == true ]]; then
    RECOMMENDED_COMMAND="bash scripts/prepare-qc-project.sh --qc-workspace $QC_WORKSPACE"
fi

if $JSON_MODE; then
    printf '{\n'
    printf '  "status": %s,\n' "$(json_escape "$OVERALL_STATUS")"
    printf '  "project_path": %s,\n' "$(json_escape "$PROJECT_PATH")"
    printf '  "strategy_path": %s,\n' "$(json_escape "$PROJECT_PATH")"
    printf '  "project_name": %s,\n' "$(json_escape "$PROJECT_NAME")"
    printf '  "qc_workspace": %s,\n' "$(json_escape "$QC_WORKSPACE")"
    printf '  "qc_workspace_source": %s,\n' "$(json_escape "$QC_WORKSPACE_SOURCE")"
    printf '  "qc_project_dir": %s,\n' "$(json_escape "$QC_PROJECT_DIR")"
    printf '  "local_main": %s,\n' "$(json_escape "$LOCAL_MAIN")"
    printf '  "qc_main": %s,\n' "$(json_escape "$QC_MAIN")"
    printf '  "project_exists": %s,\n' "$PROJECT_EXISTS"
    printf '  "config_exists": %s,\n' "$CONFIG_EXISTS"
    printf '  "local_main_exists": %s,\n' "$LOCAL_MAIN_EXISTS"
    printf '  "qc_main_exists": %s,\n' "$QC_MAIN_EXISTS"
    printf '  "file_sync_status": %s,\n' "$(json_escape "$FILE_SYNC_STATUS")"
    printf '  "local_hash": %s,\n' "$(json_escape "$LOCAL_HASH")"
    printf '  "qc_hash": %s,\n' "$(json_escape "$QC_HASH")"
    printf '  "deployment_target": %s,\n' "$(json_escape "$DEPLOYMENT_TARGET")"
    printf '  "cloud_id": %s,\n' "$(json_escape "$CLOUD_ID")"
    printf '  "cloud_status": %s,\n' "$(json_escape "$CLOUD_STATUS")"
    printf '  "ready_for_qc_mcp": %s,\n' "$READY_FOR_QC_MCP"
    printf '  "recommended_action": %s,\n' "$(json_escape "$RECOMMENDED_ACTION")"
    printf '  "recommended_command": %s\n' "$(json_escape "$RECOMMENDED_COMMAND")"
    printf '}\n'
    exit 0
fi

echo "QC sync status: $OVERALL_STATUS"
echo "Project path: $PROJECT_PATH"
echo "QC project: $QC_PROJECT_DIR"
echo "QC workspace: $QC_WORKSPACE"
echo "Project exists: $PROJECT_EXISTS"
echo "Config exists: $CONFIG_EXISTS"
echo "Deployment target: ${DEPLOYMENT_TARGET:-<missing>}"
echo "Cloud ID: ${CLOUD_ID:-<missing>}"
echo "Local main.py: $LOCAL_MAIN"
echo "QC main.py: $QC_MAIN"
echo "File sync: $FILE_SYNC_STATUS"
echo "Local hash: ${LOCAL_HASH:-<missing>}"
echo "QC hash: ${QC_HASH:-<missing>}"
echo "Cloud status: $CLOUD_STATUS"
echo "Ready for qc-mcp: $READY_FOR_QC_MCP"
echo "Recommended action: $RECOMMENDED_ACTION"
if [[ -n "$RECOMMENDED_COMMAND" ]]; then
    echo "Recommended command: $RECOMMENDED_COMMAND"
fi

if $SHOW_DIFF && [[ "$FILE_SYNC_STATUS" == "out_of_sync" ]]; then
    echo
    echo "--- diff: repo main.py vs QC main.py ---"
    diff -u "$LOCAL_MAIN" "$QC_MAIN" || true
fi
