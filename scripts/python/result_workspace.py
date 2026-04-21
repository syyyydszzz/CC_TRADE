#!/usr/bin/env python3
"""Initialize, validate, and record strategy result workspaces."""

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

try:
    from qc_backtest_artifact import (
        canonicalize_backtest_payload,
        load_canonical_backtest_artifact,
        normalize_scalar,
        summarize_backtest_payload,
    )
except ModuleNotFoundError:
    print(
        "ERROR: qc_backtest_artifact.py is required for result workspace tooling.",
        file=sys.stderr,
    )
    sys.exit(2)


ALLOWED_STATUS = {"not_run", "passed", "failed", "blocked", "needs_iteration"}
ALLOWED_STAGE = ("compile", "backtest", "optimization", "validation")
REPORT_HEADINGS = [
    "## Current Verdict",
    "## Latest Recorded Run",
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
STAGE_FILENAMES = {
    "compile": "compile.json",
    "backtest": "backtest.json",
    "optimization": "optimization.json",
    "validation": "validation.json",
}

STATUS_ALIASES = {
    "pass": "passed",
    "passed": "passed",
    "success": "passed",
    "succeeded": "passed",
    "complete": "passed",
    "completed": "passed",
    "fail": "failed",
    "failed": "failed",
    "error": "failed",
    "block": "blocked",
    "blocked": "blocked",
    "needs_iteration": "needs_iteration",
    "needs-iteration": "needs_iteration",
    "retry": "needs_iteration",
    "not_run": "not_run",
    "not-run": "not_run",
    "pending": "not_run",
}
STAGE_ORDER = {stage: index for index, stage in enumerate(ALLOWED_STAGE)}


def is_relative_to(path: Path, other: Path) -> bool:
    try:
        path.relative_to(other)
        return True
    except ValueError:
        return False


def resolve_project_dir(repo_root: Path, strategy_path: Optional[str]) -> Path:
    if strategy_path:
        candidate = (repo_root / strategy_path).resolve()
        algorithms_root = (repo_root / "algorithms").resolve()

        if candidate == repo_root.resolve():
            if not (candidate / "main.py").exists():
                raise ValueError("Repo root was selected as the project, but main.py is missing.")
            return candidate

        if not is_relative_to(candidate, algorithms_root):
            raise ValueError("Project path must resolve to the repo root or a directory under algorithms/.")
        if not candidate.exists():
            raise ValueError(f"Project path does not exist: {strategy_path}")
        if not candidate.is_dir():
            raise ValueError(f"Project path is not a directory: {strategy_path}")
        return candidate

    if (repo_root / "main.py").exists():
        return repo_root

    raise ValueError(
        "--strategy-path is required when the repo root is not already a single-strategy workspace."
    )


def as_repo_relative(path: Path, buildforce_root: Path) -> str:
    return path.resolve().relative_to(buildforce_root.resolve()).as_posix()


def load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def dump_yaml(path: Path, payload: Any) -> None:
    text = yaml.safe_dump(
        payload,
        sort_keys=False,
        default_flow_style=False,
        allow_unicode=False,
    )
    path.write_text(text, encoding="utf-8")


def load_json_mapping(path: Path) -> Dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"Artifact root must be a JSON object: {path}")
    return payload


def resolve_repo_asset(buildforce_root: Path, relative_path: str, legacy_path: Optional[str] = None) -> Path:
    primary = buildforce_root / relative_path
    if primary.exists():
        return primary
    if legacy_path is not None:
        fallback = buildforce_root / legacy_path
        if fallback.exists():
            return fallback
    raise ValueError(f"Required repository asset does not exist: {relative_path}")


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


def default_stage_section(id_key: str) -> Dict[str, Any]:
    return {
        "status": "not_run",
        id_key: None,
        "artifact": None,
        "summary": {},
    }


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
) -> Optional[Dict[str, Any]]:
    run_yaml_path = run_dir / "run.yaml"
    if not run_yaml_path.exists():
        errors.append(f"Missing latest run summary: {as_repo_relative(run_yaml_path, buildforce_root)}")
        return None

    try:
        run_data = load_yaml(run_yaml_path)
    except Exception as exc:  # noqa: BLE001
        errors.append(f"Failed to parse {as_repo_relative(run_yaml_path, buildforce_root)}: {exc}")
        return None

    if not isinstance(run_data, dict):
        errors.append("run.yaml must be a mapping.")
        return None

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
    return run_data


