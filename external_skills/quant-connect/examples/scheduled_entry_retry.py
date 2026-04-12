from datetime import timedelta

from AlgorithmImports import *


class ScheduledEntryRetry(QCAlgorithm):
    def initialize(self):
        self.set_start_date(2024, 1, 1)
        self.set_end_date(2024, 3, 31)
        self.set_cash(100000)

        self.retry_seconds = 20
        self.spx = self.add_index("SPX", Resolution.MINUTE).symbol

        option = self.add_index_option(self.spx, "SPXW", Resolution.MINUTE)
        option.set_filter(lambda universe: universe.expiration(0, 7).weeklys_only())
        self.spxw = option.symbol

        self.schedule.on(
            self.date_rules.every_day(self.spx),
            self.time_rules.at(15, 50, TimeZones.NEW_YORK),
            self.check_entry,
        )

    def check_entry(self):
        if self.is_warming_up or self.portfolio.invested:
            return
        if self.time.hour >= 16:
            return

        chain = self.current_slice.option_chains.get(self.spxw)
        if not chain:
            self.debug("No option chain available, scheduling retry")
            self.schedule_retry()
            return

        tomorrow = self.time.date() + timedelta(days=1)
        contracts = [contract for contract in chain if contract.expiry.date() == tomorrow]
        if not contracts:
            self.debug("No contracts for target expiry, scheduling retry")
            self.schedule_retry()
            return

        self.debug(f"Chain ready with {len(contracts)} contracts, proceed with spread search")

    def schedule_retry(self):
        retry_time = self.time + timedelta(seconds=self.retry_seconds)
        if retry_time.hour >= 16:
            return

        self.schedule.on(
            self.date_rules.on(retry_time.year, retry_time.month, retry_time.day),
            self.time_rules.at(retry_time.hour, retry_time.minute, TimeZones.NEW_YORK),
            self.check_entry,
        )
