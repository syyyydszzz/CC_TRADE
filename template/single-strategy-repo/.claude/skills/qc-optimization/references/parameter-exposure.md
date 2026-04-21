# Parameter Exposure For `qc-mcp` Optimization

Use this guide when repo-root `main.py` should support `create_optimization`
without turning the strategy into a bag of knobs.

## Principles

- Start from explicit defaults in code, not empty external parameters.
- Promote only 1 or 2 hypothesis-backed constants at a time.
- Keep parameter names stable and `snake_case`.
- Parse parameter values defensively and fall back to defaults on bad input.
- Mirror the same names and defaults in `spec.md` and run notes.

## Pattern

```python
class MyStrategy(QCAlgorithm):
    LOOKBACK_DEFAULT = 50
    TAKE_PROFIT_THRESHOLD_DEFAULT = 0.30

    def initialize(self):
        self.lookback = self._get_int_parameter("lookback", self.LOOKBACK_DEFAULT)
        self.take_profit_threshold = self._get_float_parameter(
            "take_profit_threshold",
            self.TAKE_PROFIT_THRESHOLD_DEFAULT,
        )

    def _get_int_parameter(self, name: str, default: int) -> int:
        raw = self.get_parameter(name)
        if raw is None or raw == "":
            return default
        try:
            return int(raw)
        except ValueError:
            self.debug(f"Invalid parameter {name}={raw!r}; using default {default}.")
            return default

    def _get_float_parameter(self, name: str, default: float) -> float:
        raw = self.get_parameter(name)
        if raw is None or raw == "":
            return default
        try:
            return float(raw)
        except ValueError:
            self.debug(f"Invalid parameter {name}={raw!r}; using default {default}.")
            return default
```

## Guidance

- Keep the default strategy readable without any external parameters.
- Expose only the thresholds or windows that the optimization run will actually vary.
- Do not parameterize the symbol, backtest dates, or every implementation detail by default.
- If native optimization is not needed yet, keep the values as ordinary constants and run a manual sensitivity pass first.
