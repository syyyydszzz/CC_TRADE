from AlgorithmImports import *


class ComboSpreadEntry(QCAlgorithm):
    def initialize(self):
        self.set_start_date(2024, 1, 1)
        self.set_end_date(2024, 3, 31)
        self.set_cash(100000)
        self.trade = None

    def enter_iron_condor(self, call_spread, put_spread, underlying_price):
        total_credit = round(call_spread["price"] + put_spread["price"], 2)

        legs = [
            Leg.create(put_spread["long_leg"].symbol, 1),
            Leg.create(put_spread["short_leg"].symbol, -1),
            Leg.create(call_spread["short_leg"].symbol, -1),
            Leg.create(call_spread["long_leg"].symbol, 1),
        ]
        self.combo_market_order(legs, 1)

        self.trade = {
            "entry_credit": total_credit,
            "put_credit": round(put_spread["price"], 2),
            "call_credit": round(call_spread["price"], 2),
            "long_put": put_spread["long_leg"].symbol,
            "short_put": put_spread["short_leg"].symbol,
            "short_call": call_spread["short_leg"].symbol,
            "long_call": call_spread["long_leg"].symbol,
            "expiry": call_spread["short_leg"].expiry,
            "entry_underlying_price": round(underlying_price, 2),
            "entry_time": self.time,
        }

        self.debug(
            f"ENTRY: credit=${total_credit:.2f} | "
            f"put={put_spread['short_leg'].strike}/{put_spread['long_leg'].strike} | "
            f"call={call_spread['short_leg'].strike}/{call_spread['long_leg'].strike}"
        )
