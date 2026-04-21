from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON_SCRIPTS = REPO_ROOT / "scripts" / "python"

if str(PYTHON_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(PYTHON_SCRIPTS))

import result_workspace  # noqa: E402


LEGACY_NESTED_BACKTEST = {
    "success": True,
    "backtest": {
        "name": "nested-backtest",
        "projectId": 123456,
        "completed": True,
        "backtestId": "nested-bt-001",
        "status": "Completed.",
        "error": None,
        "stacktrace": None,
        "hasInitializeError": False,
        "runtimeStatistics": {
            "Return": "63.11 %",
            "Fees": "-$47.70",
            "Net Profit": "$52,239.35",
            "Probabilistic Sharpe Ratio": "11.512%",
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
        "note": "",
    },
}

CANONICAL_FLAT_BACKTEST = {
    "success": True,
    "backtestId": "flat-bt-001",
    "projectId": 123456,
    "name": "flat-backtest",
    "completed": True,
    "status": "Completed.",
    "error": None,
    "stacktrace": None,
    "hasInitializeError": False,
    "runtimeStatistics": {
        "Return": "63.11 %",
        "Fees": "-$47.70",
        "Net Profit": "$52,239.35",
        "Probabilistic Sharpe Ratio": "11.512%",
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
    "note": "",
}

COMPILE_PAYLOAD = {
    "success": True,
    "compileId": "compile-001",
    "errors": [],
    "warnings": [],
}


class ResultWorkspaceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name)
        self.strategy_dir = self.root / "algorithms" / "demo_strategy"
        self.results_dir = self.strategy_dir / "results"
        self.run_id = "run-001"
        self.run_dir = self.results_dir / "artifacts" / "runs" / self.run_id

        (self.root / "workflow" / "templates").mkdir(parents=True, exist_ok=True)
        self.strategy_dir.mkdir(parents=True, exist_ok=True)
        self.run_dir.mkdir(parents=True, exist_ok=True)
        (self.results_dir / "report.md").write_text("# Report\n", encoding="utf-8")
        (self.strategy_dir / "spec.md").write_text("# Spec\n", encoding="utf-8")

        shutil.copyfile(
            REPO_ROOT / "workflow" / "templates" / "result-run-template.yaml",
            self.root / "workflow" / "templates" / "result-run-template.yaml",
        )
        shutil.copyfile(
            REPO_ROOT / "workflow" / "templates" / "result-state-template.yaml",
            self.root / "workflow" / "templates" / "result-state-template.yaml",
        )

    def write_artifacts(self, backtest_payload: dict) -> None:
        (self.run_dir / "compile.json").write_text(json.dumps(COMPILE_PAYLOAD, indent=2) + "\n", encoding="utf-8")
        (self.run_dir / "backtest.json").write_text(json.dumps(backtest_payload, indent=2) + "\n", encoding="utf-8")

    def load_run_yaml(self) -> dict:
        return yaml.safe_load((self.run_dir / "run.yaml").read_text(encoding="utf-8"))

    def load_state_yaml(self) -> dict:
        return yaml.safe_load((self.results_dir / "state.yaml").read_text(encoding="utf-8"))

    def test_record_run_supports_nested_and_flat_backtests_with_same_summary(self) -> None:
        self.write_artifacts(LEGACY_NESTED_BACKTEST)
        result_workspace.record_run(
            buildforce_root=self.root,
            strategy_dir=self.strategy_dir,
            json_mode=False,
            run_id=self.run_id,
            created_at="2026-04-13T00:00:00Z",
            open_project="demo_strategy",
            stages=["compile", "backtest"],
            parameters_json=None,
            decision_value="passed",
            decision_reason="Nested artifact test.",
            notes=None,
            notes_file=None,
        )
        nested_run = self.load_run_yaml()
        nested_backtest_json = json.loads((self.run_dir / "backtest.json").read_text(encoding="utf-8"))
        self.assertNotIn("backtest", nested_backtest_json)

        nested_summary = nested_run["backtest"]["summary"]
        self.assertEqual(nested_run["backtest"]["backtest_id"], "nested-bt-001")
        self.assertEqual(nested_summary["compounding_annual_return"], 8.489)

        flat_run_id = "run-002"
        flat_run_dir = self.results_dir / "artifacts" / "runs" / flat_run_id
        flat_run_dir.mkdir(parents=True, exist_ok=True)
        (flat_run_dir / "compile.json").write_text(json.dumps(COMPILE_PAYLOAD, indent=2) + "\n", encoding="utf-8")
        (flat_run_dir / "backtest.json").write_text(
            json.dumps(CANONICAL_FLAT_BACKTEST, indent=2) + "\n",
            encoding="utf-8",
        )
        result_workspace.record_run(
            buildforce_root=self.root,
            strategy_dir=self.strategy_dir,
            json_mode=False,
            run_id=flat_run_id,
            created_at="2026-04-13T00:01:00Z",
            open_project="demo_strategy",
            stages=["compile", "backtest"],
            parameters_json=None,
            decision_value="passed",
            decision_reason="Flat artifact test.",
            notes=None,
            notes_file=None,
        )

        flat_run = yaml.safe_load((flat_run_dir / "run.yaml").read_text(encoding="utf-8"))
        flat_summary = flat_run["backtest"]["summary"]

        self.assertEqual(
            {key: value for key, value in nested_summary.items() if key != "name"},
            {key: value for key, value in flat_summary.items() if key != "name"},
        )

    def test_record_run_fails_when_backtest_id_is_missing(self) -> None:
        malformed = {
            "success": True,
            "completed": True,
            "status": "Completed.",
            "statistics": {},
            "runtimeStatistics": {},
        }
        self.write_artifacts(malformed)

        with self.assertRaisesRegex(ValueError, "backtest_id"):
            result_workspace.record_run(
                buildforce_root=self.root,
                strategy_dir=self.strategy_dir,
                json_mode=False,
                run_id=self.run_id,
                created_at="2026-04-13T00:00:00Z",
                open_project="demo_strategy",
                stages=["compile", "backtest"],
                parameters_json=None,
                decision_value="passed",
                decision_reason="Malformed artifact test.",
                notes=None,
                notes_file=None,
            )

    def test_record_state_normalizes_completed_to_passed(self) -> None:
        self.write_artifacts(CANONICAL_FLAT_BACKTEST)
        result_workspace.record_run(
            buildforce_root=self.root,
            strategy_dir=self.strategy_dir,
            json_mode=False,
            run_id=self.run_id,
            created_at="2026-04-13T00:00:00Z",
            open_project="demo_strategy",
            stages=["compile", "backtest"],
            parameters_json=None,
            decision_value="passed",
            decision_reason="State normalization test.",
            notes=None,
            notes_file=None,
        )

        result_workspace.record_state(
            buildforce_root=self.root,
            strategy_dir=self.strategy_dir,
            json_mode=False,
            run_id=self.run_id,
            status="completed",
            latest_stage="backtest",
            last_validated_at="2026-04-13T00:00:00Z",
            next_actions=["Review results."],
            change_reference="change-001",
            runtime_session="opsx-001",
        )

        state = self.load_state_yaml()
        self.assertEqual(state["status"], "passed")
        self.assertEqual(state["latest_compile"]["status"], "passed")
        self.assertEqual(state["latest_compile"]["compile_id"], "compile-001")
        self.assertEqual(
            state["latest_compile"]["artifact"],
            "results/artifacts/runs/run-001/compile.json",
        )
        self.assertEqual(state["latest_backtest"]["status"], "passed")
        self.assertEqual(state["latest_backtest"]["backtest_id"], "flat-bt-001")
        self.assertTrue(state["latest_backtest"]["summary"])
        self.assertEqual(state["refs"]["change"], "change-001")
        self.assertEqual(state["refs"]["runtime_session"], "opsx-001")
        self.assertNotIn("buildforce_session", state["refs"])
        self.assertNotIn("achieve_session", state["refs"])
        self.assertEqual(
            result_workspace.validate_workspace(self.root, self.strategy_dir, json_mode=False),
            0,
        )

    def test_record_state_normalizes_success_to_passed(self) -> None:
        self.write_artifacts(CANONICAL_FLAT_BACKTEST)
        result_workspace.record_run(
            buildforce_root=self.root,
            strategy_dir=self.strategy_dir,
            json_mode=False,
            run_id=self.run_id,
            created_at="2026-04-13T00:00:00Z",
            open_project="demo_strategy",
            stages=["compile", "backtest"],
            parameters_json=None,
            decision_value="passed",
            decision_reason="Alias normalization test.",
            notes=None,
            notes_file=None,
        )

        result_workspace.record_state(
            buildforce_root=self.root,
            strategy_dir=self.strategy_dir,
            json_mode=False,
            run_id=self.run_id,
            status="success",
            latest_stage="backtest",
            last_validated_at="2026-04-13T00:00:00Z",
            next_actions=["Review results."],
            change_reference=None,
            runtime_session=None,
        )

        state = self.load_state_yaml()
        self.assertEqual(state["status"], "passed")

    def test_record_state_accepts_legacy_reference_kwargs(self) -> None:
        self.write_artifacts(CANONICAL_FLAT_BACKTEST)
        result_workspace.record_run(
            buildforce_root=self.root,
            strategy_dir=self.strategy_dir,
            json_mode=False,
            run_id=self.run_id,
            created_at="2026-04-13T00:00:00Z",
            open_project="demo_strategy",
            stages=["compile", "backtest"],
            parameters_json=None,
            decision_value="passed",
            decision_reason="Legacy kwargs compatibility test.",
            notes=None,
            notes_file=None,
        )

        result_workspace.record_state(
            buildforce_root=self.root,
            strategy_dir=self.strategy_dir,
            json_mode=False,
            run_id=self.run_id,
            status="passed",
            latest_stage="backtest",
            last_validated_at="2026-04-13T00:00:00Z",
            next_actions=[],
            buildforce_session="legacy-bf-001",
            achieve_session="legacy-ach-001",
        )

        state = self.load_state_yaml()
        self.assertEqual(state["refs"]["change"], "legacy-bf-001")
        self.assertEqual(state["refs"]["runtime_session"], "legacy-ach-001")

    def test_record_state_rejects_achieved_with_boundary_error(self) -> None:
        self.write_artifacts(CANONICAL_FLAT_BACKTEST)
        result_workspace.record_run(
            buildforce_root=self.root,
            strategy_dir=self.strategy_dir,
            json_mode=False,
            run_id=self.run_id,
            created_at="2026-04-13T00:00:00Z",
            open_project="demo_strategy",
            stages=["compile", "backtest"],
            parameters_json=None,
            decision_value="passed",
            decision_reason="Achieved rejection test.",
            notes=None,
            notes_file=None,
        )

        with self.assertRaisesRegex(ValueError, "Achieve runtime status"):
            result_workspace.record_state(
                buildforce_root=self.root,
                strategy_dir=self.strategy_dir,
                json_mode=False,
                run_id=self.run_id,
                status="achieved",
                latest_stage="backtest",
                last_validated_at="2026-04-13T00:00:00Z",
                next_actions=["Review results."],
                change_reference=None,
                runtime_session=None,
            )

    def test_record_state_requires_existing_run_summary(self) -> None:
        self.write_artifacts(CANONICAL_FLAT_BACKTEST)
        with self.assertRaisesRegex(ValueError, "Run summary does not exist"):
            result_workspace.record_state(
                buildforce_root=self.root,
                strategy_dir=self.strategy_dir,
                json_mode=False,
                run_id=self.run_id,
                status="passed",
                latest_stage="backtest",
                last_validated_at="2026-04-13T00:00:00Z",
                next_actions=["Review results."],
                change_reference="change-001",
                runtime_session=None,
            )

    def test_record_run_requires_compile_before_later_stage(self) -> None:
        self.write_artifacts(CANONICAL_FLAT_BACKTEST)

        with self.assertRaisesRegex(ValueError, "compile is required before backtest"):
            result_workspace.record_run(
                buildforce_root=self.root,
                strategy_dir=self.strategy_dir,
                json_mode=False,
                run_id=self.run_id,
                created_at="2026-04-13T00:00:00Z",
                open_project="demo_strategy",
                stages=["backtest"],
                parameters_json=None,
                decision_value="passed",
                decision_reason="Missing compile evidence test.",
                notes=None,
                notes_file=None,
            )

    def test_record_run_requires_stage_order(self) -> None:
        self.write_artifacts(CANONICAL_FLAT_BACKTEST)

        with self.assertRaisesRegex(ValueError, "must follow execution order"):
            result_workspace.record_run(
                buildforce_root=self.root,
                strategy_dir=self.strategy_dir,
                json_mode=False,
                run_id=self.run_id,
                created_at="2026-04-13T00:00:00Z",
                open_project="demo_strategy",
                stages=["backtest", "compile"],
                parameters_json=None,
                decision_value="passed",
                decision_reason="Out-of-order stage test.",
                notes=None,
                notes_file=None,
            )

    def test_record_state_requires_compile_before_backtest_stage(self) -> None:
        self.write_artifacts(CANONICAL_FLAT_BACKTEST)
        result_workspace.record_run(
            buildforce_root=self.root,
            strategy_dir=self.strategy_dir,
            json_mode=False,
            run_id=self.run_id,
            created_at="2026-04-13T00:00:00Z",
            open_project="demo_strategy",
            stages=["compile", "backtest"],
            parameters_json=None,
            decision_value="passed",
            decision_reason="Tampered compile evidence test.",
            notes=None,
            notes_file=None,
        )

        run_data = self.load_run_yaml()
        run_data["compile"] = result_workspace.default_stage_section("compile_id")
        (self.run_dir / "run.yaml").write_text(yaml.safe_dump(run_data, sort_keys=False), encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "requires compile evidence"):
            result_workspace.record_state(
                buildforce_root=self.root,
                strategy_dir=self.strategy_dir,
                json_mode=False,
                run_id=self.run_id,
                status="passed",
                latest_stage="backtest",
                last_validated_at="2026-04-13T00:00:00Z",
                next_actions=["Review results."],
                change_reference="change-001",
                runtime_session=None,
            )

    def test_validate_workspace_rejects_state_compile_mismatch(self) -> None:
        self.write_artifacts(CANONICAL_FLAT_BACKTEST)
        result_workspace.record_run(
            buildforce_root=self.root,
            strategy_dir=self.strategy_dir,
            json_mode=False,
            run_id=self.run_id,
            created_at="2026-04-13T00:00:00Z",
            open_project="demo_strategy",
            stages=["compile", "backtest"],
            parameters_json=None,
            decision_value="passed",
            decision_reason="Mismatch detection test.",
            notes=None,
            notes_file=None,
        )
        result_workspace.record_state(
            buildforce_root=self.root,
            strategy_dir=self.strategy_dir,
            json_mode=False,
            run_id=self.run_id,
            status="passed",
            latest_stage="backtest",
            last_validated_at="2026-04-13T00:00:00Z",
            next_actions=["Review results."],
            change_reference="change-001",
            runtime_session="opsx-001",
        )

        state = self.load_state_yaml()
        state["latest_compile"] = {
            "status": "not_run",
            "compile_id": None,
            "artifact": None,
            "summary": {},
        }
        (self.results_dir / "state.yaml").write_text(yaml.safe_dump(state, sort_keys=False), encoding="utf-8")

        self.assertEqual(
            result_workspace.validate_workspace(self.root, self.strategy_dir, json_mode=False),
            1,
        )


if __name__ == "__main__":
    unittest.main()
