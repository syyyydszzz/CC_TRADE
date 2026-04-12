---
description: Generate complete strategy report with all results and decisions
---

Generate a comprehensive strategy development report including all phases, results, and decisions.

This command will:
1. Read iteration_state.json
2. Read decisions_log.md
3. Compile all backtest results
4. Generate markdown report
5. Include performance summaries
6. List all decisions made
7. Provide deployment recommendations

**Usage**:
```
/qc-report
```

**Output**: Creates `strategy_report_<hypothesis_name>_<timestamp>.md`

**Report Sections**:
1. Executive Summary
2. Hypothesis Description
3. Implementation Details
4. In-Sample Results
5. Optimization Results (if applicable)
6. Out-of-Sample Validation
7. Decision History
8. Cost Analysis
9. Deployment Recommendations
10. Risk Assessment

**Example Output**:
```
📄 Generating Strategy Report...

✅ Report generated: strategy_report_RSI_MeanReversion_20251109.md

Summary:
├─ Hypothesis: RSI Mean Reversion with Trend Filter
├─ Status: VALIDATED_COMPLETE
├─ In-Sample Sharpe: 1.45
├─ Out-of-Sample Sharpe: 1.28
├─ Total Iterations: 2
├─ Total Cost: $0.00
└─ Recommendation: APPROVED for paper trading

📊 Open report to view full details
```

**With Screenshots**:
```
/qc-report --with-screenshots
```
Prompts you to provide screenshot paths for visual validation
