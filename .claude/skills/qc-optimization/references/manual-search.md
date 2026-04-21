# Manual Parameter Search

Use this guide when optimization should remain small, explicit, and explainable.

## Principles

- Start with 1 or 2 parameters.
- Prefer 3 to 6 combinations for an initial pass.
- Use reasonable ranges that still make economic sense.
- Avoid expanding the search before the baseline is credible.

## Good Search Shapes

- indicator period around a known default
- stop-loss width across a small practical range
- rebalance frequency across a few discrete choices

## Bad Search Shapes

- very wide ranges with no prior reason
- too many parameters at once
- tuning niche thresholds after a weak baseline

## Recording

For each optimization pass, keep:

- baseline metric
- optimized metric
- improvement percentage
- best parameter set
- reason to keep optimized params or revert to baseline
