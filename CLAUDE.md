# QC MCP Strategy Workspace Guidelines

## Core Contract

- `algorithms/` is the local source of truth for strategy code.
- `qc-mcp` is the only execution path for compile, backtest, optimization, and live or paper deployment.
- `Achieve` and `BuildForce` remain the workflow layer.
- If `qc-mcp` is unavailable, or the wrong QuantConnect project is open, stop and say so. Do not invent a fallback.

## Project Structure

- **algorithms/**: Local QuantConnect strategy folders.
- **.buildforce/**: Spec, research, plan, and session state.
- **.claude/**: Claude Code commands, project settings, skills, and hooks.
- **docs/**: `qc-mcp` integration contract and config templates.

## Required Workflow

### Strategy Changes

1. Edit files locally under `algorithms/{strategy_name}/`.
2. If `results/` is missing, initialize it with `bash .buildforce/scripts/bash/init-result-workspace.sh --strategy-path algorithms/{strategy_name}`.
3. Confirm the QuantConnect context with `read_open_project`.
4. Run `create_compile` after code changes and fix all compile failures and warnings.
5. Run `create_backtest` and `read_backtest` for validation.
6. Run `create_optimization` and `read_optimization` only when the user asks for tuning or the acceptance criteria explicitly require optimization.
7. Write raw outputs under `results/artifacts/runs/{run_id}/`, update `results/state.yaml`, then refresh `results/report.md`. Sync only the important conclusions back into `.buildforce/sessions/...` when needed.
8. Run `bash .buildforce/scripts/bash/check-result-workspace.sh --strategy-path algorithms/{strategy_name}` as a self-check after result updates.

### Workflow Commands

```bash
/achieve:goal
/achieve:list-goals
/achieve:cancel-goal

/buildforce.research
/buildforce.plan
/buildforce.build
/buildforce.complete
```

## QuantConnect MCP Expectations

- QuantConnect documents Claude Code integration through `~/.claude.json` with a `qc-mcp` HTTP server entry.
- In a host-native setup the URL is `http://localhost:3001/`.
- In a devcontainer, the repo may need `http://host.docker.internal:3001/` instead, depending on where Claude Code runs.
- `qc-mcp` operates on the project currently open in QuantConnect Local Platform. Keep the open project aligned with the local strategy you are editing.

See [docs/qc-mcp-integration.md](/Users/suyongyuan/Downloads/lean-playground-main/docs/qc-mcp-integration.md) for the project-specific contract and config examples.

## Strategy Workspace Conventions

- Preferred layout per strategy:
  - `main.py`
  - `spec.md`
  - `results/state.yaml`
  - `results/report.md`
  - `results/artifacts/runs/{run_id}/...`
- Keep strategy intent in `spec.md`.
- Keep authoritative result state in `results/state.yaml`.
- Keep the concise narrative summary in `results/report.md`.
- Keep raw compile, backtest, optimization, and validation artifacts under `results/artifacts/runs/{run_id}/`.
- Keep longer planning or iteration history in `.buildforce/sessions/`.
- Use `.buildforce/templates/result-*.{yaml,md}` as the canonical result workspace templates.
- Use `.buildforce/context/result-workspace-contract.yaml` as the canonical project contract for result persistence.
- Preferred result read order: `spec.md` -> `results/state.yaml` -> `results/report.md` -> latest `run.yaml` -> raw `*.json` only when needed.
- Helper commands:
  - `bash .buildforce/scripts/bash/init-result-workspace.sh --strategy-path algorithms/{strategy_name}`
  - `bash .buildforce/scripts/bash/check-result-workspace.sh --strategy-path algorithms/{strategy_name}`

## What Not To Use

- No `lp` commands.
- No local Lean engine assumptions.
- No `/Lean/...` paths.
- No `QuantBook` notebooks as part of the default workflow.
- No local data download helpers, brokerage wrappers, or Lean CLI shortcuts.

## Research And API References

- Use `context7` for current library or API documentation.
- Use QuantConnect's official MCP and Claude Code documentation when the workflow depends on `qc-mcp` behavior.

## Engineering Standards

- Keep responses concise and evidence-based.
- Prefer transparent, explainable strategies over opaque outputs.
- Validate with real `qc-mcp` execution results, not guesses.
- Never hide missing prerequisites behind mock behavior or fallback logic.
