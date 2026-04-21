# Common QuantConnect Implementation Errors

## Indicator Not Ready

- Symptom: `NoneType`, missing `.Value`, or unstable early-bar behavior.
- Fix: use `set_warm_up(...)` and guard with `if not indicator.is_ready: return`.

## Missing Data In Slice

- Symptom: `KeyError`, null bars, or intermittent crashes.
- Fix: use `if not slice.contains_key(symbol): return`.

## Trading During Warm-Up

- Symptom: trades fire before indicators stabilize.
- Fix: guard with `if self.is_warming_up: return`.

## Zero Or Invalid Order Quantity

- Symptom: rejected orders or no-op execution.
- Fix: validate the result of `calculate_order_quantity` before submitting.

## Overly Expensive `on_data`

- Symptom: slow backtests or runtime limits.
- Fix: move heavy work into scheduled callbacks, cache repeated calculations, and avoid large per-bar loops.

## History Request Returned Empty

- Symptom: follow-on logic breaks because the request silently returns no rows.
- Fix: guard on empty responses and verify symbol, date range, and resolution assumptions.
