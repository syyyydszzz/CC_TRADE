---
description: Initialize a new QuantConnect strategy development session (project)
---

Initialize a new autonomous hypothesis testing session for algorithmic strategy development.

This command implements Phase 1 of the 5-phase autonomous workflow.

## ⚠️ CRITICAL RULES (Read Before Executing!)

1. **Directory Structure FIRST**: Create `STRATEGIES/hypothesis_X/` directory BEFORE any file operations
2. **Never at root**: ALL hypothesis files go in `STRATEGIES/hypothesis_X/`, NEVER at root
3. **Work in hypothesis dir**: `cd` into hypothesis directory before creating files
4. **Allowed at root**: ONLY README.md, requirements.txt, .env, .gitignore, BOOTSTRAP.sh

**If you create files at root, the workflow WILL BREAK!**

---

## What This Command Does

1. Prompts for hypothesis details (name, description, rationale)
2. Generates unique hypothesis ID (auto-increment based on existing branches)
3. **Creates hypothesis directory structure FIRST** ✨ NEW
4. Creates `iteration_state.json` from template (IN hypothesis dir)
5. Populates workflow metadata (session_id, timestamps)
6. Sets autonomy mode (default: minimal, requires user approval at each phase)
7. Loads default thresholds from config or uses defaults
8. Creates git branch: `hypotheses/hypothesis-{id}-{name-slug}`
9. Makes initial commit with structured message
10. Sets next_action to `/qc-backtest`

## Usage

```bash
/qc-init
```

You will be prompted for:
- **Hypothesis name**: Short descriptive name (e.g., "RSI Mean Reversion")
- **Hypothesis description**: One-line description of the strategy
- **Hypothesis rationale**: Why you think this will work (market regime, theory, etc.)

## Implementation Steps

When this command is executed, perform these steps **IN ORDER**:

### Step 1: Gather Hypothesis Information

**⚠️ AUTONOMOUS MODE: DO NOT ASK USER UNLESS BLOCKER**

If command has arguments (e.g., `/qc-init path/to/strategy.py`):
- Extract hypothesis details from code comments/docstrings
- Auto-generate name from filename
- Proceed autonomously

If command has NO arguments:
- **ONLY THEN** ask user for:
  1. **Hypothesis Name** (required)
  2. **Hypothesis Description** (required)
  3. **Hypothesis Rationale** (required)

### Step 2: Generate Hypothesis ID

```bash
# Find highest existing hypothesis ID from git branches
HIGHEST_ID=$(git branch -a | grep 'hypotheses/hypothesis-' | sed 's/.*hypothesis-//; s/-.*//' | sort -n | tail -1)
NEW_ID=$((HIGHEST_ID + 1))
echo "Generated Hypothesis ID: $NEW_ID"
```

### Step 3: CREATE DIRECTORY STRUCTURE FIRST ⭐ CRITICAL

**⚠️ THIS MUST BE DONE BEFORE ANY FILE CREATION**

```bash
# Create slugified name for directory
HYPOTHESIS_SLUG=$(echo "$HYPOTHESIS_NAME" | tr '[:upper:]' '[:lower:]' | tr ' ' '_' | sed 's/[^a-z0-9_]//g')

# Create hypothesis directory
HYPOTHESIS_DIR="STRATEGIES/hypothesis_${NEW_ID}_${HYPOTHESIS_SLUG}"
mkdir -p "${HYPOTHESIS_DIR}"

# Create subdirectories for hypothesis organization
mkdir -p "${HYPOTHESIS_DIR}/backtest_logs"
mkdir -p "${HYPOTHESIS_DIR}/helper_classes"
mkdir -p "${HYPOTHESIS_DIR}/backup_scripts"

# IMPORTANT: Change into this directory for all subsequent operations
cd "${HYPOTHESIS_DIR}"

echo "✅ Created hypothesis directory: ${HYPOTHESIS_DIR}"
echo "✅ Created subdirectories: backtest_logs, helper_classes, backup_scripts"
echo "✅ Working directory: $(pwd)"
```

