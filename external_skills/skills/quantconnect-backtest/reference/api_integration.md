# Python API Integration

**Topic**: Direct Python API usage for QuantConnect backtesting

**Load when**: Implementing custom backtest workflows or debugging API calls

---

## QuantConnectAPI Class Usage

```python
import sys
sys.path.insert(0, 'SCRIPTS')
from qc_api import QuantConnectAPI

# Initialize API (reads credentials from .env)
api = QuantConnectAPI()
```

---

## Complete Workflow

### 1. Create Project

```python
project_id = api.create_project("TestStrategy_20241110")
print(f"Created project: {project_id}")
```

### 2. Upload Strategy File

```python
# Upload local file as Main.py in QC project
with open("strategy.py", "r") as f:
    code = f.read()

api.upload_file(project_id, code, "Main.py")
print("Strategy uploaded")
```

### 3. Create and Run Backtest

```python
backtest = api.create_backtest(project_id, "Backtest_v1")
backtest_id = backtest['backtestId']
print(f"Backtest started: {backtest_id}")
```

### 4. Wait for Completion

```python
# Polls every 5 seconds until complete or timeout
result = api.wait_for_backtest(project_id, backtest_id, timeout=600)

if 'error' in result:
    print(f"Backtest failed: {result['error']}")
else:
    print("Backtest completed successfully")
```

### 5. Parse Results

```python
from qc_api import parse_backtest_results

performance = parse_backtest_results(result)

print(f"Sharpe Ratio: {performance['sharpe_ratio']:.2f}")
print(f"Max Drawdown: {performance['max_drawdown']:.2%}")
print(f"Total Trades: {performance['total_trades']}")
print(f"Win Rate: {performance['win_rate']:.2%}")
print(f"Profit Factor: {performance['profit_factor']:.2f}")
```

---

## API Methods Reference

### create_project(name: str) -> int
Creates a new QuantConnect project.

**Parameters**:
- `name`: Unique project name (or reuses existing if found)

**Returns**: Project ID (integer)

**Example**:
```python
project_id = api.create_project("MomentumStrategy_v1")
```

---

### upload_file(project_id: int, content: str, filename: str) -> dict
Uploads code to a project.

**Parameters**:
- `project_id`: Target project ID
- `content`: Python code as string
- `filename`: Name in QC (typically "Main.py")

**Returns**: API response dict

**Example**:
```python
with open("strategy.py") as f:
    api.upload_file(project_id, f.read(), "Main.py")
```

---

### create_backtest(project_id: int, name: str) -> dict
Starts a backtest execution.

**Parameters**:
- `project_id`: Project containing strategy
- `name`: Backtest name (for identification)

**Returns**: Dict with `backtestId`

**Example**:
```python
backtest = api.create_backtest(project_id, "Test_Run_1")
backtest_id = backtest['backtestId']
```

---

### wait_for_backtest(project_id: int, backtest_id: str, timeout: int = 600) -> dict
Polls backtest until completion.

**Parameters**:
- `project_id`: Project ID
- `backtest_id`: Backtest ID from create_backtest()
- `timeout`: Max wait time in seconds (default: 600 = 10 minutes)

**Returns**: Complete backtest results dict

**Behavior**:
- Polls every 5 seconds
- Raises TimeoutError if exceeds timeout
- Returns results dict when complete

**Example**:
```python
result = api.wait_for_backtest(project_id, backtest_id, timeout=300)
```

---

### find_project_by_name(name: str) -> Optional[int]
Finds existing project by name.

**Parameters**:
- `name`: Project name to search

**Returns**: Project ID if found, None otherwise

**Example**:
```python
from qc_api import find_project_by_name

project_id = find_project_by_name("MomentumStrategy_v1")
if project_id:
    print(f"Found existing project: {project_id}")
else:
    print("Project not found, will create new")
```

---

## Error Handling

### API Authentication Errors

**Problem**: Invalid credentials or expired token

**Check**:
```python
try:
    api = QuantConnectAPI()
    projects = api.list_projects()
except Exception as e:
    if "401" in str(e):
        print("Authentication failed - check .env credentials")
    raise
```

### Project Creation Failures

**Problem**: Project name conflict or API limits

**Solution**: Use `find_project_by_name()` first:
```python
from qc_api import find_project_by_name

project_id = find_project_by_name(project_name)
if not project_id:
    project_id = api.create_project(project_name)
```

### Backtest Timeout

**Problem**: Backtest takes > timeout seconds

**Solutions**:
1. Increase timeout: `wait_for_backtest(project_id, backtest_id, timeout=1200)`
2. Reduce date range in strategy
3. Use daily resolution instead of minute data

---

## Advanced Usage

### Reusing Existing Projects

```python
# Check if project exists first
project_id = find_project_by_name("MyStrategy")

if not project_id:
    project_id = api.create_project("MyStrategy")

# Upload new version
api.upload_file(project_id, code, "Main.py")
```

### Running Multiple Backtests

```python
# Run multiple parameter variations
for param in [10, 20, 30]:
    code = generate_strategy(param)
    api.upload_file(project_id, code, "Main.py")

    backtest = api.create_backtest(project_id, f"Test_param_{param}")
    result = api.wait_for_backtest(project_id, backtest['backtestId'])

    performance = parse_backtest_results(result)
    print(f"Param {param}: Sharpe = {performance['sharpe_ratio']:.2f}")
```

---

**Related**: See `backtest_results.md` for complete results structure
