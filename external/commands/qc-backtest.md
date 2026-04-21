---
description: Run a backtest for the current hypothesis and make autonomous routing decision (project)
---

Run a backtest on QuantConnect for the current hypothesis and automatically determine the next phase based on results.

This command implements Phase 2 (Implementation) and Phase 3 (Backtest + Decision) of the 5-phase autonomous workflow.

## ⚠️ CRITICAL RULES (Read Before Executing!)

1. **Work in hypothesis directory**: ALL file operations in `STRATEGIES/hypothesis_X/`
2. **Never at root**: Strategy files go in hypothesis directory, NEVER at root
3. **Read iteration_state.json**: Find hypothesis directory from iteration_state.json
4. **Logs separate**: Backtest result logs go in `PROJECT_LOGS/`, NOT hypothesis directory
5. **Allowed at root**: ONLY README.md, requirements.txt, .env, .gitignore, BOOTSTRAP.sh

**If you create strategy files at root, the workflow WILL BREAK!**

---

## What This Command Does

1. Reads current hypothesis from iteration_state.json
2. Loads QuantConnect Skill for strategy implementation guidance
3. Generates strategy code from hypothesis (Phase 2)
4. Validates implementation (syntax, entry/exit logic, risk management)
5. Creates/updates QuantConnect project via API
6. Uploads strategy file to project
7. Runs backtest via qc_backtest.py wrapper
8. Waits for backtest completion
9. Parses results (Sharpe, drawdown, trades, etc.)
10. Applies Phase 3 decision framework
11. Makes autonomous routing decision
12. Updates iteration_state.json with results and decision
13. Commits to git with structured message including metrics

## Usage

```bash
/qc-backtest
```

No parameters required - reads everything from iteration_state.json.

## Decision Framework (Phase 3)

The command applies 4-tier threshold system to determine next action:

### Tier 1: ABANDON_HYPOTHESIS
- Sharpe < 0.5 (below minimum_viable)
- OR max_drawdown > 0.40
- OR total_trades < 30
- OR fatal implementation errors

### Tier 2: PROCEED_TO_OPTIMIZATION
- Sharpe >= 0.7 (optimization_worthy)
- AND max_drawdown <= 0.35
- AND total_trades >= 50
- Decent performance, worth optimizing

### Tier 3: PROCEED_TO_VALIDATION
- Sharpe >= 1.0 (production_ready)
- AND max_drawdown <= 0.30
- AND total_trades >= 100
- Strong baseline, can skip optimization

### Tier 4: ESCALATE_TO_HUMAN
- Sharpe > 3.0 (too_perfect_sharpe - overfitting signal)
- OR total_trades < 20 (too_few_trades)
- OR win_rate > 0.75 (win_rate_too_high)
- Suspicious results, needs human review

### Edge Cases
- If Sharpe >= 0.5 but < 0.7: PROCEED_TO_OPTIMIZATION (try to improve)
- If iteration > max_iterations: ABANDON_HYPOTHESIS (too many attempts)

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

# Check 4: No strategy files at root
if ls -1 *.py 2>/dev/null | grep -v BOOTSTRAP.sh; then
    echo "❌ ERROR: Python files found at root!"
    echo "Strategy files must be in ${HYPOTHESIS_DIR}/"
    exit 1
fi

echo "✅ Pre-flight checks passed"
echo "📁 Working with: ${HYPOTHESIS_DIR}"
```

---

## Implementation Steps

When this command is executed, perform these steps **IN ORDER**:

### Step 1: Read Current State and Find Hypothesis Directory

**⚠️ CRITICAL**: Always read from hypothesis directory, never from root

```bash
# Find hypothesis directory (latest created)
HYPOTHESIS_DIR=$(find STRATEGIES -maxdepth 1 -name "hypothesis_*" -type d | sort | tail -1)