**Verification Check**:
```bash
# Verify we're NOT at root
if [[ $(basename $(pwd)) == "CLAUDE_CODE_EXPLORE" ]]; then
    echo "❌ ERROR: Still at root directory!"
    echo "❌ Cannot create files at root - workflow will break"
    exit 1
fi

# Verify we're in hypothesis directory
if [[ ! $(pwd) =~ STRATEGIES/hypothesis_ ]]; then
    echo "❌ ERROR: Not in hypothesis directory!"
    echo "❌ Current: $(pwd)"
    echo "❌ Expected: STRATEGIES/hypothesis_X/"
    exit 1
fi

echo "✅ Directory verification passed"
```

### Step 4: Create iteration_state.json (in hypothesis directory)

**Now we're safely in `STRATEGIES/hypothesis_X/` directory**

```bash
# Copy template from project root to current directory (hypothesis dir)
cp ../../PROJECT_SCHEMAS/iteration_state_template.json iteration_state.json

# Verify file is in correct location
if [ ! -f "iteration_state.json" ]; then
    echo "❌ ERROR: Failed to create iteration_state.json"
    exit 1
fi

echo "✅ Created: $(pwd)/iteration_state.json"
```

**Populate fields using Python** (safer than sed/awk):

```python
import json
from datetime import datetime
import uuid

# We're already in STRATEGIES/hypothesis_X/ directory
with open('iteration_state.json', 'r') as f:
    state = json.load(f)

# Generate IDs
session_id = str(uuid.uuid4())
timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

# Populate hypothesis
state['current_hypothesis'] = {
    "id": NEW_ID,  # From Step 2
    "name": HYPOTHESIS_NAME,
    "description": HYPOTHESIS_DESC,
    "rationale": HYPOTHESIS_RATIONALE,
    "created": timestamp,
    "status": "research",
    "abandon_reason": None
}

# Populate metadata
state['metadata'] = {
    "session_id": session_id,
    "created_at": timestamp,
    "updated_at": timestamp,
    "claude_model": "claude-sonnet-4-5",
    "previous_hypothesis": None
}

# Set initial phase
state['current_phase'] = "research"

# Save
with open('iteration_state.json', 'w') as f:
    json.dump(state, f, indent=2)

print(f"✅ iteration_state.json populated")
print(f"   Location: {os.getcwd()}/iteration_state.json")
```

### Step 5: Create Git Branch

```bash
# Create branch name (slugify hypothesis name)
BRANCH_NAME="hypotheses/hypothesis-${NEW_ID}-$(echo "$HYPOTHESIS_NAME" | tr '[:upper:]' '[:lower:]' | tr ' ' '-' | sed 's/[^a-z0-9-]//g')"

# Create and checkout branch
git checkout -b "$BRANCH_NAME"

echo "✅ Created branch: ${BRANCH_NAME}"
```

### Step 6: Initial Commit

**⚠️ IMPORTANT**: Stage files with path from repository root

```bash
# We're in STRATEGIES/hypothesis_X/ but git needs path from root
git add "${HYPOTHESIS_DIR}/iteration_state.json"

# Alternative: Use relative path from root
# cd back to root first, then add
cd ../..  # Back to repository root
git add "${HYPOTHESIS_DIR}/iteration_state.json"

# Commit with structured message
git commit -m "research: Initialize hypothesis ${NEW_ID} - ${HYPOTHESIS_NAME}

Hypothesis: ${HYPOTHESIS_DESC}

Rationale: ${HYPOTHESIS_RATIONALE}

Directory: ${HYPOTHESIS_DIR}
Status: research → implementation
Iteration: 1
Phase: research

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>"

echo "✅ Initial commit created"
```

### Step 7: Confirm Success

Display summary:
```
═══════════════════════════════════════════════════════
✅ HYPOTHESIS INITIALIZED SUCCESSFULLY
═══════════════════════════════════════════════════════

Hypothesis ID: {id}
Name: {name}
Description: {description}

📁 Directory: {HYPOTHESIS_DIR}
🌿 Branch: {branch_name}
📄 Files created:
   ✓ {HYPOTHESIS_DIR}/iteration_state.json

Current phase: research
Next action: /qc-backtest

Ready to implement strategy!

⚠️  IMPORTANT: All hypothesis files must go in:
   {HYPOTHESIS_DIR}/

Never create files at repository root!
═══════════════════════════════════════════════════════
```

