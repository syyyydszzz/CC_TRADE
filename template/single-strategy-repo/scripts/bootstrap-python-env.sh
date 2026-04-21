#!/usr/bin/env bash
# Create or refresh the repo-local Python environment used by repo helper scripts.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

PYTHON_BIN="${PYTHON_BIN:-}"
FULL_REQUIREMENTS=false
WITH_OPENSPEC=false
MIN_NODE_VERSION="20.19.0"
NODE_BOOTSTRAP_VERSION="${NODE_BOOTSTRAP_VERSION:-$MIN_NODE_VERSION}"
NODE_BIN="${NODE_BIN:-}"
NPM_BIN="${NPM_BIN:-}"
NODE_SOURCE=""
REPO_NODE_DIR="$REPO_ROOT/.tools/node"
REPO_NODE_CURRENT_DIR="$REPO_NODE_DIR/current"
REPO_NODE_BIN="$REPO_NODE_CURRENT_DIR/bin/node"
REPO_NPM_BIN="$REPO_NODE_CURRENT_DIR/bin/npm"

print_help() {
    cat <<'EOF'
Usage: bash scripts/bootstrap-python-env.sh [OPTIONS]

Options:
  --python <path>         Explicit Python interpreter used to create .venv
  --full-requirements     Attempt to install requirements.txt after the minimal helper deps
  --with-openspec         Also ensure Node.js 20.19.0+ and bootstrap repo-local OpenSpec
  --node-version <ver>    Repo-local Node.js version to download when --with-openspec needs it
  -h, --help              Show help

Default behavior:
  - create repo-local .venv if missing
  - install/upgrade pip
  - install PyYAML for repo workflow/result helper scripts

With --with-openspec:
  - ensure a repo-local Node.js runtime under .tools/node/current
  - download official Node.js binaries into .tools/node/ when the repo-local runtime is missing or outdated
  - run bash scripts/bootstrap-openspec.sh with the repo-local Node.js runtime
EOF
}

version_gte() {
    local actual="$1"
    local minimum="$2"

    "$PYTHON_BIN" - "$actual" "$minimum" <<'PY'
import sys

actual = tuple(int(part) for part in sys.argv[1].split("."))
minimum = tuple(int(part) for part in sys.argv[2].split("."))
sys.exit(0 if actual >= minimum else 1)
PY
}

resolve_node_binaries() {
    local path_node=""
    local path_npm=""

    NODE_SOURCE=""

    if [[ -n "$NODE_BIN" || -n "$NPM_BIN" ]]; then
        if [[ -x "$NODE_BIN" && -x "$NPM_BIN" ]]; then
            NODE_SOURCE="env"
            return 0
        fi

        cat >&2 <<EOF
ERROR: NODE_BIN and NPM_BIN must both point to executable files when provided.
NODE_BIN=$NODE_BIN
NPM_BIN=$NPM_BIN
EOF
        exit 2
    fi

    if [[ -x "$REPO_NODE_BIN" && -x "$REPO_NPM_BIN" ]]; then
        NODE_BIN="$REPO_NODE_BIN"
        NPM_BIN="$REPO_NPM_BIN"
        NODE_SOURCE="repo-local"
        return 0
    fi

    path_node="$(command -v node 2>/dev/null || true)"
    path_npm="$(command -v npm 2>/dev/null || true)"
    if [[ -n "$path_node" && -n "$path_npm" ]]; then
        NODE_BIN="$path_node"
        NPM_BIN="$path_npm"
        NODE_SOURCE="path"
        return 0
    fi

    NODE_BIN=""
    NPM_BIN=""
    return 1
}

node_version() {
    "$NODE_BIN" --version | sed 's/^v//'
}

detect_node_platform() {
    local os_name=""
    local arch_name=""

    case "$(uname -s)" in
        Darwin)
            os_name="darwin"
            ;;
        Linux)
            os_name="linux"
            ;;
        *)
            echo "ERROR: Unsupported OS for repo-local Node.js bootstrap: $(uname -s)" >&2
            exit 2
            ;;
    esac

    case "$(uname -m)" in
        arm64|aarch64)
            arch_name="arm64"
            ;;
        x86_64|amd64)
            arch_name="x64"
            ;;
        *)
            echo "ERROR: Unsupported CPU architecture for repo-local Node.js bootstrap: $(uname -m)" >&2
            exit 2
            ;;
    esac

    printf '%s-%s' "$os_name" "$arch_name"
}