def validate_report(report_path: Path, warnings: List[str]) -> None:
    text = report_path.read_text(encoding="utf-8")
    for heading in REPORT_HEADINGS:
        if heading not in text:
            warnings.append(f"report.md is missing recommended heading: {heading}")


def stage_section_executed(section: Any) -> bool:
    return isinstance(section, dict) and section.get("status") != "not_run"


def ensure_compile_recorded_for_later_stages(
    sections: Dict[str, Any],
    scope_label: str,
    errors: List[str],
) -> None:
    later_stage_executed = any(
        stage_section_executed(sections.get(stage))
        for stage in ("backtest", "optimization", "validation")
    )
    if later_stage_executed and not stage_section_executed(sections.get("compile")):
        errors.append(
            f"{scope_label}.compile.status must not be not_run when backtest, optimization, or validation ran."
        )


def ensure_latest_stage_is_executed(
    state_data: Dict[str, Any],
    run_data: Dict[str, Any],
    errors: List[str],
) -> None:
    latest_stage = state_data.get("latest_stage")
    if latest_stage in ALLOWED_STAGE and not stage_section_executed(run_data.get(latest_stage)):
        errors.append(
            f"results/state.yaml.latest_stage is {latest_stage}, but run.yaml.{latest_stage}.status is not_run."
        )


def compare_latest_sections_to_run(
    state_data: Dict[str, Any],
    run_data: Dict[str, Any],
    errors: List[str],
) -> None:
    for section_name in LATEST_SECTION_SPECS:
        stage = section_name.replace("latest_", "")
        state_section = state_data.get(section_name)
        run_section = run_data.get(stage)
        if isinstance(state_section, dict) and isinstance(run_section, dict) and state_section != run_section:
            errors.append(
                f"results/state.yaml.{section_name} must match run.yaml.{stage} for results/state.yaml.latest_run_id."
            )


def stage_artifact_relative_path(run_id: str, stage: str) -> str:
    return f"results/artifacts/runs/{run_id}/{STAGE_FILENAMES[stage]}"


def stage_artifact_path(strategy_dir: Path, run_id: str, stage: str) -> Path:
    return strategy_dir / stage_artifact_relative_path(run_id, stage)


def parse_json_mapping(raw_value: Optional[str], field_name: str) -> Dict[str, Any]:
    if raw_value is None:
        return {}
    try:
        payload = json.loads(raw_value)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{field_name} must be valid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"{field_name} must decode to a JSON object.")
    return payload


def load_optional_notes(notes: Optional[str], notes_file: Optional[str]) -> str:
    if notes and notes_file:
        raise ValueError("Provide either --notes or --notes-file, not both.")
    if notes_file:
        return Path(notes_file).read_text(encoding="utf-8").strip()
    return (notes or "").strip()


def infer_stage_status(payload: Dict[str, Any]) -> str:
    if isinstance(payload.get("success"), bool):
        return "passed" if payload["success"] else "failed"
    if payload.get("error") or payload.get("stacktrace"):
        return "failed"
    status_text = str(payload.get("status") or "").strip().lower()
    if "fail" in status_text or "error" in status_text:
        return "failed"
    if "block" in status_text:
        return "blocked"
    if "need" in status_text and "iter" in status_text:
        return "needs_iteration"
    if "pass" in status_text or "success" in status_text or "complete" in status_text:
        return "passed"
    if isinstance(payload.get("completed"), bool):
        return "passed" if payload["completed"] else "failed"
    return "passed"


