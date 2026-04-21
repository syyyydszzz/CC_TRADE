# AGENTS.md

## Workflow

- Use OpenSpec as the only planning and change-artifact authority.
- Start by running `bash scripts/bootstrap-python-env.sh --with-openspec` when `./node_modules/.bin/openspec` or `./.tools/node/current/bin/node` is missing.
- Run `bash scripts/check-qc-mcp.sh` before any compile or backtest attempt.
- Primary Claude Code commands are `/opsx.explore`, `/opsx.propose`, `/opsx.apply`, `/opsx.verify`, and `/opsx.archive`.

## Repo Contract

- `main.py` and `spec.md` are the source of truth for strategy code and intent.
- `qc-mcp` is the only execution path for compile, backtest, optimization, and validation.
- `results/` is the source of truth for execution evidence.
- `openspec/changes/{change}/` is the source of truth for change planning artifacts.
- Active changes are expected to keep `proposal.md`, `specs/`, `research.md`, `design.md`, and `tasks.md`.

## Result Helpers

- `bash scripts/init-result-workspace.sh`
- `bash scripts/record-result-run.sh ...`
- `bash scripts/record-result-state.sh ...`
- `bash scripts/check-result-workspace.sh`
- `bash scripts/extract-qc-backtest-metrics.sh --artifact-path <backtest.json> --json`
- `bash scripts/prepare-qc-project.sh`
- `bash scripts/check-qc-sync.sh`
- `bash scripts/sync-qc-project.sh`

## Execution Rules

- Always confirm the open QuantConnect project with `read_open_project` before compile or backtest.
- Never hand-write `results/state.yaml` or `results/artifacts/runs/{run_id}/run.yaml`.
- Persist results in this order: raw artifacts, `record-result-run`, `record-result-state`, `results/report.md`, workspace check.
- When a backtest exists, persist `compile.json` before `backtest.json` and include both `--stage compile` and `--stage backtest` in `record-result-run`.
- Do not write planning artifacts outside `openspec/changes/`.
