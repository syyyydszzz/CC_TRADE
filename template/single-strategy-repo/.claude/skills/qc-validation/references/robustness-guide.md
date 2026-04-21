# Robustness Guide

## Core Checks

- performance degradation from IS to OOS
- robustness score, usually `OOS Sharpe / IS Sharpe`
- trade-count consistency
- drawdown expansion
- whether behavior survives regime changes

## Heuristics

- degradation `< 15%`: strong
- degradation `15% - 30%`: acceptable
- degradation `30% - 40%`: concerning
- degradation `> 40%`: often overfit

- robustness score `> 0.75`: strong
- robustness score `0.60 - 0.75`: moderate
- robustness score `< 0.60`: weak

## Common Failure Modes

- OOS trade count collapses
- one regime carries the full result
- optimized parameters stop working immediately out of sample

## Result-Layer Language

Prefer verdicts such as:

- continue with validation evidence
- needs iteration before trust
- reject current parameterization
