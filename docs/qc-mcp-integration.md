# qc-mcp Integration Contract

This repository keeps strategy source code local and delegates execution to QuantConnect's official MCP server.

## Source And Execution Boundary

- Local source of truth: `algorithms/`
- Workflow layer: `Achieve` and `BuildForce`
- Execution layer: `qc-mcp`
- No fallback: there is no local Lean, `lp`, QuantBook, or secondary execution adapter

## Repository Contract

1. Edit strategy files locally in `algorithms/{name}/`.
2. If `results/` is missing, initialize it with `bash .buildforce/scripts/bash/init-result-workspace.sh --strategy-path algorithms/{name}`.
3. Make sure the matching project is open in QuantConnect Local Platform.
4. Confirm context with `read_open_project`.
5. Run `create_compile` and fix issues reported by `read_compile`.
6. Run `create_backtest` and inspect the results with `read_backtest`.
7. Run `create_optimization` only when parameter search is required.
8. Write raw results into `results/artifacts/runs/{run_id}/`, update `results/state.yaml`, then refresh `results/report.md`. Copy only the important conclusions into `.buildforce/sessions/...` when needed.
9. Run `bash .buildforce/scripts/bash/check-result-workspace.sh --strategy-path algorithms/{name}` as a self-check.

## Result Workspace Contract

Each local strategy should keep results in a dedicated workspace:

```text
algorithms/{name}/
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

- `results/state.yaml`: authoritative machine-readable result state
- `results/report.md`: concise human and LLM-facing result summary
- `results/artifacts/runs/{run_id}/`: archived raw outputs and detailed analysis
- `.buildforce/templates/result-*.{yaml,md}`: canonical result workspace templates
- `.buildforce/context/result-workspace-contract.yaml`: canonical project contract for the result layer
- `bash .buildforce/scripts/bash/init-result-workspace.sh --strategy-path algorithms/{name}`: initialize the local result workspace
- `bash .buildforce/scripts/bash/check-result-workspace.sh --strategy-path algorithms/{name}`: validate the local result workspace contract

Preferred read order:

1. `spec.md`
2. `results/state.yaml`
3. `results/report.md`
4. latest `run.yaml`
5. raw `*.json` only when needed

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

If Claude Code runs on the host machine next to QuantConnect Local Platform, use [qc-mcp-claude-config.example.json](/Users/suyongyuan/Downloads/lean-playground-main/docs/qc-mcp-claude-config.example.json).

## Devcontainer Claude Code

If Claude Code runs inside the devcontainer while QuantConnect Local Platform runs on the host, use [qc-mcp-claude-config.devcontainer.example.json](/Users/suyongyuan/Downloads/lean-playground-main/docs/qc-mcp-claude-config.devcontainer.example.json).

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

## Why `.mcp.json` Does Not Own `qc-mcp`

This repository keeps `qc-mcp` as a user-scoped Claude Code integration because QuantConnect documents it as a `~/.claude.json` server entry tied to the user's Local Platform session. Project-local `.mcp.json` remains available for shared tools like `context7`, but it is not the canonical place for QuantConnect connectivity.
