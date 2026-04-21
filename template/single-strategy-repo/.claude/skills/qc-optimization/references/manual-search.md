# Manual Parameter Search

Use this guide when optimization should remain small, explicit, and explainable.

## Principles

- Start with 1 or 2 parameters.
- Prefer 3 to 6 combinations for an initial pass.
- Use narrow ranges that still make economic sense.
- Avoid expanding the search before the baseline is credible.
- Record the exact parameters passed to the run with `record-result-run.sh --parameters-json ...`.

## Good Search Shapes

- lookback windows around a known default
- take-profit thresholds across a small practical band
- rebalance frequencies across a few discrete choices
- tranche sizes around the current implementation defaults

## Bad Search Shapes

- very wide ranges with no prior reason
- too many parameters at once
- tuning niche thresholds after a weak baseline
- exposing every magic number in `main.py` to search

## Recording

For each optimization pass, keep:

- baseline metric
- optimized metric
- improvement percentage
- best parameter set
- reason to keep optimized params or revert to baseline
