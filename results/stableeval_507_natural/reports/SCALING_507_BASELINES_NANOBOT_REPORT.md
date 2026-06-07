# 507-Case Natural-Distribution Scaling Check: Baselines + Nanobot

## 1. Executive Summary

**Verdict: PARTIAL PASS.** The 507-case baseline evaluation completed safely. The Nanobot dry run passed, but the full Nanobot 507 run stalled during the SDK/OpenRouter network call path after 32 completed cases. I stopped the active process to avoid an indefinite background API run. The completed Nanobot records are preserved and scored only as a partial 32-case result.

This is an additive natural-distribution scaling check. It does not replace the frozen 120-case six-agent stress-enriched validation experiment.

## 2. 120-Case Freeze Safety Confirmation

Freeze manifest checked: `results/freeze_120_audit/FREEZE_120_MANIFEST.csv`
Frozen entries considered: 325
Files checked: 325
Unchanged files: 325
Missing entries: 0
Changed entries: 0
Freeze integrity verdict: **PASS**

## 3. 507 Input/Case Summary

Case file: `results/stableeval_507_natural/case_ids/natural_distribution_507_case_list.csv`
Prompt packet file: `results/stableeval_507_natural/prompt_packets/natural_distribution_507_prompt_packets.jsonl`
Cases: 507
Prompt packets: 507
Case IDs unique: 507
Case IDs match packets: True
Class distribution: stable=441, watch=45, stress=21
Schema match: pass (0 mismatches)
Leakage check: pass (0 findings)

## 4. Protocol Continuity Statement

The 507 check uses the frozen case/prompt contract from the 120-case experiment: 30-day evidence packets, hidden next-7-day labels and outcomes, the same structured output schema, Qwen via OpenRouter, temperature 0, and the frozen risk-sensitive calibration rule. Outputs were written only under `results/stableeval_507_natural/`.

## 5. Baseline Results on Full 507 Cases

| system | cases | taskA_accuracy | taskA_macro_f1 | taskA_balanced_accuracy | taskA_recall_stable | taskA_recall_watch | taskA_recall_stress | missed_depeg_rate | false_alarm_rate | binary_brier_score | deviation_mae_bps | deviation_rmse_bps |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| simple_ml_softmax_logistic | 507.0000 | 0.6410 | 0.4019 | 0.4930 | 0.6757 | 0.4222 | 0.3810 | 1.0000 | 0.0774 | 0.0673 | 17.0667 | 72.3349 |
| historical_persistence | 507.0000 | 0.6726 | 0.3867 | 0.4500 | 0.7279 | 0.2889 | 0.3333 | 0.6667 | 0.1488 | 0.1116 | 52.6647 | 154.2884 |
| threshold_rule | 507.0000 | 0.6450 | 0.3763 | 0.4461 | 0.6939 | 0.3111 | 0.3333 | 1.0000 | 0.0952 | 0.0926 | 52.6885 | 154.2875 |
| always_stable | 507.0000 | 0.8698 | 0.3101 | 0.3333 | 1.0000 | 0.0000 | 0.0000 | 1.0000 | 0.0000 | 0.0059 | 20.1696 | 72.6656 |

Interpretation: always-stable has high accuracy because the natural distribution is dominated by stable cases, but its Macro-F1, balanced accuracy, watch recall, stress recall, and missed-depeg rate show that high accuracy alone is not a trustworthy risk-monitoring result.

## 6. Nanobot Dry Run

Dry-run cases: 5
Valid JSON: 5/5 (1.0000)
Backend: openrouter/qwen/qwen-2.5-72b-instruct
Execution mode: nanobot_sdk_openrouter_agent_loop
Total estimated cost: $0.014502
Cost per case: $0.002900
Mean latency: 27.7967 seconds
Passed full-run gate: True

## 7. Full Nanobot Run Status

The full Nanobot run was attempted after the dry run passed. It completed 32 unique cases with 100% valid JSON, then stopped making progress during the Nanobot SDK/OpenRouter network call path. The active process was interrupted after the output file remained unchanged and the process stayed idle-looking. This is reported as a partial run, not a completed 507-case Nanobot result.

Completed Nanobot records: 32/507
Unique completed case IDs: 32
Backend values: openrouter/qwen/qwen-2.5-72b-instruct
Total estimated Nanobot full-run partial cost: $0.092873
Total approximate tokens: 257107
Mean latency: 29.0965 seconds

## 8. Partial Nanobot Metrics

