"""
Basic QuantConnect Algorithm Example
Minimal working momentum strategy using RSI
"""
from AlgorithmImports import *

class BasicMomentumAlgorithm(QCAlgorithm):
    """
    Simple RSI-based momentum strategy
    - Buy when RSI < 30 (oversold)
    - Sell when RSI > 70 (overbought)
    """

    def Initialize(self):
        # Set backtest period
        self.SetStartDate(2020, 1, 1)
        self.SetEndDate(2023, 12, 31)
        self.SetCash(100000)

        # Add SPY (S&P 500 ETF)
        self.symbol = self.AddEquity("SPY", Resolution.Daily).Symbol

        # Create RSI indicator (14-period)
        self.rsi = self.RSI(self.symbol, 14, Resolution.Daily)

        # Set warm-up period to ensure indicator is ready
        self.SetWarmUp(14)

    def OnData(self, data):
        """Called every time new data arrives"""

        # Don't trade during warm-up period
        if self.IsWarmingUp:
            return

        # Ensure RSI is ready
        if not self.rsi.IsReady:
            return

        # Ensure data is available for our symbol
        if not data.ContainsKey(self.symbol):
            return

        # Get current RSI value
        rsi_value = self.rsi.Current.Value

        # Entry logic: Buy when oversold
        if not self.Portfolio.Invested:
            if rsi_value < 30:
                self.SetHoldings(self.symbol, 1.0)  # Go 100% long
                self.Debug(f"BUY: RSI = {rsi_value:.2f}")

        # Exit logic: Sell when overbought
        else:
            if rsi_value > 70:
                self.Liquidate(self.symbol)
                self.Debug(f"SELL: RSI = {rsi_value:.2f}")
