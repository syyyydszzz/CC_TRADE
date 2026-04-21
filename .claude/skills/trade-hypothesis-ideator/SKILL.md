---
name: trade-hypothesis-ideator
description: >
  Generate falsifiable trade strategy hypotheses from market data, trade logs,
  and journal snippets. Use when you have a structured input bundle and want
  ranked hypothesis cards with experiment designs, kill criteria, and optional
  strategy.yaml export compatible with edge-finder-candidate/v1.
---

# Trade Hypothesis Ideator

Generate 1-5 structured hypothesis cards from a normalized input bundle, critique and rank them, then optionally export `pursue` cards into `strategy.yaml` + `metadata.json` artifacts.

## QC Integration

This skill sits at the **ideation stage**, before `opsx.propose`.

- Use it to turn market observations (TQQQ/SPY/QQQ price behavior, backtest anomalies, pattern ideas) into structured, falsifiable hypothesis cards with explicit kill criteria.
- The `references/` and `prompts/` are the primary value — use them as a thinking framework even without running the scripts.
- If running the scripts: construct the input JSON bundle manually from your observations; the schema is in `schemas/input_bundle.schema.json`.
- The exported `strategy.yaml` from `pursue` cards is NOT directly compatible with `spec.md` — treat it as a structured draft that needs manual translation into `spec.md` format before `opsx.propose`.
- After a hypothesis is validated via QC backtest, feed the result back to `evolve` to capture what worked into `strategy-design/knowledge/`.

## Workflow

1. Receive input JSON bundle.
2. Run pass 1 normalization + evidence extraction.
3. Generate hypotheses with prompts:
   - `prompts/system_prompt.md`
   - `prompts/developer_prompt_template.md` (inject `{{evidence_summary}}`)
4. Critique hypotheses with `prompts/critique_prompt_template.md`.
5. Run pass 2 ranking + output formatting + guardrails.
6. Optionally export `pursue` hypotheses via Step H strategy exporter.

## Scripts

- Pass 1 (evidence summary):

```bash
python3 skills/trade-hypothesis-ideator/scripts/run_hypothesis_ideator.py \
  --input skills/trade-hypothesis-ideator/examples/example_input.json \
  --output-dir reports/
```

- Pass 2 (rank + output + optional export):

```bash
python3 skills/trade-hypothesis-ideator/scripts/run_hypothesis_ideator.py \
  --input skills/trade-hypothesis-ideator/examples/example_input.json \
  --hypotheses reports/raw_hypotheses.json \
  --output-dir reports/ \
  --export-strategies
```

## References

- `references/hypothesis_types.md`
- `references/evidence_quality_guide.md`
