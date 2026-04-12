# QuantConnect Python Core Patterns (LEAN)

## Docs
- [Writing Algorithms: Initialization](https://www.quantconnect.com/docs/v2/writing-algorithms/initialization)
- [Key Concepts: Event Handlers](https://www.quantconnect.com/docs/v2/writing-algorithms/key-concepts/event-handlers)
- [Scheduled Events](https://www.quantconnect.com/docs/v2/writing-algorithms/scheduled-events)
- [History Requests](https://www.quantconnect.com/docs/v2/writing-algorithms/historical-data/history-requests)
- [History Responses](https://www.quantconnect.com/docs/v2/writing-algorithms/historical-data/history-responses)
- [Indicators: Automatic Indicators](https://www.quantconnect.com/docs/v2/writing-algorithms/indicators/automatic-indicators)
- [Indicators: Manual Indicators](https://www.quantconnect.com/docs/v2/writing-algorithms/indicators/manual-indicators)
- [Market Orders](https://www.quantconnect.com/docs/v2/writing-algorithms/trading-and-orders/order-types/market-orders)
- [Limit Orders](https://www.quantconnect.com/docs/v2/writing-algorithms/trading-and-orders/order-types/limit-orders)

## Initialization
- Define subscriptions and settings in `initialize`; treat it as a one-time setup hook.
- Use `set_start_date`, `set_end_date`, and `set_cash` for backtest configuration; expect start/end dates to be ignored in live trading.

## Event Handlers and OnData
- Use `on_data(self, slice)` as the primary data event handler; it receives a `Slice` with all data for a moment in time.
- Expect daily data to trigger `on_data` at market close.
- Expect `on_data` to fire even without new data when fill-forward is enabled (default).

## Slice Access
- Use `slice.contains_key(symbol)` before indexing.
- Access trade bars with `slice.bars[symbol]` and quote bars with `slice.quote_bars[symbol]` when present.

## Indicators
- Use automatic indicators via helper methods like `self.sma(symbol, period, resolution)` so they auto-register for updates.
- Update manual indicators via consolidators with `register_indicator`; avoid calling `update` if you registered them for auto-updates.
- Warm up indicators with `set_warm_up` (algorithm warm-up) or `warm_up_indicator` (indicator-specific warm-up).

## History
- Use `history(symbols, bar_count, resolution)` (or other overloads) to get historical data.
- Expect history responses to be ordered from oldest to newest, which is suitable for indicator warm-up.
- Expect most Python history requests to return a pandas DataFrame by default.

## Scheduling
- Use `self.schedule.on(date_rules, time_rules, callback)` to run scheduled logic.
- Account for live scheduled events firing at wall-clock time and backtests executing on the next data slice.

## Orders
- Place market orders with `self.market_order(symbol, quantity)`.
- Place limit orders with `self.limit_order(symbol, quantity, limit_price)`.
