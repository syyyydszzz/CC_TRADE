from AlgorithmImports import *


class IronCondorFinder:
    def __init__(
        self,
        spread_width=20,
        min_credit=1.2,
        max_credit=1.8,
        max_call_delta=0.08,
        max_put_delta=0.10,
        max_total_delta=0.18,
        credit_balance_ratio=0.7,
        max_tweak_attempts=50,
    ):
        self.spread_width = spread_width
        self.min_credit = min_credit
        self.max_credit = max_credit
        self.max_call_delta = max_call_delta
        self.max_put_delta = max_put_delta
        self.max_total_delta = max_total_delta
        self.credit_balance_ratio = credit_balance_ratio
        self.max_tweak_attempts = max_tweak_attempts

    def find_iron_condor(self, contracts, underlying_price):
        puts = sorted(
            [contract for contract in contracts if contract.right == OptionRight.PUT],
            key=lambda contract: contract.strike,
            reverse=True,
        )
        calls = sorted(
            [contract for contract in contracts if contract.right == OptionRight.CALL],
            key=lambda contract: contract.strike,
        )
        if len(puts) < 2 or len(calls) < 2:
            return None

        straddle_price = self.calculate_straddle_price(contracts, underlying_price)
        call_spread = self.find_initial_spread(calls, underlying_price, straddle_price, "CALL")
        put_spread = self.find_initial_spread(puts, underlying_price, straddle_price, "PUT")
        if not call_spread or not put_spread:
            return None

        tweaks = 0
        while tweaks < self.max_tweak_attempts:
            tweaks += 1
            total_credit = call_spread["price"] + put_spread["price"]
            total_delta = call_spread["delta"] + put_spread["delta"]

            if total_credit < self.min_credit:
                if call_spread["price"] < put_spread["price"]:
                    call_spread = self.move_spread_up(call_spread, calls, 5)
                else:
                    put_spread = self.move_spread_up(put_spread, puts, 5)
                continue

            if total_credit > self.max_credit:
                if call_spread["price"] > put_spread["price"]:
                    call_spread = self.move_spread_away(call_spread, calls, 5)
                else:
                    put_spread = self.move_spread_away(put_spread, puts, 5)
                continue

            if call_spread["delta"] > self.max_call_delta:
                call_spread = self.move_spread_away(call_spread, calls, 5)
                continue

            if put_spread["delta"] > self.max_put_delta:
                put_spread = self.move_spread_away(put_spread, puts, 5)
                continue

            if total_delta > self.max_total_delta:
                if call_spread["delta"] > put_spread["delta"]:
                    call_spread = self.move_spread_away(call_spread, calls, 5)
                else:
                    put_spread = self.move_spread_away(put_spread, puts, 5)
                continue

            if not self.is_credit_balanced(call_spread["price"], put_spread["price"]):
                if call_spread["price"] < put_spread["price"]:
                    call_spread = self.move_spread_up(call_spread, calls, 5)
                else:
                    put_spread = self.move_spread_up(put_spread, puts, 5)
                continue

            return call_spread, put_spread, tweaks

        return None

    def calculate_straddle_price(self, contracts, underlying_price):
        atm_call = min(
            [contract for contract in contracts if contract.right == OptionRight.CALL],
            key=lambda contract: abs(contract.strike - underlying_price),
        )
        atm_put = min(
            [contract for contract in contracts if contract.right == OptionRight.PUT],
            key=lambda contract: abs(contract.strike - underlying_price),
        )
        return round(atm_call.ask_price + atm_put.ask_price)

    def find_initial_spread(self, contracts, underlying_price, straddle_price, side):
        target_strike = (
            underlying_price + (2 * straddle_price)
            if side == "CALL"
            else underlying_price - (2 * straddle_price)
        )
        return self.build_spread(contracts, target_strike, side)

    def move_spread_up(self, spread, contracts, points):
        short_strike = spread["short_leg"].strike
        new_short = short_strike - points if spread["side"] == "CALL" else short_strike + points
        return self.build_spread(contracts, new_short, spread["side"])

    def move_spread_away(self, spread, contracts, points):
        short_strike = spread["short_leg"].strike
        new_short = short_strike + points if spread["side"] == "CALL" else short_strike - points
        return self.build_spread(contracts, new_short, spread["side"])

    def build_spread(self, contracts, target_short_strike, side):
        short_leg = min(contracts, key=lambda contract: abs(contract.strike - target_short_strike))

        if side == "CALL":
            long_candidates = [contract for contract in contracts if contract.strike > short_leg.strike]
            target_long_strike = short_leg.strike + self.spread_width
        else:
            long_candidates = [contract for contract in contracts if contract.strike < short_leg.strike]
            target_long_strike = short_leg.strike - self.spread_width

        if not long_candidates:
            return None

        long_leg = min(
            long_candidates,
            key=lambda contract: abs(contract.strike - target_long_strike),
        )
        return {
            "short_leg": short_leg,
            "long_leg": long_leg,
            "price": round(short_leg.bid_price - long_leg.ask_price, 2),
            "delta": abs(short_leg.greeks.delta),
            "side": side,
        }

    def is_credit_balanced(self, call_credit, put_credit):
        smaller = min(call_credit, put_credit)
        larger = max(call_credit, put_credit)
        if larger <= 0:
            return False
        return (smaller / larger) >= self.credit_balance_ratio