def normalize_result_status(status: str) -> str:
    raw_status = status.strip().lower()
    if raw_status == "achieved":
        raise ValueError("--status 'achieved' is an Achieve runtime status. Result-layer status must use 'passed'.")

    normalized = STATUS_ALIASES.get(raw_status)
    if normalized is None:
        raise ValueError(
            f"--status must resolve to one of {sorted(ALLOWED_STATUS)}. "
            f"Received: {status!r}."
        )
    return normalized


def detect_stage_identifier(payload: Dict[str, Any], stage: str) -> Any:
    if stage == "backtest":
        payload = canonicalize_backtest_payload(payload)
    candidates = [
        RUN_STAGE_SPECS[stage],
        f"{stage}Id",
        f"{stage}_id",
        "id",
    ]
    for key in candidates:
        value = payload.get(key)
        if value is not None:
            return value
    return None


def summarize_compile(payload: Dict[str, Any]) -> Dict[str, Any]:
    summary: Dict[str, Any] = {}
    warnings = payload.get("warnings")
    if isinstance(warnings, list):
        summary["warnings"] = warnings
    strategy = payload.get("strategy")
    if isinstance(strategy, str) and strategy.strip():
        summary["strategy"] = strategy
    timestamp = payload.get("timestamp")
    if isinstance(timestamp, str) and timestamp.strip():
        summary["timestamp"] = timestamp
    return summary


def summarize_backtest(payload: Dict[str, Any]) -> Dict[str, Any]:
    return summarize_backtest_payload(payload)


def summarize_generic_stage(payload: Dict[str, Any]) -> Dict[str, Any]:
    summary: Dict[str, Any] = {}
    for key in ("name", "status", "message", "error"):
        value = payload.get(key)
        normalized = normalize_scalar(value)
        if normalized is not None:
            summary[key] = normalized

    for key in ("metrics", "summary", "statistics", "validationSummary", "result"):
        nested = payload.get(key)
        if isinstance(nested, dict):
            compact: Dict[str, Any] = {}
            for nested_key, nested_value in nested.items():
                normalized = normalize_scalar(nested_value)
                if normalized is not None:
                    compact[nested_key] = normalized
            if compact:
                summary[key] = compact
                break

    return summary


def build_stage_section(strategy_dir: Path, run_id: str, stage: str, executed: bool) -> Dict[str, Any]:
    id_key = RUN_STAGE_SPECS[stage]
    if not executed:
        return default_stage_section(id_key)

    artifact_path = stage_artifact_path(strategy_dir, run_id, stage)
    if not artifact_path.exists():
        raise ValueError(f"Expected artifact for stage '{stage}' does not exist: {artifact_path}")

    if stage == "backtest":
        payload = load_canonical_backtest_artifact(artifact_path, rewrite=True)
    else:
        payload = load_json_mapping(artifact_path)
    identifier = detect_stage_identifier(payload, stage)
    if identifier is None:
        raise ValueError(f"Could not determine {id_key} from artifact: {artifact_path}")

    if stage == "compile":
        summary = summarize_compile(payload)
    elif stage == "backtest":
        summary = summarize_backtest(payload)
    else:
        summary = summarize_generic_stage(payload)

    return {
        "status": infer_stage_status(payload),
        id_key: identifier,
        "artifact": stage_artifact_relative_path(run_id, stage),
        "summary": summary,
    }


def dedupe_stages(stages: List[str]) -> List[str]:
    ordered: List[str] = []
    for stage in stages:
        if stage not in ordered:
            ordered.append(stage)
    return ordered


def normalize_recorded_stage_sequence(stages: List[str]) -> List[str]:
    ordered = dedupe_stages(stages)
    if not ordered:
        return ordered

    positions = [STAGE_ORDER[stage] for stage in ordered]
    if positions != sorted(positions):
        raise ValueError(
            "--stage values must follow execution order: "
            "compile -> backtest -> optimization -> validation."
        )

    if any(stage in ordered for stage in ("backtest", "optimization", "validation")) and "compile" not in ordered:
        raise ValueError(
            "--stage compile is required before backtest, optimization, or validation."
        )

    return ordered


