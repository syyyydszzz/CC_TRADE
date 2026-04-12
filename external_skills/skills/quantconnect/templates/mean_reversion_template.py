"""
Mean Reversion Strategy Template
Customizable mean reversion trading strategy
"""
from AlgorithmImports import *

class MeanReversionTemplate(QCAlgorithm):
    """
    Mean Reversion Strategy Template

    CUSTOMIZE THESE PARAMETERS:
    - BB_PERIOD: Bollinger Bands period
    - BB_STD: Standard deviations for bands
    - RSI_PERIOD: RSI period
    - RSI_OVERSOLD: Buy when RSI below this + price at lower band
    - MEAN_REVERSION_TARGET: Exit when price returns to mean (middle band or SMA)
    - STOP_LOSS: Stop loss percentage
    """

    # === PARAMETERS TO CUSTOMIZE ===
    BB_PERIOD = 20
    BB_STD = 2.0
    RSI_PERIOD = 14
    RSI_OVERSOLD = 35
    POSITION_SIZE = 1.0
    STOP_LOSS = 0.08  # 8% stop loss
    REVERSION_TO_MEAN = True  # Exit at mean (True) or upper band (False)

    def Initialize(self):
        # Backtest period
        self.SetStartDate(2020, 1, 1)
        self.SetEndDate(2023, 12, 31)
        self.SetCash(100000)

        # Add security
        self.symbol = self.AddEquity("SPY", Resolution.Daily).Symbol

        # Mean reversion indicators
        self.bb = self.BB(self.symbol, self.BB_PERIOD, self.BB_STD)
        self.rsi = self.RSI(self.symbol, self.RSI_PERIOD)
        self.sma = self.SMA(self.symbol, self.BB_PERIOD)  # Same as BB middle

        # Risk tracking
        self.entry_price = None

        # Warm up
        self.SetWarmUp(max(self.BB_PERIOD, self.RSI_PERIOD))

    def OnData(self, data):
        if self.IsWarmingUp:
            return

        if not self.bb.IsReady or not self.rsi.IsReady:
            return

        if not data.ContainsKey(self.symbol):
            return

        price = data[self.symbol].Close
        bb_lower = self.bb.LowerBand.Current.Value
        bb_middle = self.bb.MiddleBand.Current.Value
        bb_upper = self.bb.UpperBand.Current.Value

        # === ENTRY LOGIC (CUSTOMIZE THIS) ===
        if not self.Portfolio.Invested:
            # Mean reversion buy signal:
            # 1. Price touches or breaches lower Bollinger Band (oversold)
            # 2. RSI confirms oversold condition

            price_at_lower_band = price <= bb_lower
            rsi_oversold = self.rsi.Current.Value < self.RSI_OVERSOLD

            if price_at_lower_band and rsi_oversold:
                self.SetHoldings(self.symbol, self.POSITION_SIZE)
                self.entry_price = price
                self.Debug(f"BUY (mean reversion): Price={price:.2f}, BB_Lower={bb_lower:.2f}, RSI={self.rsi.Current.Value:.2f}")

        # === EXIT LOGIC (CUSTOMIZE THIS) ===
        else:
            # Calculate P&L
            pnl_pct = (price - self.entry_price) / self.entry_price if self.entry_price else 0

            # Exit condition 1: Stop loss
            if pnl_pct < -self.STOP_LOSS:
                self.Liquidate(self.symbol)
                self.Debug(f"STOP LOSS: Price={price:.2f}, Loss={pnl_pct:.2%}")
                self.entry_price = None

            # Exit condition 2: Mean reversion complete
            elif self.REVERSION_TO_MEAN:
                # Exit at middle band (mean)
                if price >= bb_middle:
                    self.Liquidate(self.symbol)
                    self.Debug(f"SELL (mean): Price={price:.2f}, BB_Middle={bb_middle:.2f}, Profit={pnl_pct:.2%}")
                    self.entry_price = None

            else:
                # Exit at upper band (overbought)
                if price >= bb_upper:
                    self.Liquidate(self.symbol)
                    self.Debug(f"SELL (upper band): Price={price:.2f}, BB_Upper={bb_upper:.2f}, Profit={pnl_pct:.2%}")
                    self.entry_price = None


