---
name: strategy-design
description: |
  AUTO-INVOKE when the user is designing or refining trading logic itself:
  entry signals, exit rules, position sizing, filters, or risk management.
  Use when the question is "what strategy logic should we use?" rather than
  "how do we write QCAlgorithm code?".
allowed-tools: Read, Glob, Grep
---

# Strategy Design

Use this skill when the task is to shape the strategy idea before or alongside implementation.

## Responsibilities

- Turn a hypothesis into concrete trading logic.
- Choose entry, exit, sizing, and filter patterns.
- Surface strategy anti-patterns early.
- Keep the design aligned with the local `spec.md`.

## Do Not Use This Skill For

- `QCAlgorithm` API details
- `qc-mcp` execution steps
- result artifact persistence
- backtest metric interpretation after runs already exist

## Workflow

1. Parse the design problem:
   - strategy type
   - asset class
   - timeframe
   - indicators
   - risk constraints
2. Read the relevant files in `knowledge/`.
3. Prefer high-confidence patterns that match the request.
4. Cross-check against `mistakes.yaml` before proposing logic.
5. Express the output in strategy terms:
   - entry conditions
   - exit conditions
   - sizing and exposure rules
   - filters
   - explicit risks and assumptions

## Knowledge Files

- `knowledge/entry-signals.yaml`
- `knowledge/exit-rules.yaml`
- `knowledge/risk-management.yaml`
- `knowledge/mistakes.yaml`

Treat these files as the default destination for future strategy-pattern learnings captured by `evolve`.
