# QuantConnect LEAN CLI Workflow

Use this when you want a practical cloud-only edit and backtest loop instead of isolated commands.

## Recommended Loop
1. Authenticate and initialize an organization workspace.
   - `lean login`
   - `lean init`
2. Create a project with starter files.
   - `lean project-create "My Strategy"`
   - This creates starter algorithm code, project configuration, and editor files.
3. Implement or adjust the algorithm in the project code.
4. Commit the code changes for the test so the backtest maps to a stable `code_version`.
5. Run a cloud backtest.
   - `lean cloud backtest "My Strategy" --push --open`
6. Review the results.
   - Cloud backtests print summary statistics and a link to the full results page; `--open` opens it automatically.
   - Optional: `lean report` to generate a report from the most recent backtest, or point it at a specific results JSON file if you have pulled results locally.
7. Tweak the algorithm and repeat.
   - Adjust the algorithm logic or parameters.
   - Re-run the backtest.
   - Keep iterating until the observed metrics reach your target performance threshold.

## Backtest Concurrency Rule
- Run only one cloud backtest at a time.
- Do not start the next backtest until the current one has finished and its results have been reviewed or logged.
- The safe loop is:
  - edit code
  - run `lean cloud backtest "<projectName>" --push --open`
  - wait for completion
  - capture the returned metrics and backtest link or id
  - update the research log
  - decide the next hypothesis or tweak
  - then start the next backtest

## Sync Workflow
- Pull remote changes before local work when the cloud is the source of truth:
  - `lean cloud pull`
  - `lean cloud pull --project "My Strategy"`
- Push local changes when you want the cloud copy updated:
  - `lean cloud push --project "My Strategy" --force`
- `lean cloud backtest ... --push` is the default iteration loop when you write locally but execute in QuantConnect Cloud.

## Result Retrieval
- Cloud backtests:
  - The main review path is the cloud results page opened by `--open`.
  - If you need local artifacts or a local report workflow, pull project changes first and then work from the retrieved backtest output supported by your environment.

## Research Logging
- Keep the logging workflow append-only.
- If the research log structure does not exist, create it with:
  - `python .codex/skills/quant-connect/scripts/bootstrap_research_log.py`
- Use one file per hypothesis and one file per experiment.
- Use the id itself as the filename:
  - `research_log/hypotheses/h001.md`
  - `research_log/experiments/e001.md`
- Generate ids with:
  - `python .codex/skills/quant-connect/scripts/generate_research_id.py hypothesis`
  - `python .codex/skills/quant-connect/scripts/generate_research_id.py experiment`
- Put structured metadata in YAML frontmatter.
- Use `templates/hypothesis.md` and `templates/experiment.md` as the source of truth for required fields and body sections.
- Commit the code for each meaningful test and record the resulting git commit hash as `code_version`.
- Create or update a hypothesis before running a meaningful new test.
- After each completed backtest, append an experiment entry before launching the next one.
- If the result changes your thinking, update the existing hypothesis entry or create a new hypothesis entry with its own `hypothesis_id`.

## Practical Guidance
- Start every session in the root of the organization workspace so project sync and local execution stay consistent.
- Pull before editing if teammates may have changed cloud projects.
- Prefer a tight loop:
  - implement change
  - commit the code for the run
  - run `lean cloud backtest --push --open`
  - wait for completion
  - inspect metrics and charts
  - log the experiment and any new hypothesis
  - tweak
  - re-run
- Treat target performance as a stopping condition, not a guarantee. Re-check robustness after you hit the target.