# === VARIATION: RSI Mean Reversion ===

class RSIMeanReversion(QCAlgorithm):
    """
    Simpler mean reversion using RSI only
    Buy extreme oversold, sell mean/overbought
    """

    RSI_PERIOD = 14
    RSI_EXTREME_OVERSOLD = 25  # Extreme oversold
    RSI_MEAN = 50  # Mean
    RSI_OVERBOUGHT = 70  # Overbought

    def Initialize(self):
        self.SetStartDate(2020, 1, 1)
        self.SetEndDate(2023, 12, 31)
        self.SetCash(100000)

        self.symbol = self.AddEquity("SPY", Resolution.Daily).Symbol
        self.rsi = self.RSI(self.symbol, self.RSI_PERIOD)

        self.SetWarmUp(self.RSI_PERIOD)

    def OnData(self, data):
        if self.IsWarmingUp or not self.rsi.IsReady:
            return

        if not data.ContainsKey(self.symbol):
            return

        rsi_value = self.rsi.Current.Value

        # Buy when extremely oversold
        if not self.Portfolio.Invested:
            if rsi_value < self.RSI_EXTREME_OVERSOLD:
                self.SetHoldings(self.symbol, 1.0)
                self.Debug(f"BUY: RSI={rsi_value:.2f} (extreme oversold)")

        # Sell when reverts to mean or overbought
        else:
            if rsi_value > self.RSI_MEAN:
                self.Liquidate(self.symbol)
                self.Debug(f"SELL: RSI={rsi_value:.2f} (revert to mean)")


# === VARIATION: Bollinger Band Squeeze ===

class BollingerSqueeze(QCAlgorithm):
    """
    Mean reversion during low volatility (Bollinger squeeze)
    """

    BB_PERIOD = 20
    BB_STD = 2.0
    SQUEEZE_THRESHOLD = 0.02  # Band width < 2% indicates squeeze

    def Initialize(self):
        self.SetStartDate(2020, 1, 1)
        self.SetEndDate(2023, 12, 31)
        self.SetCash(100000)

        self.symbol = self.AddEquity("SPY", Resolution.Daily).Symbol
        self.bb = self.BB(self.symbol, self.BB_PERIOD, self.BB_STD)
        self.atr = self.ATR(self.symbol, 14)

        self.SetWarmUp(self.BB_PERIOD)

    def OnData(self, data):
        if self.IsWarmingUp or not self.bb.IsReady or not self.atr.IsReady:
            return

        if not data.ContainsKey(self.symbol):
            return

        price = data[self.symbol].Close
        bb_lower = self.bb.LowerBand.Current.Value
        bb_middle = self.bb.MiddleBand.Current.Value
        bb_upper = self.bb.UpperBand.Current.Value

        # Calculate band width as percentage
        band_width = (bb_upper - bb_lower) / bb_middle

        # Only trade during squeeze (low volatility)
        in_squeeze = band_width < self.SQUEEZE_THRESHOLD

        if not self.Portfolio.Invested:
            # Buy at lower band during squeeze
            if in_squeeze and price <= bb_lower:
                self.SetHoldings(self.symbol, 1.0)
                self.Debug(f"BUY (squeeze): Price={price:.2f}, BandWidth={band_width:.2%}")

        else:
            # Exit at middle band or if squeeze breaks
            if price >= bb_middle or not in_squeeze:
                reason = "mean" if price >= bb_middle else "squeeze break"
                self.Liquidate(self.symbol)
                self.Debug(f"SELL ({reason}): Price={price:.2f}, BandWidth={band_width:.2%}")
