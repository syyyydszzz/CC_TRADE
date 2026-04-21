# Research

## Change Spec Context

- Change spec files:
  - `specs/<capability>/spec.md`: <why this delta exists>

## Codebase Context

- Relevant files:
  - `<path>`: <why it matters>

## Existing Behavior

- <current behavior>

## qc-mcp And Result Contract

- Required QC project: `<project>`
- Canonical result status values:
  - `not_run`
  - `passed`
  - `failed`
  - `blocked`
  - `needs_iteration`
- Required gates:
  - `read_open_project`
  - `create_compile`
  - `read_compile`
  - `create_backtest`
  - `read_backtest`
- Required result helpers:
  - `bash scripts/record-result-run.sh ...`
  - `bash scripts/record-result-state.sh ...`
  - `bash scripts/check-result-workspace.sh`

## Open Questions

- <question>

## Blockers

- <blocker>