## Pre-Flight Checks (Run at Start)

**Before executing this command, verify:**

```bash
# Check 1: We're at repository root
if [[ $(basename $(pwd)) != "CLAUDE_CODE_EXPLORE" ]]; then
    echo "⚠️  WARNING: Not at repository root"
    echo "Current: $(pwd)"
    echo "Run: cd /path/to/CLAUDE_CODE_EXPLORE"
fi

# Check 2: No iteration_state.json at root
if [ -f "iteration_state.json" ]; then
    echo "❌ ERROR: iteration_state.json exists at root!"
    echo "This violates Critical Rule #1"
    echo "Move it to appropriate hypothesis directory"
    exit 1
fi

# Check 3: STRATEGIES directory exists
if [ ! -d "STRATEGIES" ]; then
    echo "Creating STRATEGIES directory..."
    mkdir -p STRATEGIES
fi

echo "✅ Pre-flight checks passed"
```

## Post-Execution Verification

**After running command, verify file locations:**

```bash
# Should be EMPTY or only show allowed files
ls -1 | grep -E '\.(json|py)$' && echo "❌ ERROR: Files at root!" || echo "✅ No files at root"

# Should show our new hypothesis directory
ls -d STRATEGIES/hypothesis_*/ | tail -1

# Should show iteration_state.json in hypothesis directory
ls STRATEGIES/hypothesis_*/iteration_state.json
```

## Directory Structure Created

```
STRATEGIES/
└── hypothesis_{ID}_{name_slug}/
    ├── iteration_state.json          ← Created here, NOT at root!
    ├── backtest_logs/                ← Created for backtest-specific logs
    ├── helper_classes/               ← Created for strategy-specific helpers
    └── backup_scripts/               ← Created for version backups
```

**Future files will also go here:**
```
STRATEGIES/
└── hypothesis_{ID}_{name_slug}/
    ├── iteration_state.json           ← Phase 1 (this command)
    ├── config.json                    ← Phase 2 (QC configuration)
    ├── {strategy_name}.py             ← Phase 2 (/qc-backtest - main strategy)
    ├── optimization_params.json       ← Phase 4 (/qc-optimize)
    ├── optimization_results_*.json    ← Phase 4 (/qc-optimize)
    ├── oos_validation_results.json    ← Phase 5 (/qc-validate)
    ├── research.ipynb                 ← Phase 5 (optional analysis)
    ├── README.md                      ← Hypothesis description
    ├── backtest_logs/                 ← Backtest-specific logs
    │   └── (detailed backtest outputs)
    ├── helper_classes/                ← Strategy-specific helper classes
    │   └── (indicators, risk managers, etc.)
    └── backup_scripts/                ← Version backups
        └── (timestamped backups of strategy)
```

## Common Mistakes to Avoid

❌ **WRONG**:
```bash
# Creating files at root
cp PROJECT_SCHEMAS/iteration_state_template.json iteration_state.json  # At root!
```

✅ **CORRECT**:
```bash
# Create directory first, then cd into it
mkdir -p STRATEGIES/hypothesis_7_my_strategy
cd STRATEGIES/hypothesis_7_my_strategy
cp ../../PROJECT_SCHEMAS/iteration_state_template.json iteration_state.json  # In hypothesis dir!
```

## Notes

- **Directory creation is MANDATORY before any file operations**
- The schema includes all phase structures (backtest, optimization, validation)
- Thresholds use defaults unless overridden
- Autonomy mode defaults to "minimal" (user approval at each phase)
- Git integration is automatic and mandatory
- session_id is generated using UUID for uniqueness
- **All hypothesis files MUST be in `STRATEGIES/hypothesis_X/`**

## Next Steps

After initialization:
1. Implement the strategy code (Python algorithm) in hypothesis directory
2. Run `/qc-backtest` to test the hypothesis

---

**Version**: 2.0.0 (Fixed - Directory-First Pattern)
**Last Updated**: 2025-11-14
**Critical Fix**: Added mandatory directory creation before file operations
