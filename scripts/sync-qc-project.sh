#!/usr/bin/env bash
# Sync a local strategy main.py between the repo source-of-truth and a QuantConnect workspace project.
# Note: this only copies files on disk. It does not push Cloud Platform projects to QuantConnect.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

STRATEGY_PATH=""
QC_WORKSPACE="${QC_WORKSPACE_ROOT:-}"
PROJECT_NAME=""
DIRECTION="repo-to-qc"
JSON_MODE=false
DRY_RUN=false
DEPLOYMENT_TARGET=""
REQUIRES_CLOUD_PUSH=false
PYTHON_BIN=""

print_help() {
    cat <<'EOF'
Usage: bash scripts/sync-qc-project.sh [--strategy-path algorithms/<strategy>] [OPTIONS]

Options:
  --strategy-path <path>           Repo-local strategy path, usually algorithms/<strategy>.
                                   Omit for a single-strategy repo rooted at main.py/spec.md.
  --qc-workspace <path>            QuantConnect workspace root. Defaults to --auto-detect, then $QC_WORKSPACE_ROOT
  --project-name <name>            QuantConnect project directory name. Defaults to repo or strategy folder name
  --direction <repo-to-qc|qc-to-repo>
                                   Sync direction. Default: repo-to-qc
  --json                           Emit machine-readable JSON
  --dry-run                        Show what would happen without writing files
  -h, --help                       Show help

Examples:
  bash scripts/sync-qc-project.sh \
    --strategy-path algorithms/minimal_test_strategy_v2 \
    --qc-workspace /Users/me/Desktop/QuantConnect_project

  bash scripts/sync-qc-project.sh \
    --qc-workspace /Users/me/Desktop/QuantConnect_project \
    --direction qc-to-repo
EOF
}

json_escape() {
    "$PYTHON_BIN" -c 'import json,sys; print(json.dumps(sys.argv[1], ensure_ascii=False))' "$1"
}

read_qc_field() {
    local field_name="$1"
    "$PYTHON_BIN" - "$QC_CONFIG" "$field_name" <<'PY'
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
        --strategy-path)
            STRATEGY_PATH="${2:-}"
            shift 2
            ;;
        --qc-workspace)
            QC_WORKSPACE="${2:-}"
            shift 2
            ;;
        --project-name)
            PROJECT_NAME="${2:-}"
            shift 2
            ;;
        --direction)
            DIRECTION="${2:-}"
            shift 2
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

case "$DIRECTION" in
    repo-to-qc|qc-to-repo)
        ;;
    *)
        echo "ERROR: --direction must be repo-to-qc or qc-to-repo." >&2
        exit 2
        ;;
esac

REPO_ROOT="$(get_repo_root)" || exit 1
PYTHON_BIN="$(resolve_repo_python "$REPO_ROOT")" || exit 2
PROJECT_DIR="$(resolve_project_dir "$REPO_ROOT" "$STRATEGY_PATH")" || exit 2

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

if [[ ! -d "$QC_WORKSPACE" ]]; then
    echo "ERROR: QuantConnect workspace not found: $QC_WORKSPACE" >&2
    exit 2
fi

if [[ ! -d "$QC_PROJECT_DIR" ]]; then
    cat >&2 <<EOF
ERROR: QuantConnect project directory not found: $QC_PROJECT_DIR

Create the project in QuantConnect Local Platform first, then rerun this sync.
EOF
    exit 2
fi

if [[ ! -f "$QC_CONFIG" ]]; then
    cat >&2 <<EOF
ERROR: QuantConnect project metadata not found: $QC_CONFIG

This target does not look like a valid QuantConnect project yet.
Create or open the project through QuantConnect Local Platform first.
EOF
    exit 2
fi

if [[ -n "$QC_WORKSPACE_NOTE" ]]; then
    echo "Note: $QC_WORKSPACE_NOTE" >&2
fi

DEPLOYMENT_TARGET="$(read_qc_field "deployment-target")"
if [[ "$DEPLOYMENT_TARGET" == "Cloud Platform" ]]; then
    REQUIRES_CLOUD_PUSH=true
fi

if [[ "$DIRECTION" == "repo-to-qc" ]]; then
    SOURCE_FILE="$LOCAL_MAIN"
    TARGET_FILE="$QC_MAIN"
    SOURCE_LABEL="repo"
    TARGET_LABEL="qc"
else
    SOURCE_FILE="$QC_MAIN"
    TARGET_FILE="$LOCAL_MAIN"
    SOURCE_LABEL="qc"
    TARGET_LABEL="repo"
fi

