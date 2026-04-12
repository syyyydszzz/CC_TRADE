---
experiment_id: e001
linked_hypothesis_id: h001
date_run: 2026-03-30
code_version: abc1234
project: qc/spxw_1dte_baseline
algo_name: Spxw1dteBaseline
backtest_start: 2024-01-01
backtest_end: 2024-12-31
resolution: minute
tickers:
  - SPX
  - SPXW
hypothesis: >
  Entering closer to the close improves 1DTE iron condor credit without materially
  worsening loss frequency.
backtest_id: "<qc-backtest-id>"
results_url: "<quantconnect-results-url>"
parameters_changed:
  entry_time_et: "15:55"
quantconnect_results:
  total_orders: ""
  average_win: ""
  average_loss: ""
  compounding_annual_return: ""
  drawdown: ""
  expectancy: ""
  net_profit: ""
  profit_loss_ratio: ""
  sharpe_ratio: ""
  sortino_ratio: ""
  win_rate: ""
summary: >
  One or two sentences on what happened and whether it supports the hypothesis.
decision: Proceed
next_hypothesis: ""
tags:
  - entry-timing
  - 1dte
---

## Change Tested

Describe the code, parameter, or rules change made for this run. This should correspond to
the committed code identified by `code_version`.

## Method

Describe how the test was run and any assumptions that matter.

## Interpretation

Explain what the results mean, not just what the metrics were.

## Artifacts And Caveats

- Suspicious artifacts:
- Data issues:
- Execution anomalies:

## Next Step

Describe the immediate follow-up action.

<!-- Save as research_log/experiments/e001.md -->
