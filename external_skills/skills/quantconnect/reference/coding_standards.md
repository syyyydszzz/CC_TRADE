# QuantConnect Coding Standards

**Derived from: Claude Code Platform Specification Guide v1.0.0**

## Core Principles

1. Write deterministic, environment-safe Python
2. Avoid runtime dependencies unavailable in QC
3. Guard every data access and execution path
4. Leverage OptionStrategies to prevent structural errors
5. Prefer explicit initialization and state management

---

## Naming Conventions

### ✅ CORRECT: snake_case for variables and methods
```python
def calculate_delta_ratio(symbol, expiry):
    iv_rank = self.get_iv_rank(symbol)
    return delta_ratio

self.entry_price = price
self.position_size = 0.5
```

### ❌ WRONG: PascalCase for methods/variables
```python
def CalculateDeltaRatio(Symbol, Expiry):  # WRONG
    IVRank = self.GetIVRank(Symbol)  # WRONG
```

### ✅ PascalCase ONLY for class names
```python
class MomentumStrategy(QCAlgorithm):  # CORRECT
    pass
```

---

## Environment Compatibility

### ✅ Allowed Imports
- `pandas`, `numpy`, `sklearn`, `matplotlib`, `scipy`, `hmmlearn`
- **Always use**: `from AlgorithmImports import *`

### ❌ Disallowed Imports
- `requests`, `yfinance`, `ta`, `dotenv`, `plotly`, `openai`, `whisper`
- Any `aio` libraries (async not supported)
- `subprocess`, `os.system` (no OS access)

### ✅ Correct Import Pattern
```python
from AlgorithmImports import *

class MyAlgorithm(QCAlgorithm):
    def initialize(self):
        pass
```

### ❌ Wrong Import Pattern
```python
import os  # WRONG - no OS access
import requests  # WRONG - not available
import asyncio  # WRONG - no async support
```

---

## Algorithm Structure

### ✅ Proper Initialization
```python
class MyStrategy(QCAlgorithm):
    def initialize(self):
        # Set dates and cash FIRST
        self.set_start_date(2020, 1, 1)
        self.set_end_date(2023, 12, 31)
        self.set_cash(100000)

        # Add securities
        self.spy = self.add_equity("SPY", Resolution.Minute)

        # Initialize state
        self.symbol_data = {}
        self.entry_price = None

        # Create indicators
        self.rsi = self.rsi(self.spy.symbol, 14)

    def on_data(self, data):
        # Guard for warm-up
        if self.is_warming_up:
            return

        # Trading logic here
        pass
```

### ❌ Wrong: Dynamic initialization in on_data
```python
def on_data(self, data):
    # WRONG - don't add securities here
    self.spy = self.add_equity("SPY", Resolution.Minute)
```

---

## Method Naming

**QuantConnect uses snake_case for all methods:**

### ✅ CORRECT
```python
def initialize(self):
    self.set_start_date(2020, 1, 1)
    self.set_cash(100000)
    symbol = self.add_equity("SPY", Resolution.Daily)

def on_data(self, data):
    self.set_holdings(symbol, 1.0)
    self.liquidate(symbol)
```

### ❌ WRONG (PascalCase style - old API)
```python
def Initialize(self):  # WRONG - old style
    self.SetStartDate(2020, 1, 1)  # WRONG
    self.SetCash(100000)  # WRONG
```

**Note**: The skill.md examples use PascalCase (old API). Always use snake_case in actual code.

---

## Logging

### ✅ Use self.debug(), self.log(), self.error()
```python
self.debug(f"IV ratio: {iv_ratio:.2f}")
self.log(f"Position opened at {price}")
self.error("Error in calculation")
```

### ❌ Don't use print()
```python
print("IV ratio:", iv_ratio)  # WRONG
```

### Throttle Logging in on_data
```python
def on_data(self, data):
    # Only log once per day
    if self.time.hour == 10 and self.time.minute == 0:
        self.debug(f"Daily update: {self.portfolio.total_portfolio_value}")
```

---

## Data Access

### ✅ Guard All Data Access
```python
def on_data(self, data):
    # Check if data contains key
    if not data.contains_key(self.symbol):
        return

    # Check if bars available
    if self.symbol not in data.bars:
        return

    price = data[self.symbol].close
```

### ✅ Guard Indicator Access
```python
if not self.rsi.is_ready:
    return

rsi_value = self.rsi.current.value
```

---

## State Management

### ✅ Store State in self attributes
```python
def initialize(self):
    # Initialize state dictionaries
    self.symbol_data = {
        "SPY": {
            "roc": None,
            "greeks": None,
            "entry_price": None
        }
    }
    self.active_positions = {}
```

### ❌ Don't use globals
```python
# WRONG - no global state
global positions
positions = {}
```

---

## Options Trading

### ✅ Subscribe to Underlying First
```python
def initialize(self):
    # Add underlying FIRST
    self.spy = self.add_equity("SPY", Resolution.Minute)

    # Then add options
    option = self.add_option("SPY", Resolution.Minute)
    option.set_filter(-5, 5, 0, 30)
```

### ✅ Use OptionStrategies for Multi-Leg Trades
```python
# Calendar spread
strategy = OptionStrategies.calendar_spread(
    symbol,
    near_expiry,
    far_expiry,
    strike
)
self.add_option_strategy(strategy, 1)

# Vertical spread
strategy = OptionStrategies.bull_call_spread(
    symbol,
    lower_strike,
    upper_strike,
    expiry
)
self.add_option_strategy(strategy, 1)
```

