---
description: Generate a brand-new single-strategy repo from this template workspace.
---

User input:

$ARGUMENTS

You are running the template repo's scaffold command.

Use the `strategy-init` skill as the orchestration layer for this command.

## Goal

Create a new single-strategy repository on disk and return the generated `/opsx.propose` prompt.

## Required behavior

1. Treat `$ARGUMENTS` as the raw user request for `strategy-init`.
2. Use `bash scripts/new-strategy-repo.sh --json` as the only repo generator.
3. Run the generator from the template repo root.
4. Summarize:
   - generated repo root
   - prompt file path
   - results root
5. Print the generated `/opsx.propose` prompt inline in the final response.
6. Tell the user the exact next bootstrap sequence:
   - `bash scripts/bootstrap-python-env.sh --with-openspec`
   - `bash scripts/check-qc-mcp.sh`
   - `bash scripts/opsx.sh list --specs`
   - `claude`

## Notes

- This command belongs only in the template repo.
- It is an explicit entrypoint and UX shortcut for `strategy-init`; it does not replace the skill.
- It does not modify `~/.claude.json`.
- It does not auto-install or proxy `qc-mcp`.
