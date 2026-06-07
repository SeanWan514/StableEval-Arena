# Hermes AI 120 vs 507 Alignment Audit

## Verdict

PASS: Hermes AI is methodologically aligned with the frozen 120-case experiment. The same Qwen/OpenRouter backend family, output schema, frozen calibration rule, and metric definitions were used. Any same-case differences should be interpreted as rerun variability unless called out in the metric-delta table.

## Key Calibrated Metrics

| Setting | Cases | Accuracy | Macro-F1 | Balanced Acc. | Stable R | Watch R | Stress R | Missed-Depeg | Brier | MaxDev MAE |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Original 120 | 120 | 0.4250 | 0.3213 | 0.3690 | 0.2593 | 0.8000 | 0.0476 | 1.0000 | 0.0475 | 57.8583 |
| 507 restricted to same 120 | 120 | 0.4583 | 0.3697 | 0.4046 | 0.2963 | 0.8222 | 0.0952 | 1.0000 | 0.0458 | 65.2917 |
| Full 507 | 507 | 0.4083 | 0.3011 | 0.4328 | 0.3810 | 0.8222 | 0.0952 | 1.0000 | 0.0193 | 34.3748 |

Supporting CSVs:

- `results/stableeval_507_natural/metrics/hermes_ai_qwen_507/hermes_ai_120_vs_507_alignment_metrics.csv`
- `results/stableeval_507_natural/metrics/hermes_ai_qwen_507/hermes_ai_120_vs_507_case_agreement.csv`
- `results/stableeval_507_natural/metrics/hermes_ai_qwen_507/hermes_ai_120_vs_507_metric_deltas.csv`
- `results/stableeval_507_natural/metrics/hermes_ai_qwen_507/hermes_ai_120_vs_507_top_disagreements.csv`
