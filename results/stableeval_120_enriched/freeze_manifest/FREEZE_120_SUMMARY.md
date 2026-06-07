# Freeze 120 Summary

Created UTC: 2026-06-03T09:10:22.602723+00:00

## Scope

This additive audit freezes the completed 120-case StableEval Arena validation artifacts by recording checksums and artifact roles. It does not modify the 120-case experiment, call any LLM API, or run any 507-case scaling experiment.

## Core Counts

- Validation case list lines: 121 (header + 120 cases).
- Validation prompt packets: 120 JSONL records.
- Main base-calibrated per-platform prediction files: 6 files, each expected to contain 120 records.
- Files checksummed in manifest: 325.

## Frozen Protocol Markers

- Main validation folder: `results/stableeval_120_enriched/`.
- Main prompt packet file: `data/benchmark/stableeval_120_enriched/prompt_packets.jsonl`.
- Main evaluation variant: `results/stableeval_120_enriched/evaluation_base_calibrated/`.
- Backend config: `results/stableeval_120_enriched/model_backend.json`.
- Calibration rule: `results/stableeval_120_enriched/calibration_rule.md`.
- Agent execution metadata: `results/stableeval_120_enriched/agent_execution_metadata.csv`.

## Future 507 Guidance

Future 507 experiments should reuse the prompt contract, output schema, backend, temperature, calibration rule, and evaluator logic, but must write all new predictions, parsed outputs, metrics, tables, figures, logs, and costs to a separate 507-specific output tree.
