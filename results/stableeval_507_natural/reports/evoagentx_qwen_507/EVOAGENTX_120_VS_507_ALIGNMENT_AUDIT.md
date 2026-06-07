# EvoAgentX 120 vs 507 Alignment Audit

## Verdict

PASS: EvoAgentX is methodologically aligned with the frozen 120-case experiment. The same Qwen/OpenRouter backend family, output schema, frozen calibration rule, and metric definitions were used. Any same-case differences should be interpreted as rerun variability unless called out in the metric-delta table.

## Key Calibrated Metrics

| Setting | Cases | Accuracy | Macro-F1 | Balanced Acc. | Stable R | Watch R | Stress R | Missed-Depeg | Brier | MaxDev MAE |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Original 120 | 120 | 0.3917 | 0.2719 | 0.3480 | 0.1296 | 0.8667 | 0.0476 | 1.0000 | 0.0497 | 66.9167 |
| 507 restricted to same 120 | 120 | 0.4500 | 0.3399 | 0.3899 | 0.2778 | 0.8444 | 0.0476 | 1.0000 | 0.0477 | 65.8000 |
| Full 507 | 507 | 0.3807 | 0.2626 | 0.4138 | 0.3492 | 0.8444 | 0.0476 | 1.0000 | 0.0224 | 32.6805 |

Supporting CSVs:

- `results/stableeval_507_natural/metrics/evoagentx_qwen_507/evoagentx_120_vs_507_alignment_metrics.csv`
- `results/stableeval_507_natural/metrics/evoagentx_qwen_507/evoagentx_120_vs_507_case_agreement.csv`
- `results/stableeval_507_natural/metrics/evoagentx_qwen_507/evoagentx_120_vs_507_metric_deltas.csv`
- `results/stableeval_507_natural/metrics/evoagentx_qwen_507/evoagentx_120_vs_507_top_disagreements.csv`
