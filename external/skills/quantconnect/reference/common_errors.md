# Common QuantConnect Errors and Solutions

## Indicator Errors

### Error: "Indicator not ready"
**Problem**: Trying to access indicator value before it has enough data
```python
# WRONG
value = self.sma.Current.Value  # May throw error if not ready
```

**Solution**: Always check `IsReady` before accessing
```python
# RIGHT
if self.sma.IsReady:
    value = self.sma.Current.Value
else:
    return  # Skip this iteration
```

### Error: "AttributeError: 'NoneType' object has no attribute 'Value'"
**Problem**: Indicator returns None when not ready

**Solution**: Use `IsReady` check and warm-up period
```python
def Initialize(self):
    self.sma = self.SMA(symbol, 50)
    self.SetWarmUp(50)  # Warm up indicator

def OnData(self, data):
    if self.IsWarmingUp:
        return

    if self.sma.IsReady:
        value = self.sma.Current.Value
```

---

## Data Access Errors

### Error: "KeyError: Symbol not in data"
**Problem**: Trying to access data for symbol that may not be in current slice
```python
# WRONG
price = data[self.symbol].Close  # Throws KeyError if symbol not present
```

**Solution**: Check if data contains key first
```python
# RIGHT
if data.ContainsKey(self.symbol):
    price = data[self.symbol].Close
```

### Error: "No data available for symbol"
**Problem**: Symbol not properly added or data not available for date range

**Solution**: Verify symbol added and check date range
```python
def Initialize(self):
    # Ensure symbol is added
    self.symbol = self.AddEquity("SPY", Resolution.Daily).Symbol

    # Check backtest dates are valid
    self.SetStartDate(2020, 1, 1)  # Not too far in past
    self.SetEndDate(2023, 12, 31)  # Not in future
```

---

## Order Execution Errors

### Error: "Insufficient buying power"
**Problem**: Trying to buy more than available cash/margin allows

**Solution**: Use `SetHoldings` with percentage or calculate affordable quantity
```python
# RIGHT - percentage based
self.SetHoldings(symbol, 0.5)  # 50% of portfolio

# RIGHT - calculate affordable quantity
quantity = self.CalculateOrderQuantity(symbol, 0.5)
self.MarketOrder(symbol, quantity)
```

### Error: "Cannot sell short without margin"
**Problem**: Attempting to short without margin account

**Solution**: Check portfolio settings or avoid shorting
```python
# Only go long
if buy_signal:
    self.SetHoldings(symbol, 1.0)

# Don't short
if sell_signal:
    self.Liquidate(symbol)  # Close position only
```

### Error: "Order quantity must be non-zero"
**Problem**: Calculated quantity rounds to zero

**Solution**: Check quantity before ordering
```python
quantity = self.CalculateOrderQuantity(symbol, 0.5)
if quantity != 0:
    self.MarketOrder(symbol, quantity)
```

---

## Portfolio Errors

### Error: "Portfolio not invested but quantity > 0"
**Problem**: State mismatch, usually from stale position data

**Solution**: Use explicit position checks
```python
# Check both invested and quantity
if self.Portfolio[symbol].Invested and self.Portfolio[symbol].Quantity > 0:
    # Have long position
    pass
```

---

## Indicator Configuration Errors

### Error: "MACD signal line not available"
**Problem**: Accessing MACD components before ready

**Solution**: Check MACD readiness before accessing components
```python
if self.macd.IsReady:
    macd_value = self.macd.Current.Value
    signal_value = self.macd.Signal.Current.Value
    histogram = macd_value - signal_value
```

### Error: "Bollinger Bands upper band not found"
**Problem**: Accessing BB bands incorrectly

**Solution**: Use correct property names
```python
if self.bb.IsReady:
    upper = self.bb.UpperBand.Current.Value
    middle = self.bb.MiddleBand.Current.Value
    lower = self.bb.LowerBand.Current.Value
```

---

## Runtime Errors

### Error: "Algorithm took too long to execute"
**Problem**: OnData method is too slow (complex calculations, loops)

**Solution**: Optimize code, reduce complexity
```python
# AVOID expensive operations in OnData
def OnData(self, data):
    # Don't loop through huge datasets
    # Don't make complex calculations every bar

    # Use indicators instead
    # Cache results
    # Use scheduled events for heavy operations
```

### Error: "Memory limit exceeded"
**Problem**: Storing too much data in algorithm

**Solution**: Limit data retention
```python
# WRONG - grows forever
self.all_prices.append(price)

# RIGHT - keep only recent data
self.prices.append(price)
if len(self.prices) > 100:
    self.prices.pop(0)  # Keep only last 100
```

---

## Historical Data Errors

### Error: "History request returned empty"
**Problem**: Requesting history before warm-up or for invalid period

**Solution**: Request history after initialization, use valid periods
```python
def OnData(self, data):
    if not self.initialized:
        # Request history once
        history = self.History(self.symbol, 100, Resolution.Daily)
        if not history.empty:
            self.initialized = True
```

---

## Common Logic Errors

### Error: "Trading when shouldn't be"
**Problem**: Missing warm-up check

**Solution**: Always check warm-up status
```python
def OnData(self, data):
    if self.IsWarmingUp:
        return  # Don't trade during warm-up

    # Trading logic here
```

### Error: "Indicators giving unexpected values"
**Problem**: Using wrong resolution or period

**Solution**: Verify indicator configuration
```python
# Ensure resolution matches your needs
self.sma = self.SMA(self.symbol, 20, Resolution.Daily)  # Daily bars

# Match warm-up to indicator period
self.SetWarmUp(20)  # At least 20 days for 20-period SMA
```

---

## Debugging Tips

1. **Use Debug statements liberally**
```python
self.Debug(f"Price: {price}, Indicator: {self.sma.Current.Value}")
```

2. **Check IsReady for all indicators**
```python
if not self.indicator1.IsReady or not self.indicator2.IsReady:
    return
```

3. **Validate data availability**
```python
if not data.ContainsKey(self.symbol):
    self.Debug(f"No data for {self.symbol}")
    return
```

4. **Log entry and exit prices**
```python
self.Debug(f"BUY at {price}, RSI={self.rsi.Current.Value}")
self.Debug(f"SELL at {price}, Profit={(price-entry)/entry:.2%}")
```

5. **Use try-except for debugging**
```python
try:
    # Your code
    pass
except Exception as e:
    self.Debug(f"Error: {str(e)}")
```
