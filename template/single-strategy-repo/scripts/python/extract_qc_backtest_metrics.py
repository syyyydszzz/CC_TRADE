#!/usr/bin/env python3
"""Extract a stable metric summary from a QuantConnect backtest artifact."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict

from qc_backtest_artifact import extract_metrics_summary, load_canonical_backtest_artifact


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract normalized metrics from a saved QuantConnect backtest JSON artifact."
    )
    parser.add_argument("--repo-root")
    parser.add_argument("--artifact-path", required=True)
    parser.add_argument("--json", action="store_true", dest="json_mode")
    return parser.parse_args()


def resolve_artifact(repo_root: Path, raw_path: str) -> Path:
    path_obj = Path(raw_path)
    candidates = [path_obj]
    if not path_obj.is_absolute():
        candidates.insert(0, repo_root / path_obj)

    for candidate in candidates:
        candidate = candidate.expanduser().resolve()
        if candidate.exists():
            return candidate

    raise FileNotFoundError(f"Artifact does not exist: {raw_path}")


def repo_relative_or_absolute(repo_root: Path, path: Path) -> str:
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return str(path)


def extract_summary(payload: Dict[str, Any], artifact_path: Path, repo_root: Path) -> Dict[str, Any]:
    summary = extract_metrics_summary(payload)
    summary["artifact_path"] = repo_relative_or_absolute(repo_root, artifact_path)
    return summary


def print_human(summary: Dict[str, Any]) -> None:
    print(f"Artifact: {summary['artifact_path']}")
    print(f"Backtest: {summary.get('backtest_name') or 'unknown'}")
    print(f"Backtest ID: {summary.get('backtest_id') or 'unknown'}")
    print(f"Status: {summary.get('status') or 'unknown'}")
    print(f"Completed: {summary.get('completed')}")
    print(f"Runtime error: {summary.get('runtime_error') or 'none'}")
    print(f"Order count: {summary.get('order_count')}")
    print("Metrics:")
    for key, value in summary["metrics"].items():
        print(f"  - {key}: {value}")
    print("Runtime statistics:")
    for key, value in summary["runtime_statistics"].items():
        print(f"  - {key}: {value}")


def main() -> int:
    args = parse_args()
    raw_root = args.repo_root
    if raw_root is None:
        print("ERROR: --repo-root is required.", file=sys.stderr)
        return 2

    repo_root = Path(raw_root).expanduser().resolve()

    try:
        artifact_path = resolve_artifact(repo_root, args.artifact_path)
        payload = load_canonical_backtest_artifact(artifact_path, rewrite=False)
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"ERROR: failed to read artifact: {exc}", file=sys.stderr)
        return 1

    summary = extract_summary(payload, artifact_path, repo_root)

    if args.json_mode:
        print(json.dumps(summary, indent=2, ensure_ascii=False, sort_keys=True))
    else:
        print_human(summary)

    return 0


if __name__ == "__main__":
    sys.exit(main())
