---
description: Check whether the repo-root strategy and its QuantConnect project are actually synchronized.
---

User input:

$ARGUMENTS

You are checking whether the repo source-of-truth strategy is actually aligned with the corresponding QuantConnect project files.

## Goal

Report whether the local repo and QC project are truly synchronized, not just whether their names match.

## Required behavior

1. Confirm the repository root contains `openspec/`, `scripts/`, and `workflow/`.
2. Parse `$ARGUMENTS`.
   - Preferred input shape:
     - `/qc.sync-status`
     - `/qc.sync-status --qc-workspace /Users/me/Desktop/QuantConnect_project`
3. Preserve optional CLI-style flags from `$ARGUMENTS` and pass them through to:

   `bash scripts/check-qc-sync.sh --json ...`

4. Read the JSON output and summarize:
   - overall status
   - file sync status for `main.py`
   - deployment target
   - cloud id presence
   - whether it is ready for `qc-mcp`
   - the recommended next command
5. Be explicit that this command checks local-vs-QC file sync and QC metadata only.
   - It does not prove the currently active open project in QuantConnect Local Platform.
   - If the user needs that gate too, tell them to run a `read_open_project` probe next.