def init_workspace(buildforce_root: Path, strategy_dir: Path, json_mode: bool, force: bool) -> int:
    strategy_id = strategy_dir.name
    results_root = strategy_dir / "results"
    artifacts_root = results_root / "artifacts"
    runs_root = artifacts_root / "runs"
    state_path = results_root / "state.yaml"
    report_path = results_root / "report.md"

    template_state = load_yaml(
        resolve_repo_asset(buildforce_root, "workflow/templates/result-state-template.yaml")
    )
    report_template = resolve_repo_asset(
        buildforce_root,
        "workflow/templates/result-report-template.md",
    ).read_text(encoding="utf-8")

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
        report_path.write_text(report_payload, encoding="utf-8")

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


def record_run(
    buildforce_root: Path,
    strategy_dir: Path,
    json_mode: bool,
    run_id: str,
    created_at: str,
    open_project: str,
    stages: List[str],
    parameters_json: Optional[str],
    decision_value: str,
    decision_reason: str,
    notes: Optional[str],
    notes_file: Optional[str],
) -> int:
    if not run_id.strip():
        raise ValueError("--run-id must be a non-empty string.")

    ordered_stages = normalize_recorded_stage_sequence(stages)
    if not ordered_stages:
        raise ValueError("At least one --stage must be provided.")

    parameters = parse_json_mapping(parameters_json, "--parameters-json")
    note_text = load_optional_notes(notes, notes_file) or "Generated by result_workspace record-run."

    template = load_yaml(
        resolve_repo_asset(buildforce_root, "workflow/templates/result-run-template.yaml")
    )
    if not isinstance(template, dict):
        raise ValueError("result-run-template.yaml must be a mapping.")

    run_dir = strategy_dir / "results" / "artifacts" / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    template["run_id"] = run_id
    template["created_at"] = created_at
    template["stage_sequence"] = ["read_open_project", *ordered_stages]
    template["open_project"] = open_project
    template["local_strategy_path"] = as_repo_relative(strategy_dir, buildforce_root)
    template["parameters"] = parameters
    template["decision"] = {
        "value": decision_value,
        "reason": decision_reason,
    }
    template["notes"] = note_text

    executed = set(ordered_stages)
    for stage in ALLOWED_STAGE:
        template[stage] = build_stage_section(strategy_dir, run_id, stage, stage in executed)

    run_yaml_path = run_dir / "run.yaml"
    dump_yaml(run_yaml_path, template)

    payload = {
        "strategy_path": as_repo_relative(strategy_dir, buildforce_root),
        "run_id": run_id,
        "run_yaml": as_repo_relative(run_yaml_path, buildforce_root),
        "stage_sequence": template["stage_sequence"],
    }
    if json_mode:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(f"Recorded run summary: {payload['run_yaml']}")

    return 0


