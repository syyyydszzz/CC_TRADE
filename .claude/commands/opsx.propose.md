---
description: Create or update an OpenSpec qc-change with proposal, specs, research, design, and tasks artifacts.
---

User input:

$ARGUMENTS

You are running the repository's proposal step for the custom OpenSpec schema `qc-change`.

## Goal

Create or update a change under `openspec/changes/{change}/` with these artifacts:

- `proposal.md`
- `specs/<capability>/spec.md`
- `research.md`
- `design.md`
- `tasks.md`

## Required behavior

1. Use `openspec/config.yaml`, `openspec/schemas/qc-change/schema.yaml`, and the schema templates as the authority.
2. Require the repo-local OpenSpec CLI through `bash scripts/opsx.sh ...`. If it is unavailable, stop and direct the user to `bash scripts/bootstrap-python-env.sh --with-openspec`.
3. Create new changes with `bash scripts/opsx.sh new change <change-id>`. Do not use `openspec change create ...`.
4. Keep proposal/specs/research/design/tasks aligned with this repository contract:
   - `main.py` and `spec.md` at the repo root are source of truth
   - `qc-mcp` is the only execution path
   - `results/` is the only evidence layer
   - result write order is raw artifacts -> `record-result-run` -> `record-result-state` -> `report.md` -> workspace check
5. Proposal requirements:
   - include `Why`, `What Changes`, `Capabilities`, and `Impact`
   - include repo-specific `Target`, `Scope`, `Success Criteria`, and `Risks Or Blockers`
   - use `Capabilities` to declare every change spec that will be created or modified
6. Specs requirements:
   - strategy behavior changes default to `specs/strategy-project/spec.md`
   - execution contract changes also touch `specs/qc-execution/spec.md`
   - result-layer contract changes also touch `specs/result-workspace/spec.md`
   - use OpenSpec delta headings and ensure every requirement has at least one `#### Scenario:`
7. For strategy work, the artifacts must explicitly cover these phases:
   - design
   - local implementation
   - QC execution
   - result persistence
   - independent review
   - validation
8. Write planning artifacts only under `openspec/changes/{change}/`.
9. Before declaring success:
   - run `bash scripts/opsx.sh show <change-id>`
   - run `bash scripts/opsx.sh validate <change-id>`
   - stop if either command fails
10. Suggest `/opsx.apply` only after `proposal/specs/research/design/tasks` all exist and `validate` exits 0.
