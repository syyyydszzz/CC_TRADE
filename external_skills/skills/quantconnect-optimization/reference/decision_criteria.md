# Phase 4 Decision Criteria

**Level 2 Reference** - Load on-demand when implementing Phase 4 decision logic.

---

## Overview

After optimization completes, Phase 4 evaluates improvement and routes to next action:
- Proceed to validation (Phase 5)
- Use baseline parameters
- Escalate to human (overfitting detected)

---

## Decision Integration

```python
import sys
sys.path.insert(0, 'SCRIPTS')
from decision_logic import evaluate_optimization, route_decision

# Load baseline and optimized results
baseline_sharpe = state['phase_results']['backtest']['performance']['sharpe_ratio']
optimized_sharpe = best_sharpe

# Calculate improvement
improvement_pct = (optimized_sharpe - baseline_sharpe) / baseline_sharpe

# Evaluate
decision, reason, details = evaluate_optimization(
    baseline_sharpe=baseline_sharpe,
    optimized_sharpe=optimized_sharpe,
    improvement_pct=improvement_pct,
    thresholds=state['thresholds']
)

print(f"Decision: {decision}")
print(f"Reason: {reason}")

# Route to next phase
routing = route_decision(
    current_phase="optimization",
    decision=decision,
    iteration=state['workflow']['iteration']
)

print(f"Next Action: {routing['next_action']}")
```

---

## Decision Thresholds

From `iteration_state.json` thresholds:

| Improvement | Decision | Rationale | Next Action |
|-------------|----------|-----------|-------------|
| **< 0%** | `USE_BASELINE_PARAMS` | Optimization made it worse | Validation with baseline |
| **0% - 5%** | `USE_BASELINE_PARAMS` | Improvement too small to matter | Validation with baseline |
| **5% - 30%** | `PROCEED_TO_VALIDATION` | Good improvement, reasonable | Validation with optimized params |
| **> 30%** | `ESCALATE_TO_HUMAN` | Suspicious, likely overfit | Human review required |

---

## Possible Decisions

### 1. USE_BASELINE_PARAMS

**When**: Improvement ≤ 5%

**Reason**: Optimization didn't provide meaningful improvement

**Next Action**: `/qc-validate` with **baseline** parameters

**Example**:
```
Baseline Sharpe: 0.85
Optimized Sharpe: 0.86
Improvement: 1.2% → USE_BASELINE_PARAMS
```

### 2. PROCEED_TO_VALIDATION

**When**: 5% < Improvement ≤ 30%

**Reason**: Good improvement without overfitting risk

**Next Action**: `/qc-validate` with **optimized** parameters

**Example**:
```
Baseline Sharpe: 0.85
Optimized Sharpe: 1.05
Improvement: 23.5% → PROCEED_TO_VALIDATION
```

### 3. ESCALATE_TO_HUMAN

**When**: Improvement > 30%

**Reason**: Excessive improvement indicates possible overfitting

**Next Action**: Human review, likely use **baseline** parameters

**Example**:
```
Baseline Sharpe: 0.85
Optimized Sharpe: 1.30
Improvement: 52.9% → ESCALATE_TO_HUMAN (likely overfit!)
```

---

## Overfitting Detection

### Warning Signs

1. **Improvement > 30%** - Suspicious
2. **Sharp parameter peaks** - Indicates curve-fitting
3. **Too many parameters** - More parameters = higher overfit risk
4. **Narrow optimal range** - e.g., works at period=14 but fails at 13 and 15

### What to Do

If overfitting detected:
1. **Use baseline parameters** (safer)
2. **Reduce parameter count** (fewer DOF)
3. **Widen parameter ranges** (test robustness)
4. **Check out-of-sample** (validation will reveal truth)

---

## Integration with iteration_state.json

After decision made, update:

```python
state['phase_results']['optimization'] = {
    'status': 'completed',
    'baseline_sharpe': baseline_sharpe,
    'optimized_sharpe': optimized_sharpe,
    'improvement_pct': improvement_pct,
    'best_params': best_params,
    'decision': decision,
    'decision_reason': reason,
    'timestamp': datetime.utcnow().isoformat() + 'Z'
}

state['decisions_log'].append({
    'phase': 'optimization',
    'decision': decision,
    'reason': reason,
    'improvement': improvement_pct,
    'timestamp': datetime.utcnow().isoformat() + 'Z'
})

state['workflow']['current_phase'] = 'validation'  # If proceeding
state['workflow']['next_action'] = routing['next_action']

# Save
with open('iteration_state.json', 'w') as f:
    json.dump(state, f, indent=2)
```

---

## Customizing Thresholds

Thresholds can be adjusted in `iteration_state.json`:

```json
{
  "thresholds": {
    "optimization": {
      "min_improvement_pct": 0.05,
      "max_improvement_pct": 0.30,
      "overfitting_threshold": 0.30
    }
  }
}
```

**Conservative** (less overfitting risk):
- min_improvement: 10%
- max_improvement: 20%

**Aggressive** (accept more risk):
- min_improvement: 2%
- max_improvement: 50%

---

**Load this reference when**: Implementing Phase 4 decision logic or customizing thresholds.
