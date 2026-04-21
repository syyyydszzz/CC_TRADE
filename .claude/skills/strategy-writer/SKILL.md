---
name: strategy-writer
description: |
  AUTO-INVOKE when the user asks to write, create, build, or implement a trading strategy.
  Triggers on: "write a strategy", "create a momentum strategy", "build an RSI strategy",
  "implement mean reversion", "make a crossover algorithm", or similar requests.
allowed-tools: Read, Write, Glob, Grep, Bash, mcp__*
---

# Strategy Writer

Auto-invokes as the orchestration layer for QuantConnect strategy work in the local `algorithms/` workspace.

## Execution Contract

- `algorithms/{name}/` is the source of truth for strategy code and local notes.
- `openspec/changes/{change}/` is the source of truth for planning artifacts.
- `qc-mcp` is the only execution path for compile, backtest, optimization, and live or paper deployment.
- `LEAN CLI` may be used only to push project files when a QuantConnect project targets `Cloud Platform`.
- Do not use `lp`, local Lean executors, `/Lean/...` paths, `QuantBook`, or local data download helpers.
- If `qc-mcp` is unavailable or the wrong QuantConnect project is open, stop and tell the user.

## Role

This skill is intentionally thin. It should:

- parse the user's strategy intent and identify the target workspace
- coordinate local file updates in `algorithms/{name}/`
- route deeper work to the right capability skill instead of carrying all domain detail itself
- keep the `results/` workspace aligned with the repository contract
- treat strategy work as a phase-routed workflow, not a single undifferentiated build pass

## Skill Stack

When strategy work becomes specific, load these skills in this order:

1. `strategy-design` for entry, exit, sizing, and anti-patterns.
2. `qc-algorithm-core` for `QCAlgorithm` implementation patterns.
3. `qc-execution` for QC sync, `read_open_project`, compile, and backtest gates.
4. `result-workspace` for `results/` read and write rules.
5. `qc-backtest-analysis` after backtest results exist.
6. `qc-optimization` only when parameter search is explicitly needed.
7. `qc-validation` when robustness, out-of-sample evaluation, or closure sufficiency is needed.

## Phase Model

Use this default strategy workflow:

1. Design
2. Implementation
3. QC execution
4. Result persistence
5. Skeptical review
6. Robustness and closure verdict

If the runtime supports subagents or task delegation, prefer different subagents or explicit passes for these phases.
At minimum, the same pass that writes `main.py` should not be the only pass that decides the final continue or complete verdict.

## Project Structure

```text
algorithms/{name}/
├── main.py
├── spec.md
└── results/
    ├── state.yaml
    ├── report.md
    └── artifacts/
        └── runs/
            └── {run_id}/
                ├── run.yaml
                ├── compile.json
                ├── backtest.json
                ├── optimization.json
                ├── validation.json
                └── analysis.md
```

## Workflow

1. Parse the user's strategy requirements and identify the target strategy.
2. Read the relevant OpenSpec change artifacts when the work is already attached to a change.
3. Create or update local files under `algorithms/{name}/`.
4. If `results/` is missing, initialize it with `bash scripts/init-result-workspace.sh --strategy-path algorithms/{name}`.
5. Use `qc-execution` before any compile, backtest, optimization, or validation run.
6. After execution, use:
   - `bash scripts/record-result-run.sh ...`
   - `bash scripts/record-result-state.sh ...`
   - `bash scripts/check-result-workspace.sh --strategy-path algorithms/{name}`
7. Use `bash scripts/extract-qc-backtest-metrics.sh --artifact-path <backtest.json> --json` when a compact summary helps populate result files.
8. Keep workflow layers separate:
   - OpenSpec change artifacts live under `openspec/changes/**`
   - optional runtime loop state lives under `.claude/runtime/opsx-sessions/**`
   - strategy execution evidence lives under `algorithms/{strategy}/results/**`
9. Do not create planning artifacts outside `openspec/changes/{change}/`.
