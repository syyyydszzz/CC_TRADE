# Optimization Heuristics

## When To Optimize

- The baseline trades enough to be statistically useful.
- The strategy logic is already coherent.
- The next uncertainty is parameter sensitivity, not core design.

## When To Skip

- Compile or runtime issues still dominate.
- The baseline has very few trades.
- The strategy is still changing structurally.

## Improvement Heuristics

- `< 5%`: usually too small to matter
- `5% - 30%`: potentially useful if the parameter region is stable
- `> 30%`: often suspicious and should be treated as overfitting risk

## Stability Questions

- Does the result stay strong in neighboring parameter values?
- Did drawdown or trade count worsen materially?
- Is the "best" setting too narrow to trust?
