---
description: Run out-of-sample validation for the current strategy
---

Run out-of-sample (OOS) validation to test strategy generalization on unseen data.

## ⚠️ CRITICAL RULES (Read Before Executing!)

1. **Work in hypothesis directory**: ALL file operations in `STRATEGIES/hypothesis_X/`
2. **Never at root**: OOS validation results go in hypothesis directory, NEVER at root
3. **Read iteration_state.json**: Find hypothesis directory from iteration_state.json
4. **Logs in PROJECT_LOGS**: Detailed logs can go in `PROJECT_LOGS/`, results summary in hypothesis dir
5. **Allowed at root**: ONLY README.md, requirements.txt, .env, .gitignore, BOOTSTRAP.sh
6. **Reuse project_id**: Use SAME project_id from iteration_state.json (created during /qc-backtest)

**If you create validation files at root, the workflow WILL BREAK!**

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
    echo "Run /qc-backtest first"
    exit 1
fi

# Check 5: Optimization complete (optional - can skip to validation)
OPT_COMPLETE=$(cat "${HYPOTHESIS_DIR}/iteration_state.json" | jq -r '.phase_results.optimization.completed // false')
if [ "$OPT_COMPLETE" == "false" ]; then
    echo "⚠️  WARNING: No optimization found - using baseline parameters"
    echo "Consider running /qc-optimize first for better results"
fi

# Check 6: Strategy file exists in hypothesis directory
STRATEGY_FILE=$(find "${HYPOTHESIS_DIR}" -name "*.py" -type f | head -1)
if [ -z "$STRATEGY_FILE" ]; then
    echo "❌ ERROR: No strategy file found in ${HYPOTHESIS_DIR}!"
    echo "Run /qc-backtest first"
    exit 1
fi

# Check 7: No validation files at root
if ls -1 oos_*.json 2>/dev/null; then
    echo "❌ ERROR: Validation files found at root!"
    echo "Files must be in ${HYPOTHESIS_DIR}/"
    exit 1
fi

echo "✅ Pre-flight checks passed"
echo "📁 Working with: ${HYPOTHESIS_DIR}"
echo "📊 Baseline Sharpe: ${BASELINE_SHARPE}"
echo "🔧 Optimization: ${OPT_COMPLETE}"
```

---

**⚠️ CRITICAL RULE: REUSE SAME PROJECT_ID FROM HYPOTHESIS**

**IMPERATIVE**: Use the existing project_id from iteration_state.json
- Do NOT create a new project for validation
- Validation runs on the SAME project created during /qc-backtest
- Keeps entire hypothesis lifecycle in one project

**⚠️ AUTONOMOUS MODE: AUTO-CONFIGURE OOS PERIOD**

This command will:
1. Read current strategy and best parameters
2. **Auto-configure** OOS time period (no prompts)
   - If in-sample: 2022-2024 → OOS: 2024-2025
   - Use last 20-30% of data as OOS
3. Run OOS backtest via QuantConnect API (using EXISTING project_id)
4. Compare OOS vs in-sample performance
5. Check for degradation (Sharpe drop > 30% = fail)
6. Make final validation decision
7. Update iteration_state.json
8. **Auto-proceed or STOP** based on result
9. Log validation results to decisions_log.md

**User intervention**: NONE (unless validation fails - blocker)

**Usage**:
```
/qc-validate
```

**Automatic OOS Period Selection**:
The command will automatically select an OOS period that doesn't overlap with the in-sample period:

- In-sample: 2023-01-01 to 2023-12-31
- Out-of-sample: 2024-01-01 to 2024-12-31

**Manual OOS Period**:
```
/qc-validate --oos-start 2024-01-01 --oos-end 2024-12-31
```

**Decision Framework**:

Based on OOS degradation:

- **oos_degradation > 50%** → RETRY_OPTIMIZATION or ABANDON
- **oos_degradation > 30%** → ESCALATE (significant degradation)
- **oos_sharpe >= 1.0** → STRATEGY_COMPLETE ✅
- **else** → STRATEGY_VALIDATED_SUBOPTIMAL

Where degradation = (in_sample_sharpe - oos_sharpe) / in_sample_sharpe

**Output**:
```
🧪 Running Out-of-Sample Validation...
   Strategy: RSI Mean Reversion
   Parameters: rsi_period=14, oversold=30, overbought=70

📅 Time Periods:
   In-Sample (IS): 2023-01-01 to 2023-12-31
   Out-of-Sample (OOS): 2024-01-01 to 2024-12-31

⏳ Running OOS backtest...
   ✅ Complete (18s)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 VALIDATION RESULTS:

Performance Comparison:
┌────────────────┬──────────┬──────────┬──────────────┐
│ Metric         │ In-Sample│Out-Sample│ Degradation  │
├────────────────┼──────────┼──────────┼──────────────┤
│ Sharpe Ratio   │   1.45   │   1.28   │    11.7% ✅  │
│ Total Return   │   23%    │   18%    │    21.7%     │
│ Max Drawdown   │   12%    │   15%    │    25.0%     │
│ Win Rate       │   62%    │   58%    │     6.5%     │
│ Total Trades   │   45     │   38     │    15.6%     │
└────────────────┴──────────┴──────────┴──────────────┘

