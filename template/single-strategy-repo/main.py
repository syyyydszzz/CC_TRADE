# region imports
from AlgorithmImports import *
# endregion


class __PROJECT_CLASS_NAME__(QCAlgorithm):
    """Initial scaffold for an OpenSpec-driven single-strategy repository."""

    def initialize(self):
        self.set_start_date(2020, 1, 1)
        self.set_end_date(2022, 12, 31)
        self.set_cash(100_000)

        self.primary_symbol = self.add_equity(
            "__DEFAULT_ASSET__",
            Resolution.__DEFAULT_RESOLUTION_ENUM__,
        ).symbol
        self.set_warm_up(50, Resolution.__DEFAULT_RESOLUTION_ENUM__)

    def on_data(self, data: Slice):
        if self.is_warming_up:
            return

        if not data.contains_key(self.primary_symbol):
            return

        # Strategy logic will be implemented through the OpenSpec workflow.
        return
