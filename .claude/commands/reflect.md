---
description: Trigger post-iteration reflection for a completed strategy change. Spawns opsx-reflector to analyze execution artifacts and write knowledge entries to skill knowledge files.
---

User input:

$ARGUMENTS

## Usage

```
/reflect <change-id>
```

Run this after `/opsx.archive` to extract learnings from the completed iteration.

## Behavior

1. Parse `{change-id}` from `$ARGUMENTS`. If not provided, list available archived changes under `openspec/changes/archive/` and ask the user to specify one.

2. Confirm the change exists in one of:
   - `openspec/changes/archive/{change-id}/` (expected after archive)
   - `openspec/changes/{change-id}/` (if called before archive)

3. Spawn the `opsx-reflector` subagent with the change-id.

4. Report the reflector's findings to the user: how many knowledge entries were written, to which skills, and the top learnings.

## Notes

- This command is intentionally manual — run it when you judge the iteration had meaningful learnings worth capturing.
- If `execution-log.md` is missing from the change directory, the reflector will still run but with reduced confidence. Remind the user to fill in `execution-log.md` during future apply phases for better reflection quality.
