# Complete Error Handling Guide

**Topic**: All common backtest errors with solutions

**Load when**: Debugging backtest failures or runtime errors

---

## Error Categories

1. **Strategy Logic Errors** - Code bugs causing no trades or crashes
2. **API Errors** - Authentication, timeouts, project issues
3. **Data Access Errors** - Missing data or incorrect symbol handling
4. **Indicator Errors** - Warmup issues, not ready states

---

## Strategy Logic Errors

### 1. Strategy Never Trades (0 trades)

**Problem**: Entry conditions are too restrictive

**Symptoms**:
- Backtest completes successfully
- 0 trades executed
- Metrics all show 0 or N/A

**Common Causes**:
```python
# TOO RESTRICTIVE - Multiple ANDs reduce trigger probability
if (self.sma.IsReady and
    self.sma.Current.Value > price and
    volume > 2.0 * avg_volume and
    price > self.yesterday_high):
    self.SetHoldings(self.symbol, 1.0)
```

**Solutions**:

**Option 1**: Simplify logic
```python
# SIMPLER - Higher probability of triggering
if self.sma.IsReady and price > self.sma.Current.Value:
    self.SetHoldings(self.symbol, 1.0)
```

**Option 2**: Log entry conditions
```python
def OnData(self, data):
    if not self.sma.IsReady:
        self.Debug(f"{self.Time}: SMA not ready yet")
        return

    price = data[self.symbol].Close
    sma_value = self.sma.Current.Value

    self.Debug(f"{self.Time}: Price={price:.2f}, SMA={sma_value:.2f}")

    if price > sma_value:
        self.SetHoldings(self.symbol, 1.0)
        self.Debug(f"{self.Time}: ENTRY TRIGGERED")
```

---

### 2. Runtime Error: Object Reference Not Set

**Problem**: Accessing data that is None

**Error Message**: `NullReferenceException: Object reference not set to an instance of an object`

**Common Cause**:
```python
def OnData(self, data):
    bar = data[self.symbol]  # Can be None if symbol not in data
    price = bar.Close  # CRASHES if bar is None
```

**Solution**: Add None checks
```python
def OnData(self, data):
    # Check 1: Symbol exists in data
    if not data.ContainsKey(self.symbol):
        return

    # Check 2: Bar is not None
    bar = data[self.symbol]
    if bar is None:
        return

    # Now safe to access
    price = bar.Close
```

**Best Practice**: Always check before accessing
```python
def OnData(self, data):
    # Defensive programming
    if not data.ContainsKey(self.symbol):
        return

    bar = data[self.symbol]
    if bar is None or not hasattr(bar, 'Close'):
        return

    price = bar.Close
    # Rest of logic...
```

---

### 3. Indicator Not Ready

**Problem**: Using indicator before warmup period completes

**Error Messages**:
- `IndicatorNotReady`
- `KeyError` or `AttributeError` on `.Current`

**Common Cause**:
```python
def Initialize(self):
    self.sma = self.SMA(self.symbol, 20)  # Needs 20 bars

def OnData(self, data):
    # BUG: No ready check
    if self.sma.Current.Value > price:  # Can fail if < 20 bars seen
        self.SetHoldings(self.symbol, 1.0)
```

**Solution**: Check IsReady property
```python
def OnData(self, data):
    # Always check IsReady first
    if not self.sma.IsReady:
        return  # Skip until indicator has enough data

    if self.sma.Current.Value > price:
        self.SetHoldings(self.symbol, 1.0)
```

**Alternative**: Use warmup
```python
def Initialize(self):
    self.sma = self.SMA(self.symbol, 20)
    self.SetWarmUp(20, Resolution.Daily)  # Pre-populate indicator

def OnData(self, data):
    if self.IsWarmingUp:
        return  # Skip during warmup

    # Indicator guaranteed to be ready after warmup
    if self.sma.Current.Value > price:
        self.SetHoldings(self.symbol, 1.0)
```

---

### 4. Division by Zero

**Problem**: Dividing by zero in calculations

**Common Cause**:
```python
# BUG: price_change can be zero
percent_change = (price - yesterday_price) / yesterday_price
```

**Solution**: Add zero check
```python
if yesterday_price != 0:
    percent_change = (price - yesterday_price) / yesterday_price
else:
    percent_change = 0.0
```

---

### 5. Index Out of Range

**Problem**: Accessing list/array beyond bounds

**Common Cause**:
```python
# BUG: bars might have < 5 elements
if bars[4].Close > bars[0].Close:
    self.SetHoldings(self.symbol, 1.0)
```

