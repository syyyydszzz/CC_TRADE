#!/usr/bin/env bash
# Install the pinned OpenSpec CLI and refresh repo-managed OpenSpec assets.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
MIN_NODE_VERSION="20.19.0"
NODE_BIN="${NODE_BIN:-}"
NPM_BIN="${NPM_BIN:-}"
REPO_NODE_BIN="$REPO_ROOT/.tools/node/current/bin/node"
REPO_NPM_BIN="$REPO_ROOT/.tools/node/current/bin/npm"
NODE_BIN_DIR=""

print_help() {
    cat <<'EOF'
Usage: bash scripts/bootstrap-openspec.sh

Behavior:
  - require Node.js 20.19.0+ from PATH, env override, or .tools/node/current
  - install pinned npm dependencies from package.json
  - verify ./node_modules/.bin/openspec exists
  - run `openspec update` from the repo root
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
    print_help
    exit 0
fi

if [[ -z "$NODE_BIN" ]]; then
    if [[ -x "$REPO_NODE_BIN" ]]; then
        NODE_BIN="$REPO_NODE_BIN"
    else
    NODE_BIN="$(command -v node 2>/dev/null || true)"
    fi
fi

if [[ -z "$NPM_BIN" ]]; then
    if [[ -x "$REPO_NPM_BIN" ]]; then
        NPM_BIN="$REPO_NPM_BIN"
    else
    NPM_BIN="$(command -v npm 2>/dev/null || true)"
    fi
fi

if [[ -z "$NODE_BIN" || -z "$NPM_BIN" ]]; then
    cat >&2 <<EOF
ERROR: Node.js $MIN_NODE_VERSION+ and npm are required for OpenSpec bootstrap.

Preferred fix:
  bash scripts/bootstrap-python-env.sh --with-openspec

Or install Node manually, then rerun:
  bash scripts/bootstrap-openspec.sh
EOF
    exit 2
fi

NODE_VERSION="$("$NODE_BIN" --version | sed 's/^v//')"
python3 - "$NODE_VERSION" "$MIN_NODE_VERSION" <<'PY'
import sys

actual = tuple(int(part) for part in sys.argv[1].split("."))
minimum = tuple(int(part) for part in sys.argv[2].split("."))
if actual < minimum:
    print(
        f"ERROR: Node.js {sys.argv[2]}+ is required. Found {sys.argv[1]}.",
        file=sys.stderr,
    )
    sys.exit(1)
PY

NODE_BIN_DIR="$(cd "$(dirname "$NODE_BIN")" && pwd)"
export PATH="$NODE_BIN_DIR:$PATH"

cd "$REPO_ROOT"

"$NPM_BIN" install

OPENSPEC_BIN="$REPO_ROOT/node_modules/.bin/openspec"
if [[ ! -x "$OPENSPEC_BIN" ]]; then
    echo "ERROR: OpenSpec CLI was not installed at $OPENSPEC_BIN" >&2
    exit 2
fi

if [[ ! -d "$REPO_ROOT/openspec" ]] || [[ ! -f "$REPO_ROOT/openspec/config.yaml" ]]; then
    cat >&2 <<'EOF'
ERROR: This repository expects tracked OpenSpec assets under openspec/.
Restore the repository files before bootstrapping again.
EOF
    exit 2
fi

"$OPENSPEC_BIN" update

echo "OpenSpec bootstrap complete."
echo "CLI: $OPENSPEC_BIN"
echo "Next: use /opsx.* commands in Claude Code or bash scripts/opsx.sh list --specs"