🔍 Degradation Analysis:
   ├─ Sharpe Degradation: 11.7% (ACCEPTABLE ✅)
   ├─ Return Degradation: 21.7% (ACCEPTABLE ✅)
   ├─ Drawdown Increase: 25.0% (ACCEPTABLE ✅)
   └─ Trade Count: Similar (45 → 38)

✅ Generalization: GOOD
   Strategy performs consistently on unseen data

✅ DECISION: STRATEGY_COMPLETE
📝 Reason: OOS Sharpe 1.28 >= 1.0, degradation < 30%

📄 Updated: iteration_state.json (validation: complete)
📝 Logged: decisions_log.md
🎉 Strategy validated and ready for deployment consideration

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 NEXT STEPS:

1. ✅ Review validation results
2. 📸 Capture screenshots from QuantConnect UI for visual validation
3. 📊 Compare IS vs OOS equity curves visually
4. 🔍 Check for regime changes between periods
5. 📝 Document strategy in strategy_report.md
6. 🚀 Consider paper trading before live deployment

Use these commands:
  /qc-report     - Generate complete strategy report
  /qc-init       - Start new hypothesis
```

**Visual Validation Reminder**:
```
⚠️  IMPORTANT: Statistical validation passed, but you should:
   1. Open QuantConnect UI
   2. Compare IS and OOS equity curves visually
   3. Check for visual overfitting signs
   4. Verify trade distribution across time

   Statistical metrics can be misleading without visual confirmation!
```

**Degradation Thresholds**:

- **< 20% degradation** → Excellent generalization ✅
- **20-30% degradation** → Acceptable ⚠️
- **30-50% degradation** → Poor generalization, needs work ⚠️⚠️
- **> 50% degradation** → Failed validation ❌

**Failure Scenarios**:
```
❌ DECISION: RETRY_OPTIMIZATION
📝 Reason: OOS degradation 52% (> 50%)

Suggestions:
  - Simplify strategy (remove parameters)
  - Use more robust indicators
  - Consider walk-forward optimization
  - Test on different market regimes
```

**Complete Strategy**:
```
🎉 STRATEGY VALIDATED AND COMPLETE

Summary:
├─ Hypothesis: RSI Mean Reversion with Trend Filter
├─ In-Sample Sharpe: 1.45
├─ Out-of-Sample Sharpe: 1.28
├─ Degradation: 11.7% (Excellent)
├─ Total Trades (OOS): 38
└─ Status: READY FOR DEPLOYMENT CONSIDERATION

Next Actions:
1. Generate full report: /qc-report
2. Start paper trading
3. Monitor for 30 days before live

---

## Git Integration (AUTOMATIC)

After validation completes, **automatically commit AND tag if successful**:

**⚠️ IMPORTANT**: Stage files with paths from repository root

```bash
# Find hypothesis directory
HYPOTHESIS_DIR=$(find STRATEGIES -maxdepth 1 -name "hypothesis_*" -type d | sort | tail -1)
STATE_FILE="${HYPOTHESIS_DIR}/iteration_state.json"

# Extract validation metrics from hypothesis directory
IS_SHARPE=$(cat "${STATE_FILE}" | jq -r '.phase_results.backtest.performance.sharpe_ratio')
OOS_SHARPE=$(cat "${STATE_FILE}" | jq -r '.phase_results.validation.oos_performance.sharpe_ratio')
DEGRADATION=$(cat "${STATE_FILE}" | jq -r '.phase_results.validation.degradation')
OOS_BACKTEST_ID=$(cat "${STATE_FILE}" | jq -r '.phase_results.validation.oos_backtest_id')
DECISION=$(cat "${STATE_FILE}" | jq -r '.phase_results.validation.decision')
HYPOTHESIS_NAME=$(cat "${STATE_FILE}" | jq -r '.current_hypothesis.name')
HYPOTHESIS_ID=$(cat "${STATE_FILE}" | jq -r '.current_hypothesis.id')
ITERATION=$(cat "${STATE_FILE}" | jq -r '.workflow_state.current_iteration')

# Stage files from hypothesis directory
git add "${HYPOTHESIS_DIR}/iteration_state.json"
git add "${HYPOTHESIS_DIR}/oos_validation_results.json"
git add "${STRATEGY_FILE}"

# Optional: Stage logs from PROJECT_LOGS if they exist
if ls PROJECT_LOGS/validation_h${HYPOTHESIS_ID}*.json 2>/dev/null; then
    git add PROJECT_LOGS/validation_h${HYPOTHESIS_ID}*.json
fi

# Commit with structured message
git commit -m "$(cat <<EOF
validate: Out-of-sample validation $(echo ${DECISION} | tr '[:lower:]' '[:upper:]')

In-Sample Performance:
- Sharpe Ratio: ${IS_SHARPE}

Out-of-Sample Performance:
- Sharpe Ratio: ${OOS_SHARPE}
- Degradation: ${DEGRADATION}%
- Backtest ID: ${OOS_BACKTEST_ID}

Files:
- Results: ${HYPOTHESIS_DIR}/oos_validation_results.json
- State: ${HYPOTHESIS_DIR}/iteration_state.json
- Strategy: ${STRATEGY_FILE}

Decision: ${DECISION}
Status: $([ "${DECISION}" = "strategy_complete" ] && echo "READY FOR DEPLOYMENT" || echo "NEEDS REVIEW")
Phase: validation → complete
Iteration: ${ITERATION}

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"

# If validation PASSED, create git tag
if [ "${DECISION}" = "strategy_complete" ] || (( $(echo "${DEGRADATION} < 30" | bc -l) )); then
    VERSION="v1.0.0-h${HYPOTHESIS_ID}-$(echo ${HYPOTHESIS_NAME} | tr ' ' '-' | tr '[:upper:]' '[:lower:]')"

    git tag -a "${VERSION}" -m "Validated Strategy - ${HYPOTHESIS_NAME}
Hypothesis ID: ${HYPOTHESIS_ID}
OOS Sharpe: ${OOS_SHARPE}
Degradation: ${DEGRADATION}%
Validated: $(date +%Y-%m-%d)
Status: Ready for paper trading"

    echo "🏷️  Created tag: ${VERSION}"
fi

echo "✅ Committed validation results to git"
echo "📝 Commit: $(git log -1 --oneline)"
```

