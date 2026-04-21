Run QuantConnect native parameter optimization to find optimal strategy parameters.

## ⚠️ CRITICAL RULES (Read Before Executing!)

1. **Work in hypothesis directory**: ALL file operations in `STRATEGIES/hypothesis_X/`
2. **Never at root**: Optimization results go in hypothesis directory, NEVER at root
3. **Read iteration_state.json**: Find hypothesis directory from iteration_state.json
4. **Logs in PROJECT_LOGS**: Detailed logs go in `PROJECT_LOGS/`, results summary in hypothesis dir
5. **Allowed at root**: ONLY README.md, requirements.txt, .env, .gitignore, BOOTSTRAP.sh

**If you create optimization files at root, the workflow WILL BREAK!**

---

## Pre-Flight Checks (Run at Start)

**Before executing this command, verify:**

```bash
# Check 1: We're at repository root
if [[ $(basename $(pwd)) != "CLAUDE_CODE_EXPLORE" ]]; then
    echo "⚠️  WARNING: Not at repository root"
    echo "Current: $(pwd)"
    echo "Run: cd /path/to/CLAUDE_CODE_EXPLORE"
fi

# Check 2: Find hypothesis directory
HYPOTHESIS_DIR=$(find STRATEGIES -maxdepth 1 -name "hypothesis_*" -type d | sort | tail -1)
if [ -z "$HYPOTHESIS_DIR" ]; then
    echo "❌ ERROR: No hypothesis directory found!"
    echo "Run /qc-init first to create hypothesis"
    exit 1
fi

# Check 3: iteration_state.json exists in hypothesis directory
if [ ! -f "${HYPOTHESIS_DIR}/iteration_state.json" ]; then
    echo "❌ ERROR: iteration_state.json not found in ${HYPOTHESIS_DIR}!"
    echo "Run /qc-init first"
    exit 1
fi

# Check 4: Baseline backtest exists
BASELINE_SHARPE=$(cat "${HYPOTHESIS_DIR}/iteration_state.json" | jq -r '.phase_results.backtest.performance.sharpe_ratio // empty')
if [ -z "$BASELINE_SHARPE" ] || [ "$BASELINE_SHARPE" == "null" ]; then
    echo "❌ ERROR: No baseline backtest found!"
    echo "Run /qc-backtest first to establish baseline performance"
    exit 1
fi

# Check 5: Strategy file exists in hypothesis directory
STRATEGY_FILE=$(find "${HYPOTHESIS_DIR}" -name "*.py" -type f | head -1)
if [ -z "$STRATEGY_FILE" ]; then
    echo "❌ ERROR: No strategy file found in ${HYPOTHESIS_DIR}!"
    echo "Run /qc-backtest first"
    exit 1
fi

# Check 6: No optimization files at root
if ls -1 optimization_*.json 2>/dev/null; then
    echo "❌ ERROR: Optimization files found at root!"
    echo "Files must be in ${HYPOTHESIS_DIR}/"
    exit 1
fi

echo "✅ Pre-flight checks passed"
echo "📁 Working with: ${HYPOTHESIS_DIR}"
echo "📊 Baseline Sharpe: ${BASELINE_SHARPE}"
```

---

## Task

Execute a QuantConnect optimization job using the native QC optimization API:

1. **PREREQUISITE - Verify Baseline Backtest Exists** (already checked in pre-flight):
   - Pre-flight checks verified baseline exists
   - If checks passed, continue to step 2

