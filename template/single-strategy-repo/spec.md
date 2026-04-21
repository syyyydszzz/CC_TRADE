# __PROJECT_NAME__ — Spec

## Purpose

Initial scaffold for the single strategy owned by this repository.
This file is expected to be refined by the OpenSpec change workflow.

## Initial Universe

- Asset: __DEFAULT_ASSET__
- Resolution: __DEFAULT_RESOLUTION__

## Current Status

- Local strategy scaffold created
- Result workspace initialized
- QuantConnect project mirror should exist before compile/backtest

## Next Steps

1. Register `qc-mcp` in `~/.claude.json` if you have not done it yet.
2. Run `bash scripts/check-qc-mcp.sh`.
3. Open QuantConnect Local Platform and activate the `__PROJECT_NAME__` project.
4. Run the generated `/opsx.propose` prompt.
5. Let the workflow refine `main.py`, update this spec, and produce result artifacts.
