#!/usr/bin/env bash
# Repo-local OpenSpec CLI wrapper.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
OPENSPEC_BIN="$REPO_ROOT/node_modules/.bin/openspec"
REPO_NODE_BIN_DIR="$REPO_ROOT/.tools/node/current/bin"

if [[ ! -x "$OPENSPEC_BIN" ]]; then
    cat >&2 <<'EOF'
ERROR: OpenSpec CLI is not installed for this repository.

Run:
  bash scripts/bootstrap-python-env.sh --with-openspec
or:
  bash scripts/bootstrap-openspec.sh
EOF
    exit 2
fi

if [[ -d "$REPO_NODE_BIN_DIR" ]]; then
    export PATH="$REPO_NODE_BIN_DIR:$PATH"
fi

cd "$REPO_ROOT"
exec "$OPENSPEC_BIN" "$@"
