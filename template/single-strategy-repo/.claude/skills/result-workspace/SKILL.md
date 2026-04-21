---
name: result-workspace
description: |
  AUTO-INVOKE when the task involves reading, initializing, validating, or
  updating the repo-root `results/` workspace for the current single-strategy project.
allowed-tools: Read, Glob, Grep, Bash
---

# Result Workspace

Use this skill for the repository's result-layer contract.

## Responsibilities

- Apply the canonical `results/` structure.
- Follow the preferred read order for humans and LLMs.
- Follow the required write order after execution.
- Expect raw artifacts from an execution phase such as `qc-execution` before generating summaries.
- Use the helper scripts rather than inventing ad hoc layout rules.
- Treat `results/state.yaml` and `results/artifacts/runs/{run_id}/run.yaml` as helper-owned machine-readable files.
- Treat `results/report.md` as human-readable output that the agent may write freely.

## Read Order

1. `spec.md`
2. `results/state.yaml`
3. `results/report.md`
4. latest `run.yaml`
5. raw `*.json` only when needed

## Write Order

1. raw artifacts under `results/artifacts/runs/{run_id}/`
2. `bash scripts/record-result-run.sh ...`
3. `bash scripts/record-result-state.sh ...`
4. `results/report.md`
5. `bash scripts/check-result-workspace.sh`

## Helper Commands

- `bash scripts/init-result-workspace.sh`
- `bash scripts/record-result-run.sh ...`
- `bash scripts/record-result-state.sh ...`
- `bash scripts/check-result-workspace.sh`
- `bash scripts/extract-qc-backtest-metrics.sh --artifact-path <backtest.json> --json`

When a backtest exists, raw compile evidence must also exist and `record-result-run.sh`
must include both `--stage compile` and `--stage backtest`.

## Authority Boundaries

- OpenSpec changes under `openspec/changes/**` own planning artifacts.
- Optional runtime loop state lives under `.claude/runtime/opsx-sessions/**`.
- `results/state.yaml` is only the authoritative result state for the strategy itself.
- This skill persists evidence; it does not own `read_open_project`, compile, or backtest execution.

## Source Of Truth

- `workflow/contracts/result-workspace-contract.yaml`
- `workflow/templates/result-state-template.yaml`
- `workflow/templates/result-report-template.md`