**Solution**: Check length
```python
if len(bars) >= 5:
    if bars[4].Close > bars[0].Close:
        self.SetHoldings(self.symbol, 1.0)
```

---

## API Errors

### 6. Authentication Failed (401)

**Problem**: Invalid credentials or expired token

**Error Message**: `401 Unauthorized` or `Invalid credentials`

**Check**:
1. `.env` file exists in project root
2. Credentials are correct:
   ```bash
   QC_USER_ID=your_user_id
   QC_API_TOKEN=your_api_token
   ```
3. Token hasn't expired (regenerate at quantconnect.com)

**Test Authentication**:
```python
from qc_api import QuantConnectAPI

try:
    api = QuantConnectAPI()
    projects = api.list_projects()
    print(f"✓ Authentication successful ({len(projects)} projects)")
except Exception as e:
    print(f"✗ Authentication failed: {e}")
```

---

### 7. Project Creation Failed

**Problem**: Project name conflict or API limits

**Error Messages**:
- `Project already exists`
- `Maximum projects reached`

**Solution 1**: Use find_project_by_name first
```python
from qc_api import find_project_by_name

project_id = find_project_by_name("MyStrategy")
if project_id:
    print(f"Reusing existing project: {project_id}")
else:
    project_id = api.create_project("MyStrategy")
```

**Solution 2**: Delete old projects
- Login to quantconnect.com
- Navigate to My Projects
- Delete unused projects

---

### 8. Backtest Timeout

**Problem**: Backtest runs longer than timeout setting

**Error Message**: `TimeoutError: Backtest exceeded 600 seconds`

**Causes**:
- Large date range (> 5 years)
- High resolution data (minute vs daily)
- Complex indicators (many calculations)

**Solutions**:

**Option 1**: Increase timeout
```python
# Default: 600 seconds (10 minutes)
result = api.wait_for_backtest(project_id, backtest_id, timeout=1200)  # 20 min
```

**Option 2**: Reduce date range
```python
def Initialize(self):
    # Instead of 10 years
    self.SetStartDate(2015, 1, 1)
    self.SetEndDate(2025, 1, 1)

    # Use 3 years for faster testing
    self.SetStartDate(2022, 1, 1)
    self.SetEndDate(2025, 1, 1)
```

**Option 3**: Use daily data
```python
def Initialize(self):
    # Instead of minute data
    self.AddEquity("SPY", Resolution.Minute)

    # Use daily for faster backtests
    self.AddEquity("SPY", Resolution.Daily)
```

---

### 9. Compilation Failed

**Problem**: Python syntax errors or invalid imports

**Error Message**: `Compilation error: ...`

**Common Causes**:
- Syntax errors (missing colons, indentation)
- Invalid imports
- Undefined variables

**Debug Process**:
1. Test locally first:
   ```bash
   python3 -m py_compile strategy.py
   ```
2. Check QC logs for specific error line
3. Verify all imports are QC-compatible

---

## Data Access Errors

### 10. Symbol Not Found

**Problem**: Requesting data for invalid/delisted symbol

**Error Message**: `Symbol not found` or empty data

**Solution**: Verify symbol exists in QC database
```python
def Initialize(self):
    try:
        self.AddEquity("AAPL", Resolution.Daily)
    except Exception as e:
        self.Debug(f"Failed to add symbol: {e}")
        raise
```

---

### 11. No Data in Date Range

**Problem**: Symbol wasn't trading during specified dates

**Example**: Requesting TSLA data before 2010 IPO

**Solution**: Adjust date range or use different symbol
```python
def Initialize(self):
    # TSLA IPO: June 2010
    self.SetStartDate(2010, 6, 29)  # First trading day
```

---

## Recovery Strategies

### When to ESCALATE_TO_HUMAN
- Compilation errors you can't fix
- Persistent runtime errors after multiple fixes
- Authentication issues that persist

### When to RETRY
- Timeout errors (increase timeout)
- Transient API errors (retry after 30s)

### When to ABANDON_HYPOTHESIS
- 0 trades after simplifying logic
- Fundamental strategy flaw (can't be fixed with code changes)

---

## Debugging Checklist

When backtest fails:

1. **Check error message** - Specific error in QC logs?
2. **Verify data access** - Symbol exists? Date range valid?
3. **Test indicators** - All have IsReady checks?
4. **Simplify logic** - Remove complex conditions temporarily
5. **Add Debug statements** - Log key values
6. **Test locally** - Run Python syntax check
7. **Check API limits** - Timeout sufficient? Projects under limit?

---

**Related**: See `api_integration.md` for API methods, `workflow_examples.md` for complete examples