# Read iteration_state.json from hypothesis directory
HYPOTHESIS_NAME=$(cat "${HYPOTHESIS_DIR}/iteration_state.json" | jq -r '.current_hypothesis.name')
HYPOTHESIS_DESC=$(cat "${HYPOTHESIS_DIR}/iteration_state.json" | jq -r '.current_hypothesis.description')
HYPOTHESIS_RATIONALE=$(cat "${HYPOTHESIS_DIR}/iteration_state.json" | jq -r '.current_hypothesis.rationale')
HYPOTHESIS_ID=$(cat "${HYPOTHESIS_DIR}/iteration_state.json" | jq -r '.current_hypothesis.id')
PROJECT_ID=$(cat "${HYPOTHESIS_DIR}/iteration_state.json" | jq -r '.qc_project.project_id')
ITERATION=$(cat "${HYPOTHESIS_DIR}/iteration_state.json" | jq -r '.workflow_state.current_iteration')

echo "✅ Read state from: ${HYPOTHESIS_DIR}/iteration_state.json"
```

### Step 2: Load QuantConnect Skill

Load the QuantConnect skill to access:
- Strategy templates
- Indicator usage examples
- Entry/exit logic patterns
- Risk management best practices
- Common error patterns (NoneType checks, off-by-one)

### Step 3: Implement Strategy (Phase 2)

**⚠️ CRITICAL**: Create strategy file IN hypothesis directory

Generate strategy code based on hypothesis:

```bash
# Create slugified strategy filename
STRATEGY_SLUG=$(echo "$HYPOTHESIS_NAME" | tr '[:upper:]' '[:lower:]' | tr ' ' '_' | sed 's/[^a-z0-9_]//g')
STRATEGY_FILE="${HYPOTHESIS_DIR}/${STRATEGY_SLUG}.py"

echo "📝 Creating strategy file: ${STRATEGY_FILE}"

