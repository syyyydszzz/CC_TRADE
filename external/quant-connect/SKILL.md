---
name: quant-connect
description: Build, refactor, and explain QuantConnect LEAN algorithms in Python using QCAlgorithm, including data subscriptions, event handlers, scheduling, history, indicators, and order placement. Use when translating strategy logic into QuantConnect's Python API, debugging backtests/live behavior, or implementing core algorithm patterns.
---

# QuantConnect Python Algorithms

## Overview
Enable fast, correct construction of QuantConnect LEAN algorithms in Python. Focus on core QCAlgorithm lifecycle, data access, scheduling, indicators, history, and orders (not exhaustive API coverage).

## Workflow
1. Clarify the strategy, asset class, resolution, and backtest vs live assumptions.
2. Draft the algorithm skeleton with `initialize` and `on_data`; store `Symbol` objects from `add_*` calls.
3. Add indicators and warm-up, plus any scheduled callbacks.
4. Implement trade logic and order placement.
5. Validate data availability, market hours, and event timing.

## LEAN CLI Research Loop
- The default loop is:
  - `lean login` and `lean init` in an organization workspace, then `cd` into the workspace directory that contains `lean.json`.
  - `lean project-create --language python "<projectName>"` to scaffold a new Python project inside that LEAN workspace.
  - Edit the algorithm in the project files.
  - Commit the code changes for the test so the backtest maps to a stable `code_version`.
  - Run `lean cloud push --project "<projectName>"` to push only that project. If the local project's `cloud-id` is missing or `null`, the push step creates the cloud project first.
  - Run `lean cloud backtest "<projectName>" --name "<runName>" --open` after the push succeeds when you want a human-readable run label in QuantConnect. `lean cloud backtest` takes the cloud project name or id, not an arbitrary local folder path.
  - Wait for the backtest to finish, review the returned statistics and full results, log the experiment, then tweak the algorithm and re-run until the metrics meet the target you care about.
- Use `lean cloud pull --project "<projectName>"` before local work when cloud changes may exist, and use `lean cloud push --project "<projectName>" --force` when you want the cloud copy updated.
- Run only one cloud backtest at a time. Do not launch the next run until the current one has completed and been logged.

## Research Logging
- Keep append-only research logs during strategy work. Never delete old entries and do not rewrite history after the fact.
- If the research log structure does not exist, create it with:
  - `python .codex/skills/quant-connect/scripts/bootstrap_research_log.py`
- Generate ids with `scripts/generate_research_id.py` so `hypothesis_id` and `experiment_id` values are sequential and deterministic.
- Create or update the hypothesis entry before running a meaningful new test.
- After each completed backtest, append an experiment entry before launching the next backtest.
- Store downloaded QuantConnect backtest result payloads in `research_log/results/` so they live alongside the hypothesis and experiment logs.
- Parse saved QuantConnect results payloads with:
  - `python .codex/skills/quant-connect/scripts/extract_backtest_metrics.py <results-json>`
  - The script returns a compact JSON object with run metadata, frontmatter-ready `quantconnect_results`, and normalized numeric fields in `parsed_metrics`.
- If a completed experiment changes your thinking, update the existing hypothesis entry or create a new hypothesis entry with its own `hypothesis_id`.
- Use one file per hypothesis and one file per experiment so each entry is easy to read, diff, and load.
- Use the id itself as the filename.
- Put metadata in YAML frontmatter at the top of each file.
- Use the templates in `templates/hypothesis.md` and `templates/experiment.md`.
- The templates are the source of truth for required frontmatter fields and markdown sections.
- Commit the code for each meaningful test and record the resulting git commit hash as `code_version` in the experiment entry.

### Id Generation
- Bootstrap the research log directories with:
  - `python .codex/skills/quant-connect/scripts/bootstrap_research_log.py`
- Generate the next hypothesis_id with:
  - `python .codex/skills/quant-connect/scripts/generate_research_id.py hypothesis`
- Generate the next experiment_id with:
  - `python .codex/skills/quant-connect/scripts/generate_research_id.py experiment`
