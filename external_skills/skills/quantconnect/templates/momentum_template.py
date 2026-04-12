"""
Momentum Strategy Template
Customizable momentum-based trading strategy
"""
from AlgorithmImports import *

class MomentumStrategyTemplate(QCAlgorithm):
    """
    Momentum Strategy Template

    CUSTOMIZE THESE PARAMETERS:
    - MOMENTUM_PERIOD: Lookback period for momentum calculation
    - RSI_PERIOD: RSI period
    - RSI_OVERSOLD: Entry threshold (buy when RSI below this)
    - RSI_OVERBOUGHT: Exit threshold (sell when RSI above this)
    - POSITION_SIZE: Percentage of portfolio per position
    - STOP_LOSS: Stop loss percentage
    - TAKE_PROFIT: Take profit percentage
    """

    # === PARAMETERS TO CUSTOMIZE ===
    MOMENTUM_PERIOD = 10
    RSI_PERIOD = 14
    RSI_OVERSOLD = 30
    RSI_OVERBOUGHT = 70
    POSITION_SIZE = 1.0  # 100% of portfolio
    STOP_LOSS = 0.05  # 5%
    TAKE_PROFIT = 0.15  # 15%

    def Initialize(self):
        # Backtest period
        self.SetStartDate(2020, 1, 1)
        self.SetEndDate(2023, 12, 31)
        self.SetCash(100000)

        # Add security (CHANGE THIS to your target)
        self.symbol = self.AddEquity("SPY", Resolution.Daily).Symbol

        # Momentum indicators
        self.rsi = self.RSI(self.symbol, self.RSI_PERIOD)
        self.mom = self.MOM(self.symbol, self.MOMENTUM_PERIOD)

        # Optional: Add additional momentum indicators
        # self.macd = self.MACD(self.symbol, 12, 26, 9)
        # self.roc = self.ROC(self.symbol, self.MOMENTUM_PERIOD)

        # Risk management
        self.entry_price = None

        # Warm up
        self.SetWarmUp(max(self.RSI_PERIOD, self.MOMENTUM_PERIOD))

    def OnData(self, data):
        if self.IsWarmingUp:
            return

        if not self.rsi.IsReady or not self.mom.IsReady:
            return

        if not data.ContainsKey(self.symbol):
            return

        price = data[self.symbol].Close

        # === ENTRY LOGIC (CUSTOMIZE THIS) ===
        if not self.Portfolio.Invested:
            # Momentum condition: positive momentum
            momentum_positive = self.mom.Current.Value > 0

            # RSI condition: oversold
            rsi_oversold = self.rsi.Current.Value < self.RSI_OVERSOLD

            # Entry signal: both conditions met
            if momentum_positive and rsi_oversold:
                self.SetHoldings(self.symbol, self.POSITION_SIZE)
                self.entry_price = price
                self.Debug(f"BUY: Price={price:.2f}, MOM={self.mom.Current.Value:.2f}, RSI={self.rsi.Current.Value:.2f}")

        # === EXIT LOGIC (CUSTOMIZE THIS) ===
        else:
            # Calculate P&L
            pnl_pct = (price - self.entry_price) / self.entry_price if self.entry_price else 0

            # Exit condition 1: Stop loss
            if pnl_pct < -self.STOP_LOSS:
                self.Liquidate(self.symbol)
                self.Debug(f"STOP LOSS: Price={price:.2f}, Loss={pnl_pct:.2%}")
                self.entry_price = None

            # Exit condition 2: Take profit
            elif pnl_pct > self.TAKE_PROFIT:
                self.Liquidate(self.symbol)
                self.Debug(f"TAKE PROFIT: Price={price:.2f}, Profit={pnl_pct:.2%}")
                self.entry_price = None

            # Exit condition 3: RSI overbought
            elif self.rsi.Current.Value > self.RSI_OVERBOUGHT:
                self.Liquidate(self.symbol)
                self.Debug(f"SELL (RSI): Price={price:.2f}, RSI={self.rsi.Current.Value:.2f}")
                self.entry_price = None

            # Exit condition 4: Momentum turns negative
            elif self.mom.Current.Value < 0:
                self.Liquidate(self.symbol)
                self.Debug(f"SELL (MOM): Price={price:.2f}, MOM={self.mom.Current.Value:.2f}")
                self.entry_price = None


# === VARIATIONS ===

class MultiTimeframeMomentum(QCAlgorithm):
    """
    Advanced: Multi-timeframe momentum strategy
    Use daily trend + hourly timing
    """

    def Initialize(self):
        self.SetStartDate(2020, 1, 1)
        self.SetEndDate(2023, 12, 31)
        self.SetCash(100000)

        # Use minute resolution for base data
        self.symbol = self.AddEquity("SPY", Resolution.Minute).Symbol

        # Daily SMA for trend (50-day)
        self.daily_sma = self.SMA(self.symbol, 50, Resolution.Daily)

        # Hourly RSI for entry timing
        self.hourly_rsi = self.RSI(self.symbol, 14, Resolution.Hour)

        # Hourly momentum
        self.hourly_mom = self.MOM(self.symbol, 10, Resolution.Hour)

        self.entry_price = None
        self.SetWarmUp(50)

    def OnData(self, data):
        if self.IsWarmingUp:
            return

        if not self.daily_sma.IsReady or not self.hourly_rsi.IsReady:
            return

        if not data.ContainsKey(self.symbol):
            return

        price = data[self.symbol].Close

        # Entry: Daily trend up + hourly oversold momentum
        if not self.Portfolio.Invested:
            daily_trend_up = price > self.daily_sma.Current.Value
            hourly_oversold = self.hourly_rsi.Current.Value < 35
            hourly_mom_positive = self.hourly_mom.Current.Value > 0

            if daily_trend_up and hourly_oversold and hourly_mom_positive:
                self.SetHoldings(self.symbol, 1.0)
                self.entry_price = price
                self.Debug(f"BUY: Trend up, hourly RSI={self.hourly_rsi.Current.Value:.2f}")

        # Exit: Hourly overbought or daily trend breaks
        else:
            hourly_overbought = self.hourly_rsi.Current.Value > 65
            daily_trend_down = price < self.daily_sma.Current.Value

            if hourly_overbought or daily_trend_down:
                self.Liquidate(self.symbol)
                reason = "overbought" if hourly_overbought else "trend break"
                self.Debug(f"SELL ({reason}): RSI={self.hourly_rsi.Current.Value:.2f}")
                self.entry_price = None