if [[ ! -f "$SOURCE_FILE" ]]; then
    echo "ERROR: Source file not found: $SOURCE_FILE" >&2
    exit 2
fi

STATUS="updated"
if [[ -f "$TARGET_FILE" ]] && cmp -s "$SOURCE_FILE" "$TARGET_FILE"; then
    STATUS="in_sync"
fi

if ! $DRY_RUN && [[ "$STATUS" == "updated" ]]; then
    cp "$SOURCE_FILE" "$TARGET_FILE"
fi

ACTION="sync"
if $DRY_RUN; then
    ACTION="dry_run"
fi

if $JSON_MODE; then
    printf '{\n'
    printf '  "action": %s,\n' "$(json_escape "$ACTION")"
    printf '  "status": %s,\n' "$(json_escape "$STATUS")"
    printf '  "direction": %s,\n' "$(json_escape "$DIRECTION")"
    printf '  "project_path": %s,\n' "$(json_escape "$PROJECT_PATH")"
    printf '  "strategy_path": %s,\n' "$(json_escape "$PROJECT_PATH")"
    printf '  "project_name": %s,\n' "$(json_escape "$PROJECT_NAME")"
    printf '  "source": {"kind": %s, "file": %s},\n' "$(json_escape "$SOURCE_LABEL")" "$(json_escape "$SOURCE_FILE")"
    printf '  "target": {"kind": %s, "file": %s},\n' "$(json_escape "$TARGET_LABEL")" "$(json_escape "$TARGET_FILE")"
    printf '  "qc_workspace": %s,\n' "$(json_escape "$QC_WORKSPACE")"
    printf '  "qc_workspace_source": %s,\n' "$(json_escape "$QC_WORKSPACE_SOURCE")"
    printf '  "deployment_target": %s,\n' "$(json_escape "$DEPLOYMENT_TARGET")"
    printf '  "requires_cloud_push": %s\n' "$REQUIRES_CLOUD_PUSH"
    printf '}\n'
    exit 0
fi

if [[ "$STATUS" == "in_sync" ]]; then
    echo "Already in sync: $SOURCE_FILE -> $TARGET_FILE"
    if [[ "$QC_WORKSPACE_SOURCE" != "argument" ]]; then
        echo "Using QC workspace: $QC_WORKSPACE ($QC_WORKSPACE_SOURCE)"
    fi
    if [[ "$DIRECTION" == "repo-to-qc" ]] && $REQUIRES_CLOUD_PUSH; then
        echo "Note: deployment-target is Cloud Platform. This sync updated local workspace files only." >&2
        if [[ "$PROJECT_DIR" == "$REPO_ROOT" ]]; then
            echo "Run bash scripts/prepare-qc-project.sh --qc-workspace $QC_WORKSPACE to push the QC project before qc-mcp execution." >&2
        else
            echo "Run bash scripts/prepare-qc-project.sh --strategy-path $PROJECT_PATH --qc-workspace $QC_WORKSPACE to push the QC project before qc-mcp execution." >&2
        fi
    fi
    exit 0
fi

if $DRY_RUN; then
    echo "Dry run: would sync $SOURCE_FILE -> $TARGET_FILE"
    if [[ "$QC_WORKSPACE_SOURCE" != "argument" ]]; then
        echo "Using QC workspace: $QC_WORKSPACE ($QC_WORKSPACE_SOURCE)"
    fi
    if [[ "$DIRECTION" == "repo-to-qc" ]] && $REQUIRES_CLOUD_PUSH; then
        echo "Note: deployment-target is Cloud Platform. A follow-up lean cloud push would still be required." >&2
    fi
    exit 0
fi

echo "Synced $SOURCE_FILE -> $TARGET_FILE"
if [[ "$QC_WORKSPACE_SOURCE" != "argument" ]]; then
    echo "Using QC workspace: $QC_WORKSPACE ($QC_WORKSPACE_SOURCE)"
fi
if [[ "$DIRECTION" == "repo-to-qc" ]] && $REQUIRES_CLOUD_PUSH; then
    echo "Note: deployment-target is Cloud Platform. This sync updated local workspace files only." >&2
    if [[ "$PROJECT_DIR" == "$REPO_ROOT" ]]; then
        echo "Run bash scripts/prepare-qc-project.sh --qc-workspace $QC_WORKSPACE to push the QC project before qc-mcp execution." >&2
    else
        echo "Run bash scripts/prepare-qc-project.sh --strategy-path $PROJECT_PATH --qc-workspace $QC_WORKSPACE to push the QC project before qc-mcp execution." >&2
    fi
fi