def record_state(
    buildforce_root: Path,
    strategy_dir: Path,
    json_mode: bool,
    run_id: str,
    status: str,
    latest_stage: str,
    last_validated_at: str,
    next_actions: List[str],
    change_reference: Optional[str] = None,
    runtime_session: Optional[str] = None,
    buildforce_session: Optional[str] = None,
    achieve_session: Optional[str] = None,
) -> int:
    status = normalize_result_status(status)
    if latest_stage not in ALLOWED_STAGE:
        raise ValueError(f"--latest-stage must be one of {list(ALLOWED_STAGE)}.")

    if change_reference is None:
        change_reference = buildforce_session
    if runtime_session is None:
        runtime_session = achieve_session

    run_yaml_path = strategy_dir / "results" / "artifacts" / "runs" / run_id / "run.yaml"
    if not run_yaml_path.exists():
        raise ValueError(f"Run summary does not exist: {run_yaml_path}")

    run_data = load_yaml(run_yaml_path)
    if not isinstance(run_data, dict):
        raise ValueError("run.yaml must be a mapping.")

    latest_run_section = run_data.get(latest_stage)
    if not isinstance(latest_run_section, dict) or latest_run_section.get("status") == "not_run":
        raise ValueError(f"--latest-stage {latest_stage} is not marked as executed in run.yaml.")
    if latest_stage in ("backtest", "optimization", "validation"):
        compile_section = run_data.get("compile")
        if not stage_section_executed(compile_section):
            raise ValueError(
                "--latest-stage requires compile evidence in run.yaml. "
                "Record compile.json and include --stage compile in record-result-run first."
            )

    template = load_yaml(
        resolve_repo_asset(buildforce_root, "workflow/templates/result-state-template.yaml")
    )
    if not isinstance(template, dict):
        raise ValueError("result-state-template.yaml must be a mapping.")

    state_path = strategy_dir / "results" / "state.yaml"
    existing_state: Dict[str, Any] = {}
    if state_path.exists():
        loaded = load_yaml(state_path)
        if isinstance(loaded, dict):
            existing_state = loaded

    effective_next_actions = [item for item in next_actions if item.strip()]
    if not effective_next_actions:
        fallback_actions = existing_state.get("next_actions")
        if isinstance(fallback_actions, list) and all(isinstance(item, str) for item in fallback_actions):
            effective_next_actions = fallback_actions
        else:
            effective_next_actions = []

    template["strategy_id"] = strategy_dir.name
    template["status"] = status
    template["latest_stage"] = latest_stage
    template["latest_run_id"] = run_id
    template["last_validated_at"] = last_validated_at
    template["decision"] = run_data.get("decision") or {
        "value": status,
        "reason": "Generated by result_workspace record-state.",
    }
    template["next_actions"] = effective_next_actions

    for section_name, id_key in LATEST_SECTION_SPECS.items():
        stage = section_name.replace("latest_", "")
        section = run_data.get(stage)
        template[section_name] = section if isinstance(section, dict) else default_stage_section(id_key)

    template["refs"] = {
        "spec": "spec.md" if (strategy_dir / "spec.md").exists() else None,
        "report": "results/report.md",
        "change": change_reference,
        "runtime_session": runtime_session,
    }

    dump_yaml(state_path, template)

    payload = {
        "strategy_path": as_repo_relative(strategy_dir, buildforce_root),
        "state_yaml": as_repo_relative(state_path, buildforce_root),
        "run_id": run_id,
        "status": status,
        "latest_stage": latest_stage,
    }
    if json_mode:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(f"Recorded result state: {payload['state_yaml']}")

    return 0


