# Backtest Metrics Guide

## Priority Metrics

### Sharpe Ratio

- `< 0.5`: weak
- `0.5 - 0.7`: marginal
- `0.7 - 1.0`: acceptable baseline
- `1.0 - 1.5`: strong
- `> 3.0`: suspicious until proven otherwise

### Maximum Drawdown

- `< 20%`: strong
- `20% - 30%`: acceptable
- `30% - 40%`: concerning
- `> 40%`: usually too high

### Trade Count

- `< 20`: unreliable
- `20 - 30`: weak evidence
- `30 - 100`: usable
- `100+`: stronger confidence

### Win Rate

- Use with profit factor and average win/loss.
- `> 75%` is often a warning sign, not an automatic success.

### Profit Factor

- `< 1.3`: fragile
- `1.3 - 1.5`: acceptable
- `1.5 - 2.0`: good
- `> 3.0`: verify carefully

## Red Flags

- zero trades
- very few trades with very high Sharpe
- extreme win rate with smooth equity curve
- optimization improvement above roughly 30%
- performance that only works in one obvious regime

## Result-Layer Guidance

When summarizing a run:

- put the key metrics in `results/state.yaml`
- put the current verdict and reason in `results/report.md`
- keep long narrative analysis in `analysis.md`
