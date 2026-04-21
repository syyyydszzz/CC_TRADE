# Strategy Project

## Purpose

Define the repository contract for the single strategy owned by the repo root.

## Requirements

### Requirement: Repo root is the strategy authority

The repository SHALL treat repo-root `main.py` and `spec.md` as the only local
source of truth for the strategy.

#### Scenario: Strategy files are referenced

- **WHEN** a change proposes or implements strategy behavior
- **THEN** it references repo-root `main.py` and `spec.md` rather than `algorithms/<strategy>/...`

### Requirement: Strategy changes create change specs

The repository SHALL describe strategy behavior changes through a change spec at
`openspec/changes/{change}/specs/strategy-project/spec.md`.

#### Scenario: Strategy behavior changes are proposed

- **WHEN** `/opsx.propose` prepares a change for the current strategy
- **THEN** it creates or updates `specs/strategy-project/spec.md` with valid OpenSpec delta requirements and scenarios