install_repo_local_node() {
    local platform=""
    local archive_basename=""
    local archive_url=""
    local temp_archive=""
    local temp_extract_dir=""
    local unpacked_dir=""
    local version_dir=""

    if ! command -v curl >/dev/null 2>&1; then
        echo "ERROR: curl is required to download repo-local Node.js." >&2
        exit 2
    fi

    if ! command -v tar >/dev/null 2>&1; then
        echo "ERROR: tar is required to extract repo-local Node.js." >&2
        exit 2
    fi

    platform="$(detect_node_platform)"
    archive_basename="node-v${NODE_BOOTSTRAP_VERSION}-${platform}"
    archive_url="https://nodejs.org/dist/v${NODE_BOOTSTRAP_VERSION}/${archive_basename}.tar.gz"
    version_dir="$REPO_NODE_DIR/$archive_basename"

    mkdir -p "$REPO_NODE_DIR"

    if [[ -x "$version_dir/bin/node" && -x "$version_dir/bin/npm" ]]; then
        rm -rf "$REPO_NODE_CURRENT_DIR"
        ln -s "$version_dir" "$REPO_NODE_CURRENT_DIR"
        NODE_BIN="$REPO_NODE_BIN"
        NPM_BIN="$REPO_NPM_BIN"
        NODE_SOURCE="repo-local"
        return 0
    fi

    temp_archive="$(mktemp "${TMPDIR:-/tmp}/node-bootstrap.XXXXXX.tar.gz")"
    temp_extract_dir="$(mktemp -d "${TMPDIR:-/tmp}/node-bootstrap.XXXXXX")"

    echo "Bootstrapping repo-local Node.js v${NODE_BOOTSTRAP_VERSION} from $archive_url"
    curl -fsSL "$archive_url" -o "$temp_archive"
    tar -xzf "$temp_archive" -C "$temp_extract_dir"

    unpacked_dir="$temp_extract_dir/$archive_basename"
    if [[ ! -x "$unpacked_dir/bin/node" || ! -x "$unpacked_dir/bin/npm" ]]; then
        echo "ERROR: Downloaded Node.js archive did not contain the expected binaries." >&2
        exit 2
    fi

    rm -rf "$version_dir"
    mv "$unpacked_dir" "$version_dir"
    rm -rf "$REPO_NODE_CURRENT_DIR"
    ln -s "$version_dir" "$REPO_NODE_CURRENT_DIR"
    rm -f "$temp_archive"
    rm -rf "$temp_extract_dir"

    NODE_BIN="$REPO_NODE_BIN"
    NPM_BIN="$REPO_NPM_BIN"
    NODE_SOURCE="repo-local"
}

ensure_openspec_runtime() {
    local actual_node_version=""

    if [[ -x "$REPO_NODE_BIN" && -x "$REPO_NPM_BIN" ]]; then
        NODE_BIN="$REPO_NODE_BIN"
        NPM_BIN="$REPO_NPM_BIN"
        NODE_SOURCE="repo-local"
        actual_node_version="$(node_version)"
        if version_gte "$actual_node_version" "$MIN_NODE_VERSION"; then
            echo "OpenSpec runtime: using repo-local Node.js $actual_node_version from $NODE_BIN"
            return 0
        fi

        echo "OpenSpec runtime: found repo-local Node.js $actual_node_version, but $MIN_NODE_VERSION+ is required. Refreshing repo-local runtime."
    elif resolve_node_binaries; then
        actual_node_version="$(node_version)"
        if version_gte "$actual_node_version" "$MIN_NODE_VERSION"; then
            echo "OpenSpec runtime: found Node.js $actual_node_version from $NODE_SOURCE; installing repo-local runtime under .tools/node/current for deterministic OpenSpec execution."
        else
            echo "OpenSpec runtime: found Node.js $actual_node_version from $NODE_SOURCE, but $MIN_NODE_VERSION+ is required. Installing repo-local runtime."
        fi
    else
        echo "OpenSpec runtime: Node.js $MIN_NODE_VERSION+ not found. Installing repo-local runtime under .tools/node/current."
    fi

    install_repo_local_node
    actual_node_version="$(node_version)"
    if ! version_gte "$actual_node_version" "$MIN_NODE_VERSION"; then
        echo "ERROR: Repo-local Node.js bootstrap produced $actual_node_version, but $MIN_NODE_VERSION+ is required." >&2
        exit 2
    fi

    echo "OpenSpec runtime: using repo-local Node.js $actual_node_version from $NODE_BIN"
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --python)
            PYTHON_BIN="${2:-}"
            shift 2
            ;;
        --full-requirements)
            FULL_REQUIREMENTS=true
            shift
            ;;
        --with-openspec)
            WITH_OPENSPEC=true
            shift
            ;;
        --node-version)
            NODE_BOOTSTRAP_VERSION="${2:-}"
            shift 2
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

if [[ -z "$PYTHON_BIN" ]]; then
    if PYTHON_BIN="$(command -v python3 2>/dev/null)"; then
        :
    else
        echo "ERROR: python3 is required to bootstrap the repo-local .venv." >&2
        exit 2
    fi
fi

if [[ ! -x "$PYTHON_BIN" ]]; then
    echo "ERROR: Python interpreter is not executable: $PYTHON_BIN" >&2
    exit 2
fi

cd "$REPO_ROOT"

if [[ ! -d .venv ]]; then
    "$PYTHON_BIN" -m venv .venv
fi

VENV_PYTHON="$REPO_ROOT/.venv/bin/python"

if [[ ! -x "$VENV_PYTHON" ]]; then
    echo "ERROR: Failed to create repo-local Python environment at $REPO_ROOT/.venv" >&2
    exit 2
fi

"$VENV_PYTHON" -m pip install --upgrade pip >/dev/null
"$VENV_PYTHON" -m pip install "PyYAML>=6,<7"

if $FULL_REQUIREMENTS; then
    "$VENV_PYTHON" -m pip install -r "$REPO_ROOT/requirements.txt"
fi

if $WITH_OPENSPEC; then
    ensure_openspec_runtime
    NODE_BIN="$NODE_BIN" NPM_BIN="$NPM_BIN" bash "$SCRIPT_DIR/bootstrap-openspec.sh"
fi

echo "Repo Python environment ready: $VENV_PYTHON"
echo "Repo helper scripts will now prefer .venv automatically."

if $WITH_OPENSPEC; then
    echo "OpenSpec runtime ready: $NODE_BIN"
    echo "OpenSpec CLI bootstrap completed via scripts/bootstrap-openspec.sh"
fi
