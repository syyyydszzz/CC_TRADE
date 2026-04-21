from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON_SCRIPTS = REPO_ROOT / "scripts" / "python"

import sys

if str(PYTHON_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(PYTHON_SCRIPTS))

from qc_backtest_artifact import (  # noqa: E402
    canonicalize_backtest_artifact_file,
    canonicalize_backtest_payload,
    extract_metrics_summary,
    summarize_backtest_payload,
)


LEGACY_NESTED_PAYLOAD = {
    "success": True,
    "backtest": {
        "note": "",
        "name": "legacy-nested-demo",
        "projectId": 123456,
        "completed": True,
        "optimizationId": None,
        "backtestId": "nested-backtest-id",
        "status": "Completed.",
        "error": None,
        "stacktrace": None,
        "progress": 1,
        "hasInitializeError": False,
        "parameterSet": [],
        "runtimeStatistics": {
            "Equity": "$163,108.54",
            "Fees": "-$47.70",
            "Net Profit": "$52,239.35",
            "Probabilistic Sharpe Ratio": "11.512%",
            "Return": "63.11 %",
        },
        "statistics": {
            "Total Orders": "27",
            "Average Win": "10.43%",
            "Average Loss": "-4.09%",
            "Compounding Annual Return": "8.489%",
            "Drawdown": "27.500%",
            "Expectancy": "0.913",
            "Start Equity": "100000",
            "End Equity": "163108.54",
            "Net Profit": "63.109%",
            "Sharpe Ratio": "0.348",
            "Sortino Ratio": "0.308",
            "Win Rate": "54%",
            "Profit-Loss Ratio": "2.55",
        },
        "charts": ["Strategy Equity"],
    },
}


CANONICAL_FLAT_PAYLOAD = {
    "success": True,
    "backtestId": "nested-backtest-id",
    "projectId": 123456,
    "name": "legacy-nested-demo",
    "completed": True,
    "status": "Completed.",
    "error": None,
    "stacktrace": None,
    "hasInitializeError": False,
    "runtimeStatistics": {
        "Equity": "$163,108.54",
        "Fees": "-$47.70",
        "Net Profit": "$52,239.35",
        "Probabilistic Sharpe Ratio": "11.512%",
        "Return": "63.11 %",
    },
    "statistics": {
        "Total Orders": "27",
        "Average Win": "10.43%",
        "Average Loss": "-4.09%",
        "Compounding Annual Return": "8.489%",
        "Drawdown": "27.500%",
        "Expectancy": "0.913",
        "Start Equity": "100000",
        "End Equity": "163108.54",
        "Net Profit": "63.109%",
        "Sharpe Ratio": "0.348",
        "Sortino Ratio": "0.308",
        "Win Rate": "54%",
        "Profit-Loss Ratio": "2.55",
    },
    "optimizationId": None,
    "parameterSet": [],
    "progress": 1,
    "charts": ["Strategy Equity"],
    "note": "",
}


class QcBacktestArtifactTests(unittest.TestCase):
    def test_nested_payload_canonicalizes_to_flat_schema(self) -> None:
        canonical = canonicalize_backtest_payload(LEGACY_NESTED_PAYLOAD)

        self.assertEqual(canonical["backtestId"], "nested-backtest-id")
        self.assertEqual(canonical["projectId"], 123456)
        self.assertEqual(canonical["status"], "Completed.")
        self.assertNotIn("backtest", canonical)
        self.assertEqual(
            canonical["statistics"]["Compounding Annual Return"],
            LEGACY_NESTED_PAYLOAD["backtest"]["statistics"]["Compounding Annual Return"],
        )
        self.assertEqual(
            canonical["runtimeStatistics"]["Return"],
            LEGACY_NESTED_PAYLOAD["backtest"]["runtimeStatistics"]["Return"],
        )

    def test_extract_summary_matches_for_nested_and_flat_payloads(self) -> None:
        nested_summary = extract_metrics_summary(LEGACY_NESTED_PAYLOAD)
        flat_summary = extract_metrics_summary(CANONICAL_FLAT_PAYLOAD)

        self.assertEqual(nested_summary, flat_summary)
        self.assertEqual(nested_summary["backtest_id"], "nested-backtest-id")
        self.assertEqual(nested_summary["metrics"]["compounding_annual_return"], 8.489)
        self.assertEqual(nested_summary["runtime_statistics"]["runtime_return_pct"], 63.11)

    def test_summary_matches_for_nested_and_flat_payloads(self) -> None:
        nested_summary = summarize_backtest_payload(LEGACY_NESTED_PAYLOAD)
        flat_summary = summarize_backtest_payload(CANONICAL_FLAT_PAYLOAD)

        self.assertEqual(nested_summary, flat_summary)
        self.assertEqual(nested_summary["name"], "legacy-nested-demo")
        self.assertEqual(nested_summary["total_orders"], 27)

    def test_migration_is_flattening_and_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            artifact_path = Path(temp_dir) / "backtest.json"
            artifact_path.write_text(json.dumps(LEGACY_NESTED_PAYLOAD, indent=2) + "\n", encoding="utf-8")

            changed, _payload = canonicalize_backtest_artifact_file(artifact_path)
            self.assertTrue(changed)

            migrated = json.loads(artifact_path.read_text(encoding="utf-8"))
            self.assertNotIn("backtest", migrated)
            self.assertEqual(migrated["backtestId"], "nested-backtest-id")
            self.assertEqual(migrated["projectId"], 123456)
            self.assertEqual(migrated["status"], "Completed.")
            self.assertEqual(
                migrated["statistics"]["Net Profit"],
                LEGACY_NESTED_PAYLOAD["backtest"]["statistics"]["Net Profit"],
            )
            self.assertEqual(
                migrated["runtimeStatistics"]["Net Profit"],
                LEGACY_NESTED_PAYLOAD["backtest"]["runtimeStatistics"]["Net Profit"],
            )

            changed_again, _payload = canonicalize_backtest_artifact_file(artifact_path)
            self.assertFalse(changed_again)

    def test_missing_backtest_id_reports_clear_error(self) -> None:
        malformed = {
            "success": True,
            "completed": True,
            "status": "Completed.",
            "statistics": {},
            "runtimeStatistics": {},
        }

        with self.assertRaisesRegex(ValueError, "backtestId"):
            extract_metrics_summary(malformed)


if __name__ == "__main__":
    unittest.main()
