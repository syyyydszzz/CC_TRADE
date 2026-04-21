---
name: strategy-project
description: |
  AUTO-INVOKE when the user asks to create, build, or evolve the strategy owned by
  the current repo. Treat the repo as a single-strategy project rooted at main.py.
allowed-tools: Read, Write, Glob, Grep, Bash, mcp__*
---

# Strategy Project

Use this skill as the orchestration layer for a single-strategy QuantConnect repo.

## Execution Contract

- `main.py` and `spec.md` at the repo root are the source of truth for the strategy.
- `openspec/changes/{change}/` is the source of truth for planning artifacts.
- Strategy behavior changes attached to an OpenSpec change default to `openspec/changes/{change}/specs/strategy-project/spec.md`.
- `qc-mcp` is the only execution path for compile, backtest, optimization, and validation.
- `LEAN CLI` may be used only to push project files when a QuantConnect project targets `Cloud Platform`.
- Do not use `lp`, local Lean executors, `/Lean/...` paths, `QuantBook`, or local data download helpers.
- If `qc-mcp` is unavailable, stop and direct the user to `bash scripts/check-qc-mcp.sh`.

## Role

This skill is intentionally thin. It should:

- parse the user's strategy intent against the current repo
- coordinate local file updates in `main.py`, `spec.md`, and `results/`
- route deeper work to the right capability skill instead of carrying all domain detail itself
- keep the `results/` workspace aligned with the repository contract
- treat strategy work as a phase-routed workflow, not a single undifferentiated build pass

## Skill Stack

Load these skills in this order when strategy work becomes specific:

1. `strategy-design`
2. `qc-algorithm-core`
3. `qc-execution`
4. `result-workspace`
5. `qc-backtest-analysis`
6. `qc-optimization`
7. `qc-validation`

## Phase Model

Use this default strategy workflow:

1. Design
2. Implementation
3. QC execution
4. Result persistence
5. Skeptical review
6. Optional parameter optimization
7. Robustness and closure verdict

Keep implementation, execution, and closure judgment separated whenever practical.

## Project Structure

```text
main.py
spec.md
results/
  state.yaml
  report.md
  artifacts/
    runs/
      {run_id}/
```

## Workflow

1. Parse the user's strategy requirements for the current repo.
2. Read the relevant OpenSpec change artifacts when the work is already attached to a change.
3. Create or update local files under the repo root.
4. If `results/` is missing, initialize it with `bash scripts/init-result-workspace.sh`.
5. Use `qc-execution` before any compile, backtest, or validation run.
6. After execution, use:
   - raw artifacts under `results/artifacts/runs/{run_id}/`, with `compile.json` before `backtest.json` when backtesting
   - `bash scripts/record-result-run.sh ...`
   - `bash scripts/record-result-state.sh ...`
   - `bash scripts/check-result-workspace.sh`
7. Use `bash scripts/extract-qc-backtest-metrics.sh --artifact-path <backtest.json> --json` when a compact summary helps populate result files.
8. When the baseline is credible and the next uncertainty is parameter sensitivity, use `qc-optimization` before `qc-validation`.
9. Keep workflow layers separate:
   - OpenSpec change artifacts live under `openspec/changes/**`
   - optional runtime loop state lives under `.claude/runtime/opsx-sessions/**`
   - strategy execution evidence lives under `results/**`
10. Do not create planning artifacts outside `openspec/changes/{change}/`.
