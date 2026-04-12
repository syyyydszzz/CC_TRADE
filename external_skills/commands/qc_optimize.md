Run QuantConnect native parameter optimization to find optimal strategy parameters.

## Task

Execute a QuantConnect optimization job using the native QC optimization API:

1. **PREREQUISITE - Verify Baseline Backtest Exists**:
   - Read `iteration_state.json` to check if a baseline backtest has been completed
   - If NO baseline backtest exists OR backtest_results is empty:
     - **STOP and run baseline first**: `/qc-backtest`
     - Display error message: "ERROR: No baseline backtest found. Run /qc-backtest first to establish baseline performance before optimization."
     - EXIT without running optimization
   - If baseline exists, continue to step 2

2. **Check Current State**:
   - Read `iteration_state.json` to get current project_id and baseline metrics
   - Verify strategy file exists and is parameterized with `get_parameter()`
   - Extract baseline Sharpe ratio for comparison

3. **Upload Parameterized Strategy**:
   - Upload `test_strategy.py` to QuantConnect project
   - Ensure strategy uses `get_parameter("param_name", default_value)` for all optimizable parameters
   - Compile the project to get compile ID

4. **Configure Optimization**:
   - Read or create `optimization_params.json` with native QC format:
     ```json
     {
       "parameters": [
         {"name": "rsi_oversold", "min": 30, "max": 45, "step": 5},
         {"name": "bb_distance_pct", "min": 1.02, "max": 1.10, "step": 0.04}
       ],
       "target": "TotalPerformance.PortfolioStatistics.SharpeRatio",
       "targetTo": "max",
       "nodeType": "O2-8",
       "parallelNodes": 2
     }
     ```
   - Estimate cost and total combinations
   - Show user the optimization plan

5. **Run Native QC Optimization**:
   - Use `qc_backtest.py --optimize` with native QC API
   - Submit optimization job via `/optimizations/create` endpoint
   - Wait for completion (can take 10-30 minutes)
   - Poll status every 15-30 seconds

6. **Analyze Results**:
   - Parse optimization results from QC API
   - Extract best parameters (by Sharpe ratio or specified target)
   - Calculate improvement vs baseline
   - Check for overfitting indicators:
     - Improvement > 30% (suspicious)
     - Sharp peaks in parameter space (overfitted)
     - High parameter sensitivity (not robust)

7. **Apply Decision Framework**:
   ```python
   if improvement > 0.30:
       decision = "ESCALATE"
       reason = "Suspicious improvement (>30%), possible overfitting"

   elif parameter_sensitivity > 0.5:
       decision = "USE_ROBUST_PARAMS"
       reason = "High parameter sensitivity, use median of top quartile"
       params = median_of_top_quartile(results)

   elif improvement > 0.05:
       decision = "PROCEED_TO_VALIDATION"
       reason = "Good improvement (>5%), test OOS with optimized params"

   else:
       decision = "PROCEED_TO_VALIDATION"
       reason = "Minimal improvement, test OOS with baseline params"
   ```

8. **Update State Files**:
   - Update `iteration_state.json`:
     ```json
     {
       "optimization": {
         "status": "completed",
         "optimization_id": "...",
         "best_parameters": {...},
         "improvement": 0.15,
         "decision": "proceed_to_validation"
       }
     }
     ```
   - Log to `decisions_log.md` with full optimization results
   - Save raw results to `optimization_results_YYYYMMDD_HHMMSS.json`

9. **Present Results**:
   ```
   ═══════════════════════════════════════════════════════════
   OPTIMIZATION COMPLETE
   ═══════════════════════════════════════════════════════════

   🔧 Optimization ID: abc123
   📊 Combinations Tested: 24
   ⏱️  Duration: 15 minutes

   🏆 Best Parameters:
      rsi_oversold: 35
      bb_distance_pct: 1.06
      use_trend_filter: 0 (disabled)

   📈 Performance:
      Baseline Sharpe: 0.45
      Optimized Sharpe: 0.92
      Improvement: +104%

   ⚠️  DECISION: ESCALATE
   📝 Reason: Improvement >30%, possible overfitting

   🎯 Recommendation:
      - Review parameter sensitivity
      - Check if results are robust across top quartile
      - Consider out-of-sample validation on different period
   ```

