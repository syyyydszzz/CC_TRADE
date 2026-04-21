# Result Workspace

## Purpose

Define the canonical local persistence layer for execution evidence under the
repo-root `results/` directory.

## Requirements

### Requirement: Result state uses canonical statuses

The result workspace SHALL persist only these status values in `results/state.yaml`
and `results/artifacts/runs/{run_id}/run.yaml`: `not_run`, `passed`, `failed`,
`blocked`, and `needs_iteration`.

#### Scenario: Result state is recorded

- **WHEN** `bash scripts/record-result-state.sh ...` updates `results/state.yaml`
- **THEN** the persisted status uses only the canonical result-layer vocabulary

### Requirement: Compile and backtest evidence stay internally consistent

The result workspace SHALL keep `results/state.yaml` synchronized with the
latest `run.yaml`, including compile and backtest sections.

#### Scenario: Latest run is a backtest

- **WHEN** `results/state.yaml.latest_stage` is `backtest`
- **THEN** `latest_compile` and `latest_backtest` match the latest `run.yaml` and neither executed stage is `not_run`

### Requirement: Later stages require compile evidence

The result workspace SHALL reject or fail validation for any backtest,
optimization, or validation record that does not include executed compile
evidence in the same run.

#### Scenario: A backtest run is recorded

- **WHEN** `run.yaml.backtest.status` is not `not_run`
- **THEN** `run.yaml.compile.status` is not `not_run` and `run.yaml.compile.artifact` points to `compile.json`

### Requirement: Result write order is fixed

The repository SHALL write execution evidence in this order: raw artifacts,
`run.yaml`, `results/state.yaml`, `results/report.md`, workspace self-check.

#### Scenario: Backtest results are persisted

- **WHEN** execution completes
- **THEN** raw artifacts are written before helper-owned summaries and the workspace check runs last
