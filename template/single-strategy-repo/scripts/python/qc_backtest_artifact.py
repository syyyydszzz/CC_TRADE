#!/usr/bin/env python3
"""Shared helpers for reading and canonicalizing QuantConnect backtest artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, MutableMapping, Tuple


CORE_STAT_KEYS = {
    "Sharpe Ratio": "sharpe_ratio",
    "Sortino Ratio": "sortino_ratio",
    "Drawdown": "drawdown",
    "Net Profit": "net_profit",
    "Compounding Annual Return": "compounding_annual_return",
    "Win Rate": "win_rate",
    "Profit-Loss Ratio": "profit_loss_ratio",
    "Expectancy": "expectancy",
    "Average Win": "average_win",
    "Average Loss": "average_loss",
    "Total Orders": "total_orders",
}

RUNTIME_STAT_KEYS = {
    "Return": "runtime_return_pct",
    "Fees": "fees",
    "Net Profit": "runtime_net_profit",
    "Probabilistic Sharpe Ratio": "runtime_probabilistic_sharpe_ratio",
}

CANONICAL_FIELD_ORDER = (
    "success",
    "backtestId",
    "projectId",
    "name",
    "completed",
    "status",
    "error",
    "stacktrace",
    "hasInitializeError",
    "runtimeStatistics",
    "statistics",
    "optimizationId",
    "parameterSet",
    "progress",
    "charts",
    "note",
)

EXCLUDED_ROOT_KEYS = frozenset({"backtest"})
MISSING = object()


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
        try:
            return float(cleaned[:-1])
        except ValueError:
            return text

    try:
        if "." in cleaned:
            return float(cleaned)
        return int(cleaned)
    except ValueError:
        return text


def load_json_object(path: Path) -> Dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"Artifact root must be a JSON object: {path}")
    return payload


def _pick_present(mappings: Iterable[Mapping[str, Any]], key: str, default: Any = MISSING) -> Any:
    for mapping in mappings:
        if key in mapping:
            return mapping[key]
    return default


def _pick_mapping(mappings: Iterable[Mapping[str, Any]], key: str) -> Dict[str, Any]:
    for mapping in mappings:
        value = mapping.get(key, MISSING)
        if isinstance(value, dict):
            return dict(value)
    return {}


def _pick_bool(mappings: Iterable[Mapping[str, Any]], key: str, default: bool | None = None) -> bool | None:
    value = _pick_present(mappings, key, MISSING)
    if isinstance(value, bool):
        return value
    return default


def _coerce_success(
    root_payload: Mapping[str, Any],
    business_payload: Mapping[str, Any],
    completed: bool | None,
    error: Any,
    stacktrace: Any,
) -> bool:
    value = _pick_present((root_payload, business_payload), "success", MISSING)
    if isinstance(value, bool):
        return value
    if completed is not None:
        return completed and not bool(error or stacktrace)
    return not bool(error or stacktrace)


def canonicalize_backtest_payload(payload: Mapping[str, Any]) -> Dict[str, Any]:
    if not isinstance(payload, Mapping):
        raise ValueError("Backtest artifact root must be a mapping.")

    root_payload = dict(payload)
    nested_payload = root_payload.get("backtest")
    business_payload = dict(nested_payload) if isinstance(nested_payload, MutableMapping) else dict(root_payload)

    completed = _pick_bool((business_payload, root_payload), "completed")
    status = _pick_present((business_payload, root_payload), "status", None)
    error = _pick_present((business_payload, root_payload), "error", None)
    stacktrace = _pick_present((business_payload, root_payload), "stacktrace", None)

    canonical: Dict[str, Any] = {
        "success": _coerce_success(root_payload, business_payload, completed, error, stacktrace),
        "backtestId": _pick_present((business_payload, root_payload), "backtestId", None),
        "projectId": _pick_present((business_payload, root_payload), "projectId", None),
        "name": _pick_present((business_payload, root_payload), "name", None),
        "completed": completed,
        "status": status,
        "error": error,
        "stacktrace": stacktrace,
        "hasInitializeError": _pick_bool((business_payload, root_payload), "hasInitializeError", False),
        "runtimeStatistics": _pick_mapping((business_payload, root_payload), "runtimeStatistics"),
        "statistics": _pick_mapping((business_payload, root_payload), "statistics"),
        "optimizationId": _pick_present((business_payload, root_payload), "optimizationId", None),
        "parameterSet": _pick_present((business_payload, root_payload), "parameterSet", None),
        "progress": _pick_present((business_payload, root_payload), "progress", None),
        "charts": _pick_present((business_payload, root_payload), "charts", None),
        "note": _pick_present((business_payload, root_payload), "note", None),
    }

    ordered: Dict[str, Any] = {}
    for key in CANONICAL_FIELD_ORDER:
        ordered[key] = canonical[key]

    for source in (business_payload, root_payload):
        for key, value in source.items():
            if key in ordered or key in EXCLUDED_ROOT_KEYS:
                continue
            ordered[key] = value

    return ordered


def dumps_canonical_backtest_payload(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"


def load_canonical_backtest_artifact(path: Path, rewrite: bool = False) -> Dict[str, Any]:
    raw_payload = load_json_object(path)
    canonical_payload = canonicalize_backtest_payload(raw_payload)
    if rewrite:
        canonical_text = dumps_canonical_backtest_payload(canonical_payload)
        current_text = path.read_text(encoding="utf-8")
        if current_text != canonical_text:
            path.write_text(canonical_text, encoding="utf-8")
    return canonical_payload


def canonicalize_backtest_artifact_file(path: Path) -> Tuple[bool, Dict[str, Any]]:
    canonical_payload = load_canonical_backtest_artifact(path, rewrite=False)
    canonical_text = dumps_canonical_backtest_payload(canonical_payload)
    current_text = path.read_text(encoding="utf-8")
    changed = current_text != canonical_text
    if changed:
        path.write_text(canonical_text, encoding="utf-8")
    return changed, canonical_payload


def require_backtest_identifier(payload: Mapping[str, Any]) -> str:
    backtest_id = payload.get("backtestId")
    if not isinstance(backtest_id, str) or not backtest_id.strip():
        raise ValueError("Backtest artifact is missing canonical top-level backtestId.")
    return backtest_id


def summarize_backtest_payload(payload: Mapping[str, Any]) -> Dict[str, Any]:
    canonical_payload = canonicalize_backtest_payload(payload)
    summary: Dict[str, Any] = {}

    name = canonical_payload.get("name")
    if isinstance(name, str) and name.strip():
        summary["name"] = name

    status = canonical_payload.get("status")
    if isinstance(status, str) and status.strip():
        summary["status"] = status

    runtime_error = canonical_payload.get("error") or canonical_payload.get("stacktrace")
    if isinstance(runtime_error, str) and runtime_error.strip():
        summary["runtime_error"] = runtime_error

    statistics = canonical_payload.get("statistics")
    if isinstance(statistics, dict):
        for raw_key, normalized_key in CORE_STAT_KEYS.items():
            value = normalize_scalar(statistics.get(raw_key))
            if value is not None:
                summary[normalized_key] = value

        start_equity = normalize_scalar(statistics.get("Start Equity"))
        end_equity = normalize_scalar(statistics.get("End Equity"))
        if start_equity is not None:
            summary["start_equity"] = start_equity
        if end_equity is not None:
            summary["end_equity"] = end_equity

    runtime_statistics = canonical_payload.get("runtimeStatistics")
    if isinstance(runtime_statistics, dict):
        for raw_key, normalized_key in RUNTIME_STAT_KEYS.items():
            value = normalize_scalar(runtime_statistics.get(raw_key))
            if value is not None:
                summary[normalized_key] = value

    return summary


def extract_metrics_summary(payload: Mapping[str, Any]) -> Dict[str, Any]:
    canonical_payload = canonicalize_backtest_payload(payload)
    require_backtest_identifier(canonical_payload)

    metrics = {
        normalized_key: normalize_scalar((canonical_payload.get("statistics") or {}).get(raw_key))
        for raw_key, normalized_key in CORE_STAT_KEYS.items()
    }
    runtime_metrics = {
        normalized_key: normalize_scalar((canonical_payload.get("runtimeStatistics") or {}).get(raw_key))
        for raw_key, normalized_key in RUNTIME_STAT_KEYS.items()
    }

    return {
        "backtest_id": canonical_payload.get("backtestId"),
        "project_id": canonical_payload.get("projectId"),
        "backtest_name": canonical_payload.get("name"),
        "status": canonical_payload.get("status"),
        "completed": canonical_payload.get("completed"),
        "runtime_error": canonical_payload.get("error") or canonical_payload.get("stacktrace"),
        "order_count": normalize_scalar((canonical_payload.get("statistics") or {}).get("Total Orders")),
        "metrics": metrics,
        "runtime_statistics": runtime_metrics,
    }
