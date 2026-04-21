# QC Strategy Template Repo Guidelines

## Repo Role

- This repo is a template/framework repo, not the long-term working repo for a strategy.
- Use `/strategy.init` or `bash scripts/new-strategy-repo.sh ...` to generate a new single-strategy repo.
- Do not treat `examples/strategies/` as the main workflow authority.

## Primary Workflow

Template-repo entrypoint:

```text
/strategy.init
```

Template-repo repo-generation intent may also auto-route through the `strategy-init` skill.

Generated single-strategy repos use:

```text
/opsx.explore
/opsx.propose
/opsx.apply
/opsx.verify
/opsx.archive
/qc.sync-status
/qc.sync
```

## Generated Repo Contract

Each generated repo should use this authority model:

- `main.py` and `spec.md` at repo root are the source of truth.
- `openspec/changes/{change}/` is the only planning and workflow artifact authority.
- active changes keep `proposal.md`, `specs/`, `research.md`, `design.md`, and `tasks.md`
- `qc-mcp` is the only execution path for compile, backtest, optimization, and validation.
- `results/` is the only execution evidence layer.

## qc-mcp Placement

- `qc-mcp` stays user-scoped in `~/.claude.json`.
- Generated repos include docs and a validation script, but they do not register the server for the user.
- Use `bash scripts/check-qc-mcp.sh` inside a generated repo before compile or backtest work.
