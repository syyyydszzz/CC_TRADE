---
name: qc-algorithm-core
description: |
  AUTO-INVOKE when writing or refactoring QuantConnect Python algorithm code:
  QCAlgorithm lifecycle, subscriptions, indicators, scheduling, history, orders,
  and common implementation bugs. Use after the strategy logic is chosen.
allowed-tools: Read, Glob, Grep
---

# QC Algorithm Core

Use this skill when the question is how to express trading logic as valid QuantConnect Python code.

## Responsibilities

- Translate strategy logic into `QCAlgorithm` structure.
- Apply correct patterns for subscriptions, history, indicators, scheduling, and orders.
- Catch common implementation bugs before compile or backtest.
- Avoid custom attribute names that are easy to confuse with `QCAlgorithm` members, such as `self.symbol`; prefer ticker-specific names like `self.spy` or neutral names like `self.primary_symbol`.
- Only use external libraries supported in QuantConnect's cloud environment. Avoid pip-installable packages not available in LEAN. When in doubt, use native LEAN methods.

## Do Not Use This Skill For

- LEAN CLI or cloud push workflows
- research logs or experiment ledgers
- result workspace persistence
- metric interpretation after backtests

## Workflow

1. Read `references/quantconnect-python-core.md` for the base implementation pattern.
2. Read `references/common-errors.md` when debugging readiness, missing data, or order issues.
3. Use `references/examples/` for small, local examples only when a concrete pattern is needed.
4. Keep the output aligned with the local `spec.md` and current `results/` contract.

## References

- `references/quantconnect-python-core.md`
- `references/common-errors.md`
- `references/examples/basic_buy_and_hold.py`
- `references/examples/sma_crossover.py`
- `references/examples/weekly_momentum_rotation.py`
- `references/examples/scheduled_entry_retry.py`