10. **Next Steps Guidance**:
   - If PROCEED_TO_VALIDATION → Use `/qc-validate`
   - If ESCALATE → Review results, manual analysis
   - If USE_ROBUST_PARAMS → Re-run with median params from top quartile

## Requirements

- Parameterized strategy with `get_parameter()` calls
- Valid QuantConnect API credentials in `.env`
- `optimization_params.json` with parameter ranges
- Sufficient QC cloud credits for optimization run

## Important Notes

- **Native QC Optimization**: Uses QuantConnect's built-in grid search, NOT manual backtest loops
- **Cost**: Optimization costs QC credits (estimate before running)
- **Time**: Can take 10-30 minutes depending on parameter combinations
- **Overfitting Risk**: Always validate optimized parameters out-of-sample
- **Parameter Format**: Must use `{"name": "...", "min": X, "max": Y, "step": Z}` format

## Error Handling

- **If no baseline backtest** → **CRITICAL ERROR**: Display "ERROR: No baseline backtest found. Run /qc-backtest first." and EXIT. Do NOT proceed with optimization.
- If strategy not parameterized → Error with instructions to add `get_parameter()`
- If optimization fails → Log error, suggest reducing parameter combinations
- If API error → Check credentials, network, QC service status

## Command Separation

- **`/qc-backtest`**: Runs a SINGLE backtest with current parameters. Use this for baseline and validation runs.
- **`/qc-optimize`**: Runs MULTIPLE backtests with different parameter combinations via QC's native optimization API. Requires baseline first.
- Never mix these two operations. Always run `/qc-backtest` before `/qc-optimize`.

---

## Git Integration (AUTOMATIC)

After optimization completes, **automatically commit results**:

```bash
# Extract optimization metrics from iteration_state.json
OPT_ID=$(cat iteration_state.json | grep '"optimization_id"' | sed 's/.*: "//;s/",//')
BEST_SHARPE=$(cat iteration_state.json | grep '"best_sharpe"' | head -1 | sed 's/[^0-9.-]*//g')
BASELINE_SHARPE=$(cat iteration_state.json | grep '"baseline_sharpe"' | head -1 | sed 's/[^0-9.-]*//g')
IMPROVEMENT=$(cat iteration_state.json | grep '"improvement"' | head -1 | sed 's/[^0-9.-]*//g')
DECISION=$(cat iteration_state.json | grep 'optimization.*decision' | sed 's/.*: "//;s/",//')
ITERATION=$(cat iteration_state.json | grep '"iteration_count"' | head -1 | sed 's/[^0-9]*//g')

# Extract best parameters (JSON object)
BEST_PARAMS=$(cat iteration_state.json | grep -A 10 '"best_parameters"')

# Stage files
git add iteration_state.json optimization_results*.json test_strategy.py decisions_log.md

# Commit with structured message
git commit -m "$(cat <<EOF
optimize: Parameter optimization complete

Optimization ID: ${OPT_ID}
Combinations Tested: $(cat optimization_results*.json 2>/dev/null | grep -c '"backtest_id"' || echo "N/A")

Performance:
- Baseline Sharpe: ${BASELINE_SHARPE}
- Optimized Sharpe: ${BEST_SHARPE}
- Improvement: ${IMPROVEMENT}%

Best Parameters:
${BEST_PARAMS}

Decision: ${DECISION}
Phase: optimization → validation
Iteration: ${ITERATION}

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"

echo "✅ Committed optimization results to git"
echo "📝 Commit: $(git log -1 --oneline)"
```
