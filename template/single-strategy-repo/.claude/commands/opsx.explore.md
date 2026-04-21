---
description: Explore the repository, strategy context, and OpenSpec long-lived specs before proposing or applying a change.
---

User input:

$ARGUMENTS

You are running the repository's OpenSpec-first exploration step.

## Goal

Gather the context needed for an upcoming or existing `qc-change` without creating legacy planning artifacts outside OpenSpec.

## Required behavior

1. Treat `openspec/changes/{change}/` as the only planning authority.
2. Read these first when relevant:
   - `AGENTS.md`
   - `openspec/config.yaml`
   - `openspec/specs/**/*.md`
   - `spec.md`
   - `results/`
3. If the task touches strategy execution, identify:
   - target repo-root source files
   - QC prerequisites
   - result-layer write order
   - key helper scripts under `scripts/`
   - blockers or unknowns
4. Present findings in a reusable structure:
   - scope summary
   - key files
   - execution prerequisites
   - result-layer constraints
   - open questions or blockers
5. Do not create planning artifacts outside `openspec/changes/`.
6. Suggest `/opsx.propose` as the next step when exploration is sufficient.
