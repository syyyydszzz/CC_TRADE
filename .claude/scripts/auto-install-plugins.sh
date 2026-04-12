#!/bin/bash
# Auto-install project plugins if not present

set -euo pipefail

PLUGIN_ID="achieve@claude-achieve-plugin"
INSTALLED_FILE="$HOME/.claude/plugins/installed_plugins.json"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
MARKETPLACE_DIR="$REPO_ROOT/claude-achieve-plugin-main"

if ! command -v claude >/dev/null 2>&1; then
  exit 0
fi

# Check if plugin is already installed
if [[ -f "$INSTALLED_FILE" ]] && grep -q "$PLUGIN_ID" "$INSTALLED_FILE"; then
  exit 0  # Already installed
fi

# Register the vendored marketplace directory in this repository
if [[ -d "$MARKETPLACE_DIR" ]]; then
  claude plugin marketplace add "$MARKETPLACE_DIR" 2>/dev/null || true
fi

claude plugin install "$PLUGIN_ID" --scope project 2>/dev/null || true
