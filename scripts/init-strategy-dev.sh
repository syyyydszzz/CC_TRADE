#!/usr/bin/env bash
# Backward-compatible wrapper for the new single-strategy repo generator.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cat >&2 <<'EOF'
Note: scripts/init-strategy-dev.sh is deprecated.
Use bash scripts/new-strategy-repo.sh ... instead.
EOF

exec bash "$SCRIPT_DIR/new-strategy-repo.sh" "$@"
