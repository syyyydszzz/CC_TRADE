"""
Standards-Compliant QuantConnect Algorithm
Follows all coding standards from qc_guide.json
"""
from AlgorithmImports import *

class StandardsCompliantStrategy(QCAlgorithm):
    """
    Demonstration of QuantConnect coding standards:
    - snake_case for all methods and variables
    - Proper initialization
    - Guard clauses for all data access
    - No emojis, no disallowed imports
    - State management in self attributes
    """

    def initialize(self):
        """Initialize algorithm - called once at start"""

        # Set backtest period and capital
        self.set_start_date(2020, 1, 1)
        self.set_end_date(2023, 12, 31)
        self.set_cash(100000)

        # Add securities
        self.spy = self.add_equity("SPY", Resolution.Daily)

        # Create indicators
        self.rsi = self.rsi(self.spy.symbol, 14)
        self.sma = self.sma(self.spy.symbol, 50)

        # Initialize state (in initialize, not on_data)
        self.entry_price = None
        self.position_size = 1.0
        self.symbol_data = {
            "rsi_value": None,
            "sma_value": None
        }

        # Set warm-up period
        self.set_warm_up(50)

    def on_data(self, data):
        """Called every time new data arrives"""

        # Guard 1: Skip during warm-up
        if self.is_warming_up:
            return

        # Guard 2: Check indicator readiness
        if not self.rsi.is_ready or not self.sma.is_ready:
            return

        # Guard 3: Validate data availability
        if not data.contains_key(self.spy.symbol):
            return

        # Access data safely
        price = data[self.spy.symbol].close

        # Store indicator values in state
        self.symbol_data["rsi_value"] = self.rsi.current.value
        self.symbol_data["sma_value"] = self.sma.current.value

        # Entry logic
        if not self.portfolio.invested:
            self._check_entry_signal(price)

        # Exit logic
        else:
            self._check_exit_signal(price)

    def _check_entry_signal(self, price):
        """
        Entry logic separated into method for clarity
        Uses snake_case for method name
        """
        rsi_oversold = self.symbol_data["rsi_value"] < 30
        price_above_sma = price > self.symbol_data["sma_value"]

        if rsi_oversold and price_above_sma:
            self.set_holdings(self.spy.symbol, self.position_size)
            self.entry_price = price

            # Use self.debug() not print()
            self.debug(
                f"BUY: Price={price:.2f}, "
                f"RSI={self.symbol_data['rsi_value']:.2f}, "
                f"SMA={self.symbol_data['sma_value']:.2f}"
            )

    def _check_exit_signal(self, price):
        """Exit logic with stop loss and take profit"""

        if not self.entry_price:
            return

        # Calculate P&L
        pnl_pct = (price - self.entry_price) / self.entry_price

        # Exit conditions
        rsi_overbought = self.symbol_data["rsi_value"] > 70
        stop_loss_hit = pnl_pct < -0.05  # 5% stop loss
        take_profit_hit = pnl_pct > 0.15  # 15% take profit

        if rsi_overbought or stop_loss_hit or take_profit_hit:
            self.liquidate(self.spy.symbol)

            # Determine exit reason
            if stop_loss_hit:
                reason = "STOP LOSS"
            elif take_profit_hit:
                reason = "TAKE PROFIT"
            else:
                reason = "RSI OVERBOUGHT"

            self.debug(
                f"{reason}: Price={price:.2f}, "
                f"PnL={pnl_pct:.2%}"
            )

            # Reset state
            self.entry_price = None

    def on_order_event(self, order_event):
        """Track order fills for debugging"""

        if order_event.status == OrderStatus.Filled:
            self.debug(
                f"Order filled: {order_event.symbol} "
                f"@ {order_event.fill_price:.2f}, "
                f"Qty: {order_event.fill_quantity}"
            )


# Example with multiple securities
class MultiSymbolStandards(QCAlgorithm):
    """Demonstrates standards with multiple securities"""

    def initialize(self):
        self.set_start_date(2020, 1, 1)
        self.set_end_date(2023, 12, 31)
        self.set_cash(100000)

        # Add multiple symbols
        self.symbols = [
            self.add_equity("SPY", Resolution.Daily).symbol,
            self.add_equity("QQQ", Resolution.Daily).symbol
        ]

        # Create per-symbol state dict
        self.symbol_data = {}
        for symbol in self.symbols:
            self.symbol_data[symbol] = {
                "rsi": self.rsi(symbol, 14),
                "entry_price": None
            }

        self.set_warm_up(14)

    def on_data(self, data):
        if self.is_warming_up:
            return

        # Process each symbol
        for symbol in self.symbols:
            # Guard: check indicator ready
            if not self.symbol_data[symbol]["rsi"].is_ready:
                continue

            # Guard: check data available
            if not data.contains_key(symbol):
                continue

            self._process_symbol(symbol, data[symbol].close)

    def _process_symbol(self, symbol, price):
        """Process individual symbol (extract to method)"""

        rsi = self.symbol_data[symbol]["rsi"].current.value

        # Entry
        if not self.portfolio[symbol].invested:
            if rsi < 30:
                # Allocate 25% per symbol (4 max positions)
                self.set_holdings(symbol, 0.25)
                self.symbol_data[symbol]["entry_price"] = price
                self.debug(f"BUY {symbol}: Price={price:.2f}, RSI={rsi:.2f}")

        # Exit
        else:
            if rsi > 70:
                self.liquidate(symbol)
                entry = self.symbol_data[symbol]["entry_price"]
                pnl = (price - entry) / entry if entry else 0
                self.debug(f"SELL {symbol}: PnL={pnl:.2%}")
                self.symbol_data[symbol]["entry_price"] = None