# Verification: Ensure not creating at root
if [[ "${STRATEGY_FILE}" != STRATEGIES/* ]]; then
    echo "❌ ERROR: Strategy file path doesn't start with STRATEGIES/!"
    echo "❌ Path: ${STRATEGY_FILE}"
    echo "❌ Cannot create at root - workflow will break"
    exit 1
fi
```

**Python strategy template** (to be created at `${STRATEGY_FILE}`):

```python
# File: ${STRATEGY_FILE}
# Created in: ${HYPOTHESIS_DIR}/
# Hypothesis: ${HYPOTHESIS_NAME}

class HypothesisStrategy(QCAlgorithm):
    def Initialize(self):
        # Set dates, cash, resolution
        # Add equities/assets
        # Configure indicators
        # Set warmup period

    def OnData(self, data):
        # Entry logic (from hypothesis)
        # Exit logic (from hypothesis)
        # Risk management (stop loss, position sizing)

# Error handling:
# - Check for None before accessing data
# - Validate indicators are ready
# - Handle missing data gracefully
```

**After creating strategy file, verify location**:

```bash
# Verify file was created in hypothesis directory
if [ ! -f "${STRATEGY_FILE}" ]; then
    echo "❌ ERROR: Failed to create ${STRATEGY_FILE}"
    exit 1
fi

# Verify it's NOT at root
if [ -f "$(basename ${STRATEGY_FILE})" ]; then
    echo "❌ ERROR: Strategy file created at root!"
    echo "❌ File: $(basename ${STRATEGY_FILE})"
    echo "❌ This violates Critical Rule #2"
    exit 1
fi

echo "✅ Strategy file created: ${STRATEGY_FILE}"
echo "✅ Location verified: In hypothesis directory"
```

### Step 4: Validate Implementation

**⚠️ AUTONOMOUS MODE: AUTO-FIX ERRORS WITHOUT USER INTERVENTION**

Check for common issues:
- Syntax errors
- Missing entry logic
- Missing exit logic
- Missing risk management
- NoneType access (data[symbol] without checking)
- Off-by-one errors in loops
- Indicator warmup not handled

If validation fails:
- **Automatically fix** the issue
- Increment fix_attempts
- Retry backtest
- If fix_attempts >= 3: **THEN** ESCALATE_TO_HUMAN (blocker)
- Otherwise: Continue autonomously

### Step 5: Create/Update QC Project

**⚠️ CRITICAL RULE: ONE PROJECT ID PER HYPOTHESIS**

**IMPERATIVE**: Reuse the SAME project_id for:
- All backtests of this hypothesis
- All optimizations of this hypothesis
- All validations of this hypothesis

**ONLY create new project if**:
- project_id is null (first time)
- User explicitly requests new project
- Major strategy rewrite (not bug fixes)

```bash
# If PROJECT_ID is null, create new project ONLY ONCE
if [ "$PROJECT_ID" == "null" ]; then
    python SCRIPTS/qc_backtest.py --create --name "${HYPOTHESIS_NAME}" --output project_result.json
    PROJECT_ID=$(cat project_result.json | jq -r '.projects.projects[0].projectId')
    PROJECT_URL="https://www.quantconnect.com/project/${PROJECT_ID}"

    # Update iteration_state.json with project_id (SAVE THIS!)
    # project.project_id = $PROJECT_ID
    # project.project_name = ...
    # project.strategy_file = ...
    # project.qc_url = $PROJECT_URL
fi

# For ALL subsequent backtests: REUSE existing PROJECT_ID
# Update code in existing project, don't create new one
```

### Step 6: Upload Strategy and Run Backtest

**⚠️ CRITICAL: Always use --project-id flag to reuse existing project**

**⚠️ CRITICAL: Backtest result logs go in hypothesis backtest_logs/ directory, NOT at root**

```bash
# Ensure backtest_logs directory exists in hypothesis directory
mkdir -p "${HYPOTHESIS_DIR}/backtest_logs"

# Create backtest result filename with timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKTEST_LOG="${HYPOTHESIS_DIR}/backtest_logs/backtest_iteration_${ITERATION}_${TIMESTAMP}.json"

echo "📝 Saving backtest log: ${BACKTEST_LOG}"

# Verify path before running backtest
if [[ "${BACKTEST_LOG}" != STRATEGIES/*/backtest_logs/* ]]; then
    echo "❌ ERROR: Backtest log path doesn't point to hypothesis backtest_logs/!"
    echo "❌ Path: ${BACKTEST_LOG}"
    exit 1
fi

# ALWAYS pass existing project_id to reuse the same project
# This updates code in existing project instead of creating new one
python SCRIPTS/qc_backtest.py --run \
    --project-id "${PROJECT_ID}" \
    --name "Backtest_iteration_${ITERATION}" \
    --file "${STRATEGY_FILE}" \
    --output "${BACKTEST_LOG}"

# Check if backtest succeeded
if [ $? -ne 0 ]; then
    echo "❌ ERROR: Backtest failed"
    # Update iteration_state.json with error
    # ESCALATE_TO_HUMAN or retry
    exit 1
fi

echo "✅ Backtest log saved: ${BACKTEST_LOG}"
```

**Verification after backtest**:

```bash
# Verify backtest log created in hypothesis backtest_logs/
if [ ! -f "${BACKTEST_LOG}" ]; then
    echo "❌ ERROR: Backtest log not created!"
    exit 1
fi

# Verify it's in the correct subdirectory
if [[ "${BACKTEST_LOG}" != STRATEGIES/*/backtest_logs/* ]]; then
    echo "❌ ERROR: Backtest log not in hypothesis backtest_logs/!"
    exit 1
fi

# Verify NOT created at root
if ls -1 backtest_*.json 2>/dev/null; then
    echo "⚠️  WARNING: Backtest files at root - should be in ${HYPOTHESIS_DIR}/backtest_logs/"
fi

# Verify NOT created in PROJECT_LOGS
if ls -1 PROJECT_LOGS/backtest_*.json 2>/dev/null; then
    echo "⚠️  WARNING: Backtest files in PROJECT_LOGS/ - should be in ${HYPOTHESIS_DIR}/backtest_logs/"
fi

echo "✅ Backtest result properly stored in ${HYPOTHESIS_DIR}/backtest_logs/"
```

**Project ID Lifecycle**:
- `/qc-init` → Creates project, saves PROJECT_ID to iteration_state.json
- `/qc-backtest` → Reuses PROJECT_ID (updates code, runs new backtest)
- `/qc-optimize` → Reuses PROJECT_ID (runs optimization)
- `/qc-validate` → Reuses PROJECT_ID (runs validation)

**Result**: One hypothesis = One project with complete history

### Step 7: Parse Results

```bash
# Extract metrics from backtest log in PROJECT_LOGS
BACKTEST_ID=$(cat "${BACKTEST_LOG}" | jq -r '.backtest_id')
SHARPE=$(cat "${BACKTEST_LOG}" | jq -r '.performance.sharpe_ratio')
MAX_DRAWDOWN=$(cat "${BACKTEST_LOG}" | jq -r '.performance.max_drawdown')
TOTAL_RETURN=$(cat "${BACKTEST_LOG}" | jq -r '.performance.total_return')
TOTAL_TRADES=$(cat "${BACKTEST_LOG}" | jq -r '.performance.total_trades')
WIN_RATE=$(cat "${BACKTEST_LOG}" | jq -r '.performance.win_rate')

echo "📊 Results parsed from: ${BACKTEST_LOG}"
```

### Step 8: Apply Decision Framework

```bash
# Decision logic (pseudocode - implement in actual command)
DECISION="UNKNOWN"
REASON=""

# Check overfitting signals first
if (( $(echo "$SHARPE > 3.0" | bc -l) )); then
    DECISION="ESCALATE_TO_HUMAN"
    REASON="Sharpe ratio too perfect ($SHARPE > 3.0), possible overfitting"
elif (( $TOTAL_TRADES < 20 )); then
    DECISION="ESCALATE_TO_HUMAN"
    REASON="Too few trades ($TOTAL_TRADES < 20), unreliable statistics"
elif (( $(echo "$WIN_RATE > 0.75" | bc -l) )); then
    DECISION="ESCALATE_TO_HUMAN"
    REASON="Win rate suspiciously high ($WIN_RATE > 0.75)"
    
# Check minimum viable
elif (( $(echo "$SHARPE < 0.5" | bc -l) )); then
    DECISION="ABANDON_HYPOTHESIS"
    REASON="Sharpe ratio below minimum viable ($SHARPE < 0.5)"
elif (( $(echo "$MAX_DRAWDOWN > 0.40" | bc -l) )); then
    DECISION="ABANDON_HYPOTHESIS"
    REASON="Max drawdown too high ($MAX_DRAWDOWN > 0.40)"
elif (( $TOTAL_TRADES < 30 )); then
    DECISION="ABANDON_HYPOTHESIS"
    REASON="Insufficient trades for statistical significance ($TOTAL_TRADES < 30)"
    
# Check production ready (can skip optimization)
elif (( $(echo "$SHARPE >= 1.0" | bc -l) )) && (( $(echo "$MAX_DRAWDOWN <= 0.30" | bc -l) )) && (( $TOTAL_TRADES >= 100 )); then
    DECISION="PROCEED_TO_VALIDATION"
    REASON="Strong baseline performance (Sharpe $SHARPE, DD $MAX_DRAWDOWN), ready for validation"
    
# Check optimization worthy
elif (( $(echo "$SHARPE >= 0.7" | bc -l) )) && (( $(echo "$MAX_DRAWDOWN <= 0.35" | bc -l) )) && (( $TOTAL_TRADES >= 50 )); then
    DECISION="PROCEED_TO_OPTIMIZATION"
    REASON="Decent performance (Sharpe $SHARPE), worth optimizing parameters"
    
# Marginal case - try optimization
elif (( $(echo "$SHARPE >= 0.5" | bc -l) )); then
    DECISION="PROCEED_TO_OPTIMIZATION"
    REASON="Marginal performance (Sharpe $SHARPE), attempting optimization"
    
else
    DECISION="ABANDON_HYPOTHESIS"
    REASON="Performance does not meet criteria"
fi
```

### Step 9: Update iteration_state.json

**⚠️ CRITICAL**: Update iteration_state.json IN hypothesis directory

```bash
# Update iteration_state.json in hypothesis directory
STATE_FILE="${HYPOTHESIS_DIR}/iteration_state.json"

echo "📝 Updating state file: ${STATE_FILE}"

# Verify state file exists
if [ ! -f "${STATE_FILE}" ]; then
    echo "❌ ERROR: iteration_state.json not found at ${STATE_FILE}"
    exit 1
fi

# Update using Python (safer than sed/awk)
python3 -c "
import json
from datetime import datetime

with open('${STATE_FILE}', 'r') as f:
    state = json.load(f)

# Update phase_results.backtest section
state['phase_results']['backtest'] = {
    'completed': True,
    'timestamp': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
    'backtest_id': '${BACKTEST_ID}',
    'performance': {
        'sharpe_ratio': ${SHARPE},
        'max_drawdown': ${MAX_DRAWDOWN},
        'total_return': ${TOTAL_RETURN},
        'total_trades': ${TOTAL_TRADES},
        'win_rate': ${WIN_RATE}
    },
    'decision': '${DECISION}',
    'decision_reason': '${REASON}'
}

# Update workflow section
state['workflow_state']['current_phase'] = 'backtest'
state['workflow_state']['updated_at'] = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')

# Update decisions_log
state.setdefault('decisions_log', []).append({
    'phase': 'backtest',
    'decision': '${DECISION}',
    'reason': '${REASON}',
    'timestamp': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
})

# Update cost_tracking
state['cost_tracking']['api_calls'] += 1
state['cost_tracking']['backtests_run'] += 1

# Save
with open('${STATE_FILE}', 'w') as f:
    json.dump(state, f, indent=2)

print('✅ State file updated')
"

echo "✅ Updated: ${STATE_FILE}"
```

### Step 10: Git Commit

**⚠️ IMPORTANT**: Stage files with paths from repository root

```bash
# We're at repository root - add files with full paths
git add "${HYPOTHESIS_DIR}/iteration_state.json"
git add "${STRATEGY_FILE}"
git add "${BACKTEST_LOG}"

# Structured commit message
git commit -m "backtest: Complete iteration ${ITERATION} - ${DECISION}

Results:
- Sharpe Ratio: ${SHARPE}
- Max Drawdown: ${MAX_DRAWDOWN}
- Total Return: ${TOTAL_RETURN}
- Total Trades: ${TOTAL_TRADES}
- Win Rate: ${WIN_RATE}
- Backtest ID: ${BACKTEST_ID}

Decision: ${DECISION}
Reason: ${REASON}

Files:
- Strategy: ${STRATEGY_FILE}
- State: ${HYPOTHESIS_DIR}/iteration_state.json
- Log: ${BACKTEST_LOG}

Phase: backtest → $(echo ${DECISION} | tr '[:upper:]' '[:lower:]' | sed 's/_/ /g')
Iteration: ${ITERATION}

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>"

echo "✅ Git commit created"
```

### Step 11: Execute Next Action Autonomously

**⚠️ AUTONOMOUS MODE: AUTO-EXECUTE NEXT PHASE**

Based on decision, **automatically proceed**:

- **PROCEED_TO_OPTIMIZATION** → Auto-run `/qc-optimize` (no user interaction)
- **PROCEED_TO_VALIDATION** → Auto-run `/qc-validate` (no user interaction)
- **ABANDON_HYPOTHESIS** → Display summary and STOP (wait for user to create new hypothesis)
- **ESCALATE_TO_HUMAN** → Display results and STOP (blocker - needs review)

Display summary only for ABANDON or ESCALATE:
```
✅ Backtest complete!

Hypothesis: {name}
Iteration: {iteration}

📊 Results:
  Sharpe Ratio: {sharpe}
  Max Drawdown: {drawdown}%
  Total Return: {return}%
  Total Trades: {trades}
  Win Rate: {win_rate}%

✅ DECISION: {decision}
📝 Reason: {reason}

[If PROCEED decisions: Already executed /qc-optimize or /qc-validate autonomously]
[If ABANDON/ESCALATE: Awaiting user action]
```

## Post-Execution Verification

**After running command, verify file locations:**

```bash
# Should be EMPTY (no .py files except allowed)
ls -1 *.py 2>/dev/null && echo "❌ ERROR: Python files at root!" || echo "✅ No .py files at root"

# Should show strategy file in hypothesis directory
ls "${HYPOTHESIS_DIR}"/*.py 2>/dev/null && echo "✅ Strategy in hypothesis directory" || echo "❌ ERROR: No strategy file!"

# Should show iteration_state.json in hypothesis directory
ls "${HYPOTHESIS_DIR}/iteration_state.json" && echo "✅ State file in hypothesis directory" || echo "❌ ERROR: No state file!"

# Should show backtest log in hypothesis backtest_logs/
ls "${HYPOTHESIS_DIR}"/backtest_logs/backtest_*.json && echo "✅ Backtest log in hypothesis backtest_logs/" || echo "❌ ERROR: No backtest log!"

# Should NOT be at root
ls -1 backtest_*.json 2>/dev/null && echo "❌ ERROR: Backtest files at root!" || echo "✅ No backtest files at root"

# Should NOT be in PROJECT_LOGS (old location)
ls -1 PROJECT_LOGS/backtest_*.json 2>/dev/null && echo "⚠️  WARNING: Backtest files in PROJECT_LOGS/ (should be in hypothesis backtest_logs/)" || echo "✅ No backtest files in PROJECT_LOGS"
```

---

## Common Mistakes to Avoid

❌ **WRONG**:
```bash
# Creating strategy file at root
cat > my_strategy.py <<EOF  # At root!
class MyStrategy(QCAlgorithm):
    ...
EOF
```

✅ **CORRECT**:
```bash
# Find hypothesis directory first
HYPOTHESIS_DIR=$(find STRATEGIES -maxdepth 1 -name "hypothesis_*" -type d | sort | tail -1)

# Create strategy file IN hypothesis directory
STRATEGY_FILE="${HYPOTHESIS_DIR}/my_strategy.py"
cat > "${STRATEGY_FILE}" <<EOF
class MyStrategy(QCAlgorithm):
    ...
EOF
```

❌ **WRONG**:
```bash
# Reading iteration_state.json from root
cat iteration_state.json | jq -r '.hypothesis.name'
```

✅ **CORRECT**:
```bash
# Reading from hypothesis directory
cat "${HYPOTHESIS_DIR}/iteration_state.json" | jq -r '.current_hypothesis.name'
```

❌ **WRONG**:
```bash
# Saving backtest results at root
python SCRIPTS/qc_backtest.py --output backtest_result.json  # At root!
```

❌ **ALSO WRONG**:
```bash
# Saving in PROJECT_LOGS instead of hypothesis directory
mkdir -p PROJECT_LOGS
python SCRIPTS/qc_backtest.py --output PROJECT_LOGS/backtest_result.json  # Wrong location!
```

✅ **CORRECT**:
```bash
# Saving backtest results in hypothesis backtest_logs/
HYPOTHESIS_DIR=$(find STRATEGIES -maxdepth 1 -name "hypothesis_*" -type d | sort | tail -1)
mkdir -p "${HYPOTHESIS_DIR}/backtest_logs"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
python SCRIPTS/qc_backtest.py --output "${HYPOTHESIS_DIR}/backtest_logs/backtest_iteration_1_${TIMESTAMP}.json"
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
│       ├── iteration_state.json              ✅ (updated)
│       ├── config.json                       ✅ (QC configuration)
│       ├── strategy_name.py                  ✅ (created here!)
│       ├── README.md                         ✅ (hypothesis description)
│       ├── backtest_logs/                    ✅ (backtest-specific logs)
│       │   └── backtest_iteration_1_TIMESTAMP.json  ✅ (created here!)
│       ├── helper_classes/                   ✅ (strategy-specific helpers)
│       └── backup_scripts/                   ✅ (version backups)
│
└── PROJECT_LOGS/
    └── (global logs if needed, NOT backtest logs)
```

---

## Notes

- Automatically loads QuantConnect Skill for implementation guidance
- Decision framework uses 4-tier thresholds from iteration_state.json
- Git commit message includes all key metrics for audit trail
- Overfitting signals checked before performance thresholds
- Implementation validation prevents common bugs (NoneType, off-by-one)
- Max 3 fix attempts before escalating to human
- **All hypothesis files MUST be in `STRATEGIES/hypothesis_X/`**
- **Backtest logs MUST be in `PROJECT_LOGS/`**

## Next Steps

Based on decision:
- **PROCEED_TO_OPTIMIZATION**: Run `/qc-optimize` to improve parameters
- **PROCEED_TO_VALIDATION**: Run `/qc-validate` for out-of-sample testing
- **ABANDON_HYPOTHESIS**: Run `/qc-init` to start new hypothesis
- **ESCALATE_TO_HUMAN**: Review results, adjust strategy, rerun backtest

Corresponds to Week 1 Implementation checklist items:
- "Create /qc-backtest command (Phase 2 & 3)"
- "Load QuantConnect Skill"
- "Generate strategy code from hypothesis"
- "Evaluate backtest results (Phase 3 decision logic)"

---

**Version**: 2.0.0 (Fixed - Directory-First Pattern)
**Last Updated**: 2025-11-14
**Critical Fix**: Added mandatory hypothesis directory usage, pre-flight checks, verification
