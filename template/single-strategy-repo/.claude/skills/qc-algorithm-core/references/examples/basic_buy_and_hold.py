from AlgorithmImports import *


class BuyAndHold(QCAlgorithm):
    def initialize(self):
        self.set_start_date(2023, 1, 1)
        self.set_end_date(2023, 12, 31)
        self.set_cash(100000)

        self.primary_symbol = self.add_equity("SPY", Resolution.DAILY).symbol
        self.set_benchmark(self.primary_symbol)

    def on_data(self, slice: Slice):
        if self.portfolio.invested:
            return
        if not slice.contains_key(self.primary_symbol):
            return
        self.set_holdings(self.primary_symbol, 1.0)
