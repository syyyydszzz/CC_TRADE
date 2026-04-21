#!/usr/bin/env bash
# Common helpers for repo-local workflow scripts.

get_repo_root() {
    local current_dir="$PWD"

    if [ -d "$current_dir/openspec" ] && [ -d "$current_dir/scripts" ] && [ -d "$current_dir/workflow" ]; then
        echo "$current_dir"
        return 0
    fi

    cat >&2 <<'EOF'
ERROR: repository root not found in the current directory.

Run this command from the repo root containing:
  - openspec/
  - scripts/
  - workflow/
EOF
    return 1
}

get_buildforce_root() {
    get_repo_root
}

REPO_PYTHON_SOURCE=""

resolve_repo_python() {
    local repo_root="${1:-}"
    local candidate=""

    REPO_PYTHON_SOURCE=""

    if [[ -n "${REPO_PYTHON:-}" ]]; then
        if [[ -x "$REPO_PYTHON" ]]; then
            REPO_PYTHON_SOURCE="env"
            printf '%s' "$REPO_PYTHON"
            return 0
        fi

        cat >&2 <<EOF
ERROR: REPO_PYTHON is set but not executable: $REPO_PYTHON
EOF
        return 1
    fi

    if [[ -n "$repo_root" && -x "$repo_root/.venv/bin/python" ]]; then
        REPO_PYTHON_SOURCE="repo-venv"
        printf '%s' "$repo_root/.venv/bin/python"
        return 0
    fi

    if candidate="$(command -v python3 2>/dev/null)"; then
        REPO_PYTHON_SOURCE="path"
        printf '%s' "$candidate"
        return 0
    fi

    cat >&2 <<EOF
ERROR: No usable Python interpreter found for repo scripts.

Preferred fix:
  bash scripts/bootstrap-python-env.sh
EOF
    return 1
}

resolve_buildforce_python() {
    resolve_repo_python "$@"
}

is_single_strategy_repo() {
    local repo_root="$1"
    [[ -f "$repo_root/main.py" ]] && [[ -f "$repo_root/spec.md" ]]
}

is_multi_strategy_repo() {
    local repo_root="$1"
    [[ -d "$repo_root/algorithms" ]]
}

resolve_project_dir() {
    local repo_root="$1"
    local requested_path="${2:-}"
    local candidate=""
    local algorithms_root="$repo_root/algorithms"

    if [[ -n "$requested_path" ]]; then
        candidate="$(cd "$repo_root" && python3 -c 'import os,sys; print(os.path.realpath(os.path.join(sys.argv[1], sys.argv[2])))' "$repo_root" "$requested_path")"

        if [[ ! -d "$candidate" ]]; then
            cat >&2 <<EOF
ERROR: Project directory not found: $requested_path
EOF
            return 1
        fi

        case "$candidate" in
            "$repo_root")
                if ! is_single_strategy_repo "$repo_root"; then
                    cat >&2 <<'EOF'
