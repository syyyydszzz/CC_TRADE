---
description: Verify an OpenSpec qc-change against tasks, QC evidence, and result workspace integrity.
---

User input:

$ARGUMENTS

You are running the verification step for an OpenSpec `qc-change`.

## Required behavior

1. Load the target change from `openspec/changes/{change}/`.
2. Fail fast on any command error, parsing error, missing field, or internal exception. Do not continue after a failed verification sub-step.
3. Run `bash scripts/opsx.sh validate <change>` first and stop immediately if change validation fails.
4. Verify that required tasks are complete and that blockers are documented if they are not.
5. For strategy work, validate:
   - `compile.json` and `backtest.json` exist when a backtest was executed
   - `results/state.yaml` matches the latest `run.yaml`, including `latest_compile` and `latest_backtest`
   - `results/report.md` reflects the current verdict
   - `bash scripts/check-result-workspace.sh` passes
   - completed tasks still match the final code and result files
6. Read the current `proposal.md` and verify its success criteria dynamically. Do not hardcode a count such as "six criteria".
7. Treat any missing gates, missing evidence, stale tasks, or contract violations as blockers that prevent archive.
8. Do not invent semantic mappings that are not written in the repository authority. For example, do not claim `passed` means `backtest_ok` unless the files explicitly say so.
9. Do not create planning artifacts outside `openspec/changes/{change}/`.
10. Suggest `/opsx.archive` only when the change is actually ready to close.
