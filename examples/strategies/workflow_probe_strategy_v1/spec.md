# Workflow Probe Strategy V1 — Spec

## Purpose

This strategy exists solely to **validate the full pipeline**:

> Claude Code → skill invocation → OpenSpec → qc-mcp compile/backtest → result workspace persistence → validation gates

It is **not** designed for alpha generation or live deployment.

## Strategy Logic

| Parameter     | Value                          |
|---------------|-------------------------------|
| Asset         | SPY (daily)                    |
| Entry         | SMA(20) crosses above SMA(50) |
| Exit          | SMA(20) crosses below SMA(50) |
| Sizing        | 100% long on entry, liquidate on exit |
| Warm-up       | 50 bars                        |
| Backtest      | 2020-01-01 → 2022-12-31        |
| Starting cash | $100,000                       |

## Design Decisions

- **SPY** was chosen because daily data is always available in any QC workspace.
- **SMA crossover** was chosen because it is simple, has no edge-case data requirements,
  and compiles reliably without needing special data subscriptions.
- **100% sizing** was chosen for probe clarity — no partial fill or rounding edge cases.
- **No profit target is set.** Any completed backtest (positive or negative return) satisfies
  the pipeline validation criterion.

## Acceptance Criteria

The strategy is considered **validated** when:

1. `create_compile` returns success (zero errors).
2. `create_backtest` completes without runtime error.
3. `results/artifacts/runs/{run_id}/` contains `compile.json` and `backtest.json`.
4. `record-result-run.sh` generates `run.yaml` without error.
5. `record-result-state.sh` generates `results/state.yaml` without error.
6. `check-result-workspace.sh` exits 0.
7. Result workspace checks and change verification pass.

## Out of Scope

- Optimization or parameter search
- Live or paper deployment
- Risk management beyond the simple crossover exit
- Modifications to any other strategy directory