| system | cases | taskA_accuracy | taskA_macro_f1 | taskA_balanced_accuracy | taskA_recall_stable | taskA_recall_watch | taskA_recall_stress | missed_depeg_rate | false_alarm_rate | binary_brier_score | deviation_mae_bps | deviation_rmse_bps | valid_json_rate | failure_rate | total_estimated_cost_usd | cost_per_case_usd | avg_latency_seconds | avg_total_tokens |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nanobot_qwen_partial32_raw | 32.0000 | 0.3438 | 0.2402 | 0.4444 | 0.3333 | 1.0000 | 0.0000 | 1.0000 | 0.0345 | 0.1169 | 120.3125 | 305.8711 | 1.0000 | 0.0000 | 0.0929 | 0.0029 | 29.0965 | 8034.5938 |
| nanobot_qwen_partial32_calibrated | 32.0000 | 0.3750 | 0.3311 | 0.5111 | 0.3333 | 1.0000 | 0.2000 | 1.0000 | 0.0345 | 0.1169 | 120.3125 | 305.8711 | 1.0000 | 0.0000 | 0.0929 | 0.0029 | 29.0965 | 8034.5938 |

These partial metrics are not directly comparable to the full 507 baseline rows because they cover only the first 32 completed Nanobot cases.

## 9. Cost/Latency/Token Summary

| system | cases | total_estimated_cost_usd | cost_per_case_usd | avg_latency_seconds | avg_total_tokens | valid_json_rate | failure_rate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| nanobot_qwen_partial32_calibrated | 32.0000 | 0.0929 | 0.0029 | 29.0965 | 8034.5938 | 1.0000 | 0.0000 |
| nanobot_qwen_partial32_raw | 32.0000 | 0.0929 | 0.0029 | 29.0965 | 8034.5938 | 1.0000 | 0.0000 |
| always_stable | 507.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 0.0000 |
| historical_persistence | 507.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 0.0000 |
| simple_ml_softmax_logistic | 507.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 0.0000 |
| threshold_rule | 507.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 0.0000 |

## 10. Confusion Matrix Summary

Confusion matrices were written for all full baselines and for the raw/calibrated partial Nanobot results under `results/stableeval_507_natural/confusion_matrices/`.

## 11. 507 vs. 120 Interpretation

The 507 natural-distribution baseline results support the methodological point from the 120-case validation: ordinary accuracy can look strong when stable cases dominate, while Macro-F1, balanced accuracy, stress recall, and missed-depeg rate expose trustworthiness weaknesses. The completed partial Nanobot records are too small to support a full 507 Nanobot claim.

## 12. Paper-Ready Interpretation Paragraph

As an additive robustness check, we evaluated non-LLM baselines on the full 507-case natural-distribution pool. The always-stable baseline reaches high accuracy because 441 of 507 cases are stable, but it has zero watch/stress recall and a missed-depeg rate of 1.0. This confirms that StableEval Arena should not be interpreted through accuracy alone: trustworthy stablecoin risk assessment requires balanced class metrics, stress recall, missed-depeg diagnostics, calibration, and operational cost metrics. A Nanobot Qwen dry run passed, but the attempted full 507 Nanobot run stalled after 32 completed cases, so we report those records only as partial operational evidence rather than a completed full-scale agent result.

## 13. Exact Files Created Under `results/stableeval_507_natural/`

