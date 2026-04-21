---
description: Archive a verified OpenSpec qc-change and close the workflow cleanly.
---

User input:

$ARGUMENTS

You are running the archive step for an OpenSpec `qc-change`.

## Required behavior

1. Confirm verification already succeeded for the target change.
2. Treat `openspec/changes/{change}/` as the only planning archive authority.
3. Re-run `bash scripts/opsx.sh validate <change>` and stop if it fails.
4. Re-run `bash scripts/check-result-workspace.sh` and stop if it fails.
5. Do not archive when QC gates, compile/backtest evidence, result checks, or required tasks are still failing.
6. Keep any summary tied to the OpenSpec change and the strategy result workspace.
7. If the optional thin runtime loop is active, it may be updated separately under `.claude/runtime/opsx-sessions/`, but archive must not depend on Achieve session state.
8. Run `bash scripts/opsx.sh archive <change> -y` to merge delta specs into `openspec/specs/` and move the change directory to `openspec/changes/archive/`.
