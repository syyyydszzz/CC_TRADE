---
description: Sync the repo-root strategy into the QuantConnect project and push cloud code when required.
---

User input:

$ARGUMENTS

You are synchronizing the repo source-of-truth strategy into its QuantConnect project mirror so qc-mcp executes the latest code.

## Goal

Copy the local `main.py` into the matching QC project and, when the QC project targets Cloud Platform, push the updated project to QuantConnect cloud.

## Required behavior

1. Confirm the repository root contains `openspec/`, `scripts/`, and `workflow/`.
2. Parse `$ARGUMENTS`.
   - Preferred input shape:
     - `/qc.sync`
     - `/qc.sync --qc-workspace /Users/me/Desktop/QuantConnect_project`
     - `/qc.sync --force`
3. Preserve optional CLI-style flags from `$ARGUMENTS` and pass them through to:

   `bash scripts/prepare-qc-project.sh --json ...`

4. Run the sync command from the repo root.
5. Read the JSON output and summarize:
   - sync status
   - deployment target
   - cloud id
   - whether a cloud push happened
   - the QC workspace and QC project paths used
6. Be explicit about the remaining gate:
   - This command syncs files and cloud code only
   - It does not prove the currently active open project in QuantConnect Local Platform
   - If the user wants to execute qc-mcp next, tell them to run `read_open_project`
