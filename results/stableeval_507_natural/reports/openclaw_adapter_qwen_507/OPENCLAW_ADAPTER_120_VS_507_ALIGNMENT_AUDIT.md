# OpenClaw adapter 120 vs 507 Alignment Audit

## Verdict

PARTIAL PASS: OpenClaw adapter is methodologically aligned with the frozen 120-case experiment. The same Qwen/OpenRouter backend family, output schema, frozen calibration rule, and metric definitions were used. Any same-case differences should be interpreted as rerun variability unless called out in the metric-delta table.

## Key Calibrated Metrics

| Setting | Cases | Accuracy | Macro-F1 | Balanced Acc. | Stable R | Watch R | Stress R | Missed-Depeg | Brier | MaxDev MAE |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Original 120 | 120 | 0.4083 | 0.3176 | 0.3675 | 0.1852 | 0.8222 | 0.0952 | 1.0000 | 0.0482 | 62.0000 |
| 507 restricted to same 120 | 120 | 0.4083 | 0.2963 | 0.3591 | 0.1852 | 0.8444 | 0.0476 | 1.0000 | 0.0491 | 67.3167 |
| Full 507 | 507 | 0.3531 | 0.2485 | 0.4032 | 0.3175 | 0.8444 | 0.0476 | 1.0000 | 0.0229 | 34.6548 |

Supporting CSVs:

- `results/stableeval_507_natural/metrics/openclaw_adapter_qwen_507/openclaw_adapter_120_vs_507_alignment_metrics.csv`
- `results/stableeval_507_natural/metrics/openclaw_adapter_qwen_507/openclaw_adapter_120_vs_507_case_agreement.csv`
- `results/stableeval_507_natural/metrics/openclaw_adapter_qwen_507/openclaw_adapter_120_vs_507_metric_deltas.csv`
- `results/stableeval_507_natural/metrics/openclaw_adapter_qwen_507/openclaw_adapter_120_vs_507_top_disagreements.csv`
