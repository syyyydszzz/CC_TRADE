#!/usr/bin/env bash
# Generate a new single-strategy repository from the local template workspace.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

PROJECT_NAME=""
TARGET_DIR=""
ASSET="SPY"
RESOLUTION="daily"
FORCE=false
GIT_INIT=false
JSON_MODE=false

print_help() {
    cat <<'EOF'
Usage: bash scripts/new-strategy-repo.sh --project-name <name> --target-dir <path> [OPTIONS]

Options:
  --project-name <name>    Required. New repository name, e.g. tqqq-trend-daily-v1
  --target-dir <path>      Required. Parent directory where the new repo will be created
  --asset <ticker>         Default asset written into the scaffold. Default: SPY
  --resolution <value>     Default resolution: daily | hourly | minute. Default: daily
  --git-init               Run git init in the generated repository
  --force                  Replace the target directory if it already exists
  --json                   Emit machine-readable JSON summary
  -h, --help               Show help
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --project-name)
            PROJECT_NAME="${2:-}"
            shift 2
            ;;
        --target-dir)
            TARGET_DIR="${2:-}"
            shift 2
            ;;
        --asset)
            ASSET="${2:-}"
            shift 2
            ;;
        --resolution)
            RESOLUTION="${2:-}"
            shift 2
            ;;
        --git-init)
            GIT_INIT=true
            shift
            ;;
        --force)
            FORCE=true
            shift
            ;;
        --json)
            JSON_MODE=true
            shift
            ;;
        -h|--help)
            print_help
            exit 0
            ;;
        *)
            echo "ERROR: Unknown argument: $1" >&2
            print_help >&2
            exit 2
            ;;
    esac
done

if [[ -z "$PROJECT_NAME" || -z "$TARGET_DIR" ]]; then
    echo "ERROR: --project-name and --target-dir are required." >&2
    print_help >&2
    exit 2
fi

if [[ ! "$PROJECT_NAME" =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ ]]; then
    echo "ERROR: project name must match ^[A-Za-z0-9][A-Za-z0-9._-]*$" >&2
    exit 2
fi

case "$(printf '%s' "$RESOLUTION" | tr '[:upper:]' '[:lower:]')" in
    daily)
        RESOLUTION="daily"
        RESOLUTION_ENUM="DAILY"
        ;;
    hour|hourly)
        RESOLUTION="hourly"
        RESOLUTION_ENUM="HOUR"
        ;;
    minute|minutely)
        RESOLUTION="minute"
        RESOLUTION_ENUM="MINUTE"
        ;;
    *)
        echo "ERROR: --resolution must be one of: daily, hourly, minute" >&2
        exit 2
        ;;
esac

REPO_ROOT="$(get_repo_root)" || exit 1
PYTHON_BIN="$(resolve_repo_python "$REPO_ROOT")" || exit 2
TEMPLATE_ROOT="$REPO_ROOT/template/single-strategy-repo"
FINAL_DIR="$TARGET_DIR/$PROJECT_NAME"

if [[ ! -d "$TEMPLATE_ROOT" ]]; then
    echo "ERROR: Template directory not found: $TEMPLATE_ROOT" >&2
    exit 2
fi

if [[ -e "$FINAL_DIR" ]]; then
    if ! $FORCE; then
        echo "ERROR: Target directory already exists: $FINAL_DIR" >&2
        exit 2
    fi
    rm -rf "$FINAL_DIR"
fi

mkdir -p "$TARGET_DIR"
mkdir -p "$FINAL_DIR"
cp -R "$TEMPLATE_ROOT/." "$FINAL_DIR/"
if [[ -f "$REPO_ROOT/package-lock.json" ]]; then
    cp "$REPO_ROOT/package-lock.json" "$FINAL_DIR/package-lock.json"
fi

CLASS_NAME="$("$PYTHON_BIN" - "$PROJECT_NAME" <<'PY'
import re
import sys

name = sys.argv[1]
parts = re.split(r'[^A-Za-z0-9]+', name)
print("".join(part[:1].upper() + part[1:] for part in parts if part))
PY
)"

PROMPT_DIR="$FINAL_DIR/openspec/.temp/strategy-init"
PROMPT_FILE="$PROMPT_DIR/${PROJECT_NAME}-opsx-prompt.txt"
mkdir -p "$PROMPT_DIR"

"$PYTHON_BIN" - "$FINAL_DIR" "$PROJECT_NAME" "$CLASS_NAME" "$ASSET" "$RESOLUTION" "$RESOLUTION_ENUM" "$PROMPT_FILE" <<'PY'
from pathlib import Path
import sys

