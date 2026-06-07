# StableEval-507-Natural Index

This folder contains the completed 507-case natural-distribution scaling block for StableEval Arena. It complements, but does not replace, the stress-enriched `StableEval-120-Enriched` validation under `results/stableeval_120_enriched/`.

## Canonical Paper-Use Files

| Use | File |
|---|---|
| 507 case list | `data/benchmark/stableeval_507_natural/case_list.csv` |
| 507 labels | `data/benchmark/stableeval_507_natural/labels.csv` |
| 507 prompt packets | `data/benchmark/stableeval_507_natural/prompt_packets.jsonl` |
| Final v6 leaderboard | `results/stableeval_507_natural/final_tables/stableeval_507_natural_v6_leaderboard.csv` |
| Baseline predictions | `results/stableeval_507_natural/baselines/raw_predictions.csv` |
| Baseline metrics | `results/stableeval_507_natural/metrics/baseline_prediction_quality_507.csv` |
| Metric recomputation | `results/stableeval_507_natural/metrics/verification/` |
| Alignment and stress audits | `results/stableeval_507_natural/reports/` and `results/stableeval_507_natural/metrics/` |
| Cost/reliability logs | `results/stableeval_507_natural/costs/` |

## Systems In The v6 Leaderboard

Baselines:

- `always_stable`
- `historical_persistence`
- `threshold_rule`
- `simple_ml_softmax_logistic`

Native/framework-level agents:

- `nanobot_qwen_507`
- `langgraph_qwen_507`
- `hermes_ai_qwen_507`
- `evoagentx_qwen_507`

Adapter-based `-Claw` extensions:

- `openclaw_adapter_qwen_507`
- `nanoclaw_adapter_qwen_507`

OpenClaw and NanoClaw native CMDOP execution was not verified in this release; cite them as adapter-based extensions.

## Raw And Calibrated Predictions

Raw outputs preserve the model's original categorical label:

```text
results/stableeval_507_natural/raw_predictions/
```

Calibrated outputs apply the frozen `risk_sensitive_v1_posthoc_frozen` categorical calibration rule:

```text
results/stableeval_507_natural/calibrated_predictions/
```

Calibration does not change probability or max-deviation fields.

## Superseded Artifacts

Dry runs, continuation traces, partial Nanobot 32-case outputs, and v2-v5 progress leaderboards were removed from the public release tree. The canonical public table is the v6 leaderboard in `final_tables/`.

## Release-Safe Verification

Use this no-API command to recompute the v6 leaderboard, stress audit, and cost/reliability summary from saved outputs into a temporary directory:

```bash
python scripts/evaluate/recompute_stableeval_507_natural.py \
  --root . \
  --out /tmp/stableeval_release_audit/stableeval_507_natural_recompute
```

The historical `finalize_*.py` scripts under `scripts/run_agents/stableeval_507_natural/` are retained for original-run provenance, not as the public verification entry point.
