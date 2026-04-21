#!/usr/bin/env bash
# Validate user-scoped qc-mcp registration for Claude Code.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

JSON_MODE=false

print_help() {
    cat <<'EOF'
Usage: bash scripts/check-qc-mcp.sh [--json]

Behavior:
  - checks ~/.claude.json for an mcpServers.qc-mcp entry
  - reports the configured URL when present
  - prints host-native and devcontainer example config paths when missing

This script validates server registration only.
It does not verify the currently open QuantConnect Local Platform project.
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --json)
            JSON_MODE=true
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
CLAUDE_CONFIG="$HOME/.claude.json"
HOST_EXAMPLE="$REPO_ROOT/docs/qc-mcp-claude-config.example.json"
DEVCONTAINER_EXAMPLE="$REPO_ROOT/docs/qc-mcp-claude-config.devcontainer.example.json"

"$PYTHON_BIN" - "$CLAUDE_CONFIG" "$HOST_EXAMPLE" "$DEVCONTAINER_EXAMPLE" "$JSON_MODE" <<'PY'
import json
import sys
from pathlib import Path

config_path = Path(sys.argv[1]).expanduser()
host_example = Path(sys.argv[2])
devcontainer_example = Path(sys.argv[3])
json_mode = sys.argv[4] == "true"

payload = {
    "ok": False,
    "config_path": str(config_path),
    "qc_mcp_registered": False,
    "url": None,
    "mode_hint": None,
    "host_example": str(host_example),
    "devcontainer_example": str(devcontainer_example),
    "notes": [
        "This checks only user-scoped qc-mcp registration.",
        "You still need read_open_project to confirm the active QuantConnect project.",
    ],
}

errors = []
warnings = []

if not config_path.exists():
    errors.append(f"Missing Claude config: {config_path}")
else:
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"Invalid JSON in {config_path}: {exc}")
    else:
        mcp_servers = data.get("mcpServers")
        if not isinstance(mcp_servers, dict):
            errors.append("~/.claude.json is missing mcpServers.")
        else:
            qc_mcp = mcp_servers.get("qc-mcp")
            if not isinstance(qc_mcp, dict):
                errors.append("~/.claude.json is missing mcpServers.qc-mcp.")
            else:
                payload["qc_mcp_registered"] = True
                url = qc_mcp.get("url")
                payload["url"] = url
                if isinstance(url, str):
                    if url == "http://localhost:3001/":
                        payload["mode_hint"] = "host-native"
                    elif url == "http://host.docker.internal:3001/":
                        payload["mode_hint"] = "devcontainer"
                    else:
                        warnings.append(f"qc-mcp is registered with a non-standard URL: {url}")
                else:
                    warnings.append("qc-mcp is registered but has no string url field.")

if payload["qc_mcp_registered"]:
    payload["ok"] = True

if json_mode:
    payload["errors"] = errors
    payload["warnings"] = warnings
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    sys.exit(0 if payload["ok"] else 1)

if payload["ok"]:
    print("qc-mcp registration: OK")
    print(f"Claude config: {payload['config_path']}")
    print(f"URL: {payload['url'] or '<missing>'}")
    print(f"Mode hint: {payload['mode_hint'] or 'custom'}")
    print("Next gate: run read_open_project to verify the active QuantConnect Local Platform project.")
    if warnings:
        for item in warnings:
            print(f"WARNING: {item}")
    sys.exit(0)

print("qc-mcp registration: FAIL")
for item in errors:
    print(f"ERROR: {item}")
for item in warnings:
    print(f"WARNING: {item}")
print(f"Host-native example: {host_example}")
print(f"Devcontainer example: {devcontainer_example}")
print("Add qc-mcp to ~/.claude.json, then rerun this check.")
sys.exit(1)
PY
