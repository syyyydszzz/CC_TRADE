---
name: strategy-init
description: |
  AUTO-INVOKE only in the template repo when the user asks to create, generate,
  scaffold, or initialize a new single-strategy repository.
  Triggers on: "开新仓", "建新仓", "新建策略仓", "create a new strategy repo",
  "generate a strategy repo", "scaffold a repo", "/strategy.init", or similar.
allowed-tools: Read, Glob, Grep, Bash
---

# Strategy Init

Use this skill only in the template repo.

## Role

This skill is the orchestration layer for creating a brand-new single-strategy repo.
It does not create repo files directly. The generator script is the only source of truth.

## Source Of Truth

- Always use `bash scripts/new-strategy-repo.sh`
- Prefer `--json` so the result is machine-readable
- Never hand-create or hand-edit generated scaffold files as a substitute for the script

## Preconditions

Before doing anything substantial, confirm the current repo looks like the template repo:

- `scripts/new-strategy-repo.sh` exists
- `template/single-strategy-repo/` exists
- `openspec/`, `scripts/`, and `workflow/` exist at repo root

If this is not the template repo, stop and tell the user to run this from the template workspace.

## Inputs

Map user intent to these generator inputs:

- `--project-name` required
- `--target-dir` required
- `--asset` optional, default `SPY`
- `--resolution` optional, default `daily`
- `--git-init` optional
- `--force` optional

## Inference Rules

Use reasonable defaults, but keep destructive actions explicit.

- If the user clearly names the project, use that as `--project-name`
- If the user describes a strategy but does not give a repo name, derive a short hyphen-case name and state the assumption
- If `--asset` is obvious from the project name or request, infer it; otherwise use the script default
- If `--resolution` is not specified, use the script default `daily`
- If the target directory is not given and there is no repo-documented default, ask one concise question
- Do not assume `--force` unless the user clearly wants replacement
- Do not assume `--git-init` unless the user asks for it or the workflow contract explicitly requires it

## Workflow

1. Parse the user's intent into generator arguments.
2. Normalize:
   - project name to a valid repo name
   - resolution to `daily`, `hourly`, or `minute`
3. Run:

   `bash scripts/new-strategy-repo.sh --project-name <name> --target-dir <dir> [--asset <ticker>] [--resolution <value>] [--git-init] [--force] --json`

4. Read the JSON result and capture:
   - `project_root`
   - `prompt_file`
   - `results_root`
5. Read the generated prompt file and return it inline to the user.
6. Tell the user the exact next bootstrap sequence:
   - `cd <project_root>`
   - `bash scripts/bootstrap-python-env.sh --with-openspec`
   - `bash scripts/check-qc-mcp.sh`
   - `bash scripts/opsx.sh list --specs`
   - `claude`

## Response Contract

Return a concise summary containing:

- generated repo root
- prompt file path
- results root
- whether assumptions were made
- the generated `/opsx.propose` prompt
- the exact next commands

## Do Not

- Do not create repo files manually
- Do not modify `~/.claude.json`
- Do not auto-register or proxy `qc-mcp`
- Do not pass `--force` unless the user explicitly wants replacement
- Do not continue if the generator script fails
