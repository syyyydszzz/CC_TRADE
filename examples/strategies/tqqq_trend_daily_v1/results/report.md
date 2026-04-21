# Result Report — tqqq_trend_daily_v1

## Current Verdict

- **Status:** `passed`
- **Latest run:** `run_20260413_001`
- **Decision:** `continue` — backtest completed cleanly; strategy is viable for further development

## Strategy

**TQQQ Daily Trend Following v1** — Long Only, Dual SMA(200) Filter

| Field        | Value           |
|--------------|-----------------|
| Asset        | TQQQ            |
| Filter       | SPY SMA(200)    |
| Direction    | Long only       |
| Resolution   | Daily           |
| Parameters   | 1 (window = 200)|
| Backtest     | 2018-01-01 → 2024-12-31 |

## Key Metrics

| Metric                    | Value       |
|---------------------------|-------------|
| Net Profit                | **812.3%**  |
| Compounding Annual Return | **37.1%**   |
| Max Drawdown              | **51.8%**   |
| Sharpe Ratio              | **0.806**   |
| Sortino Ratio             | 0.734       |
| Total Orders              | 35          |
| Portfolio Turnover        | **1.35%**   |
| Win Rate                  | 41%         |
| Avg Win / Avg Loss        | 53.7% / -4.1% |
| Profit-Loss Ratio         | 13.03       |
| Expectancy                | 4.777       |
| Total Fees                | $3,380.63   |
| Estimated Capacity        | $180M       |

## Latest Validated Run

- Run ID: `run_20260413_001`
- Open project: `tqqq_trend_daily_v1` (id: 30038329)
- Local strategy path: `algorithms/tqqq_trend_daily_v1/`
- Latest stage: `backtest`
- Backtest ID: `f5070f6c662f9fa6d7822e8dde77dc28`
- Compile ID: `38cb424937f274e1a069d0bf029d7b8f-844c01aee8550f36a2288ad8fad557fa`

## Why

The dual SMA(200) trend filter successfully avoids leveraged TQQQ exposure during the 2022 bear market while remaining long during the 2019, 2020-recovery, and 2023-2024 bull phases. Very low turnover (1.35%) confirms the strategy only trades on genuine trend-state changes.

## Interpretation

The strategy captures TQQQ's powerful bull-market returns while using the SPY 200-day SMA as a broad market regime filter to reduce leveraged exposure during bear markets. With only 35 trades across 7 years (1.35% annualized turnover), it achieves excellent capital efficiency.

The 51.8% max drawdown is expected for a 3x leveraged ETF strategy — this is the cost of capturing 37% annualized returns. The 550-day recovery period is the key risk to monitor.

The asymmetric trade profile (41% win rate, 13x profit-loss ratio) is classic trend-following: many small exits at a loss, few large wins.

## Risk Notes

- Max drawdown of 51.8% — unsuitable without drawdown tolerance
- Drawdown recovery: 550 days — long recovery periods during bear markets
- Probabilistic Sharpe Ratio of 21.7% — limited statistical confidence from 7-year sample
- No walk-forward or out-of-sample validation performed yet

## Artifact References

- State: `results/state.yaml`
- Run summary: `results/artifacts/runs/run_20260413_001/run.yaml`
- Compile artifact: `results/artifacts/runs/run_20260413_001/compile.json`
- Backtest artifact: `results/artifacts/runs/run_20260413_001/backtest.json`

## Next Actions

- Review drawdown profile and consider position sizing (e.g., 80% allocation vs 100%)
- Optional: walk-forward validation via `qc-validation`
- Optional: parameter sensitivity check around window=200
