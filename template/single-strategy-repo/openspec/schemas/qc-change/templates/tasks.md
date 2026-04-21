# Tasks

## Design

- [ ] Finalize strategy or workflow design details and confirm the required change specs under `specs/`

## Local Implementation

- [ ] Update repo-root source files to match the approved change
- [ ] Keep completed task descriptions aligned with the final implementation shape if compile/backtest fixes change the code

## QC Execution

- [ ] Confirm the active QC project with `read_open_project`
- [ ] Run `create_compile` and `read_compile`, resolve every error and warning, and save `compile.json`
- [ ] Run `create_backtest` and `read_backtest`, then save `backtest.json`

## Result Persistence

- [ ] Write raw compile/backtest artifacts under `results/artifacts/runs/{run_id}/`
- [ ] Run `bash scripts/record-result-run.sh ...` with `--stage compile` before `--stage backtest` when backtest evidence exists
- [ ] Run `bash scripts/record-result-state.sh ...` using only canonical result statuses: `not_run`, `passed`, `failed`, `blocked`, `needs_iteration`
- [ ] Refresh `results/report.md`
- [ ] Run `bash scripts/check-result-workspace.sh`

## Independent Review

- [ ] Confirm completed tasks still match the final code and machine-readable result files
- [ ] Review the run outcome separately from the implementation pass

## Validation

- [ ] Run `bash scripts/opsx.sh validate <change>` and resolve every change validation issue
- [ ] Verify proposal success criteria against the current proposal text
- [ ] Confirm compile/backtest evidence and result truth are internally consistent
- [ ] Decide whether the change is ready to archive
