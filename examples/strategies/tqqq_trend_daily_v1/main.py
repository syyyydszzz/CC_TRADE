# region imports
from AlgorithmImports import *
# endregion


class TqqqTrendDailyV1(QCAlgorithm):
    """
    TQQQ Daily Trend Following v1

    Strategy:
      - Long TQQQ (100%) when TQQQ.Close > SMA(200) AND SPY.Close > SMA(200)
      - Cash otherwise

    Design principles:
      - Long-only, daily resolution
      - Single parameter (window = 200) — avoids overfitting
      - State-change-only orders — very low turnover
      - SPY SMA filter as broad market regime guard
    """

    SMA_PERIOD = 200

    def initialize(self):
        self.set_start_date(2018, 1, 1)
        self.set_end_date(2024, 12, 31)
        self.set_cash(100_000)

        # Primary asset
        self.tqqq = self.add_equity("TQQQ", Resolution.DAILY).symbol

        # Market filter asset (not traded directly)
        self.spy = self.add_equity("SPY", Resolution.DAILY).symbol

        # SMA(200) indicators — automatic, daily resolution
        self.tqqq_sma = self.sma(self.tqqq, self.SMA_PERIOD, Resolution.DAILY)
        self.spy_sma = self.sma(self.spy, self.SMA_PERIOD, Resolution.DAILY)

        # Warm up enough bars for both indicators
        self.set_warm_up(self.SMA_PERIOD, Resolution.DAILY)

    def on_data(self, slice: Slice):
        # Skip until warm-up period ends
        if self.is_warming_up:
            return

        # Wait until both indicators are ready
        if not self.tqqq_sma.is_ready or not self.spy_sma.is_ready:
            return

        # Require price data for both symbols
        if not slice.contains_key(self.tqqq) or not slice.contains_key(self.spy):
            return

        tqqq_price = slice.bars[self.tqqq].close
        spy_price = slice.bars[self.spy].close

        tqqq_above = tqqq_price > self.tqqq_sma.current.value
        spy_above = spy_price > self.spy_sma.current.value

        in_uptrend = tqqq_above and spy_above

        if in_uptrend:
            # Enter long only on state change (low turnover)
            if not self.portfolio.invested:
                self.set_holdings(self.tqqq, 1.0)
        else:
            # Exit to cash only on state change
            if self.portfolio.invested:
                self.liquidate(self.tqqq)