---

## Post-Execution Verification

**After running command, verify file locations:**

```bash
# Should be EMPTY (no validation files at root)
ls -1 oos_*.json 2>/dev/null && echo "❌ ERROR: Validation files at root!" || echo "✅ No validation files at root"

# Should show OOS validation results in hypothesis directory
ls "${HYPOTHESIS_DIR}"/oos_validation_results.json 2>/dev/null && echo "✅ Validation results in hypothesis directory" || echo "❌ ERROR: No validation results!"

# Should show updated iteration_state.json in hypothesis directory
ls "${HYPOTHESIS_DIR}/iteration_state.json" && echo "✅ State file in hypothesis directory" || echo "❌ ERROR: No state file!"

# Should show strategy file in hypothesis directory
ls "${HYPOTHESIS_DIR}"/*.py 2>/dev/null && echo "✅ Strategy in hypothesis directory" || echo "❌ ERROR: No strategy file!"
```

---

## Common Mistakes to Avoid

❌ **WRONG**:
```bash
# Saving validation results at root
cat > oos_validation_results.json <<EOF  # At root!
{
  "oos_sharpe": 1.28,
  ...
}
EOF
```

✅ **CORRECT**:
```bash
# Find hypothesis directory first
HYPOTHESIS_DIR=$(find STRATEGIES -maxdepth 1 -name "hypothesis_*" -type d | sort | tail -1)

# Create results file IN hypothesis directory
RESULTS_FILE="${HYPOTHESIS_DIR}/oos_validation_results.json"
cat > "${RESULTS_FILE}" <<EOF
{
  "oos_sharpe": 1.28,
  ...
}
EOF
```

❌ **WRONG**:
```bash
# Reading iteration_state.json from root
cat iteration_state.json | jq -r '.validation.oos_sharpe'
```

✅ **CORRECT**:
```bash
# Reading from hypothesis directory
STATE_FILE="${HYPOTHESIS_DIR}/iteration_state.json"
cat "${STATE_FILE}" | jq -r '.phase_results.validation.oos_performance.sharpe_ratio'
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
│       ├── iteration_state.json            ✅ (updated)
│       ├── config.json                     ✅ (QC configuration)
│       ├── strategy_name.py                ✅ (main strategy)
│       ├── optimization_params.json        ✅ (if Phase 4 reached)
│       ├── optimization_results_*.json     ✅ (if Phase 4 reached)
│       ├── oos_validation_results.json     ✅ (created here!)
│       ├── research.ipynb                  ✅ (if Phase 5 reached)
│       ├── README.md                       ✅ (hypothesis description)
│       ├── backtest_logs/                  ✅ (backtest-specific logs)
│       ├── helper_classes/                 ✅ (strategy-specific helpers)
│       └── backup_scripts/                 ✅ (version backups)
│
└── PROJECT_LOGS/
    └── validation_hX_*.json                ✅ (optional logs)
```

---

**Tag created only if**:
- Decision = STRATEGY_COMPLETE, OR
- Degradation < 30% (acceptable performance)

---

**Version**: 2.0.0 (Fixed - Directory-First Pattern)
**Last Updated**: 2025-11-14
**Critical Fix**: Added mandatory hypothesis directory usage, pre-flight checks, verification