2. **Check Current State and Find Hypothesis Directory**:
   **⚠️ CRITICAL**: Always read from hypothesis directory, never from root

   ```bash
   # Find hypothesis directory (latest created)
   HYPOTHESIS_DIR=$(find STRATEGIES -maxdepth 1 -name "hypothesis_*" -type d | sort | tail -1)

   # Read iteration_state.json from hypothesis directory
   STATE_FILE="${HYPOTHESIS_DIR}/iteration_state.json"

   HYPOTHESIS_ID=$(cat "${STATE_FILE}" | jq -r '.current_hypothesis.id')
   HYPOTHESIS_NAME=$(cat "${STATE_FILE}" | jq -r '.current_hypothesis.name')
   PROJECT_ID=$(cat "${STATE_FILE}" | jq -r '.qc_project.project_id')
   BASELINE_SHARPE=$(cat "${STATE_FILE}" | jq -r '.phase_results.backtest.performance.sharpe_ratio')

   # Find strategy file in hypothesis directory
   STRATEGY_FILE=$(find "${HYPOTHESIS_DIR}" -name "*.py" -type f | head -1)

   echo "✅ Read state from: ${STATE_FILE}"
   echo "📁 Strategy file: ${STRATEGY_FILE}"
   echo "📊 Baseline Sharpe: ${BASELINE_SHARPE}"
   ```

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
   - Use `qc_optimize.py run` with native QC API
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
   **⚠️ CRITICAL**: Save all files IN hypothesis directory

   ```bash
   # Create timestamp for results file
   TIMESTAMP=$(date +%Y%m%d_%H%M%S)
   RESULTS_FILE="${HYPOTHESIS_DIR}/optimization_results_${TIMESTAMP}.json"

   echo "💾 Saving optimization results: ${RESULTS_FILE}"

   # Verification: Ensure not saving at root
   if [[ "${RESULTS_FILE}" != STRATEGIES/* ]]; then
       echo "❌ ERROR: Results file path doesn't start with STRATEGIES/!"
       echo "❌ Path: ${RESULTS_FILE}"
       echo "❌ Cannot create at root - workflow will break"
       exit 1
   fi

   # Save raw optimization results to hypothesis directory
   cat > "${RESULTS_FILE}" <<EOF
   {
     "optimization_id": "...",
     "best_parameters": {...},
     "improvement": 0.15,
     "all_results": [...]
   }
   EOF

   # Verify file created in hypothesis directory
   if [ ! -f "${RESULTS_FILE}" ]; then
       echo "❌ ERROR: Failed to create ${RESULTS_FILE}"
       exit 1
   fi

   # Verify NOT created at root
   if [ -f "optimization_results_${TIMESTAMP}.json" ]; then
       echo "❌ ERROR: Optimization results created at root!"
       echo "❌ This violates Critical Rule #2"
       exit 1
   fi

   echo "✅ Optimization results saved: ${RESULTS_FILE}"

   # Update iteration_state.json in hypothesis directory
   STATE_FILE="${HYPOTHESIS_DIR}/iteration_state.json"

   python3 -c "
   import json
   from datetime import datetime

   with open('${STATE_FILE}', 'r') as f:
       state = json.load(f)

   # Update phase_results.optimization section
   state['phase_results']['optimization'] = {
       'completed': True,
       'timestamp': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
       'optimization_id': '...',
       'best_parameters': {...},
       'improvement': 0.15,
       'decision': 'proceed_to_validation'
   }

   # Update workflow section
   state['workflow_state']['current_phase'] = 'optimization'
   state['workflow_state']['updated_at'] = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')

   # Save
   with open('${STATE_FILE}', 'w') as f:
       json.dump(state, f, indent=2)

   print('✅ State file updated')
   "

   echo "✅ Updated: ${STATE_FILE}"
   ```

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

**⚠️ IMPORTANT**: Stage files with paths from repository root

```bash
# Extract optimization metrics from iteration_state.json in hypothesis directory
STATE_FILE="${HYPOTHESIS_DIR}/iteration_state.json"

OPT_ID=$(cat "${STATE_FILE}" | jq -r '.phase_results.optimization.optimization_id')
BEST_SHARPE=$(cat "${STATE_FILE}" | jq -r '.phase_results.optimization.best_sharpe')
BASELINE_SHARPE=$(cat "${STATE_FILE}" | jq -r '.phase_results.backtest.performance.sharpe_ratio')
IMPROVEMENT=$(cat "${STATE_FILE}" | jq -r '.phase_results.optimization.improvement')
DECISION=$(cat "${STATE_FILE}" | jq -r '.phase_results.optimization.decision')
ITERATION=$(cat "${STATE_FILE}" | jq -r '.workflow_state.current_iteration')

# Extract best parameters (JSON object)
BEST_PARAMS=$(cat "${STATE_FILE}" | jq -r '.phase_results.optimization.best_parameters')

# Stage files from hypothesis directory
git add "${HYPOTHESIS_DIR}/iteration_state.json"
git add "${HYPOTHESIS_DIR}/optimization_results_"*.json
git add "${STRATEGY_FILE}"

# Commit with structured message
git commit -m "$(cat <<EOF
optimize: Parameter optimization complete

Optimization ID: ${OPT_ID}
Combinations Tested: $(cat "${HYPOTHESIS_DIR}/optimization_results_"*.json 2>/dev/null | jq -r '.all_results | length' || echo "N/A")

Performance:
- Baseline Sharpe: ${BASELINE_SHARPE}
- Optimized Sharpe: ${BEST_SHARPE}
- Improvement: ${IMPROVEMENT}%

Best Parameters:
${BEST_PARAMS}

Files:
- Results: ${HYPOTHESIS_DIR}/optimization_results_*.json
- State: ${HYPOTHESIS_DIR}/iteration_state.json
- Strategy: ${STRATEGY_FILE}

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

---

## Post-Execution Verification

**After running command, verify file locations:**

```bash
# Should be EMPTY (no optimization files at root)
ls -1 optimization_*.json 2>/dev/null && echo "❌ ERROR: Optimization files at root!" || echo "✅ No optimization files at root"

