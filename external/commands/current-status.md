---
description: Display previous session status and next steps for continuity
---

Read the previous session status to understand what was accomplished and what to do next.

This command displays:
1. Previous session summary
2. Current project state
3. Next steps to continue work
4. Context for session-to-session continuity

**Usage**:
```
/current-status
```

This reads: `PROJECT_DOCUMENTATION/CORE/SETUP/NEXT_STEPS/CURRENT_STATUS.md`

**When to use**:
- **At the start of every new session** (first thing to run)
- After context loss or confusion
- To understand project state
- To get next steps

**Difference from /qc-status**:
- `/current-status`: Session continuity (what was done, what's next)
- `/qc-status`: Workflow status (active hypothesis, backtest results)

**Example output**:
```
Last Session Summary:
- Added emoji ban rule to all QC help files
- Created qc_backtest.json documentation
- Fixed Progressive Disclosure patterns
- Updated README.md

Current State:
- All QC workflows documented (196K total)
- Autonomous execution patterns established
- Help system complete with lazy loading

Next Steps:
1. Test the help system with actual queries
2. Verify emoji ban warnings are clear
3. Run autonomous backtest template
```

