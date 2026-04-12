# Complete Workflow Examples

**Topic**: End-to-end `/qc-backtest` command workflows

**Load when**: Implementing `/qc-backtest` command or understanding complete integration

---

## Example 1: Basic `/qc-backtest` Workflow

### Step-by-Step Execution

```bash
# Step 1: Read hypothesis from iteration_state.json
HYPOTHESIS=$(cat iteration_state.json | jq -r '.hypothesis.description')
PROJECT_ID=$(cat iteration_state.json | jq -r '.project.project_id')

echo "Hypothesis: $HYPOTHESIS"
echo "Project ID: $PROJECT_ID"

# Step 2: Generate strategy code (Claude generates based on hypothesis)
# Output: strategy.py

# Step 3: Run backtest via wrapper script
python SCRIPTS/qc_backtest.py --run \
    --name "Hypothesis_3_Momentum" \
    --file strategy.py \
    --output PROJECT_LOGS/backtest_result.json

# Step 4: Evaluate results and make decision
python3 << 'EOF'
import json, sys
sys.path.insert(0, 'SCRIPTS')
from decision_logic import evaluate_backtest, route_decision

# Load backtest results
with open('PROJECT_LOGS/backtest_result.json') as f:
    results = json.load(f)

# Load iteration state
with open('iteration_state.json') as f:
    state = json.load(f)

# Evaluate backtest metrics
decision, reason, details = evaluate_backtest(
    results['performance'],
    state['thresholds']
)

# Determine next action
routing = route_decision(
    current_phase="backtest",
    decision=decision,
    iteration=state['workflow']['iteration']
)

print(f"DECISION={decision}")
print(f"REASON={reason}")
print(f"NEXT_ACTION={routing['next_action']}")
print(f"NEXT_PHASE={routing['next_phase']}")
EOF

# Step 5: Update iteration_state.json with decision
# (Claude updates state file)

# Step 6: Git commit
git add iteration_state.json strategy.py PROJECT_LOGS/backtest_result.json
git commit -m "backtest: Complete iteration 1 - PROCEED_TO_OPTIMIZATION

Results:
- Sharpe: 0.85
- Drawdown: 22%
- Trades: 67
- Win Rate: 42%
- Profit Factor: 1.8

Decision: PROCEED_TO_OPTIMIZATION
Reason: Decent baseline performance, optimization likely to improve further"
```

---

## Example 2: ABANDON_HYPOTHESIS Decision

### Scenario: Poor Sharpe Ratio

**Backtest Results**:
```json
{
  "performance": {
    "sharpe_ratio": 0.3,
    "max_drawdown": 0.38,
    "total_trades": 89,
    "win_rate": 0.35,
    "profit_factor": 1.1
  }
}
```

**Decision Logic**:
```python
decision, reason, details = evaluate_backtest(
    results['performance'],
    state['thresholds']
)

# Output:
# decision = "ABANDON_HYPOTHESIS"
# reason = "Sharpe ratio 0.3 below minimum threshold 0.5"
```

**Routing**:
```python
routing = route_decision("backtest", "ABANDON_HYPOTHESIS", iteration=1)

# Output:
# {
#   "next_phase": "research",
#   "next_action": "START_NEW_HYPOTHESIS",
#   "iteration": 1
# }
```

**Git Commit**:
```bash
git commit -m "backtest: Iteration 1 - ABANDON_HYPOTHESIS

Results:
- Sharpe: 0.30 ❌ (threshold: 0.50)
- Drawdown: 38% ⚠️
- Trades: 89 ✓
- Win Rate: 35%
- Profit Factor: 1.1

Decision: ABANDON_HYPOTHESIS
Reason: Poor risk-adjusted returns, not worth optimizing

Next: Start new hypothesis with different approach"
```

---

## Example 3: ESCALATE_TO_HUMAN Decision

### Scenario: Suspiciously Good Results

**Backtest Results**:
```json
{
  "performance": {
    "sharpe_ratio": 4.2,
    "max_drawdown": 0.05,
    "total_trades": 25,
    "win_rate": 0.88,
    "profit_factor": 5.8
  }
}
```

**Decision Logic**:
```python
decision, reason, details = evaluate_backtest(
    results['performance'],
    state['thresholds']
)

# Output:
# decision = "ESCALATE_TO_HUMAN"
# reason = "Multiple overfitting signals: Sharpe=4.2 (>3.0), WinRate=0.88 (>0.75), Trades=25 (<30)"
```

**What to Check**:
1. Look-ahead bias (using future data)
2. Data leakage (indicator peeking)
3. Unrealistic assumptions (no slippage, instant fills)
4. Bug in strategy code

**Example Look-Ahead Bias**:
```python
# BUG: Using tomorrow's close for today's entry decision
def OnData(self, data):
    tomorrow_close = self.History(self.symbol, 2, Resolution.Daily)['close'][-1]
    if tomorrow_close > price:  # This is future data!
        self.SetHoldings(self.symbol, 1.0)
```

**Fix**:
```python
def OnData(self, data):
    # Only use data available at decision time
    if self.sma.Current.Value > price:
        self.SetHoldings(self.symbol, 1.0)
```

---

## Example 4: PROCEED_TO_VALIDATION (Skip Optimization)

### Scenario: Already Excellent Results

**Backtest Results**:
```json
{
  "performance": {
    "sharpe_ratio": 1.35,
    "max_drawdown": 0.18,
    "total_trades": 142,
    "win_rate": 0.53,
    "profit_factor": 2.1
  }
}
```

**Decision Logic**:
```python
decision, reason, details = evaluate_backtest(
    results['performance'],
    state['thresholds']
)

# Output:
# decision = "PROCEED_TO_VALIDATION"
# reason = "Excellent baseline performance (Sharpe 1.35), skip optimization"
```

