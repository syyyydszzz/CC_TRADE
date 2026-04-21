# AGENTS.md

## Workflow

- This repo is a template repo. Generate a new single-strategy repo before doing real strategy implementation work.
- Use `bash scripts/new-strategy-repo.sh ...` or `/strategy.init ...` as the main entrypoint here.
- The template repo may use the `strategy-init` skill to interpret user intent, but the script remains the only repo generator.
- The generated repo, not this template repo, owns `/opsx.*`, `main.py`, `spec.md`, `results/`, and QC execution.

## Template Assets

- `template/single-strategy-repo/` contains the checked-in single-strategy skeleton.
- `openspec/`, `workflow/`, and selected `.claude/skills/` are copied into generated repos.
- `docs/qc-mcp-*.json` and `scripts/check-qc-mcp.sh` define the user-scoped `qc-mcp` integration boundary.

## qc-mcp Rules

- `qc-mcp` stays in `~/.claude.json`.
- This repo must not try to auto-register or proxy `qc-mcp`.
- Generated repos should run `bash scripts/check-qc-mcp.sh` before compile or backtest work.
