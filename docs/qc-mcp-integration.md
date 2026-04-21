# qc-mcp Integration Contract

This repository keeps single-strategy source code local and delegates execution to QuantConnect's official MCP server.

## Source And Execution Boundary

- Local source of truth: repo-root `main.py` and `spec.md`
- Workflow layer: `OpenSpec`
- Execution layer: `qc-mcp`
- `LEAN CLI` may be used only for official project synchronization to Cloud Platform targets, such as `lean cloud push`
- No fallback: there is no local Lean engine execution, `lp`, QuantBook, or secondary execution adapter

## Repository Contract

1. Edit strategy files locally at the repo root.
2. If `results/` is missing, initialize it with `bash scripts/init-result-workspace.sh`.
3. Run `bash scripts/check-qc-mcp.sh`. If it fails, stop and fix `~/.claude.json` first.
4. Prepare the QuantConnect execution source with `bash scripts/prepare-qc-project.sh`. Pass `--qc-workspace <qc-workspace-root>` when auto-detection is unavailable or ambiguous.
5. `prepare-qc-project.sh` syncs repo `main.py` to the QC workspace and, when `deployment-target` is `Cloud Platform`, runs `lean cloud push` so `qc-mcp` executes the latest uploaded cloud code.
6. Make sure the matching project is open in QuantConnect Local Platform.
7. Confirm context with `read_open_project`.
8. Run `create_compile` and fix **all** issues and warnings reported by `read_compile` before proceeding.
9. Run `create_backtest` and inspect the results with `read_backtest`.
10. Write raw results into `results/artifacts/runs/{run_id}/`. When a backtest runs, persist both `compile.json` and `backtest.json`, then generate `run.yaml` and `results/state.yaml` through the helper scripts, then refresh `results/report.md`.
11. Run `bash scripts/check-result-workspace.sh` as a self-check.

## Strategy Skill Stack

- `strategy-project`: entry orchestrator for the current repo's strategy
- `strategy-design`: strategy logic, entry, exit, sizing, and anti-patterns
- `qc-algorithm-core`: `QCAlgorithm` implementation guidance
- `result-workspace`: result-layer contract and helper scripts
- `qc-backtest-analysis`: result interpretation and failure analysis
- `qc-validation`: robustness and out-of-sample interpretation

## Result Workspace Contract

The repo keeps results in a dedicated workspace:

```text
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
        optimization.json
        validation.json
        analysis.md
```

- `results/state.yaml`: authoritative machine-readable result state using only `not_run`, `passed`, `failed`, `blocked`, or `needs_iteration`
- `results/report.md`: concise human and LLM-facing result summary
- `results/artifacts/runs/{run_id}/`: archived raw outputs and detailed analysis
- `workflow/templates/result-*.{yaml,md}`: canonical result workspace templates
- `workflow/contracts/result-workspace-contract.yaml`: canonical project contract for the result layer
- `bash scripts/init-result-workspace.sh`: initialize the local result workspace
- `bash scripts/check-result-workspace.sh`: validate the local result workspace contract
- `bash scripts/extract-qc-backtest-metrics.sh --artifact-path <backtest.json> --json`: summarize raw backtest artifacts for result updates
- `bash scripts/prepare-qc-project.sh [--qc-workspace <qc-workspace-root>]`: sync repo `main.py` into the QC workspace and push the QC project to the cloud when the project targets `Cloud Platform`
- `bash scripts/sync-qc-project.sh [--qc-workspace <qc-workspace-root>]`: sync repo `main.py` to or from a separate QuantConnect workspace project
- `sync-qc-project.sh` only copies files on disk. It does not update a Cloud Platform project's remote code by itself.

Preferred read order:

1. `spec.md`
2. `results/state.yaml`
3. `results/report.md`
4. latest `run.yaml`
5. raw `*.json` only when needed

Preferred write order:

1. raw artifacts (`compile.json` before `backtest.json` when backtesting)
2. `bash scripts/record-result-run.sh ...`
3. `bash scripts/record-result-state.sh ...`
4. `results/report.md`
5. `bash scripts/check-result-workspace.sh`

## Official Claude Code Configuration

QuantConnect documents Claude Code setup through `~/.claude.json` with:

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


Official references:

- QuantConnect Claude Code setup: https://www.quantconnect.com/docs/v2/ai-assistance/mcp-server/claude-code
- QuantConnect MCP key concepts and tool list: https://www.quantconnect.com/docs/v2/ai-assistance/mcp-server/key-concepts

## Host-Native Claude Code

If Claude Code runs on the host machine next to QuantConnect Local Platform, use [qc-mcp-claude-config.example.json](qc-mcp-claude-config.example.json).

## Devcontainer Claude Code

If Claude Code runs inside the devcontainer while QuantConnect Local Platform runs on the host, use [qc-mcp-claude-config.devcontainer.example.json](qc-mcp-claude-config.devcontainer.example.json).

That example switches the endpoint to `http://host.docker.internal:3001/`.

Notes:

- On macOS and Windows, `host.docker.internal` usually works out of the box.
- On Linux, you may need to add `--add-host=host.docker.internal:host-gateway` to the container runtime.
- The repository does not auto-install or proxy `qc-mcp`; it assumes you are following QuantConnect's official Local Platform setup.

## Tool Expectations

The core `qc-mcp` tools used by this repository are:

- `read_open_project`
- `create_compile`
- `create_backtest`
- `read_backtest`
- `create_optimization`
- `read_optimization`
- `create_live_algorithm`
- `read_live_algorithm`

Do not call `list_backtests` unless absolutely necessary — it fetches all historical backtests and is expensive. Use `read_open_project` to confirm the active project and `results/state.yaml` to find the latest run.

## Indicator Naming Convention

When creating indicator objects, never overwrite built-in indicator method names. Use a different variable name, preferably with a leading underscore:

```python
# Wrong — overwrites the built-in self.rsi method
self.rsi = self.rsi(self._symbol, 14)

# Correct
self._rsi = self.rsi(self._symbol, 14)
```

This prevents conflicts with `QCAlgorithm` built-in methods and ensures code reliability.

## Why `.mcp.json` Does Not Own `qc-mcp`

This repository keeps `qc-mcp` as a user-scoped Claude Code integration because QuantConnect documents it as a `~/.claude.json` server entry tied to the user's Local Platform session. Project-local `.mcp.json` remains available for shared tools like `context7`, but it is not the canonical place for QuantConnect connectivity.
