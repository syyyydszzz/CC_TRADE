---
name: qc-backtest-analysis
description: |
  AUTO-INVOKE when reading backtest results, debugging failed backtests, or
  deciding whether a strategy is credible enough to continue. Use after raw
  backtest artifacts already exist.
allowed-tools: Read, Glob, Grep, Bash
---

# QC Backtest Analysis

Use this skill when the work is about interpreting backtest evidence, not writing the algorithm itself.

## Responsibilities

- Explain key metrics and what they imply.
- Detect obvious failure modes such as zero trades or suspiciously perfect performance.
- Help translate raw backtest output into concise result-state updates.
- Provide a skeptical pass that challenges optimistic interpretations.
- Prefer a different agent or explicit pass from the one that wrote `main.py` when possible.

## Workflow

1. Read `results/state.yaml` and `results/report.md` first when they exist.
2. Read the latest `run.yaml` before drilling into raw JSON.
3. Use `bash scripts/extract-qc-backtest-metrics.sh --artifact-path <backtest.json> --json` when a compact summary is needed.
4. Use `references/metrics-guide.md` for interpretation.
5. Use `references/backtest-errors.md` when the run failed or behaved unexpectedly.
6. State whether the evidence supports `passed`, `needs_iteration`, or further validation.
7. Keep conclusions short enough to fit `results/report.md`.

## Do Not Use This Skill For

- backtest execution orchestration
- writing or refactoring the strategy itself
- phase routing language from older workflows
- legacy project-log layouts or legacy session-state files

## References

- `references/metrics-guide.md`
- `references/backtest-errors.md`
