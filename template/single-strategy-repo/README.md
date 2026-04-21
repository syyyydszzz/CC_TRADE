# __PROJECT_NAME__

> Single-strategy QuantConnect repository: `main.py` and `spec.md` are the source of truth, `qc-mcp` is the only execution path, and `results/` is the only evidence layer.

## Core Contract

- `main.py` and `spec.md` at the repo root are the source of truth.
- `openspec/changes/{change}/` is the only planning and workflow artifact authority.
- `qc-mcp` is the only execution path for compile, backtest, optimization, and validation.
- `results/` is the only execution evidence layer.
- Each active change should contain `proposal.md`, `specs/`, `research.md`, `design.md`, and `tasks.md`.

## Bootstrap

```bash
bash scripts/bootstrap-python-env.sh --with-openspec
bash scripts/check-qc-mcp.sh
bash scripts/opsx.sh list --specs
```

Bootstrap behavior:

- prepares `.venv`
- installs or refreshes repo-local Node.js under `.tools/node/current` for OpenSpec
- installs the pinned `@fission-ai/openspec` package
- validates user-scoped `qc-mcp` registration separately

## Primary Workflow

Default Claude workflow:

- `/opsx.explore`
- `/opsx.propose`
- `/opsx.apply`
- `/opsx.verify`
- `/opsx.archive`

Optional QC sync helpers:

- `/qc.sync-status`
- `/qc.sync`

## Result Workspace

Canonical result-layer assets:

- `results/state.yaml`
- `results/report.md`
- `results/artifacts/runs/{run_id}/`

Preferred write order:

1. raw artifacts (`compile.json` before `backtest.json` when backtesting)
2. `bash scripts/record-result-run.sh ...`
3. `bash scripts/record-result-state.sh ...`
4. `results/report.md`
5. `bash scripts/check-result-workspace.sh`

## qc-mcp

This repo does not own `qc-mcp` server registration.
Keep `qc-mcp` in `~/.claude.json`, then use:

```bash
bash scripts/check-qc-mcp.sh
```

Reference examples:

- `docs/qc-mcp-claude-config.example.json`
- `docs/qc-mcp-claude-config.devcontainer.example.json`
