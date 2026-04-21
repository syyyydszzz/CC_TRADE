---
description: Review backtest results for an OpenSpec qc-change. Cold-reads execution artifacts against proposal success criteria.
---

User input:

$ARGUMENTS

## Usage

```
/opsx.review-result <change-id> [run-id]
```

Run this after `/opsx.apply` completes QC execution, or any time you want an independent verdict on the current backtest results.

If `run-id` is omitted, the subagent will use the latest run from `results/state.yaml`.

## Preconditions

1. Parse `{change}` and optional `{run_id}` from `$ARGUMENTS`. If `{change}` is not provided, ask the user to specify one.
2. Confirm `openspec/changes/{change}/proposal.md` exists.
3. Confirm `results/state.yaml` exists — if not, stop and tell the user that no backtest results exist yet. Suggest running `/opsx.apply` first.
4. If `{run_id}` was provided, confirm `results/artifacts/runs/{run_id}/backtest.json` exists.

## Behavior

Spawn the `review-result` subagent with:
- The change-id
- The run-id (explicit if provided, otherwise instruct the subagent to read it from `results/state.yaml`)

Do NOT pass any context about what the implementer or executor decided. The reviewer reads artifacts cold.

Wait for its verdict.

## After review

| Verdict | Action |
|---|---|
| `APPROVE` | Report success. Suggest running `/opsx.verify {change}` then `/opsx.archive {change}`. |
| `REVISE` | Report the findings clearly. Tell the user what needs to be addressed. Do not suggest archive. |
| `BLOCKED` | Report the blocking issues. Tell the user to resolve them before proceeding. |

## Hard rules

- Never pass the implementer's or executor's reasoning to the reviewer.
- Do not modify any artifacts.
- Do not run compile or backtest yourself.
