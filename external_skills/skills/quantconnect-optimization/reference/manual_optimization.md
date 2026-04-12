# Manual Parameter Grid Optimization

**Level 2 Reference** - Load on-demand when implementing manual optimization (free tier approach).

---

## Overview

Manual parameter grid optimization uses sequential backtests via the backtest API instead of the native QC optimization engine. This approach is **free** (no subscription required) but slower.

### When to Use

- Free tier users (no Quant Researcher subscription)
- Small parameter grids (< 20 combinations)
- MVP testing before investing in paid tier
- Full control over parameter combinations needed

---

## Implementation

```python
import sys
sys.path.insert(0, 'SCRIPTS')
from qc_api import QuantConnectAPI
import json
import time

def manual_optimize(project_id, param_grid, strategy_template):
    """
    Manual parameter optimization using sequential backtests.

    Args:
        project_id: QC project ID (from iteration_state.json)
        param_grid: List of parameter combinations
        strategy_template: Strategy code with {param} placeholders

    Returns:
        best_params: Best parameter combination
        best_sharpe: Best Sharpe ratio achieved
        all_results: All parameter results
    """
    api = QuantConnectAPI()

    all_results = []
    best_sharpe = -999
    best_params = None

    for i, params in enumerate(param_grid):
        print(f"Testing combination {i+1}/{len(param_grid)}: {params}")

        # Modify strategy code with current parameters
        strategy_code = strategy_template.format(**params)

        # Upload modified strategy
        api.upload_file(project_id, strategy_code, "Main.py")

        # Run backtest
        backtest = api.create_backtest(project_id, f"Optimize_{i+1}")
        backtest_id = backtest['backtestId']

        # Wait for completion
        result = api.wait_for_backtest(project_id, backtest_id, timeout=600)

        # Parse results
        performance = api.parse_backtest_results(result)
        sharpe = performance['sharpe_ratio']

        all_results.append({
            'params': params,
            'sharpe': sharpe,
            'drawdown': performance['max_drawdown'],
            'trades': performance['total_trades']
        })

        # Track best
        if sharpe > best_sharpe:
            best_sharpe = sharpe
            best_params = params

        # Rate limit (avoid API throttling)
        time.sleep(2)

    return best_params, best_sharpe, all_results
```

---

## Parameter Grid Example

```python
# Define parameter grid
param_grid = [
    {'sma_period': 10, 'stop_loss': 0.03},
    {'sma_period': 14, 'stop_loss': 0.03},
    {'sma_period': 20, 'stop_loss': 0.03},
    {'sma_period': 10, 'stop_loss': 0.05},
    {'sma_period': 14, 'stop_loss': 0.05},
    {'sma_period': 20, 'stop_loss': 0.05},
]

# Strategy template with placeholders
strategy_template = '''
class Strategy(QCAlgorithm):
    def Initialize(self):
        self.SetStartDate(2020, 1, 1)
        self.SetEndDate(2023, 12, 31)
        self.SetCash(100000)

        self.symbol = self.AddEquity("SPY", Resolution.Daily).Symbol
        self.sma = self.SMA(self.symbol, {sma_period}, Resolution.Daily)
        self.stop_loss_pct = {stop_loss}

    def OnData(self, data):
        if not self.sma.IsReady:
            return

        if not data.ContainsKey(self.symbol):
            return

        bar = data[self.symbol]
        if bar is None:
            return

        price = bar.Close

        # Entry logic
        if not self.Portfolio.Invested:
            if price > self.sma.Current.Value:
                self.SetHoldings(self.symbol, 1.0)
                self.entry_price = price

        # Exit logic (stop loss)
        if self.Portfolio.Invested:
            if price < self.entry_price * (1 - self.stop_loss_pct):
                self.Liquidate()
'''

# Run optimization
best_params, best_sharpe, all_results = manual_optimize(
    project_id=project_id,  # From iteration_state.json
    param_grid=param_grid,
    strategy_template=strategy_template
)

print(f"Best params: {best_params}")
print(f"Best Sharpe: {best_sharpe}")
```

---

## Best Practices

### 1. Start Small

Test with 3-6 combinations first:
```python
# Small grid for testing
param_grid = [
    {'sma_period': 10},
    {'sma_period': 20},
    {'sma_period': 30},
]
```

### 2. Limit Parameter Count

- **1-2 parameters**: Good (fast, less overfitting risk)
- **3-4 parameters**: Acceptable (watch for overfitting)
- **5+ parameters**: Risky (high overfitting risk, slow)

### 3. Use Reasonable Ranges

```python
# GOOD: Reasonable ranges
param_grid = [
    {'rsi_period': 10},   # Min reasonable
    {'rsi_period': 14},   # Standard
    {'rsi_period': 20},   # Max reasonable
]

# BAD: Too wide, overfitting risk
param_grid = [
    {'rsi_period': 2},    # Too low
    {'rsi_period': 100},  # Too high
]
```

### 4. Monitor Execution Time

- **3x3 grid (9 combinations)**: ~15-20 minutes
- **5x5 grid (25 combinations)**: ~45-60 minutes
- **10x10 grid (100 combinations)**: ~3-5 hours

Plan accordingly and use small grids for MVP.

---

## Comparison: Manual vs Native QC API

| Feature | Manual Grid | Native QC API |
|---------|-------------|---------------|
| **Cost** | Free (backtest API only) | Paid (Quant Researcher tier + QCC credits) |
| **Speed** | Slow (sequential) | Fast (parallel) |
| **Control** | Full control | Limited control |
| **Setup** | Simple | Complex |
| **Best for** | MVP, small grids | Production, large grids |

---

## Complete Workflow Example

See `examples/complete_workflow.md` for end-to-end manual optimization example.

---

**Load this reference when**: Implementing manual optimization for free tier users or MVP testing.
