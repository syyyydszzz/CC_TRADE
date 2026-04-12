# Project Organization Rules

## Naming Conventions

### Command Files vs Script Files

**RULE: Commands use hyphens, Scripts use underscores**

```
CORRECT:
.claude/commands/
  ├── qc-init.md           # Commands: hyphen-separated
  ├── qc-backtest.md
  ├── qc-optimize.md
  ├── qc-validate.md
  └── qc-walkforward.md

SCRIPTS/
  ├── qc_backtest.py       # Scripts: underscore_separated
  ├── qc_optimize.py
  └── qc_validate.py
```

**Rationale:**
- Clear visual differentiation between commands and scripts
- Commands are user-facing (slash commands like `/qc-optimize`)
- Scripts are internal implementation (Python files)
- Avoids confusion when referencing files

**Wrong:**
```
❌ .claude/commands/qc_optimize.md   # Wrong: should use hyphen
❌ SCRIPTS/qc-backtest.py            # Wrong: should use underscore
```

---

## Documentation Placement

### ✅ ALL Reports Go to PROJECT_DOCUMENTATION

**RULE: Never store reports/documentation in hypothesis strategy directories**

```
CORRECT Structure:
PROJECT_DOCUMENTATION/
  ├── H5/                    # Hypothesis 5 research & analysis
  ├── H6/                    # Hypothesis 6 research & analysis
  ├── SCRIPT_FIXES/          # Bug reports for tooling/scripts
  ├── MONTE_CARLO_ENHANCEMENTS/
  └── MONTECARLO_VALIDATION/

WRONG:
STRATEGIES/hypothesis_5_statistical_arbitrage/
  └── my_report.md           # ❌ NEVER put reports here
```

### Report Classification

- **Hypothesis-specific research** → `PROJECT_DOCUMENTATION/H{N}/`
  - Example: Pair selection analysis, regime studies, backtest interpretations

- **Script/tooling fixes** → `PROJECT_DOCUMENTATION/SCRIPT_FIXES/`
  - Example: Bug investigations in qc_backtest.py, workflow issues

- **Methodology enhancements** → `PROJECT_DOCUMENTATION/{CATEGORY}/`
  - Example: Monte Carlo methods, optimization frameworks

**Keep strategy directories clean: only code, no documentation**

---

## Directory Structure

### STRATEGIES/
Contains only executable code for each hypothesis:
- Strategy Python files
- Jupyter notebooks for research/validation
- Helper scripts specific to the strategy
- iteration_state.json

**NO documentation, reports, or analysis files**

### PROJECT_DOCUMENTATION/
Contains all documentation, reports, and analysis:
- Hypothesis-specific folders (H5/, H6/, etc.)
- Methodology documentation
- Bug investigation reports
- Research findings

---

## Why This Matters

This separation:
1. Keeps strategy code clean and focused
2. Makes documentation easy to find
3. Prevents clutter in hypothesis directories
4. Ensures consistency across the project
5. Reduces progressive disclosure failures (repeating same feedback)