- `results/stableeval_507_natural/baselines/raw_predictions.csv`
- `results/stableeval_507_natural/baselines/raw_predictions.jsonl`
- `results/stableeval_507_natural/case_ids/natural_distribution_507_case_list.csv`
- `results/stableeval_507_natural/confusion_matrices/always_stable_507_confusion_matrix.csv`
- `results/stableeval_507_natural/confusion_matrices/always_stable_507_confusion_matrix.png`
- `results/stableeval_507_natural/confusion_matrices/historical_persistence_507_confusion_matrix.csv`
- `results/stableeval_507_natural/confusion_matrices/historical_persistence_507_confusion_matrix.png`
- `results/stableeval_507_natural/confusion_matrices/nanobot_qwen_partial32_calibrated_confusion_matrix.csv`
- `results/stableeval_507_natural/confusion_matrices/nanobot_qwen_partial32_calibrated_confusion_matrix.png`
- `results/stableeval_507_natural/confusion_matrices/nanobot_qwen_partial32_raw_confusion_matrix.csv`
- `results/stableeval_507_natural/confusion_matrices/nanobot_qwen_partial32_raw_confusion_matrix.png`
- `results/stableeval_507_natural/confusion_matrices/simple_ml_softmax_logistic_507_confusion_matrix.csv`
- `results/stableeval_507_natural/confusion_matrices/simple_ml_softmax_logistic_507_confusion_matrix.png`
- `results/stableeval_507_natural/confusion_matrices/threshold_rule_507_confusion_matrix.csv`
- `results/stableeval_507_natural/confusion_matrices/threshold_rule_507_confusion_matrix.png`
- `results/stableeval_507_natural/costs/baseline_cost_report_507.csv`
- `results/stableeval_507_natural/costs/nanobot_qwen_507_partial32_cost_report.csv`
- `results/stableeval_507_natural/dry_run_nanobot_qwen/DRY_RUN_5_VALIDATION_SUMMARY.md`
- `results/stableeval_507_natural/dry_run_nanobot_qwen/dry_run_5_case_list.csv`
- `results/stableeval_507_natural/dry_run_nanobot_qwen/dry_run_5_prompt_packets.jsonl`
- `results/stableeval_507_natural/dry_run_nanobot_qwen/dry_run_5_selection_metadata.json`
- `results/stableeval_507_natural/dry_run_nanobot_qwen/dry_run_5_validation_summary.json`
- `results/stableeval_507_natural/dry_run_nanobot_qwen/nanobot_qwen_dry_run_5_raw.jsonl`
- `results/stableeval_507_natural/logs/nanobot_qwen_507_full_raw.log`
- `results/stableeval_507_natural/logs/nanobot_qwen_dry_run_5.log`
- `results/stableeval_507_natural/metadata/FREEZE_120_INTEGRITY_AFTER_SCALING.md`
- `results/stableeval_507_natural/metadata/README.md`
- `results/stableeval_507_natural/metadata/agent_execution_metadata_120_reference.csv`
- `results/stableeval_507_natural/metadata/baseline_507_notes.json`
- `results/stableeval_507_natural/metadata/baseline_507_notes_corrected.json`
- `results/stableeval_507_natural/metadata/calibration_rule.md`
- `results/stableeval_507_natural/metadata/freeze_120_integrity_after_scaling.json`
- `results/stableeval_507_natural/metadata/input_readiness_507.json`
- `results/stableeval_507_natural/metadata/model_backend.json`
- `results/stableeval_507_natural/metadata/scaling_507_protocol_snapshot.json`
- `results/stableeval_507_natural/metrics/baseline_prediction_quality_507.csv`
- `results/stableeval_507_natural/metrics/nanobot_qwen_507_partial32_prediction_quality.csv`
- `results/stableeval_507_natural/metrics/nanobot_qwen_507_partial32_summary.json`
- `results/stableeval_507_natural/metrics/scaling_507_baselines_plus_nanobot_partial32_quality.csv`
- `results/stableeval_507_natural/parsed_predictions/nanobot_qwen_507_partial32_calibrated_predictions.csv`
- `results/stableeval_507_natural/parsed_predictions/nanobot_qwen_507_partial32_calibrated_predictions.jsonl`
- `results/stableeval_507_natural/parsed_predictions/nanobot_qwen_507_partial32_raw_predictions.csv`
- `results/stableeval_507_natural/parsed_predictions/nanobot_qwen_507_partial32_raw_predictions.jsonl`
- `results/stableeval_507_natural/prompt_packets/natural_distribution_507_prompt_packets.jsonl`
- `results/stableeval_507_natural/raw_outputs/nanobot_qwen_507_calibrated_partial32/nanobot_predictions.jsonl`
- `results/stableeval_507_natural/raw_outputs/nanobot_qwen_507_raw/nanobot_predictions.jsonl`
- `results/stableeval_507_natural/reports/BASELINE_507_SUMMARY.md`
- `results/stableeval_507_natural/reports/INPUT_READINESS_507.md`
- `results/stableeval_507_natural/reports/SCALING_507_BASELINES_NANOBOT_REPORT.md`
- `results/stableeval_507_natural/tables/baseline_results_507.csv`
- `results/stableeval_507_natural/tables/nanobot_qwen_507_partial32_results.csv`
- `results/stableeval_507_natural/tables/scaling_507_baselines_plus_nanobot_partial32_leaderboard.csv`

## 14. Caveats

- The 507 baseline results are complete.
- The full Nanobot 507 result is not complete and should not be used as a final benchmark row.
- An earlier baseline metadata note is superseded by `results/stableeval_507_natural/metadata/baseline_507_notes_corrected.json`, because the final baseline metrics include `simple_ml_softmax_logistic`.
- No OpenClaw, NanoClaw, LangGraph, Hermes AI, or EvoAgentX 507 run was performed.
- No paper source was edited.

## 15. Recommended Next Step

Do not add the partial Nanobot row as a main 507 result. Use the full 507 baseline table as a natural-distribution robustness check. Before retrying Nanobot, add or configure a bounded SDK timeout/resume-safe execution path in a new 507-specific run folder, then resume from the 32 completed case IDs only if explicitly approved.