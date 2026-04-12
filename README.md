# QC MCP Strategy Workspace

> Claude Code workflow layer for QuantConnect strategy development: local source in `algorithms/`, orchestration through Achieve + BuildForce, execution only through `qc-mcp`.

## Architecture

- `algorithms/` is the source-of-truth workspace for strategy code and local docs.
- `Achieve` provides the goal loop and stop-hook driven continuation.
- `BuildForce` provides spec, research, and plan artifacts under `.buildforce/`.
- `qc-mcp` is the only execution layer for compile, backtest, optimization, and live or paper deployment.

This repository no longer ships `lp`, a local Lean runtime, QuantBook notebooks, data download helpers, or any fallback execution path.

## What Stays

- Claude Code project configuration in `.claude/`
- `/achieve:*` plugin workflow
- `/buildforce.*` command workflow
- `.buildforce/` session and artifact structure
- Local strategy projects under `algorithms/`

## What Changed

- All compile, backtest, optimization, and live validation must go through `qc-mcp`.
- Local file edits still happen in this repository.
- Verification now means: edit locally, run `qc-mcp`, then write conclusions back into local docs or BuildForce artifacts.
- If `qc-mcp` is unavailable, the workflow stops. There is no local fallback.

## Getting Started

### 1. Connect Claude Code to `qc-mcp`

QuantConnect's official Claude Code setup uses `~/.claude.json` with:

```json
{
  "mcpServers": {
    "qc-mcp": {
      "type": "http",
      "url": "http://localhost:3001/"
    }
  }
}
```

Use the project examples in [docs/qc-mcp-integration.md](/Users/suyongyuan/Downloads/lean-playground-main/docs/qc-mcp-integration.md):

- [docs/qc-mcp-claude-config.example.json](/Users/suyongyuan/Downloads/lean-playground-main/docs/qc-mcp-claude-config.example.json) for host-native Claude Code
- [docs/qc-mcp-claude-config.devcontainer.example.json](/Users/suyongyuan/Downloads/lean-playground-main/docs/qc-mcp-claude-config.devcontainer.example.json) for Claude Code running inside the devcontainer

### 2. Open the matching QuantConnect project

`qc-mcp` operates on the project currently open in QuantConnect Local Platform. Before asking Claude to compile or backtest, make sure the open project is the one that matches the local strategy you are editing.

### 3. Work locally in `algorithms/`

Create or update a strategy folder such as:

```text
algorithms/my_strategy/
  main.py
  spec.md
  results/
    state.yaml
    report.md
    artifacts/
      runs/
        {run_id}/
          run.yaml
          compile.json
          backtest.json
```

The repository keeps the editable source locally. `qc-mcp` is only used to execute and read results.

Before the first compile or backtest for a strategy workspace, initialize the result layer with:

```bash
bash .buildforce/scripts/bash/init-result-workspace.sh --strategy-path algorithms/{name}
```

## Recommended Workflow

1. Create or refine a strategy in `algorithms/{name}/main.py`.
2. Initialize the strategy result workspace if `results/` does not exist yet.
3. Use `/achieve:goal` for goal-driven iteration, or `/buildforce.plan` and `/buildforce.build` for artifact-driven execution.
4. Ask Claude to confirm the QuantConnect context with `read_open_project`.
5. Run `create_compile` and resolve every compile error or warning.
6. Run `create_backtest` and `read_backtest` to evaluate the strategy.
7. If the goal requires tuning, run `create_optimization` and `read_optimization`.
8. Persist raw execution outputs under `results/artifacts/runs/{run_id}/`, update `results/state.yaml`, then refresh `results/report.md`.
9. Run `bash .buildforce/scripts/bash/check-result-workspace.sh --strategy-path algorithms/{name}` as a contract self-check.

## Result Workspace Contract

- `results/state.yaml` is the authoritative machine-readable result state for the strategy.
- `results/report.md` is the concise human and LLM-facing summary of the current verdict.
- `results/artifacts/runs/{run_id}/` stores raw `qc-mcp` outputs, `run.yaml`, and any longer-form analysis.
- Canonical result workspace templates live under `.buildforce/templates/`.
- Canonical project-level guidance for this contract lives under `.buildforce/context/result-workspace-contract.yaml`.
- Preferred read order: `spec.md` -> `results/state.yaml` -> `results/report.md` -> latest `run.yaml` -> raw `*.json` only when needed.
- Preferred write order: raw artifacts first, then `results/state.yaml`, then `results/report.md`.
- Helper commands:
  - `bash .buildforce/scripts/bash/init-result-workspace.sh --strategy-path algorithms/{name}`
  - `bash .buildforce/scripts/bash/check-result-workspace.sh --strategy-path algorithms/{name}`

## Repository Layout

```text
.buildforce/                      # BuildForce workflow state, templates, and sessions
.claude/                          # Claude Code commands, skills, and project settings
algorithms/                       # Local strategy source-of-truth
docs/                             # qc-mcp contract and config templates
```

## Notes

- `.mcp.json` remains reserved for project-local shared MCP servers such as `context7`.
- The official `qc-mcp` connection is user-scoped and documented by QuantConnect for `~/.claude.json`.
- The sample strategy source remains in [algorithms/sample_sma_crossover/main.py](/Users/suyongyuan/Downloads/lean-playground-main/algorithms/sample_sma_crossover/main.py).
