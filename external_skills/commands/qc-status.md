---
description: Check current status of the autonomous workflow
---

Display the current status of the autonomous strategy development workflow.

This command will:
1. Read iteration_state.json
2. Display current hypothesis
3. Show current phase and progress
4. Display recent decisions
5. Show cost tracking
6. List next steps

**Usage**:
```
/qc-status
```

**Output Example**:
```
═══════════════════════════════════════════════════════════
AUTONOMOUS WORKFLOW STATUS
═══════════════════════════════════════════════════════════

📋 Current Hypothesis: RSI Mean Reversion with Trend Filter
   Description: Buy on RSI oversold + BB lower, only in uptrends
   Status: backtest_complete
   Created: 2025-11-09 22:30:00

🔧 Project Info:
   Project ID: 26120873
   Name: TestStrategy_Phase1_VALIDATED
   File: test_strategy.py

📍 Current Phase: validation
   Completed Phases: research → implementation → backtest

📊 Latest Backtest:
   Backtest ID: 691852b80fe50a0015e01c1737a2e654
   Sharpe: 0.0 | Drawdown: 0% | Return: 0% | Trades: 0
   Decision: ESCALATE
   Reason: Too few trades (0 < 10), insufficient data

🔄 Optimization:
   Status: not_started
   Attempts: 0/3

✓ Validation:
   Status: pending
   OOS Test: not_run

📈 Progress:
   Iteration: 1 / 3
   API Calls: 5
   Backtests: 1
   Cost: $0.00

📝 Recent Decisions:
   [22:45] ESCALATE - Too few trades, review entry conditions

🎯 Next Steps:
   1. Relax entry conditions (RSI < 35 instead of 30)
   2. Test on different time period (2020-2022)
   3. Consider removing 200 SMA filter

═══════════════════════════════════════════════════════════

💡 Suggested Actions:
   - Modify strategy: test_strategy.py
   - Run new backtest: /qc-backtest
   - Start new hypothesis: /qc-init
```

**With Details**:
```
/qc-status --detailed
```
Shows full iteration_state.json content and all decisions from decisions_log.md
