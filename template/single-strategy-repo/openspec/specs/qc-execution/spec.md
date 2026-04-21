# qc-execution

## Purpose

Describe the repository-wide execution contract for compile, backtest, optimization,
and validation through `qc-mcp`.

## Requirements

### Requirement: qc-mcp is the only execution path

The repository SHALL use `qc-mcp` as the only execution path for compile,
backtest, optimization, and validation gates.

#### Scenario: Compile gate runs

- **WHEN** a strategy change reaches QC execution
- **THEN** the agent runs `bash scripts/check-qc-mcp.sh` and uses `qc-mcp` tools rather than a local Lean executor

### Requirement: Active QC project must match the repo

The repository SHALL confirm the currently open QuantConnect project before any
compile or backtest request.

#### Scenario: Wrong project is open

- **WHEN** `read_open_project` reports a project that does not match the repo
- **THEN** execution stops and the mismatch is reported as a blocker

### Requirement: Compile evidence is persisted before backtest evidence

The repository SHALL read compile results and persist `compile.json` before a
backtest run is recorded.

#### Scenario: Backtest is executed

- **WHEN** a compile succeeds and a backtest is started
- **THEN** the run directory contains `compile.json` and `backtest.json` before `run.yaml` or `results/state.yaml` is generated
