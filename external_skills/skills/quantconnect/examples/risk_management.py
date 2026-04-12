"""
Risk Management Patterns for QuantConnect
Demonstrates various risk management techniques
"""
from AlgorithmImports import *

class RiskManagementDemo(QCAlgorithm):
    """
    Demonstrates risk management patterns:
    - Stop loss
    - Take profit
    - Position sizing by volatility
    - Maximum drawdown protection
    - Position limits
    """

    def Initialize(self):
        self.SetStartDate(2020, 1, 1)
        self.SetEndDate(2023, 12, 31)
        self.SetCash(100000)

        self.symbol = self.AddEquity("SPY", Resolution.Daily).Symbol

        # Indicators for signals and risk
        self.rsi = self.RSI(self.symbol, 14)
        self.atr = self.ATR(self.symbol, 14)

        # === Risk Parameters ===
        self.stop_loss_pct = 0.05  # 5% stop loss
        self.take_profit_pct = 0.10  # 10% take profit
        self.max_drawdown = 0.20  # 20% maximum drawdown
        self.risk_per_trade = 0.01  # Risk 1% of portfolio per trade

        # === State Tracking ===
        self.entry_price = None
        self.peak_portfolio_value = self.Portfolio.TotalPortfolioValue

        self.SetWarmUp(20)

    def OnData(self, data):
        if self.IsWarmingUp:
            return

        if not self.rsi.IsReady or not self.atr.IsReady:
            return

        if not data.ContainsKey(self.symbol):
            return

        price = data[self.symbol].Close

        # === Pattern 1: Maximum Drawdown Protection ===
        self.CheckMaxDrawdown()

        # === Pattern 2: Entry with Position Sizing ===
        if not self.Portfolio.Invested:
            # Simple entry signal (RSI oversold)
            if self.rsi.Current.Value < 30:
                # Calculate position size based on volatility
                position_size = self.CalculatePositionSize(price)

                self.SetHoldings(self.symbol, position_size)
                self.entry_price = price
                self.Debug(f"BUY: Price={price:.2f}, Size={position_size:.2%}, RSI={self.rsi.Current.Value:.2f}")

        # === Pattern 3: Exit with Stop Loss and Take Profit ===
        else:
            pnl_pct = (price - self.entry_price) / self.entry_price

            # Stop Loss
            if pnl_pct < -self.stop_loss_pct:
                self.Liquidate(self.symbol)
                self.Debug(f"STOP LOSS: Price={price:.2f}, Entry={self.entry_price:.2f}, Loss={pnl_pct:.2%}")
                self.entry_price = None

            # Take Profit
            elif pnl_pct > self.take_profit_pct:
                self.Liquidate(self.symbol)
                self.Debug(f"TAKE PROFIT: Price={price:.2f}, Entry={self.entry_price:.2f}, Profit={pnl_pct:.2%}")
                self.entry_price = None

            # Trailing Stop using ATR
            elif self.UseTrailingStop(price):
                pass  # Handled in method

    def CalculatePositionSize(self, current_price):
        """
        Pattern: Position Sizing by Volatility
        Risk fixed percentage of portfolio per trade
        """
        if not self.atr.IsReady:
            return 0.5  # Default 50% if ATR not ready

        # Calculate volatility as percentage
        volatility = self.atr.Current.Value / current_price

        # Position size to risk 1% of portfolio
        # If volatility is 2% and we want to risk 1%, position size = 1% / 2% = 50%
        if volatility > 0:
            position_size = self.risk_per_trade / volatility
        else:
            position_size = 0.5

        # Cap at 100% (no leverage)
        position_size = min(position_size, 1.0)

        # Floor at 10%
        position_size = max(position_size, 0.1)

        return position_size

    def UseTrailingStop(self, current_price):
        """
        Pattern: Trailing Stop using ATR
        Stop loss moves up with price, locks in profits
        """
        if not self.entry_price or not self.atr.IsReady:
            return False

        # Calculate stop distance (2x ATR)
        stop_distance = self.atr.Current.Value * 2

        # Only trail upwards
        highest_price = max(self.entry_price, current_price)

        # Trigger if price falls below (highest - stop_distance)
        if current_price < (highest_price - stop_distance):
            self.Liquidate(self.symbol)
            profit_pct = (current_price - self.entry_price) / self.entry_price
            self.Debug(f"TRAILING STOP: Price={current_price:.2f}, Entry={self.entry_price:.2f}, PnL={profit_pct:.2%}")
            self.entry_price = None
            return True

        return False

    def CheckMaxDrawdown(self):
        """
        Pattern: Maximum Drawdown Protection
        Liquidate all positions if drawdown exceeds threshold
        """
        current_value = self.Portfolio.TotalPortfolioValue

        # Update peak
        if current_value > self.peak_portfolio_value:
            self.peak_portfolio_value = current_value

        # Calculate current drawdown
        drawdown = (self.peak_portfolio_value - current_value) / self.peak_portfolio_value

        # Emergency liquidation if max drawdown exceeded
        if drawdown > self.max_drawdown:
            self.Liquidate()
            self.Debug(f"MAX DRAWDOWN EXCEEDED: {drawdown:.2%} > {self.max_drawdown:.2%}")
            self.Quit(f"Max drawdown {drawdown:.2%} exceeded threshold")


# === Alternative Pattern: Fixed Dollar Stop Loss ===
class FixedDollarStopLoss(QCAlgorithm):
    """Stop loss based on fixed dollar amount"""

    def Initialize(self):
        self.SetStartDate(2020, 1, 1)
        self.SetCash(100000)
        self.symbol = self.AddEquity("SPY", Resolution.Daily).Symbol
        self.rsi = self.RSI(self.symbol, 14)

        self.max_loss_per_trade = 500  # Max $500 loss per trade
        self.entry_value = None

    def OnData(self, data):
        if not self.rsi.IsReady or not data.ContainsKey(self.symbol):
            return

        # Entry
        if not self.Portfolio.Invested and self.rsi.Current.Value < 30:
            self.SetHoldings(self.symbol, 1.0)
            self.entry_value = self.Portfolio.TotalPortfolioValue

        # Exit: Fixed dollar stop loss
        if self.Portfolio.Invested and self.entry_value:
            current_value = self.Portfolio.TotalPortfolioValue
            loss = self.entry_value - current_value

            if loss > self.max_loss_per_trade:
                self.Liquidate(self.symbol)
                self.Debug(f"STOP: Loss ${loss:.2f} exceeded ${self.max_loss_per_trade}")
                self.entry_value = None