- Use the returned id for both the frontmatter field and the filename.
- Filename examples:
  - `research_log/hypotheses/h001.md`
  - `research_log/experiments/e001.md`

### Hypotheses Log
- Store each idea as a separate file in `research_log/hypotheses/`.
- Use `templates/hypothesis.md` as the canonical structure for files keyed by `hypothesis_id`.

### Experiments Log
- Store each experiment as a separate file in `research_log/experiments/`.
- Default to one file per backtest. Only group multiple backtests into one file when they are a tightly related batch testing the same change.
- Use `templates/experiment.md` as the canonical structure for files keyed by `experiment_id`.

### Frontmatter Guidance
- Keep structured fields in frontmatter and the narrative interpretation in the markdown body.
- Prefer simple scalar fields and short lists so the files remain easy to parse.
- Follow the body sections defined in the templates instead of inventing ad hoc layouts.

## Core Patterns (Python)
- Define a single class inheriting `QCAlgorithm`. Use `initialize` for setup and `on_data(self, slice)` as the primary data event handler.
- Use `add_equity` (or other `add_*`) in `initialize` and store the returned `Symbol` for later `Slice` access.
- Use indicator helpers like `self.sma(symbol, period, resolution)` for auto-updating indicators; use `self.set_warm_up` or `self.warm_up_indicator` so indicators are ready before trading.
- Use `self.history(...)` in `initialize` or runtime to fetch recent data for features and checks.

### Minimal Skeleton
```python
from AlgorithmImports import *

class MyAlgo(QCAlgorithm):
    def initialize(self):
        self.set_start_date(2023, 1, 1)
        self.set_cash(100000)
        self.symbol = self.add_equity("SPY", Resolution.MINUTE).symbol
        self.sma = self.sma(self.symbol, 20, Resolution.DAILY)
        self.set_warm_up(20, Resolution.DAILY)

    def on_data(self, slice: Slice):
        if self.is_warming_up:
            return
        if not slice.contains_key(self.symbol):
            return
        if self.sma.is_ready and not self.portfolio.invested:
            self.market_order(self.symbol, 10)
```

## Scheduling
- Use `self.schedule.on(date_rules..., time_rules..., callback)` for timed logic.
- Account for the fact that in backtests, scheduled events run on the next data slice; in live, they run at the scheduled clock time.

## Data Access
- Use `slice.contains_key(symbol)` before accessing per-symbol data.
- Access trade bars via `slice.bars[symbol]` and quote bars via `slice.quote_bars[symbol]` when present.

## Orders
- Use `self.market_order(symbol, quantity)` for immediate execution and `self.limit_order(symbol, quantity, limit_price)` for price-constrained orders.

## References
- Read `references/quantconnect-python-core.md` for quick patterns, doc links, and API nuances.
- Read `references/CLI.md` for a concise LEAN CLI workflow covering project creation, research, sync, backtests, and result review.
- Use `scripts/bootstrap_research_log.py` to initialize the research log directories.
- Use `scripts/generate_research_id.py` for deterministic hypothesis and experiment ids.
- Use `scripts/extract_backtest_metrics.py` to pull the key QuantConnect metrics from a saved results JSON file.

## Examples
- `examples/basic_buy_and_hold.py`: minimal single-asset QCAlgorithm skeleton.
- `examples/sma_crossover.py`: indicator-driven long/flat equity strategy.
- `examples/weekly_momentum_rotation.py`: scheduled rebalance using recent return ranking.
- `examples/event_aware_expiry_selection.py`: choosing valid option expiries around event days and exchange-open checks.
- `examples/scheduled_entry_retry.py`: scheduled entry attempts with retry-until-close logic.
- `examples/iron_condor_finder.py`: selecting and iteratively tweaking iron condor spreads from an option chain.
- `examples/combo_spread_entry.py`: placing a multi-leg combo order and storing trade state for later monitoring.
- `examples/combo_limit_order_manager.py`: managing a repriced combo limit order for multi-leg entries.
