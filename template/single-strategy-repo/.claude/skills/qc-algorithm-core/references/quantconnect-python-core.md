# QuantConnect Python Core Patterns

Use this file for the minimal implementation patterns that are compatible with this repository's `qc-mcp` workflow.

## Core Rules

- Use `from AlgorithmImports import *`.
- Implement one class inheriting from `QCAlgorithm`.
- Put one-time setup in `initialize`.
- Use `on_data(self, slice)` as the default event handler unless scheduling is a better fit.

## Initialization

- Set backtest boundaries with `set_start_date`, `set_end_date`, and `set_cash`.
- Add subscriptions in `initialize` and store the returned `Symbol`.
- Keep initialization deterministic and lightweight.

## Data Access

- Check `slice.contains_key(symbol)` before indexing.
- Use `slice.bars[symbol]` or `slice.quote_bars[symbol]` only when present.
- Expect fill-forward behavior in many backtests.

## Indicators

- Prefer automatic indicators such as `self.sma(symbol, period, resolution)`.
- Use `set_warm_up` or `warm_up_indicator` before relying on indicator values.
- Check readiness before using `.current.value`.

## History

- Use `history(...)` to seed features or compare recent bars.
- Treat history as ordered oldest to newest.
- Guard against empty responses.

## Scheduling

- Use `self.schedule.on(...)` for rebalance or maintenance logic.
- Remember scheduled events behave slightly differently in live vs backtest timing.

## Orders

- Use `set_holdings` for allocation-level intent.
- Use `market_order` or `limit_order` when order-type control matters.
- Check calculated quantities before sending zero-size orders.
