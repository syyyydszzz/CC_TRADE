Run Monte Carlo walk-forward optimization to validate strategy robustness across different time periods.

## Task

Execute walk-forward analysis with Monte Carlo randomization to assess parameter stability:

1. **PREREQUISITE - Verify Baseline Exists**:
   - Read `iteration_state.json` to check if baseline backtest and optimization have been completed
   - If NO baseline or optimization results → Display error and EXIT
   - Required state: baseline_backtest_id, optimization completed

2. **Configure Walk-Forward Parameters**:
   - Read or create `walkforward_config.json`:
     ```json
     {
       "total_period": {
         "start": "2020-01-01",
         "end": "2023-12-31"
       },
       "train_test_split": 0.60,
       "monte_carlo_runs": 10,
       "walk_forward_windows": 5,
       "method": "monte_carlo",
       "parameters_to_optimize": [
         "rsi_oversold",
         "bb_distance_pct",
         "use_trend_filter"
       ],
       "validation_metric": "sharpe_ratio"
     }
     ```

3. **Monte Carlo Walk-Forward Method**:
   - **For each of N Monte Carlo runs**:
     1. Randomly sample training period (60% of total period)
     2. Reserve remaining data as out-of-sample test period
     3. Run optimization on training period
     4. Backtest optimized parameters on test period
     5. Record performance degradation (training vs testing)

4. **Execute Monte Carlo Runs**:
   ```python
   import random
   from datetime import datetime, timedelta

   results = []
   for run in range(monte_carlo_runs):
       # Random sampling of training period
       total_days = (end_date - start_date).days
       train_days = int(total_days * train_test_split)

       # Random start point for training window
       max_start_offset = total_days - train_days - (total_days * 0.4)
       start_offset = random.randint(0, max_start_offset)

       train_start = start_date + timedelta(days=start_offset)
       train_end = train_start + timedelta(days=train_days)
       test_start = train_end + timedelta(days=1)
       test_end = start_date + timedelta(days=total_days)

       # Optimize on training data
       optimization_result = run_optimization(train_start, train_end)
       best_params = optimization_result['best_parameters']

       # Validate on test data
       test_result = run_backtest(test_start, test_end, best_params)

       # Record degradation
       degradation = (optimization_result['sharpe'] - test_result['sharpe']) / optimization_result['sharpe']

       results.append({
           'run': run,
           'train_period': [train_start, train_end],
           'test_period': [test_start, test_end],
           'train_sharpe': optimization_result['sharpe'],
           'test_sharpe': test_result['sharpe'],
           'degradation': degradation,
           'best_params': best_params
       })
   ```

5. **Analyze Aggregate Results**:
   - Calculate statistics across all Monte Carlo runs:
     - Mean degradation
     - Std dev of degradation
     - % of runs with degradation > 30% (overfitting indicator)
     - Parameter stability (how often same params are chosen)
     - Sharpe ratio distribution (mean, median, std)

6. **Apply Robustness Decision Framework**:
   ```python
   mean_degradation = np.mean([r['degradation'] for r in results])
   std_degradation = np.std([r['degradation'] for r in results])
   pct_overfit = sum(1 for r in results if r['degradation'] > 0.30) / len(results)

   if pct_overfit > 0.50:
       decision = "ABANDON_STRATEGY"
       reason = f"Overfitting in {pct_overfit:.0%} of Monte Carlo runs"

   elif mean_degradation > 0.40:
       decision = "HIGH_RISK"
       reason = f"Average degradation {mean_degradation:.1%} indicates poor generalization"

   elif std_degradation > 0.25:
       decision = "UNSTABLE_PARAMETERS"
       reason = f"High variance ({std_degradation:.1%}) suggests parameter instability"

   elif mean_degradation < 0.15 and std_degradation < 0.10:
       decision = "ROBUST_STRATEGY"
       reason = f"Low degradation ({mean_degradation:.1%}) with low variance"

   else:
       decision = "PROCEED_WITH_CAUTION"
       reason = f"Moderate degradation ({mean_degradation:.1%}), acceptable stability"
   ```