**Routing**:
```python
routing = route_decision("backtest", "PROCEED_TO_VALIDATION", iteration=1)

# Output:
# {
#   "next_phase": "validation",
#   "next_action": "RUN_VALIDATION",
#   "iteration": 1
# }
```

**Next Step**: Run `/qc-validate` (skip `/qc-optimize`)

---

## Example 5: Python API Integration

### Complete Python Workflow

```python
import json
import sys
sys.path.insert(0, 'SCRIPTS')
from qc_api import QuantConnectAPI, parse_backtest_results, find_project_by_name
from decision_logic import evaluate_backtest, route_decision

# Initialize
api = QuantConnectAPI()

# Read state
with open('iteration_state.json') as f:
    state = json.load(f)

hypothesis_name = state['hypothesis']['name']
project_name = f"H{state['workflow']['hypothesis_number']}_{hypothesis_name}"

# Create or reuse project
project_id = find_project_by_name(project_name)
if not project_id:
    project_id = api.create_project(project_name)
    print(f"Created new project: {project_id}")
else:
    print(f"Reusing existing project: {project_id}")

# Upload strategy
with open('strategy.py') as f:
    code = f.read()
api.upload_file(project_id, code, "Main.py")
print("Strategy uploaded")

# Run backtest
backtest = api.create_backtest(project_id, f"Iteration_{state['workflow']['iteration']}")
backtest_id = backtest['backtestId']
print(f"Backtest started: {backtest_id}")

# Wait for completion
result = api.wait_for_backtest(project_id, backtest_id, timeout=600)

if 'error' in result:
    print(f"❌ Backtest failed: {result['error']}")
    sys.exit(1)

# Parse results
performance = parse_backtest_results(result)
print("\n=== Results ===")
print(f"Sharpe: {performance['sharpe_ratio']:.2f}")
print(f"Drawdown: {performance['max_drawdown']:.2%}")
print(f"Trades: {performance['total_trades']}")
print(f"Win Rate: {performance['win_rate']:.2%}")
print(f"Profit Factor: {performance['profit_factor']:.2f}")

# Save results
output = {
    'project_id': project_id,
    'project_name': project_name,
    'backtest_id': backtest_id,
    'performance': performance,
    'qc_url': f"https://www.quantconnect.com/project/{project_id}"
}
with open('PROJECT_LOGS/backtest_result.json', 'w') as f:
    json.dump(output, f, indent=2)

# Evaluate and route
decision, reason, details = evaluate_backtest(performance, state['thresholds'])
routing = route_decision("backtest", decision, state['workflow']['iteration'])

print(f"\n=== Decision ===")
print(f"Decision: {decision}")
print(f"Reason: {reason}")
print(f"Next Action: {routing['next_action']}")
print(f"Next Phase: {routing['next_phase']}")

# Update state (simplified - full logic would merge properly)
state['backtest'] = {
    'project_id': project_id,
    'backtest_id': backtest_id,
    'performance': performance,
    'decision': decision,
    'reason': reason
}
state['workflow']['current_phase'] = routing['next_phase']
state['workflow']['iteration'] = routing['iteration']

with open('iteration_state.json', 'w') as f:
    json.dump(state, f, indent=2)

print("\n✅ Workflow complete")
```

---

## Example 6: Handling 0 Trades

### Problem: Strategy never triggers

**Initial Strategy** (too restrictive):
```python
def OnData(self, data):
    if not self.sma.IsReady or not self.rsi.IsReady:
        return

    price = data[self.symbol].Close
    volume = data[self.symbol].Volume

    # TOO MANY CONDITIONS
    if (price > self.sma.Current.Value and
        self.rsi.Current.Value < 30 and
        volume > 2.0 * self.avg_volume and
        self.Time.hour == 10):  # Only trade at 10am
        self.SetHoldings(self.symbol, 1.0)
```

**Result**: 0 trades

**Fix** (simplify):
```python
def OnData(self, data):
    if not self.sma.IsReady:
        return

    price = data[self.symbol].Close

    # SIMPLIFIED - Higher probability of triggering
    if price > self.sma.Current.Value:
        self.SetHoldings(self.symbol, 1.0)
    elif price < self.sma.Current.Value:
        self.Liquidate()
```

**Result**: 67 trades ✓

---

## Example 7: Iteration Loop

### Multiple Hypothesis Testing

```bash
# Hypothesis 1: Simple momentum
HYPOTHESIS="Buy when price > 20-day SMA, sell when below"
# Run backtest → ABANDON (Sharpe 0.4)

# Hypothesis 2: RSI mean reversion
HYPOTHESIS="Buy RSI < 30, sell RSI > 70"
# Run backtest → PROCEED_TO_OPTIMIZATION (Sharpe 0.9)

# Hypothesis 3: Breakout strategy
HYPOTHESIS="Buy on 20-day high breakout"
# Run backtest → ESCALATE (Sharpe 3.5, suspicious)
```

---

## Integration Points

### 1. `/qc-backtest` Command
- Reads `iteration_state.json`
- Generates `strategy.py`
- Calls `qc_backtest.py --run`
- Evaluates via `decision_logic.py`
- Updates `iteration_state.json`
- Commits to git

### 2. Decision Framework
- `evaluate_backtest()` - Apply thresholds
- `route_decision()` - Determine next phase
- Returns structured decision + routing

### 3. Git Workflow
- Structured commit messages
- Include metrics in commit body
- Tag decision and reason
- Reference hypothesis number

---

**Related**: See `api_integration.md` for API details, `error_handling.md` for debugging
