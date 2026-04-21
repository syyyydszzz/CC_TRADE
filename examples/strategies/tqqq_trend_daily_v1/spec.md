# tqqq_trend_daily_v1 — Spec

## Strategy Summary

TQQQ Daily Trend Following — Long Only, Dual SMA(200) Filter

## Universe

| Field      | Value           |
|------------|-----------------|
| Asset      | TQQQ            |
| Filter     | SPY (not traded)|
| Resolution | Daily           |
| Direction  | Long only       |

## Logic

**Entry:** `TQQQ.Close > SMA(200, TQQQ)` AND `SPY.Close > SMA(200, SPY)`  
**Exit:** Either condition breaks → liquidate to cash  
**Sizing:** 100% when long, 0% when out  
**Order trigger:** State change only (prevents redundant orders)

## Parameters

| Parameter    | Value | Rationale                              |
|--------------|-------|----------------------------------------|
| SMA window   | 200   | Canonical period, avoids overfitting   |

## Design Principles

- **Low turnover**: only trade on trend state changes
- **Anti-overfitting**: 1 parameter, well-known natural period
- **Market filter**: SPY SMA prevents leveraged exposure during broad bear markets
- **Simple**: 2 conditions, 2 indicators, 1 position size

## Backtest Period

2018-01-01 → 2024-12-31  
Covers: 2018 Q4 correction, 2019 bull, COVID crash + recovery, 2021 bull, 2022 bear

## Current Status

- [x] main.py written and synced to QC
- [ ] Compile gate
- [ ] Backtest gate
- [ ] Result workspace populated

## Next Steps

1. Confirm open QC project is `tqqq_trend_daily_v1`
2. run `create_compile` → `read_compile`
3. run `create_backtest` → `read_backtest`
4. Persist results and finalize session
