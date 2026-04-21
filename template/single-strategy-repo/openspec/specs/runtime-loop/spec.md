# Runtime Loop

## Purpose

Define the optional thin runtime loop for repeated validation against an existing
OpenSpec change.

## Requirements

### Requirement: Runtime loop is optional

The repository SHALL treat the runtime loop as optional and disabled by default.

#### Scenario: User does not enable a loop session

- **WHEN** a change runs through `explore -> propose -> apply -> verify -> archive`
- **THEN** no runtime session is required for the primary workflow

### Requirement: Runtime loop stores minimal session state

Runtime loop state SHALL live under `.claude/runtime/opsx-sessions/` and track
only change-oriented runtime fields.

#### Scenario: Runtime session is started

- **WHEN** `bash scripts/opsx-session-start.sh --change-id <change>` is used
- **THEN** the session stores the change id plus minimal runtime fields such as attempts, last gate, iteration, and status
