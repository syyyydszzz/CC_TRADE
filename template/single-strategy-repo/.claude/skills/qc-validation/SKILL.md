---
name: qc-validation
description: |
  AUTO-INVOKE when the work is about out-of-sample checks, robustness, regime
  sensitivity, or deciding whether a backtest result is stable enough to trust
  and close out.
allowed-tools: Read, Glob, Grep
---

# QC Validation

Use this skill when the next question is robustness rather than raw backtest quality.

## Responsibilities

- Design sensible in-sample and out-of-sample comparisons.
- Interpret degradation and robustness rather than just headline returns.
- Decide whether the evidence supports continue, reject, or another iteration.
- Prefer an independent review pass from the implementation and execution phases when possible.

## Workflow

1. Start from the latest validated baseline or optimized run.
2. Read `references/robustness-guide.md`.
3. Compare in-sample and out-of-sample behavior across multiple metrics.
4. Record the verdict in result-state language, not old phase language.
5. Be explicit whether the evidence is only enough to continue iterating or enough to close the workflow.

## Do Not Use This Skill For

- `qc_validate.py`
- deployment routing
- old "Phase 5" assumptions
- rewriting `main.py` or owning compile/backtest execution

## References

- `references/robustness-guide.md`
