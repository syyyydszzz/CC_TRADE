# __PROJECT_NAME__ Guidelines

## Core Contract

- `main.py` and `spec.md` are the source of truth for strategy code and intent.
- `openspec/changes/{change}/` is the only planning and workflow artifact authority.
- Each change is expected to keep `proposal.md`, `specs/`, `research.md`, `design.md`, and `tasks.md`.
- `qc-mcp` is the only execution path for compile, backtest, optimization, and validation.
- `results/` is the only execution evidence layer.
- If `qc-mcp` is unavailable or the wrong QuantConnect project is open, stop and say so.

## Primary Workflow

Default command surface:

```text
/opsx.explore
/opsx.propose
/opsx.apply
/opsx.verify
/opsx.archive
```

Optional QC sync helpers:

```text
/qc.sync-status
/qc.sync
```

## Strategy Changes

1. Edit files locally at the repo root.
2. If `results/` is missing, initialize it with `bash scripts/init-result-workspace.sh`.
3. Run `bash scripts/check-qc-mcp.sh`.
4. Sync the QC mirror with `bash scripts/prepare-qc-project.sh`.
5. Confirm the open project with `read_open_project`.
6. Run `create_compile` and resolve every compile failure or warning.
7. Run `create_backtest` and `read_backtest` for validation.
8. Persist results in this order:
   - raw artifacts (`compile.json` before `backtest.json` when backtesting)
   - `bash scripts/record-result-run.sh ...`
   - `bash scripts/record-result-state.sh ...`
   - `results/report.md`
   - `bash scripts/check-result-workspace.sh`
9. Keep planning artifacts only in `openspec/changes/{change}/`.

## Result Conventions

- Keep intent in `spec.md`.
- Keep machine-readable result state in `results/state.yaml`.
- Keep concise human summary in `results/report.md`.
- Keep raw compile, backtest, optimization, and validation artifacts under `results/artifacts/runs/{run_id}/`.
- Never hand-write `results/state.yaml` or `results/artifacts/runs/{run_id}/run.yaml`.
- Result-layer status values are limited to `not_run`, `passed`, `failed`, `blocked`, and `needs_iteration`.

## qc-mcp Placement

- QuantConnect documents Claude Code integration through `~/.claude.json` with a `qc-mcp` HTTP server entry.
- In a host-native setup the URL is usually `http://localhost:3001/`.
- In a devcontainer the repo may need `http://host.docker.internal:3001/` instead.
- This repo includes example configs under `docs/`, but it does not write `~/.claude.json` for you.

## Skill Self-Repair

When executing any skill and the failure is caused by the skill itself (stale path, wrong command, outdated step) rather than environment or user input:

1. Edit the SKILL.md directly to fix the problem. Do not wait for user confirmation.
2. Continue execution using the patched skill.
3. Append one entry to that skill's `knowledge/repairs.yaml` with `source: self-repair`, describing what was wrong and what was fixed.

## Post-Session Learning

After completing any meaningful work (error resolution, successful implementation, discovered pattern):
- The `evolve` skill may silently capture learnings to the relevant skill's `knowledge/` folder.
- After `/opsx.archive`, run `/reflect <change-id>` to trigger a systematic post-iteration reflection.
