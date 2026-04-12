from AlgorithmImports import *


class SmaCrossover(QCAlgorithm):
    def initialize(self):
        self.set_start_date(2022, 1, 1)
        self.set_end_date(2023, 12, 31)
        self.set_cash(100000)

        self.symbol = self.add_equity("SPY", Resolution.DAILY).symbol
        self.fast = self.sma(self.symbol, 20, Resolution.DAILY)
        self.slow = self.sma(self.symbol, 50, Resolution.DAILY)
        self.set_warm_up(50, Resolution.DAILY)

    def on_data(self, slice: Slice):
        if self.is_warming_up:
            return
        if not (self.fast.is_ready and self.slow.is_ready):
            return

        if self.fast.current.value > self.slow.current.value:
            if not self.portfolio.invested:
                self.set_holdings(self.symbol, 1.0)
        else:
            if self.portfolio.invested:
                self.liquidate(self.symbol)
