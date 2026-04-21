#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


CORE_STAT_KEYS = {
    "Total Orders": "total_orders",
    "Average Win": "average_win",
    "Average Loss": "average_loss",
    "Compounding Annual Return": "compounding_annual_return",
    "Drawdown": "drawdown",
    "Expectancy": "expectancy",
    "Net Profit": "net_profit",
    "Profit-Loss Ratio": "profit_loss_ratio",
    "Sharpe Ratio": "sharpe_ratio",
    "Sortino Ratio": "sortino_ratio",
    "Win Rate": "win_rate",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Extract frontmatter-ready QuantConnect metrics from a saved backtest "
            "results JSON payload."
        )
    )
    parser.add_argument("results_file", help="Path to the saved QuantConnect results JSON file.")
    parser.add_argument(
        "--indent",
        type=int,
        default=2,
        help="Indent level for JSON output. Defaults to 2.",
    )
    return parser.parse_args()


def normalize_scalar(value: Any) -> int | float | str | None:
    if value is None:
        return None

    if isinstance(value, (int, float)):
        return value

    if not isinstance(value, str):
        return str(value)

    text = value.strip()
    if text == "":
        return None

    cleaned = text.replace(",", "").replace("$", "")
    if cleaned.endswith("%"):
        number_text = cleaned[:-1]
        try:
            return float(number_text)
        except ValueError:
            return text

    try:
        if "." in cleaned:
            return float(cleaned)
        return int(cleaned)
    except ValueError:
        return text


def extract_metrics(payload: dict[str, Any], source_path: Path) -> dict[str, Any]:
    state = payload.get("state") or {}
    algorithm_configuration = payload.get("algorithmConfiguration") or {}
    statistics = payload.get("statistics") or {}
    runtime_statistics = payload.get("runtimeStatistics") or {}

    quantconnect_results = {
        normalized_key: statistics.get(raw_key, "")
        for raw_key, normalized_key in CORE_STAT_KEYS.items()
    }

    parsed_metrics = {
        normalized_key: normalize_scalar(statistics.get(raw_key))
        for raw_key, normalized_key in CORE_STAT_KEYS.items()
    }

    extra_statistics = {
        key: value
        for key, value in statistics.items()
        if key not in CORE_STAT_KEYS
    }

    return {
        "source_file": str(source_path),
        "backtest_name": state.get("Name") or algorithm_configuration.get("name"),
        "status": state.get("Status"),
        "runtime_error": state.get("RuntimeError") or None,
        "start_time_utc": state.get("StartTime"),
        "end_time_utc": state.get("EndTime"),
        "backtest_start": (algorithm_configuration.get("startDate") or "")[:10] or None,
        "backtest_end": (algorithm_configuration.get("endDate") or "")[:10] or None,
        "order_count": normalize_scalar(state.get("OrderCount")),
        "log_count": normalize_scalar(state.get("LogCount")),
        "insight_count": normalize_scalar(state.get("InsightCount")),
        "quantconnect_results": quantconnect_results,
        "parsed_metrics": parsed_metrics,
        "runtime_statistics": runtime_statistics,
        "extra_statistics": extra_statistics,
    }


def main() -> None:
    args = parse_args()
    source_path = Path(args.results_file).expanduser().resolve()
    payload = json.loads(source_path.read_text())
    extracted = extract_metrics(payload, source_path)
    print(json.dumps(extracted, indent=args.indent, sort_keys=True))


if __name__ == "__main__":
    main()
