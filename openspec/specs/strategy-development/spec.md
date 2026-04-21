# Strategy Development

## Purpose

Define the repository-level workflow for iterating on a single QuantConnect strategy.

## Requirements

### Requirement: Strategy changes use a staged workflow

The repository SHALL express strategy work as a staged workflow covering design,
local implementation, QC execution, result persistence, independent review, and
validation before archive.

#### Scenario: Strategy change is prepared for implementation

- **WHEN** `/opsx.propose` prepares a `qc-change`
- **THEN** its planning artifacts describe those six stages explicitly

### Requirement: Strategy changes stay inside OpenSpec

The repository SHALL keep all planning artifacts for a strategy change under
`openspec/changes/{change}/`.

#### Scenario: Change artifacts are created

- **WHEN** a user proposes or updates a strategy change
- **THEN** proposal, specs, research, design, and tasks live only under the change directory
