from datetime import datetime, timedelta

from AlgorithmImports import *


class EventAwareExpirySelection(QCAlgorithm):
    def initialize(self):
        self.set_start_date(2024, 1, 1)
        self.set_end_date(2024, 3, 31)
        self.set_cash(100000)

        self.event_dates = {
            datetime(2024, 1, 31).date(),
            datetime(2024, 2, 13).date(),
            datetime(2024, 3, 20).date(),
        }

        self.spx = self.add_index("SPX", Resolution.MINUTE).symbol
        option = self.add_index_option(self.spx, "SPXW", Resolution.MINUTE)
        option.set_filter(lambda universe: universe.expiration(6, 10).weeklys_only())
        self.spxw = option.symbol

        self.schedule.on(
            self.date_rules.every_day(self.spx),
            self.time_rules.at(15, 0, TimeZones.NEW_YORK),
            self.log_target_expiry,
        )

    def log_target_expiry(self):
        target_expiry = self.next_valid_expiry(self.time.date())
        if target_expiry is None:
            self.debug("No valid expiry found")
            return
        self.debug(f"Selected expiry {target_expiry}")

    def next_valid_expiry(self, from_date):
        # Prefer 7 DTE, but fall back when the preferred expiry lands on or after an event day.
        candidates = [
            from_date + timedelta(days=7),
            from_date + timedelta(days=6),
            from_date + timedelta(days=8),
        ]

        for expiry_date in candidates:
            if not self.is_valid_expiry_candidate(expiry_date):
                continue
            return expiry_date
        return None

    def is_valid_expiry_candidate(self, expiry_date):
        if expiry_date.weekday() >= 5:
            return False
        if not self.securities[self.spx].exchange.date_is_open(expiry_date):
            return False
        if expiry_date in self.event_dates:
            return False
        if (expiry_date - timedelta(days=1)) in self.event_dates:
            return False
        return True
