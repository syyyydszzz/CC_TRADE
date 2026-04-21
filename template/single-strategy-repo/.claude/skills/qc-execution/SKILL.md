---
name: qc-execution
description: |
  AUTO-INVOKE when preparing QuantConnect execution context or running qc-mcp
  gates such as read_open_project, compile, backtest, optimization, or
  validation. Use after strategy logic and local code are ready, and before
  result persistence or backtest interpretation.
allowed-tools: Read, Glob, Grep, Bash, mcp__*
---

# QC Execution

Use this skill for the execution phase only.

## Responsibilities

- Prepare the QC mirror from the repo source of truth.
- Block immediately when `qc-mcp` is not configured and point to `bash scripts/check-qc-mcp.sh`.
- Verify the currently open QuantConnect project before any execution.
- Run qc-mcp compile, backtest, optimization, or validation gates.
- Stop quickly on wrong-project, sync, or runtime blockers.
- Persist raw execution artifacts so downstream result skills can take over.

## Phase Boundary

Inputs:

- local `main.py`
- local `spec.md`
- an agreed strategy design already chosen

Outputs:

- verified QC project context
- raw `compile.json`, `backtest.json`, `optimization.json`, or `validation.json`
- factual execution status only

This skill must not:

- redesign the strategy
- rewrite `QCAlgorithm` logic as its main job
- hand-author `results/state.yaml` or `run.yaml`
- give the final "strategy is good enough" verdict by itself

## Workflow

1. Run `bash scripts/check-qc-mcp.sh` first and stop immediately if `qc-mcp` is not registered for Claude.
2. Run `bash scripts/prepare-qc-project.sh ...` to sync repo code into the QC project mirror.
3. Call `read_open_project` and stop immediately if the open project is not the target strategy.
4. Run `create_compile` and `read_compile` before any backtest.
5. If compile passes, run `create_backtest` and `read_backtest`.
6. Before optimization, confirm the intended search parameters are exposed in repo-root `main.py` and that compile evidence is current.
7. Run optimization or validation tools only when the user or the plan explicitly requires them.
8. Write raw `compile.json`, `backtest.json`, `optimization.json`, or `validation.json` under `results/artifacts/runs/{run_id}/` for downstream persistence.
9. Hand off to `result-workspace` for machine-readable persistence and to analysis skills for interpretation.

## Handoff Rules

- `result-workspace` owns `record-result-run.sh`, `record-result-state.sh`, and `check-result-workspace.sh`.
- `qc-backtest-analysis` owns skeptical interpretation of run quality.
- `qc-optimization` owns parameter selection, search size, and whether optimized params are trustworthy.
- `qc-validation` owns robustness and closure recommendations.

## Do Not Use This Skill For

- entry or exit design
- indicator selection heuristics
- post-backtest storytelling in `results/report.md`
- runtime-loop completion decisions without downstream review
