---
name: qc-optimization
description: |
  AUTO-INVOKE when the user asks for parameter tuning or when a strategy has a
  credible baseline and the next question is whether parameter search is worth it.
  Use for search design and interpretation, not for command-level orchestration.
allowed-tools: Read, Glob, Grep
---

# QC Optimization

Use this skill when the problem is how to search parameters without turning the result into curve fit noise.

## Responsibilities

- Decide whether optimization is warranted.
- Keep parameter searches narrow, interpretable, and defensible.
- Judge whether optimization improvement is meaningful or suspicious.

## Workflow

1. Start from a real baseline backtest result, not a theoretical idea.
2. Read `references/manual-search.md` for grid sizing guidance.
3. Read `references/optimization-heuristics.md` for interpretation rules.
4. Prefer small, explicit parameter grids before broader search.
5. Record both the best result and the tradeoffs in `results/state.yaml` and `results/report.md`.

## Do Not Use This Skill For

- `qc_optimize.py`
- legacy session-state files from older workflows
- paid-tier API assumptions
- automatic routing decisions copied from older workflows

## References

- `references/manual-search.md`
- `references/optimization-heuristics.md`