### ❌ Don't use market_order for combos
```python
# WRONG for multi-leg
self.market_order(call_contract.symbol, 1)
self.market_order(put_contract.symbol, -1)
```

### ✅ Guard Option Chain Access
```python
def on_data(self, data):
    # Check if option chains available
    if not data.option_chains:
        return

    # Check specific underlying
    if self.spy.symbol not in data.option_chains:
        return

    chain = data.option_chains[self.spy.symbol]

    # Convert to list before filtering
    contracts = list(chain)

    # Filter and sort
    calls = [c for c in contracts if c.right == OptionRight.Call]
```

### ✅ Refresh Contracts Every Trade
```python
def on_data(self, data):
    # DON'T reuse old contract references
    # Always get fresh contracts from current chain

    chain = data.option_chains[self.spy.symbol]
    fresh_contracts = list(chain)

    # Use fresh contracts for trading
    selected = self.filter_contracts(fresh_contracts)
```

---

## Execution Rules

### ✅ Check Portfolio State Before Trading
```python
def on_data(self, data):
    # Check if already invested
    if not self.portfolio.invested:
        # Open new position
        self.set_holdings(symbol, 1.0)

    # Don't re-enter if already invested
```

### ✅ Use on_order_event for Fill Tracking
```python
def on_order_event(self, order_event):
    if order_event.status == OrderStatus.Filled:
        self.active_positions[order_event.symbol] = {
            "fill_price": order_event.fill_price,
            "quantity": order_event.fill_quantity
        }
        self.debug(f"Filled: {order_event.symbol} @ {order_event.fill_price}")
```

---

## Performance Best Practices

### ❌ Don't Loop with history()
```python
# WRONG - expensive loop
for bar in self.history(["SPY"], 100, Resolution.Minute):
    # Process each bar
```

### ✅ Prefetch Data Outside Loops
```python
# CORRECT - fetch once
history = self.history(["SPY"], 100, Resolution.Minute)
close_prices = history["close"]

# Process vectorized
returns = close_prices.pct_change()
```

### ✅ Use Consolidators and Indicators
```python
# Built-in indicators are optimized
self.rsi = self.rsi(symbol, 14)
self.sma = self.sma(symbol, 50)

# Don't manually calculate every bar
```

---

## Compatibility Notes

### ❌ No Async/Await
```python
# WRONG - QC is synchronous
async def on_data(self, data):
    await self.some_async_function()
```

### ❌ No File I/O
```python
# WRONG - no file system access
with open("data.csv", "w") as f:
    f.write("data")
```

### ❌ No subprocess/os.system
```python
# WRONG - no OS commands
import os
os.system("echo hello")

import subprocess
subprocess.run(["ls"])
```

### ✅ Python 3.8 Compatible
```python
# Use f-strings (supported)
message = f"Price: {price:.2f}"

# Don't use features from Python 3.9+
# (e.g., dict merge operator |)
```

---

## Quick Checklist

Before running backtest:

- [ ] ✅ snake_case for all variables and methods
- [ ] ✅ PascalCase only for class names
- [ ] ✅ `from AlgorithmImports import *`
- [ ] ✅ No disallowed imports (requests, yfinance, async, etc.)
- [ ] ✅ `initialize()` sets dates, cash, adds securities
- [ ] ✅ State initialized in `initialize()`, not `on_data()`
- [ ] ✅ Use `self.debug()` not `print()`
- [ ] ✅ Guard `on_data()` with `if self.is_warming_up: return`
- [ ] ✅ Guard data access with `data.contains_key(symbol)`
- [ ] ✅ Check `indicator.is_ready` before accessing
- [ ] ✅ Use `OptionStrategies` for multi-leg trades
- [ ] ✅ Subscribe to underlying before adding options
- [ ] ✅ No file I/O, no async, no subprocess
- [ ] ✅ No emojis in code

---

## Examples Summary

### Minimal Working Algorithm (Standards Compliant)
```python
from AlgorithmImports import *

class StandardsCompliantAlgo(QCAlgorithm):
    """Demonstrates all coding standards"""

    def initialize(self):
        # Set dates and cash
        self.set_start_date(2020, 1, 1)
        self.set_end_date(2023, 12, 31)
        self.set_cash(100000)

        # Add security
        self.spy = self.add_equity("SPY", Resolution.Daily)

        # Create indicator
        self.rsi = self.rsi(self.spy.symbol, 14)

        # Initialize state
        self.entry_price = None

        # Warm up
        self.set_warm_up(14)

    def on_data(self, data):
        """Trading logic - called every bar"""

        # Guard: warm-up
        if self.is_warming_up:
            return

        # Guard: indicator ready
        if not self.rsi.is_ready:
            return

        # Guard: data available
        if not data.contains_key(self.spy.symbol):
            return

        # Get price
        price = data[self.spy.symbol].close

        # Entry logic
        if not self.portfolio.invested:
            if self.rsi.current.value < 30:
                self.set_holdings(self.spy.symbol, 1.0)
                self.entry_price = price
                self.debug(f"BUY: Price={price:.2f}, RSI={self.rsi.current.value:.2f}")

        # Exit logic
        else:
            if self.rsi.current.value > 70:
                self.liquidate(self.spy.symbol)
                profit = (price - self.entry_price) / self.entry_price
                self.debug(f"SELL: Price={price:.2f}, Profit={profit:.2%}")
                self.entry_price = None
```

This algorithm follows ALL standards:
- ✅ snake_case methods
- ✅ Proper initialization
- ✅ Guards on all access
- ✅ self.debug() for logging
- ✅ State in self attributes
- ✅ No disallowed imports
- ✅ No async, file I/O, or OS calls
