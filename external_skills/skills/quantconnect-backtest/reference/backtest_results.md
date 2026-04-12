# Complete Backtest Results Structure

**Topic**: Full backtest results schema and metric definitions

**Load when**: Need to understand all available metrics beyond the top 4

---

## Results JSON Structure

```json
{
  "project_id": 26135853,
  "project_name": "MomentumStrategy_20241110",
  "backtest_id": "abc123def456",
  "performance": {
    // Primary Metrics (Phase 3 Decision)
    "sharpe_ratio": 0.85,
    "max_drawdown": 0.22,
    "total_trades": 67,
    "win_rate": 0.42,

    // Secondary Metrics
    "loss_rate": 0.58,
    "profit_factor": 1.8,
    "total_return": 0.45,

    // Risk Metrics
    "alpha": 0.12,
    "beta": 0.95,
    "annual_variance": 0.08,
    "annual_standard_deviation": 0.28,
    "tracking_error": 0.05,

    // Advanced Metrics
    "information_ratio": 1.2,
    "treynor_ratio": 0.15,
    "total_fees": 245.80,
    "estimated_capacity": 50000000
  },
  "qc_url": "https://www.quantconnect.com/project/26135853"
}
```

---

## Metric Definitions

### Primary Metrics (Always Use for Decisions)

#### sharpe_ratio
**Definition**: Risk-adjusted return metric
**Formula**: `(Return - Risk-Free Rate) / Volatility`
**Range**: -∞ to +∞ (typically -2.0 to 3.0)
**QuantConnect Reports**: Annual Sharpe
**Decision Thresholds**:
- < 0.5: Poor (ABANDON)
- 0.5 - 0.7: Marginal
- 0.7 - 1.0: Acceptable (OPTIMIZE)
- 1.0 - 1.5: Good (VALIDATE)
- 1.5 - 2.0: Very Good
- > 3.0: **SUSPICIOUS** (likely overfitting)

#### max_drawdown
**Definition**: Maximum peak-to-trough decline
**Formula**: `(Trough - Peak) / Peak`
**Range**: 0.0 to 1.0 (reported as decimal, e.g., 0.22 = 22%)
**Decision Thresholds**:
- < 0.20: Excellent
- 0.20 - 0.30: Good (acceptable)
- 0.30 - 0.40: Concerning (needs strong Sharpe)
- > 0.40: Too High (ABANDON)

#### total_trades
**Definition**: Number of completed trades
**Range**: 0 to ∞
**Statistical Significance**:
- < 20: Unreliable (ESCALATE or ABANDON)
- 20 - 30: Low confidence (minimum viable)
- 30 - 50: Moderate confidence
- 50 - 100: Good confidence
- 100+: Excellent confidence

#### win_rate
**Definition**: Percentage of winning trades
**Formula**: `Winning Trades / Total Trades`
**Range**: 0.0 to 1.0
**Overfitting Signal**: > 0.75 is suspicious
**Typical by Strategy**:
- Trend Following: 0.30 - 0.50
- Momentum: 0.40 - 0.55
- Mean Reversion: 0.55 - 0.70

---

### Secondary Metrics

#### loss_rate
**Definition**: Percentage of losing trades
**Formula**: `Losing Trades / Total Trades`
**Note**: Always equals `1.0 - win_rate`

#### profit_factor
**Definition**: Ratio of gross profit to gross loss
**Formula**: `Gross Profit / Gross Loss`
**Range**: 0.0 to +∞
**Thresholds**:
- < 1.0: Losing strategy (ABANDON)
- 1.0 - 1.3: Marginal (costs may kill it)
- 1.3 - 1.5: Acceptable
- 1.5 - 2.0: Good
- 2.0 - 3.0: Very Good
- > 3.0: Exceptional (verify no overfitting)

#### total_return
**Definition**: Total cumulative return
**Formula**: `(Final Equity - Initial Equity) / Initial Equity`
**Range**: -1.0 to +∞ (can exceed 1.0 for >100% return)
**Note**: **NOT** the primary metric - use Sharpe instead!
**Why**: High returns with high volatility = bad risk-adjusted performance

---

### Risk Metrics

#### alpha
**Definition**: Excess return vs benchmark
**Formula**: `Strategy Return - (Beta × Benchmark Return)`
**Range**: -∞ to +∞
**Interpretation**:
- Positive alpha = Outperforming benchmark
- Negative alpha = Underperforming benchmark

#### beta
**Definition**: Correlation to benchmark
**Formula**: `Covariance(Strategy, Benchmark) / Variance(Benchmark)`
**Range**: -∞ to +∞ (typically -2.0 to 2.0)
**Interpretation**:
- β = 1.0: Moves with market
- β > 1.0: More volatile than market
- β < 1.0: Less volatile than market
- β < 0.0: Inverse correlation to market

#### annual_variance
**Definition**: Annualized volatility squared
**Formula**: `(Annual Std Dev)²`
**Use**: Portfolio risk calculations

#### annual_standard_deviation
**Definition**: Annualized volatility
**Formula**: `Std Dev of Returns × √252` (for daily data)
**Range**: 0.0 to +∞
**Interpretation**: Higher = more volatile

#### tracking_error
**Definition**: Standard deviation of excess returns vs benchmark
**Formula**: `Std Dev(Strategy Return - Benchmark Return)`
**Use**: Measures consistency vs benchmark

---

### Advanced Metrics

#### information_ratio
**Definition**: Risk-adjusted excess return vs benchmark
**Formula**: `(Strategy Return - Benchmark Return) / Tracking Error`
**Range**: -∞ to +∞
**Interpretation**: Similar to Sharpe, but benchmark-relative

#### treynor_ratio
**Definition**: Return per unit of systematic risk
**Formula**: `(Return - Risk-Free Rate) / Beta`
**Use**: Compare strategies with different beta exposures

#### total_fees
**Definition**: Total transaction costs
**Units**: Currency (USD)
**Interpretation**: High fees can erode profitability

#### estimated_capacity
**Definition**: Maximum capital strategy can handle
**Units**: Currency (USD)
**Interpretation**: Slippage and market impact limits

---

## Common Confusion

### "Why isn't total_return the primary metric?"

**Answer**: Because **risk-adjusted returns matter more than raw returns.**

**Example**:
- Strategy A: 50% return, 40% drawdown, Sharpe 0.4 ❌
- Strategy B: 30% return, 15% drawdown, Sharpe 1.2 ✅

Strategy B is better despite lower returns because it achieves them with much less risk.

### "What if Sharpe is good but win_rate is low?"

**Answer**: This is fine! Trend-following strategies often have 30-40% win rates but large winners.

**Check**: Ensure profit_factor > 1.5 (winners outweigh losers).

### "When should I look at alpha and beta?"

**Answer**: Only if comparing to a specific benchmark (e.g., S&P 500).

For absolute return strategies (not benchmark-relative), focus on Sharpe and drawdown.

---

## Parsing Results in Python

```python
from qc_api import parse_backtest_results

result = api.wait_for_backtest(project_id, backtest_id)
performance = parse_backtest_results(result)

# Access any metric
print(f"Sharpe: {performance['sharpe_ratio']}")
print(f"Alpha: {performance.get('alpha', 'N/A')}")
print(f"Fees: ${performance.get('total_fees', 0):.2f}")
```

**Note**: `parse_backtest_results()` handles missing metrics gracefully.

---

**Related**: See `api_integration.md` for API usage, `backtesting-analysis` skill for interpretation