final_dir = Path(sys.argv[1])
project_name = sys.argv[2]
class_name = sys.argv[3]
asset = sys.argv[4]
resolution = sys.argv[5]
resolution_enum = sys.argv[6]
prompt_file = Path(sys.argv[7])

replacements = {
    "__PROJECT_NAME__": project_name,
    "__PROJECT_CLASS_NAME__": class_name,
    "__DEFAULT_ASSET__": asset,
    "__DEFAULT_RESOLUTION__": resolution,
    "__DEFAULT_RESOLUTION_ENUM__": resolution_enum,
}

text_files = [
    final_dir / "main.py",
    final_dir / "spec.md",
    final_dir / "README.md",
    final_dir / "CLAUDE.md",
    final_dir / "AGENTS.md",
]

for path in text_files:
    text = path.read_text(encoding="utf-8")
    for old, new in replacements.items():
        text = text.replace(old, new)
    path.write_text(text, encoding="utf-8")

prompt_text = (
    f"/opsx.propose 为当前仓库创建一个新的 qc-change。目标是研发一个真实但简单、可解释、低出错风险的 "
    f"{asset} {resolution} 策略。proposal/specs/research/design/tasks 必须完整生成。"
    "proposal 必须包含 Why、What Changes、Capabilities、Impact 以及 repo-specific 的 Target、Scope、Success Criteria、Risks Or Blockers。"
    "默认必须生成 specs/strategy-project/spec.md；如果变更执行或结果契约，再额外生成 specs/qc-execution/spec.md 和/或 specs/result-workspace/spec.md。"
    "所有 change specs 必须使用 OpenSpec delta 语法，并且每个 Requirement 都至少带一个 #### Scenario:。"
    "research、design、tasks 必须明确写出 phase 切分："
    "strategy-design 负责策略设计，qc-algorithm-core 负责本地代码实现，"
    "qc-execution 负责 QC 项目同步与 read_open_project/compile/backtest gates，"
    "result-workspace 负责 results 落盘，qc-backtest-analysis 与 qc-validation 负责独立评审。"
    "不得修改仓库外文件。必须把 qc-mcp 前置条件、结果层契约和 helper 顺序写进 artifacts："
    "先写 raw artifacts 到 results/artifacts/runs/{run_id}/，当有 backtest 时必须同时持久化 compile.json 和 backtest.json；"
    "然后只允许通过 bash scripts/record-result-run.sh 和 bash scripts/record-result-state.sh 生成 run.yaml 与 results/state.yaml，"
    "其中 record-result-run 必须包含 --stage compile，再记录 --stage backtest；"
    "record-result-state 只能使用 not_run、passed、failed、blocked、needs_iteration 这套状态值；"
    "禁止手写这两个文件；再更新 results/report.md；最后运行 bash scripts/check-result-workspace.sh。"
    f"如果当前打开的 QC 项目不是 {project_name}，必须立即停止并报告阻塞。"
    "完成 proposal 后必须运行 bash scripts/opsx.sh show <change-id> 和 bash scripts/opsx.sh validate <change-id>，"
    "只有 validate 成功后才能继续走 /opsx.apply、/opsx.verify、/opsx.archive。"
)
prompt_file.write_text(prompt_text + "\n", encoding="utf-8")
PY

(
    cd "$FINAL_DIR"
    bash scripts/init-result-workspace.sh --force >/dev/null
)

if $GIT_INIT; then
    git init "$FINAL_DIR" >/dev/null
fi

if $JSON_MODE; then
    "$PYTHON_BIN" - "$FINAL_DIR" "$PROMPT_FILE" "$GIT_INIT" <<'PY'
import json
import sys
from pathlib import Path

final_dir = Path(sys.argv[1])
prompt_file = Path(sys.argv[2])
git_init = sys.argv[3] == "true"

print(json.dumps({
    "project_root": str(final_dir),
    "prompt_file": str(prompt_file),
    "git_initialized": git_init,
    "results_root": str(final_dir / "results"),
}, indent=2, ensure_ascii=False))
PY
    exit 0
fi

echo "Generated single-strategy repo: $FINAL_DIR"
echo "Prompt file: $PROMPT_FILE"
echo "Results root: $FINAL_DIR/results"
if $GIT_INIT; then
    echo "Git: initialized"
fi
echo
echo "Next:"
echo "  cd $FINAL_DIR"
echo "  bash scripts/bootstrap-python-env.sh --with-openspec"
echo "  bash scripts/check-qc-mcp.sh"
echo "  bash scripts/opsx.sh list --specs"
echo "  claude"
echo
echo "Prompt:"
cat "$PROMPT_FILE"
