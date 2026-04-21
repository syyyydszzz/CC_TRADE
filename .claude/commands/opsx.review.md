---
description: Review an OpenSpec qc-change before apply. Checks plan quality, spec clarity, and code compatibility.
---

User input:

$ARGUMENTS

## Usage

```
/opsx.review <change-id>
```

Run this before `/opsx.apply` to confirm the change is ready. Can also be run after updating planning artifacts to re-check readiness.

## Preconditions

1. Parse `{change}` from `$ARGUMENTS`. If not provided, list available changes under `openspec/changes/` and ask the user to specify one.
2. Confirm `openspec/changes/{change}/proposal.md` exists — if not, stop and tell the user to run `/opsx.propose` first.
3. Confirm at least one file exists under `openspec/changes/{change}/specs/`.
4. Confirm `openspec/changes/{change}/tasks.md` exists.

## Behavior

Spawn the `review-pre` subagent with:
- The change-id
- Path to `openspec/changes/{change}/`

Wait for its verdict.

## After review

| Verdict | Action |
|---|---|
| `APPROVE` | Report to user. Suggest running `/opsx.apply {change}`. |
| `REVISE` | Report the blocking issues clearly. Tell the user what needs to be fixed before apply. Do not suggest apply. |
| `BLOCKED` | Report unresolvable blockers. Tell the user to resolve them before proceeding. |

## Hard rules

- Do not modify any planning artifacts.
- Do not spawn any other subagent.
- Do not run `opsx.sh validate` yourself — the subagent handles its own reads.
