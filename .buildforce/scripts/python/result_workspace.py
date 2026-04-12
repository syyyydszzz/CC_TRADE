#!/usr/bin/env python3
"""Initialize and validate strategy result workspaces."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import yaml
except ModuleNotFoundError:
    print(
        "ERROR: PyYAML is required for result workspace tooling. "
        "Install dependencies with `pip install -r requirements.txt`.",
        file=sys.stderr,
    )
    sys.exit(2)


ALLOWED_STATUS = {"not_run", "passed", "failed", "blocked", "needs_iteration"}
ALLOWED_STAGE = {"compile", "backtest", "optimization", "validation"}
REPORT_HEADINGS = [
    "## Current Verdict",
    "## Latest Validated Run",
    "## Key Metrics",
    "## Why",
    "## Next Actions",
    "## Artifact References",
]
LATEST_SECTION_SPECS = {
    "latest_compile": "compile_id",
    "latest_backtest": "backtest_id",
    "latest_optimization": "optimization_id",
    "latest_validation": "validation_id",
}
RUN_STAGE_SPECS = {
    "compile": "compile_id",
    "backtest": "backtest_id",
    "optimization": "optimization_id",
    "validation": "validation_id",
}


def is_relative_to(path: Path, other: Path) -> bool:
    try:
        path.relative_to(other)
        return True
    except ValueError:
        return False


def normalize_strategy_path(buildforce_root: Path, strategy_path: str) -> Path:
    candidate = (buildforce_root / strategy_path).resolve()
    algorithms_root = (buildforce_root / "algorithms").resolve()

    if not is_relative_to(candidate, algorithms_root):
        raise ValueError("Strategy path must resolve under algorithms/.")
    if not candidate.exists():
        raise ValueError(f"Strategy path does not exist: {strategy_path}")
    if not candidate.is_dir():
        raise ValueError(f"Strategy path is not a directory: {strategy_path}")
    return candidate


def as_repo_relative(path: Path, buildforce_root: Path) -> str:
    return path.resolve().relative_to(buildforce_root.resolve()).as_posix()


def load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text())


def dump_yaml(path: Path, payload: Any) -> None:
    text = yaml.safe_dump(
        payload,
        sort_keys=False,
        default_flow_style=False,
        allow_unicode=False,
    )
    path.write_text(text)


def resolve_existing_reference(buildforce_root: Path, strategy_dir: Path, raw_path: str) -> Optional[Path]:
    path_obj = Path(raw_path)
    candidates: List[Path] = []
    if path_obj.is_absolute():
        candidates.append(path_obj)
    else:
        candidates.append(strategy_dir / path_obj)
        candidates.append(buildforce_root / path_obj)
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def check_python_environment() -> None:
    if sys.version_info < (3, 9):
        print("ERROR: python3 3.9+ is required for result workspace tooling.", file=sys.stderr)
        sys.exit(2)


def init_workspace(buildforce_root: Path, strategy_dir: Path, json_mode: bool, force: bool) -> int:
    strategy_id = strategy_dir.name
    results_root = strategy_dir / "results"
    artifacts_root = results_root / "artifacts"
    runs_root = artifacts_root / "runs"
    state_path = results_root / "state.yaml"
    report_path = results_root / "report.md"

    template_state = load_yaml(buildforce_root / ".buildforce/templates/result-state-template.yaml")
    report_template = (buildforce_root / ".buildforce/templates/result-report-template.md").read_text()

    state_payload = template_state
    state_payload["strategy_id"] = strategy_id
    state_payload["refs"]["spec"] = "spec.md" if (strategy_dir / "spec.md").exists() else None
    state_payload["refs"]["report"] = "results/report.md"

    report_payload = report_template.replace("<strategy-id>", strategy_id)

    created: List[str] = []
    skipped: List[str] = []
    overwritten: List[str] = []

    for directory in (results_root, artifacts_root, runs_root):
        if directory.exists():
            skipped.append(as_repo_relative(directory, buildforce_root))
        else:
            directory.mkdir(parents=True, exist_ok=True)
            created.append(as_repo_relative(directory, buildforce_root))

    if state_path.exists() and not force:
        skipped.append(as_repo_relative(state_path, buildforce_root))
    else:
        if state_path.exists():
            overwritten.append(as_repo_relative(state_path, buildforce_root))
        else:
            created.append(as_repo_relative(state_path, buildforce_root))
        dump_yaml(state_path, state_payload)

    if report_path.exists() and not force:
        skipped.append(as_repo_relative(report_path, buildforce_root))
    else:
        if report_path.exists():
            overwritten.append(as_repo_relative(report_path, buildforce_root))
        else:
            created.append(as_repo_relative(report_path, buildforce_root))
        report_path.write_text(report_payload)

    payload = {
        "strategy_path": as_repo_relative(strategy_dir, buildforce_root),
        "strategy_id": strategy_id,
        "results_root": as_repo_relative(results_root, buildforce_root),
        "created": created,
        "skipped": skipped,
        "overwritten": overwritten,
    }

    if json_mode:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(f"Initialized result workspace for {payload['strategy_path']}")
        print(f"Results root: {payload['results_root']}")
        print(f"Created: {', '.join(created) if created else 'none'}")
        print(f"Skipped: {', '.join(skipped) if skipped else 'none'}")
        print(f"Overwritten: {', '.join(overwritten) if overwritten else 'none'}")

    return 0


def expect(condition: bool, errors: List[str], message: str) -> None:
    if not condition:
        errors.append(message)


def expect_string(value: Any, errors: List[str], message: str, allow_none: bool = False) -> None:
    if value is None and allow_none:
        return
    if not isinstance(value, str) or not value.strip():
        errors.append(message)


def validate_latest_section(
    buildforce_root: Path,
    strategy_dir: Path,
    section_name: str,
    section: Any,
    id_key: str,
    errors: List[str],
) -> None:
    if not isinstance(section, dict):
        errors.append(f"{section_name} must be a mapping.")
        return

    for key in ("status", id_key, "artifact", "summary"):
        if key not in section:
            errors.append(f"{section_name}.{key} is required.")

    status = section.get("status")
    if status not in ALLOWED_STATUS:
        errors.append(f"{section_name}.status must be one of {sorted(ALLOWED_STATUS)}.")

    identifier = section.get(id_key)
    if identifier is not None and not isinstance(identifier, (str, int)):
        errors.append(f"{section_name}.{id_key} must be null, string, or integer.")

    artifact = section.get("artifact")
    if artifact is not None:
        if not isinstance(artifact, str) or not artifact.strip():
            errors.append(f"{section_name}.artifact must be null or a non-empty string.")
        elif resolve_existing_reference(buildforce_root, strategy_dir, artifact) is None:
            errors.append(f"{section_name}.artifact does not exist: {artifact}")

    if not isinstance(section.get("summary"), dict):
        errors.append(f"{section_name}.summary must be a mapping.")


def validate_run_yaml(
    buildforce_root: Path,
    strategy_dir: Path,
    run_dir: Path,
    errors: List[str],
) -> None:
    run_yaml_path = run_dir / "run.yaml"
    if not run_yaml_path.exists():
        errors.append(f"Missing latest run summary: {as_repo_relative(run_yaml_path, buildforce_root)}")
        return

    try:
        run_data = load_yaml(run_yaml_path)
    except Exception as exc:  # noqa: BLE001
        errors.append(f"Failed to parse {as_repo_relative(run_yaml_path, buildforce_root)}: {exc}")
        return

    if not isinstance(run_data, dict):
        errors.append("run.yaml must be a mapping.")
        return

    required_fields = [
        "run_id",
        "created_at",
        "stage_sequence",
        "open_project",
        "local_strategy_path",
        "parameters",
        "compile",
        "backtest",
        "optimization",
        "validation",
        "decision",
        "notes",
    ]
    for field in required_fields:
        if field not in run_data:
            errors.append(f"run.yaml is missing required field: {field}")

    run_id = run_data.get("run_id")
    if run_id != run_dir.name:
        errors.append(f"run.yaml run_id must match directory name: expected {run_dir.name}, got {run_id}")

    expect_string(run_data.get("created_at"), errors, "run.yaml.created_at must be a non-empty string.")
    stage_sequence = run_data.get("stage_sequence")
    if not isinstance(stage_sequence, list) or not stage_sequence or not all(
        isinstance(item, str) and item.strip() for item in stage_sequence
    ):
        errors.append("run.yaml.stage_sequence must be a non-empty list of strings.")

    expect_string(run_data.get("open_project"), errors, "run.yaml.open_project must be a non-empty string.")
    expect_string(
        run_data.get("local_strategy_path"),
        errors,
        "run.yaml.local_strategy_path must be a non-empty string.",
    )

    if not isinstance(run_data.get("parameters"), dict):
        errors.append("run.yaml.parameters must be a mapping.")

    for section_name, id_key in RUN_STAGE_SPECS.items():
        validate_latest_section(
            buildforce_root,
            strategy_dir,
            f"run.yaml.{section_name}",
            run_data.get(section_name),
            id_key,
            errors,
        )

    decision = run_data.get("decision")
    if not isinstance(decision, dict):
        errors.append("run.yaml.decision must be a mapping.")
    else:
        expect_string(decision.get("value"), errors, "run.yaml.decision.value must be a non-empty string.")
        expect_string(decision.get("reason"), errors, "run.yaml.decision.reason must be a non-empty string.")

    expect_string(run_data.get("notes"), errors, "run.yaml.notes must be a string.")


def validate_report(report_path: Path, errors: List[str]) -> None:
    text = report_path.read_text()
    for heading in REPORT_HEADINGS:
        if heading not in text:
            errors.append(f"report.md is missing required heading: {heading}")


def validate_workspace(buildforce_root: Path, strategy_dir: Path, json_mode: bool) -> int:
    errors: List[str] = []
    warnings: List[str] = []

    results_root = strategy_dir / "results"
    state_path = results_root / "state.yaml"
    report_path = results_root / "report.md"
    runs_root = results_root / "artifacts" / "runs"

    expect(results_root.exists(), errors, "Missing results/ directory.")
    expect(state_path.exists(), errors, "Missing results/state.yaml.")
    expect(report_path.exists(), errors, "Missing results/report.md.")
    expect(runs_root.exists(), errors, "Missing results/artifacts/runs/ directory.")

    state_data: Dict[str, Any] = {}
    if state_path.exists():
        try:
            loaded = load_yaml(state_path)
            if isinstance(loaded, dict):
                state_data = loaded
            else:
                errors.append("results/state.yaml must be a mapping.")
        except Exception as exc:  # noqa: BLE001
            errors.append(f"Failed to parse {as_repo_relative(state_path, buildforce_root)}: {exc}")

    if report_path.exists():
        validate_report(report_path, errors)

    if state_data:
        required_fields = [
            "schema_version",
            "strategy_id",
            "status",
            "latest_stage",
            "latest_run_id",
            "last_validated_at",
            "latest_compile",
            "latest_backtest",
            "latest_optimization",
            "latest_validation",
            "decision",
            "next_actions",
            "refs",
        ]
        for field in required_fields:
            if field not in state_data:
                errors.append(f"results/state.yaml is missing required field: {field}")

        if not isinstance(state_data.get("schema_version"), int):
            errors.append("results/state.yaml.schema_version must be an integer.")

        if state_data.get("strategy_id") != strategy_dir.name:
            errors.append(
                f"results/state.yaml.strategy_id must match strategy directory name: {strategy_dir.name}"
            )

        if state_data.get("status") not in ALLOWED_STATUS:
            errors.append(f"results/state.yaml.status must be one of {sorted(ALLOWED_STATUS)}.")

        latest_stage = state_data.get("latest_stage")
        if latest_stage is not None and latest_stage not in ALLOWED_STAGE:
            errors.append("results/state.yaml.latest_stage must be null or a valid stage.")

        latest_run_id = state_data.get("latest_run_id")
        if latest_run_id is not None and (not isinstance(latest_run_id, str) or not latest_run_id.strip()):
            errors.append("results/state.yaml.latest_run_id must be null or a non-empty string.")

        last_validated_at = state_data.get("last_validated_at")
        if last_validated_at is not None and (not isinstance(last_validated_at, str) or not last_validated_at.strip()):
            errors.append("results/state.yaml.last_validated_at must be null or a non-empty string.")

        decision = state_data.get("decision")
        if not isinstance(decision, dict):
            errors.append("results/state.yaml.decision must be a mapping.")
        else:
            expect_string(decision.get("value"), errors, "results/state.yaml.decision.value must be a non-empty string.")
            expect_string(
                decision.get("reason"),
                errors,
                "results/state.yaml.decision.reason must be a non-empty string.",
            )

        next_actions = state_data.get("next_actions")
        if not isinstance(next_actions, list) or not all(isinstance(item, str) for item in next_actions):
            errors.append("results/state.yaml.next_actions must be a list of strings.")

        refs = state_data.get("refs")
        if not isinstance(refs, dict):
            errors.append("results/state.yaml.refs must be a mapping.")
        else:
            spec_ref = refs.get("spec")
            if spec_ref is not None:
                if not isinstance(spec_ref, str) or not spec_ref.strip():
                    errors.append("results/state.yaml.refs.spec must be null or a non-empty string.")
                elif resolve_existing_reference(buildforce_root, strategy_dir, spec_ref) is None:
                    errors.append(f"results/state.yaml.refs.spec does not exist: {spec_ref}")

            report_ref = refs.get("report")
            if not isinstance(report_ref, str) or not report_ref.strip():
                errors.append("results/state.yaml.refs.report must be a non-empty string.")
            elif resolve_existing_reference(buildforce_root, strategy_dir, report_ref) is None:
                errors.append(f"results/state.yaml.refs.report does not exist: {report_ref}")

            for ref_key in ("buildforce_session", "achieve_session"):
                ref_value = refs.get(ref_key)
                if ref_value is not None and not isinstance(ref_value, str):
                    errors.append(f"results/state.yaml.refs.{ref_key} must be null or a string.")

        for section_name, id_key in LATEST_SECTION_SPECS.items():
            validate_latest_section(
                buildforce_root,
                strategy_dir,
                section_name,
                state_data.get(section_name),
                id_key,
                errors,
            )

        if latest_run_id is None:
            if latest_stage is not None:
                errors.append("results/state.yaml.latest_stage must be null when latest_run_id is null.")
            if last_validated_at is not None:
                errors.append("results/state.yaml.last_validated_at must be null in pre-run state.")
            if isinstance(decision, dict) and decision.get("value") != "not_run":
                errors.append("results/state.yaml.decision.value must be not_run in pre-run state.")
            for section_name, id_key in LATEST_SECTION_SPECS.items():
                section = state_data.get(section_name)
                if isinstance(section, dict):
                    if section.get("status") != "not_run":
                        errors.append(f"{section_name}.status must be not_run in pre-run state.")
                    if section.get(id_key) is not None:
                        errors.append(f"{section_name}.{id_key} must be null in pre-run state.")
                    if section.get("artifact") is not None:
                        errors.append(f"{section_name}.artifact must be null in pre-run state.")
                    if section.get("summary") != {}:
                        errors.append(f"{section_name}.summary must be empty in pre-run state.")
        else:
            run_dir = runs_root / latest_run_id
            validate_run_yaml(buildforce_root, strategy_dir, run_dir, errors)

    payload = {
        "strategy_path": as_repo_relative(strategy_dir, buildforce_root),
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
    }

    if json_mode:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        prefix = "OK" if not errors else "FAIL"
        print(f"{prefix}: result workspace check for {payload['strategy_path']}")
        if errors:
            for item in errors:
                print(f"- ERROR: {item}")
        if warnings:
            for item in warnings:
                print(f"- WARNING: {item}")

    return 0 if not errors else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Initialize and validate strategy result workspaces.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    for command_name in ("init", "check"):
        subparser = subparsers.add_parser(command_name)
        subparser.add_argument("--buildforce-root", required=True)
        subparser.add_argument("--strategy-path", required=True)
        subparser.add_argument("--json", action="store_true")
        if command_name == "init":
            subparser.add_argument("--force", action="store_true")

    return parser


def main() -> int:
    check_python_environment()
    parser = build_parser()
    args = parser.parse_args()

    buildforce_root = Path(args.buildforce_root).resolve()

    try:
        strategy_dir = normalize_strategy_path(buildforce_root, args.strategy_path)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if args.command == "init":
        return init_workspace(buildforce_root, strategy_dir, args.json, args.force)
    if args.command == "check":
        return validate_workspace(buildforce_root, strategy_dir, args.json)

    parser.error("Unknown command.")
    return 2


if __name__ == "__main__":
    sys.exit(main())
