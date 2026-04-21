# Optional OpenSpec Runtime Sessions

This directory stores optional thin loop session state for OpenSpec-driven work.

- Start a session with `bash scripts/opsx-session-start.sh --change-id <change-id>`.
- Update status or attempts with `bash scripts/opsx-session-update.sh ...`.
- If you want Claude Code to reuse the old stop-hook loop pattern, wire `bash scripts/opsx-stop-hook.sh` into a local Stop hook manually.

This runtime layer is intentionally thin:

- It does not own planning artifacts.
- It only references an existing `openspec/changes/{change}`.
- It tracks runtime-only fields such as status, attempts, iteration, and last gate.
