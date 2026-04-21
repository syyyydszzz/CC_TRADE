---
name: qc-optimization
description: |
  AUTO-INVOKE when a strategy already has a credible baseline backtest and the
  next question is whether to tune a small set of parameters without breaking
  the repo's qc-mcp and results/ contract.
allowed-tools: Read, Glob, Grep, Bash
---

# QC Optimization

Use this skill when the work is about parameter search and parameter sensitivity,
not inventing a new strategy structure.

## Responsibilities

- Decide whether optimization is warranted or still premature.
- Choose a small, explainable parameter surface.
- Make optimizable parameters explicit in repo-root `main.py`.
- Keep the search compatible with `qc-mcp` execution and the `results/` workspace.
- Judge whether optimized parameters are meaningful enough to keep or only strong enough to motivate validation.

## Workflow

1. Read `spec.md`, `results/state.yaml`, `results/report.md`, and the latest `run.yaml` before proposing a search.
2. Require a credible baseline compile + backtest first; use `qc-backtest-analysis` if the baseline is still ambiguous.
3. Read:
   - `references/manual-search.md`
   - `references/optimization-heuristics.md`
   - `references/parameter-exposure.md`
4. Prefer 1 or 2 parameters and small neighboring ranges around the current defaults.
5. Keep the repo-root strategy readable:
   - leave defaults explicit in code
   - expose only intended search parameters through `self.get_parameter(...)` helpers when native QC optimization is required
   - mirror chosen defaults and parameter names in `spec.md`
6. Hand off execution to `qc-execution` for:
   - `bash scripts/check-qc-mcp.sh`
   - `bash scripts/prepare-qc-project.sh`
   - `read_open_project`
   - `create_compile` when optimization-related code changed
   - `create_optimization` and `read_optimization`
7. Hand off persistence to `result-workspace`:
   - write raw `optimization.json` under `results/artifacts/runs/{run_id}/`
   - run `bash scripts/record-result-run.sh ... --stage compile --stage optimization`
   - run `bash scripts/record-result-state.sh ... --latest-stage optimization`
   - refresh `results/report.md`
   - run `bash scripts/check-result-workspace.sh`
8. Use `qc-validation` after optimization when the next question is out-of-sample robustness rather than parameter selection.

## Do Not Use This Skill For

- inventing a new entry or exit model instead of tuning an existing one
- legacy `iteration_state.json`, hypothesis directories, or `PROJECT_LOGS/`
- broad 3+ dimensional search spaces by default
- hardcoding a QC project id or bypassing `read_open_project`
- hand-writing `results/state.yaml` or `run.yaml`

## References

- `references/manual-search.md`
- `references/optimization-heuristics.md`
- `references/parameter-exposure.md`