7. **Update State Files**:
   - Update `iteration_state.json`:
     ```json
     {
       "walkforward": {
         "status": "completed",
         "method": "monte_carlo",
         "runs": 10,
         "mean_degradation": 0.18,
         "std_degradation": 0.09,
         "pct_overfit": 0.10,
         "decision": "robust_strategy",
         "most_common_params": {...}
       }
     }
     ```
   - Log to `decisions_log.md` with full Monte Carlo results
   - Save detailed results to `walkforward_results_YYYYMMDD_HHMMSS.json`

8. **Present Results**:
   ```
   ═══════════════════════════════════════════════════════════
   MONTE CARLO WALK-FORWARD ANALYSIS COMPLETE
   ═══════════════════════════════════════════════════════════

   📊 Monte Carlo Runs: 10
   📅 Total Period: 2020-01-01 to 2023-12-31
   📈 Train/Test Split: 60/40%

   🎲 Aggregate Results:
      Mean Training Sharpe: 0.85
      Mean Testing Sharpe: 0.72
      Mean Degradation: 15.3%
      Std Dev Degradation: 8.7%

   🚩 Overfitting Analysis:
      Runs with >30% degradation: 1/10 (10%)
      Runs with <15% degradation: 6/10 (60%)

   🔧 Parameter Stability:
      Most common rsi_oversold: 35 (appeared 7/10 times)
      Most common bb_distance_pct: 1.06 (appeared 6/10 times)
      Most common use_trend_filter: 0 (appeared 8/10 times)

   ✅ DECISION: ROBUST_STRATEGY
   📝 Reason: Low degradation (15.3%) with low variance (8.7%)

   🎯 Recommendation:
      Strategy shows good generalization across different time periods.
      Recommended parameters for live trading:
      - rsi_oversold: 35
      - bb_distance_pct: 1.06
      - use_trend_filter: False

   Next Step: Proceed to paper trading or live testing
   ```

9. **Git Integration** (AUTOMATIC):
   ```bash
   git add iteration_state.json walkforward_results*.json decisions_log.md
   git commit -m "$(cat <<EOF
   validate: Monte Carlo walk-forward analysis complete

   Monte Carlo Runs: 10
   Period: 2020-01-01 to 2023-12-31
   Train/Test Split: 60/40%

   Results:
   - Mean Training Sharpe: 0.85
   - Mean Testing Sharpe: 0.72
   - Mean Degradation: 15.3%
   - Std Degradation: 8.7%
   - Overfitting Rate: 10%

   Most Stable Parameters:
   - rsi_oversold: 35 (70% consensus)
   - bb_distance_pct: 1.06 (60% consensus)
   - use_trend_filter: 0 (80% consensus)

   Decision: ROBUST_STRATEGY
   Generalization: Excellent

   Phase: validation → production_ready

   🤖 Generated with Claude Code
   Co-Authored-By: Claude <noreply@anthropic.com>
   EOF
   )"
   ```

## Requirements

- Completed baseline backtest and optimization
- Valid QuantConnect API credentials
- `walkforward_config.json` with Monte Carlo parameters
- Sufficient QC cloud credits for multiple backtest runs

## Important Notes

- **Cost**: Monte Carlo walk-forward runs N×2 backtests (N optimizations + N validations)
- **Time**: Can take hours depending on number of runs
- **Robustness**: Higher N (runs) = more reliable results, but higher cost
- **Random Seed**: Use fixed seed for reproducibility if needed
- **Validation**: This is the FINAL validation step before live trading

## Command Separation

- **`/qc-backtest`**: Single backtest with current parameters
- **`/qc-optimize`**: Single optimization run (grid search)
- **`/qc-validate`**: Single out-of-sample validation
- **`/qc-walkforward`**: Monte Carlo walk-forward (multiple optimizations + validations)

## Next Steps After Completion

- If ROBUST_STRATEGY → Proceed to paper trading
- If PROCEED_WITH_CAUTION → Additional testing recommended
- If UNSTABLE_PARAMETERS → Review parameter ranges, reduce search space
- If ABANDON_STRATEGY → Start new hypothesis with `/qc-init`
