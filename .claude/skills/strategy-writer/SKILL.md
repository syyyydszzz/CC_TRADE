---
name: strategy-writer
description: |
  AUTO-INVOKE when the user asks to write, create, build, or implement a trading strategy.
  Triggers on: "write a strategy", "create a momentum strategy", "build an RSI strategy",
  "implement mean reversion", "make a crossover algorithm", or similar requests.
allowed-tools: Read, Write, Glob, Grep, Bash, mcp__*
---

# Strategy Writer

**Auto-invokes to create QuantConnect trading strategies in the local `algorithms/` workspace.**

## Execution Contract

- `algorithms/{name}/` is the source of truth for strategy code and local notes.
- `qc-mcp` is the only execution path for compile, backtest, optimization, and live or paper deployment.
- Do not use `lp`, local Lean executors, `/Lean/...` paths, `QuantBook`, or local data download helpers.
- If `qc-mcp` is unavailable or the wrong QuantConnect project is open, stop and tell the user. There is no fallback path.

## Project Structure

Each strategy folder should contain:

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

### 1. Parse Requirements

Parse the user's request for:

- **Strategy type**: momentum, mean-reversion, breakout, trend-following, pairs
- **Asset class**: equity, crypto, forex, futures, options
- **Timeframe**: intraday, daily, weekly
- **Indicators**: specific indicators or signals mentioned
- **Risk parameters**: position size, stops, targets mentioned

### 2. Load Relevant Knowledge

Read all files from `.claude/skills/strategy-writer/knowledge/`.

For each knowledge file:

- Filter entries by tags matching strategy type, asset class, timeframe
- Prioritize high-confidence entries
- Load both patterns to apply and anti-patterns to avoid

### 3. Design Strategy

Based on requirements and knowledge:

- Select the entry signal approach
- Design exit rules
- Define position sizing
- Add explicit risk management

### 4. Create Or Update Local Files

- Create `algorithms/{name}/` if it does not exist.
- Keep `main.py`, `spec.md`, and the `results/` workspace in sync.
- If `results/` is missing, initialize it with `bash .buildforce/scripts/bash/init-result-workspace.sh --strategy-path algorithms/{name}`.
- Use `results/state.yaml` as the authoritative machine-readable result state.
- Use `results/report.md` as the concise current verdict for humans and LLMs.
- Use `results/artifacts/runs/{run_id}/` for raw outputs and longer-form analysis.
- Use `.buildforce/templates/result-*.{yaml,md}` as canonical templates for the result workspace.
- Follow `.buildforce/context/result-workspace-contract.yaml` when it exists.
- Use QuantConnect conventions:
  - `from AlgorithmImports import *`
  - class inherits from `QCAlgorithm`
  - implement `initialize()` and `on_data()`

### 5. Validate QuantConnect Context

Before execution:

- Use `read_open_project` to confirm the currently open QuantConnect project.
- Make sure the open project corresponds to the strategy being edited locally.
- If the project context is wrong, stop and ask the user to correct it before running execution tools.

### 6. Compile Through `qc-mcp`

- Run `create_compile`.
- Read the result with `read_compile`.
- Fix all compile failures and warnings before moving to backtesting.

### 7. Backtest Through `qc-mcp`

- Run `create_backtest`.
- Read the result with `read_backtest`.
- Persist raw outputs under `results/artifacts/runs/{run_id}/`.
- Update `results/state.yaml` with key metrics, decision, next actions, and session refs.
- Refresh `results/report.md` with the latest validated summary.
- Run `bash .buildforce/scripts/bash/check-result-workspace.sh --strategy-path algorithms/{name}` as a self-check after updating the workspace.

### 8. Optimize Only When Needed

- Run `create_optimization` and `read_optimization` only if the user asks for optimization or success criteria require parameter search.
- Persist optimization outputs under the same `results/artifacts/runs/{run_id}/`.
- Record the best parameter set and tradeoffs in `results/state.yaml` and `results/report.md`.

### 9. Sync Workflow Artifacts

- If a BuildForce session is active, reflect important findings in `.buildforce/sessions/{currentSession}/`.
- If an Achieve loop is active, use `qc-mcp` compile and backtest outputs as the evidence for continue or complete decisions.
- Do not copy Achieve runtime authority into the result state. Store only `achieve_session` and `buildforce_session` references under `results/state.yaml`.
- Preferred result read order: `spec.md` -> `results/state.yaml` -> `results/report.md` -> latest `run.yaml` -> raw `*.json` only when needed.
- Preferred helper commands: `init-result-workspace.sh` before the first run, `check-result-workspace.sh` after result updates.