def validate_workspace(buildforce_root: Path, strategy_dir: Path, json_mode: bool) -> int:
    errors: List[str] = []
    warnings: List[str] = []

    results_root = strategy_dir / "results"
    state_path = results_root / "state.yaml"
    report_path = results_root / "report.md"
    runs_root = results_root / "artifacts" / "runs"

    expect(results_root.exists(), errors, "Missing results/ directory.")
    expect(state_path.exists(), errors, "Missing results/state.yaml.")
    expect(runs_root.exists(), errors, "Missing results/artifacts/runs/ directory.")
    if not report_path.exists():
        warnings.append("Missing results/report.md.")

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
        validate_report(report_path, warnings)

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
                warnings.append(f"results/state.yaml.refs.report does not exist: {report_ref}")

            for ref_key in ("change", "runtime_session", "buildforce_session", "achieve_session"):
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
            run_data = validate_run_yaml(buildforce_root, strategy_dir, run_dir, errors)
            if isinstance(run_data, dict):
                ensure_compile_recorded_for_later_stages(run_data, "run.yaml", errors)
                ensure_latest_stage_is_executed(state_data, run_data, errors)
                compare_latest_sections_to_run(state_data, run_data, errors)

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
    parser = argparse.ArgumentParser(description="Initialize, validate, and record strategy result workspaces.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init")
    init_parser.add_argument("--repo-root")
    init_parser.add_argument("--buildforce-root")
    init_parser.add_argument(
        "--strategy-path",
        help="Repo-local strategy path under algorithms/. Omit when the repo root itself is the single strategy.",
    )
    init_parser.add_argument("--json", action="store_true")
    init_parser.add_argument("--force", action="store_true")

    check_parser = subparsers.add_parser("check")
    check_parser.add_argument("--repo-root")
    check_parser.add_argument("--buildforce-root")
    check_parser.add_argument(
        "--strategy-path",
        help="Repo-local strategy path under algorithms/. Omit when the repo root itself is the single strategy.",
    )
    check_parser.add_argument("--json", action="store_true")

    record_run_parser = subparsers.add_parser("record-run")
    record_run_parser.add_argument("--repo-root")
    record_run_parser.add_argument("--buildforce-root")
    record_run_parser.add_argument(
        "--strategy-path",
        help="Repo-local strategy path under algorithms/. Omit when the repo root itself is the single strategy.",
    )
    record_run_parser.add_argument("--run-id", required=True)
    record_run_parser.add_argument("--created-at", required=True)
    record_run_parser.add_argument("--open-project", required=True)
    record_run_parser.add_argument("--stage", action="append", choices=list(ALLOWED_STAGE), required=True)
    record_run_parser.add_argument("--parameters-json")
    record_run_parser.add_argument("--decision-value", required=True)
    record_run_parser.add_argument("--decision-reason", required=True)
    record_run_parser.add_argument("--notes")
    record_run_parser.add_argument("--notes-file")
    record_run_parser.add_argument("--json", action="store_true")

    record_state_parser = subparsers.add_parser("record-state")
    record_state_parser.add_argument("--repo-root")
    record_state_parser.add_argument("--buildforce-root")
    record_state_parser.add_argument(
        "--strategy-path",
        help="Repo-local strategy path under algorithms/. Omit when the repo root itself is the single strategy.",
    )
    record_state_parser.add_argument("--run-id", required=True)
    record_state_parser.add_argument("--status", required=True)
    record_state_parser.add_argument("--latest-stage", required=True, choices=list(ALLOWED_STAGE))
    record_state_parser.add_argument("--last-validated-at", required=True)
    record_state_parser.add_argument("--next-action", action="append", default=[])
    record_state_parser.add_argument("--change")
    record_state_parser.add_argument("--workflow-change")
    record_state_parser.add_argument("--buildforce-session")
    record_state_parser.add_argument("--runtime-session")
    record_state_parser.add_argument("--achieve-session")
    record_state_parser.add_argument("--json", action="store_true")

    return parser


def main() -> int:
    check_python_environment()
    parser = build_parser()
    args = parser.parse_args()

    raw_root = getattr(args, "repo_root", None) or getattr(args, "buildforce_root", None)
    if raw_root is None:
        print("ERROR: --repo-root is required.", file=sys.stderr)
        return 2

    buildforce_root = Path(raw_root).resolve()

    try:
        strategy_dir = resolve_project_dir(buildforce_root, getattr(args, "strategy_path", None))
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    try:
        if args.command == "init":
            return init_workspace(buildforce_root, strategy_dir, args.json, args.force)
        if args.command == "check":
            return validate_workspace(buildforce_root, strategy_dir, args.json)
        if args.command == "record-run":
            return record_run(
                buildforce_root=buildforce_root,
                strategy_dir=strategy_dir,
                json_mode=args.json,
                run_id=args.run_id,
                created_at=args.created_at,
                open_project=args.open_project,
                stages=args.stage,
                parameters_json=args.parameters_json,
                decision_value=args.decision_value,
                decision_reason=args.decision_reason,
                notes=args.notes,
                notes_file=args.notes_file,
            )
        if args.command == "record-state":
            change_reference = (
                args.change
                or args.workflow_change
                or args.buildforce_session
            )
            runtime_session = args.runtime_session or args.achieve_session
            return record_state(
                buildforce_root=buildforce_root,
                strategy_dir=strategy_dir,
                json_mode=args.json,
                run_id=args.run_id,
                status=args.status,
                latest_stage=args.latest_stage,
                last_validated_at=args.last_validated_at,
                next_actions=args.next_action,
                change_reference=change_reference,
                runtime_session=runtime_session,
            )
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    parser.error("Unknown command.")
    return 2


if __name__ == "__main__":
    sys.exit(main())
