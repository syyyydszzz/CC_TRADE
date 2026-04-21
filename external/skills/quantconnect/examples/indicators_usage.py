"""
QuantConnect Indicators Usage Examples
Demonstrates common technical indicators
"""
from AlgorithmImports import *

class IndicatorsDemo(QCAlgorithm):
    """Demonstrates usage of common technical indicators"""

    def Initialize(self):
        self.SetStartDate(2020, 1, 1)
        self.SetEndDate(2023, 12, 31)
        self.SetCash(100000)

        self.symbol = self.AddEquity("SPY", Resolution.Daily).Symbol

        # === Moving Averages ===
        self.sma_20 = self.SMA(self.symbol, 20)  # Simple MA
        self.ema_20 = self.EMA(self.symbol, 20)  # Exponential MA
        self.wma_20 = self.WMA(self.symbol, 20)  # Weighted MA

        # === Momentum Indicators ===
        self.rsi = self.RSI(self.symbol, 14)  # Relative Strength Index
        self.macd = self.MACD(self.symbol, 12, 26, 9)  # MACD
        self.mom = self.MOM(self.symbol, 10)  # Momentum
        self.roc = self.ROC(self.symbol, 10)  # Rate of Change
        self.sto = self.STO(self.symbol, 14, 3, 3)  # Stochastic

        # === Volatility Indicators ===
        self.bb = self.BB(self.symbol, 20, 2)  # Bollinger Bands
        self.atr = self.ATR(self.symbol, 14)  # Average True Range
        self.std = self.STD(self.symbol, 20)  # Standard Deviation

        # === Volume Indicators ===
        self.obv = self.OBV(self.symbol)  # On-Balance Volume
        self.ad = self.AD(self.symbol)  # Accumulation/Distribution

        # Warm up all indicators
        self.SetWarmUp(50)

    def OnData(self, data):
        """Demonstrate accessing indicator values"""

        if self.IsWarmingUp:
            return

        # Always check if indicators are ready
        if not self.sma_20.IsReady:
            return

        # === Accessing Moving Average Values ===
        sma_value = self.sma_20.Current.Value
        ema_value = self.ema_20.Current.Value

        # === Accessing Momentum Indicators ===
        rsi_value = self.rsi.Current.Value  # 0-100
        macd_signal = self.macd.Signal.Current.Value
        macd_hist = self.macd.Current.Value - macd_signal
        momentum_value = self.mom.Current.Value

        # === Accessing Bollinger Bands ===
        bb_upper = self.bb.UpperBand.Current.Value
        bb_middle = self.bb.MiddleBand.Current.Value
        bb_lower = self.bb.LowerBand.Current.Value

        # === Accessing Volatility ===
        atr_value = self.atr.Current.Value
        std_value = self.std.Current.Value

        # Example strategy: Bollinger Band bounce with RSI confirmation
        if data.ContainsKey(self.symbol):
            price = data[self.symbol].Close

            # Buy signal: Price at lower band + RSI oversold
            if not self.Portfolio.Invested:
                if price < bb_lower and rsi_value < 30:
                    self.SetHoldings(self.symbol, 1.0)
                    self.Debug(f"BUY: Price={price:.2f}, BB_Lower={bb_lower:.2f}, RSI={rsi_value:.2f}")

            # Sell signal: Price at upper band or RSI overbought
            else:
                if price > bb_upper or rsi_value > 70:
                    self.Liquidate(self.symbol)
                    self.Debug(f"SELL: Price={price:.2f}, BB_Upper={bb_upper:.2f}, RSI={rsi_value:.2f}")

        # Optional: Plot indicators
        self.Plot("Indicators", "RSI", rsi_value)
        self.Plot("Indicators", "SMA", sma_value)
