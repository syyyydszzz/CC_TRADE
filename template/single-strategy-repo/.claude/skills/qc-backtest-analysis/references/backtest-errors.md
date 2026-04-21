# Backtest Error Patterns

## No Trades

- Entry logic may be too restrictive.
- Start by checking a simpler trigger and confirm the strategy can trade at all.

## Missing Data Or Null Bars

- Guard on `slice.contains_key(symbol)` before access.
- Check whether the expected subscription or option chain is actually available.

## Indicator Not Ready

- Use warm-up and readiness guards.
- Avoid reading indicator values during early bars.

## Runtime Limits Or Slow Execution

- Move heavy work out of `on_data`.
- Reduce repeated history calls and large per-bar loops.

## Suspiciously Perfect Results

- Look for look-ahead bias, unrealistic execution assumptions, or over-tuned parameters.

## What To Record

- the failure mode
- the most likely root cause
- the next concrete change to test
