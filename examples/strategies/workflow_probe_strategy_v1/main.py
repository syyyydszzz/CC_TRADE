# Workflow Probe Strategy V1
# Purpose: Pipeline validation (Claude Code + skill + OpenSpec + qc-mcp)
# NOT intended for live trading or alpha generation.
#
# Logic: SPY daily SMA(20)/SMA(50) crossover
#   Entry:  SMA(20) crosses above SMA(50) → long SPY 100%
#   Exit:   SMA(20) crosses below SMA(50) → liquidate

from AlgorithmImports import *


class WorkflowProbeStrategyV1(QCAlgorithm):

    def Initialize(self):
        # Backtest window
        self.SetStartDate(2020, 1, 1)
        self.SetEndDate(2022, 12, 31)
        self.SetCash(100_000)

        # Universe: single liquid equity
        self.symbol = self.AddEquity("SPY", Resolution.Daily).Symbol

        # Indicators
        self.fast = self.SMA(self.symbol, 20, Resolution.Daily)
        self.slow = self.SMA(self.symbol, 50, Resolution.Daily)

        # Warm-up: enough bars for the slow SMA to be ready
        self.SetWarmUp(50, Resolution.Daily)

        # Track previous crossover state to detect cross events
        self._prev_fast_above = None

    def OnData(self, data: Slice):
        # Skip until indicators are warmed up
        if self.IsWarmingUp:
            return

        # Skip if indicators are not ready or symbol not in slice
        if not self.fast.IsReady or not self.slow.IsReady:
            return
        if self.symbol not in data.Bars:
            return

        fast_val = self.fast.Current.Value
        slow_val = self.slow.Current.Value
        fast_above = fast_val > slow_val

        # Detect crossover on first bar after warm-up
        if self._prev_fast_above is None:
            self._prev_fast_above = fast_above
            return

        # Golden cross: fast crosses above slow → go long
        if fast_above and not self._prev_fast_above:
            if not self.Portfolio[self.symbol].Invested:
                self.SetHoldings(self.symbol, 1.0)
                self.Log(f"LONG entry: SMA20={fast_val:.2f} > SMA50={slow_val:.2f}")

        # Death cross: fast crosses below slow → exit
        elif not fast_above and self._prev_fast_above:
            if self.Portfolio[self.symbol].Invested:
                self.Liquidate(self.symbol)
                self.Log(f"EXIT: SMA20={fast_val:.2f} < SMA50={slow_val:.2f}")

        self._prev_fast_above = fast_above

    def OnEndOfAlgorithm(self):
        self.Log(
            f"Workflow Probe V1 complete | "
            f"Final portfolio value: {self.Portfolio.TotalPortfolioValue:.2f}"
        )
