from datetime import timedelta

from AlgorithmImports import *


class ComboLimitOrderManager:
    def __init__(
        self,
        algorithm,
        entry_limit_offset=0.05,
        order_refresh_minutes=1,
        walk_after_unchanged_refreshes=2,
        walk_increment=0.05,
    ):
        self.algorithm = algorithm
        self.entry_limit_offset = entry_limit_offset
        self.order_refresh_minutes = order_refresh_minutes
        self.walk_after_unchanged_refreshes = walk_after_unchanged_refreshes
        self.walk_increment = walk_increment
        self.pending_entry = None

    @property
    def is_pending(self):
        return self.pending_entry is not None

    def submit_entry_order(self, call_spread, put_spread):
        market_credit = round(call_spread["price"] + put_spread["price"], 2)
        limit_price = self.credit_limit_price(market_credit)

        legs = [
            Leg.create(put_spread["long_leg"].symbol, 1),
            Leg.create(put_spread["short_leg"].symbol, -1),
            Leg.create(call_spread["short_leg"].symbol, -1),
            Leg.create(call_spread["long_leg"].symbol, 1),
        ]
        tickets = self.algorithm.combo_limit_order(legs, 1, limit_price)

        self.pending_entry = {
            "tickets": self.normalize_tickets(tickets),
            "call_symbols": {
                "short": call_spread["short_leg"].symbol,
                "long": call_spread["long_leg"].symbol,
            },
            "put_symbols": {
                "short": put_spread["short_leg"].symbol,
                "long": put_spread["long_leg"].symbol,
            },
            "submitted_at": self.algorithm.time,
            "last_market_credit": market_credit,
            "offset": self.entry_limit_offset,
            "unchanged_refreshes": 0,
        }

    def manage(self):
        if not self.pending_entry:
            return

        if self.algorithm.time - self.pending_entry["submitted_at"] < timedelta(
            minutes=self.order_refresh_minutes
        ):
            return

        market_credit = self.current_market_credit()
        if market_credit is None:
            self.cancel("missing price data")
            return

        market_credit = round(market_credit, 2)
        if market_credit == self.pending_entry["last_market_credit"]:
            self.pending_entry["unchanged_refreshes"] += 1
            if self.pending_entry["unchanged_refreshes"] < self.walk_after_unchanged_refreshes:
                self.pending_entry["submitted_at"] = self.algorithm.time
                return
            new_offset = max(0.0, self.pending_entry["offset"] - self.walk_increment)
            self.replace(market_credit, new_offset)
            return

        self.replace(market_credit, self.entry_limit_offset)

    def replace(self, market_credit, offset):
        call_symbols = self.pending_entry["call_symbols"]
        put_symbols = self.pending_entry["put_symbols"]
        self.cancel("repricing entry")

        limit_price = self.credit_limit_price(market_credit, offset)
        legs = [
            Leg.create(put_symbols["long"], 1),
            Leg.create(put_symbols["short"], -1),
            Leg.create(call_symbols["short"], -1),
            Leg.create(call_symbols["long"], 1),
        ]
        tickets = self.algorithm.combo_limit_order(legs, 1, limit_price)
        self.pending_entry = {
            "tickets": self.normalize_tickets(tickets),
            "call_symbols": call_symbols,
            "put_symbols": put_symbols,
            "submitted_at": self.algorithm.time,
            "last_market_credit": market_credit,
            "offset": offset,
            "unchanged_refreshes": 0,
        }

    def cancel(self, reason):
        if not self.pending_entry:
            return
        for ticket in self.pending_entry["tickets"]:
            if ticket.status in (OrderStatus.NEW, OrderStatus.SUBMITTED, OrderStatus.PARTIALLY_FILLED):
                self.algorithm.transactions.cancel_order(ticket.order_id, reason)
        self.pending_entry = None

    def current_market_credit(self):
        if not self.pending_entry:
            return None

        call_symbols = self.pending_entry["call_symbols"]
        put_symbols = self.pending_entry["put_symbols"]
        call_credit = self.vertical_credit(call_symbols["short"], call_symbols["long"])
        put_credit = self.vertical_credit(put_symbols["short"], put_symbols["long"])
        if call_credit is None or put_credit is None:
            return None
        return call_credit + put_credit

    def vertical_credit(self, short_symbol, long_symbol):
        short_bid = self.algorithm.securities[short_symbol].bid_price
        long_ask = self.algorithm.securities[long_symbol].ask_price
        if short_bid is None or long_ask is None:
            return None
        return short_bid - long_ask

    def credit_limit_price(self, market_credit, offset=None):
        if offset is None:
            offset = self.entry_limit_offset
        return round(max(0.05, market_credit - offset), 2)

    def normalize_tickets(self, tickets):
        if isinstance(tickets, list):
            return tickets
        return [tickets]