ERROR: Repo root was requested as the project, but this repository is not a single-strategy repo.
EOF
                    return 1
                fi
                printf '%s' "$candidate"
                return 0
                ;;
            "$algorithms_root"/*)
                printf '%s' "$candidate"
                return 0
                ;;
        esac

        cat >&2 <<EOF
ERROR: Project path must resolve to the repo root or a directory under algorithms/: $requested_path
EOF
        return 1
    fi

    if is_single_strategy_repo "$repo_root"; then
        printf '%s' "$repo_root"
        return 0
    fi

    cat >&2 <<'EOF'
ERROR: No project path was provided, and this repository is not a single-strategy repo.

Pass --strategy-path algorithms/<strategy> when operating on a multi-strategy example workspace.
EOF
    return 1
}

project_relative_path() {
    local repo_root="$1"
    local project_dir="$2"

    if [[ "$project_dir" == "$repo_root" ]]; then
        printf '.'
    else
        python3 -c 'import os,sys; print(os.path.relpath(sys.argv[2], sys.argv[1]))' "$repo_root" "$project_dir"
    fi
}

default_project_name() {
    local repo_root="$1"
    local project_dir="$2"

    if [[ "$project_dir" == "$repo_root" ]]; then
        basename "$repo_root"
    else
        basename "$project_dir"
    fi
}

QC_WORKSPACE_SOURCE=""
QC_WORKSPACE_NOTE=""
QC_WORKSPACE_RESOLVED=""

_append_unique_line() {
    local current="$1"
    local candidate="$2"

    if [[ -z "$candidate" ]]; then
        printf '%s' "$current"
        return 0
    fi

    case $'\n'"$current"$'\n' in
        *$'\n'"$candidate"$'\n'*)
            printf '%s' "$current"
            return 0
            ;;
    esac

    if [[ -z "$current" ]]; then
        printf '%s' "$candidate"
    else
        printf '%s\n%s' "$current" "$candidate"
    fi
}

is_valid_qc_workspace_root() {
    local workspace_root="$1"
    local project_name="${2:-}"

    [[ -n "$workspace_root" ]] || return 1
    [[ -d "$workspace_root" ]] || return 1
    [[ -f "$workspace_root/lean.json" ]] || return 1

    if [[ -n "$project_name" ]]; then
        [[ -d "$workspace_root/$project_name" ]] || return 1
        [[ -f "$workspace_root/$project_name/config.json" ]] || return 1
    fi

    return 0
}

resolve_qc_workspace_root() {
    local requested_root="${1:-}"
    local project_name="${2:-}"
    local candidates=""
    local discovered=""
    local candidate=""
    local invalid_requested=""
    local invalid_env=""

    QC_WORKSPACE_SOURCE=""
    QC_WORKSPACE_NOTE=""
    QC_WORKSPACE_RESOLVED=""

    if [[ -n "$requested_root" ]]; then
        if is_valid_qc_workspace_root "$requested_root" "$project_name"; then
            QC_WORKSPACE_SOURCE="argument"
            QC_WORKSPACE_RESOLVED="$requested_root"
            return 0
        fi
        invalid_requested="$requested_root"
    fi

    if [[ -n "${QC_WORKSPACE_ROOT:-}" ]]; then
        if is_valid_qc_workspace_root "$QC_WORKSPACE_ROOT" "$project_name"; then
            QC_WORKSPACE_SOURCE="env"
            QC_WORKSPACE_RESOLVED="$QC_WORKSPACE_ROOT"
            return 0
        fi
        invalid_env="$QC_WORKSPACE_ROOT"
    fi

    candidates="$(_append_unique_line "$candidates" "$HOME/Desktop/QuantConnect_project")"
    candidates="$(_append_unique_line "$candidates" "$HOME/Documents/QuantConnect_project")"
    candidates="$(_append_unique_line "$candidates" "$HOME/QuantConnect_project")"

    while IFS= read -r candidate; do
        discovered="$(dirname "$candidate")"
        candidates="$(_append_unique_line "$candidates" "$discovered")"
    done < <(find "$HOME" -maxdepth 4 -name lean.json 2>/dev/null)

    while IFS= read -r candidate; do
        [[ -n "$candidate" ]] || continue
        if is_valid_qc_workspace_root "$candidate" "$project_name"; then
            case "$candidate" in
                "$HOME/Desktop/QuantConnect_project"|"$HOME/Documents/QuantConnect_project"|"$HOME/QuantConnect_project")
                    QC_WORKSPACE_SOURCE="default"
                    ;;
                *)
                    QC_WORKSPACE_SOURCE="auto"
                    ;;
            esac

            if [[ -n "$invalid_requested" ]]; then
                QC_WORKSPACE_NOTE="Ignoring invalid --qc-workspace: $invalid_requested. Falling back to detected workspace: $candidate"
            elif [[ -n "$invalid_env" ]]; then
                QC_WORKSPACE_NOTE="Ignoring invalid QC_WORKSPACE_ROOT: $invalid_env. Falling back to detected workspace: $candidate"
            fi

            QC_WORKSPACE_RESOLVED="$candidate"
            return 0
        fi
    done <<< "$candidates"

    if [[ -n "$invalid_requested" ]]; then
        cat >&2 <<EOF
ERROR: QuantConnect workspace not found: $invalid_requested

No valid QC workspace was auto-detected after the explicit path failed.
Expected a workspace root containing lean.json and project metadata for:
  $project_name
EOF
        return 1
    fi

    if [[ -n "$invalid_env" ]]; then
        cat >&2 <<EOF
ERROR: QC_WORKSPACE_ROOT is set but invalid: $invalid_env

No valid QC workspace was auto-detected after the environment fallback failed.
Expected a workspace root containing lean.json and project metadata for:
  $project_name
EOF
        return 1
    fi

    cat >&2 <<EOF
ERROR: Could not find a QuantConnect workspace automatically.

Pass --qc-workspace <path> or set QC_WORKSPACE_ROOT to a workspace root that contains:
  - lean.json
  - $project_name/config.json
EOF
    return 1
}
