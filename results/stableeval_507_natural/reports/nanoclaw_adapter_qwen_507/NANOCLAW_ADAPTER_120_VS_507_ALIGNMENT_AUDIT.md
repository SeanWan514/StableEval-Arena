# NanoClaw adapter 120 vs 507 Alignment Audit

## Verdict

PASS: NanoClaw adapter is methodologically aligned with the frozen 120-case experiment. The same Qwen/OpenRouter backend family, output schema, frozen calibration rule, and metric definitions were used. Any same-case differences should be interpreted as rerun variability unless called out in the metric-delta table.

## Key Calibrated Metrics

| Setting | Cases | Accuracy | Macro-F1 | Balanced Acc. | Stable R | Watch R | Stress R | Missed-Depeg | Brier | MaxDev MAE |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Original 120 | 120 | 0.4417 | 0.3278 | 0.3850 | 0.2407 | 0.8667 | 0.0476 | 1.0000 | 0.0498 | 66.3583 |
| 507 restricted to same 120 | 120 | 0.4750 | 0.3674 | 0.4060 | 0.3704 | 0.8000 | 0.0476 | 1.0000 | 0.0476 | 65.7000 |
| Full 507 | 507 | 0.4714 | 0.3041 | 0.4352 | 0.4580 | 0.8000 | 0.0476 | 1.0000 | 0.0205 | 31.6724 |

Supporting CSVs:

- `results/stableeval_507_natural/metrics/nanoclaw_adapter_qwen_507/nanoclaw_adapter_120_vs_507_alignment_metrics.csv`
- `results/stableeval_507_natural/metrics/nanoclaw_adapter_qwen_507/nanoclaw_adapter_120_vs_507_case_agreement.csv`
- `results/stableeval_507_natural/metrics/nanoclaw_adapter_qwen_507/nanoclaw_adapter_120_vs_507_metric_deltas.csv`
- `results/stableeval_507_natural/metrics/nanoclaw_adapter_qwen_507/nanoclaw_adapter_120_vs_507_top_disagreements.csv`
