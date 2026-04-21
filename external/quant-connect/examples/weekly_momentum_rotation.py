from AlgorithmImports import *


class WeeklyMomentumRotation(QCAlgorithm):
    def initialize(self):
        self.set_start_date(2021, 1, 1)
        self.set_end_date(2023, 12, 31)
        self.set_cash(100000)

        self.symbols = [
            self.add_equity("SPY", Resolution.DAILY).symbol,
            self.add_equity("TLT", Resolution.DAILY).symbol,
        ]

        self.schedule.on(
            self.date_rules.every(DayOfWeek.MONDAY),
            self.time_rules.after_market_open(self.symbols[0], 10),
            self.rebalance,
        )

    def rebalance(self):
        history = self.history(self.symbols, 21, Resolution.DAILY)
        if history.empty:
            return

        returns = {}
        for symbol in self.symbols:
            df = history.loc[symbol]
            if len(df) < 2:
                continue
            returns[symbol] = df["close"].iloc[-1] / df["close"].iloc[0] - 1

        if not returns:
            return

        winner = max(returns, key=returns.get)
        self.set_holdings(winner, 1.0)
        for symbol in self.symbols:
            if symbol != winner:
                self.liquidate(symbol)
