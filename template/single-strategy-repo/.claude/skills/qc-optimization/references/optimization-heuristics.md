# Optimization Heuristics

## When To Optimize

- The baseline trades enough to be statistically useful.
- The strategy logic is already coherent.
- The next uncertainty is parameter sensitivity, not core design.
- The expected search can be explained in plain trading terms.

## When To Skip

- Compile or runtime issues still dominate.
- The baseline has very few trades.
- The strategy is still changing structurally.
- The likely improvement would come from adding new logic, not tuning current defaults.

## Improvement Heuristics

- `< 5%`: usually too small to matter
- `5% - 30%`: potentially useful if the parameter region is stable
- `> 30%`: often suspicious and should be treated as overfitting risk

## Stability Questions

- Does the result stay strong in neighboring parameter values?
- Did drawdown or trade count worsen materially?
- Is the "best" setting too narrow to trust?
- Does the optimized result still make sense in light of the strategy thesis?