# Should show optimization results in hypothesis directory
ls "${HYPOTHESIS_DIR}"/optimization_results_*.json 2>/dev/null && echo "✅ Optimization results in hypothesis directory" || echo "❌ ERROR: No optimization results!"

# Should show updated iteration_state.json in hypothesis directory
ls "${HYPOTHESIS_DIR}/iteration_state.json" && echo "✅ State file in hypothesis directory" || echo "❌ ERROR: No state file!"

# Should show strategy file in hypothesis directory
ls "${HYPOTHESIS_DIR}"/*.py 2>/dev/null && echo "✅ Strategy in hypothesis directory" || echo "❌ ERROR: No strategy file!"
```

---

## Common Mistakes to Avoid

❌ **WRONG**:
```bash
# Saving optimization results at root
cat > optimization_results.json <<EOF  # At root!
{
  "optimization_id": "...",
  ...
}
EOF
```

✅ **CORRECT**:
```bash
# Find hypothesis directory first
HYPOTHESIS_DIR=$(find STRATEGIES -maxdepth 1 -name "hypothesis_*" -type d | sort | tail -1)

# Create results file IN hypothesis directory
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RESULTS_FILE="${HYPOTHESIS_DIR}/optimization_results_${TIMESTAMP}.json"
cat > "${RESULTS_FILE}" <<EOF
{
  "optimization_id": "...",
  ...
}
EOF
```

❌ **WRONG**:
```bash
# Reading iteration_state.json from root
cat iteration_state.json | jq -r '.optimization.best_params'
```

✅ **CORRECT**:
```bash
# Reading from hypothesis directory
STATE_FILE="${HYPOTHESIS_DIR}/iteration_state.json"
cat "${STATE_FILE}" | jq -r '.phase_results.optimization.best_parameters'
```

---

## Directory Structure After Execution

```
/
├── README.md                  ✅ (allowed at root)
├── BOOTSTRAP.sh               ✅ (allowed at root)
├── requirements.txt           ✅ (allowed at root)
├── .env                       ✅ (allowed at root)
├── .gitignore                 ✅ (allowed at root)
│
├── SCRIPTS/
│   └── strategy_components/   ✅ (shared components)
│       ├── sentiment/
│       │   ├── kalshi_regime_detector.py
│       │   ├── kalshi_fed_hedge.py
│       │   ├── kalshi_vol_forecast.py
│       │   ├── kalshi_sentiment_monitor.py
│       │   └── kalshi_api_wrapper.py
│       └── (other shared components)
│
├── STRATEGIES/
│   └── hypothesis_X_name/
│       ├── iteration_state.json                ✅ (updated)
│       ├── config.json                         ✅ (QC configuration)
│       ├── strategy_name.py                    ✅ (exists)
│       ├── optimization_params.json            ✅ (parameter ranges)
│       ├── optimization_results_TIMESTAMP.json ✅ (created here!)
│       ├── README.md                           ✅ (hypothesis description)
│       ├── backtest_logs/                      ✅ (backtest-specific logs)
│       ├── helper_classes/                     ✅ (strategy-specific helpers)
│       └── backup_scripts/                     ✅ (version backups)
│
└── PROJECT_LOGS/
    └── (optimization logs can go here optionally)
```

---

**Version**: 2.0.0 (Fixed - Directory-First Pattern)
**Last Updated**: 2025-11-14
**Critical Fix**: Added mandatory hypothesis directory usage, pre-flight checks, verification
