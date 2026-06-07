# Nanobot Qwen 507 Completion Report

## 1. Executive Summary

PASS: the full 507-case Nanobot continuation completed safely and was evaluated. The final merged Nanobot raw output contains 507 records for 507 unique case IDs, with no corrupt JSONL lines, no duplicates, no missing cases, and no final failed cases.

This is a 507-case natural-distribution scaling check for baselines plus Nanobot only. It does not replace the frozen 120-case six-agent stress-enriched validation.

## 2. 120 Freeze Safety Confirmation

- Freeze manifest checked: `results/freeze_120_audit/FREEZE_120_MANIFEST.csv`
- Checked frozen files: 325
- Missing frozen files: 0
- Changed frozen files: 0
- Verdict: **PASS**

No frozen 120-case artifacts were modified.

## 3. Existing Partial Output Summary

- Original partial source: `results/stableeval_507_natural/raw_outputs/nanobot_qwen_507_raw/nanobot_predictions.jsonl`
- Original partial records: 32
- Continuation source: `results/stableeval_507_natural/raw_outputs/nanobot_qwen_507_continuation/nanobot_predictions_continuation.jsonl`
- Continuation records: 475
- Final merged records: 507
- Complete SHA256: `da18af013f7333a8b051ad85930c23a595a7fb086e249b471b34fb7ee26f9f11`

## 4. Continuation Method

The continuation runner skipped already completed case IDs, processed only missing cases, saved after each successful case, and used bounded retries. It wrote only under `results/stableeval_507_natural/`.

- Runner: `scripts/run_agents/stableeval_507_natural/run_nanobot_qwen_507_resume_safe.py`
- Agent: Nanobot only
- Backend: `qwen/qwen-2.5-72b-instruct` via OpenRouter
- Temperature: 0
- Batch size: 25 for the full continuation
- Per-case timeout: 180 seconds
- Max retries: 3
- Failed final cases: none
- Retry summary: {"attempt_rows": 476, "cases_with_retry": ["USDC_2025060923"], "failed_attempts": 1, "max_attempt": 2, "successful_attempts": 475}

One transient OpenRouter upstream provider error occurred for `USDC_2025060923`; it was not appended as a prediction and succeeded on attempt 2 with the same Qwen model.

## 5. Case and Label Summary

- Total cases: 507
- Class distribution: stable=441, watch=45, stress=21
- Sustained severe depeg positives: 3

## 6. Raw and Calibrated Nanobot Metrics

| system | accuracy | macro_f1 | balanced_accuracy | stable_recall | watch_recall | stress_recall | missed_depeg_rate | brier | max_dev_mae_bps | valid_json | cost_usd |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| nanobot_qwen_507_raw | 0.3550 | 0.2232 | 0.3888 | 0.3220 | 0.8444 | 0.0000 | 1.0000 | 0.0226 | 30.2416 | 1.0000 | 1.4710 |
| nanobot_qwen_507_calibrated | 0.3945 | 0.2874 | 0.4275 | 0.3651 | 0.8222 | 0.0952 | 1.0000 | 0.0226 | 30.2416 | 1.0000 | 1.4710 |

Calibration improved Macro-F1 from 0.2232 to 0.2874, balanced accuracy from 0.3888 to 0.4275, and stress recall from 0.0000 to 0.0952. It did not change probability or max-deviation metrics.

## 7. Baseline Comparison

| system | taskA_accuracy | taskA_macro_f1 | taskA_balanced_accuracy | taskA_recall_stress | missed_depeg_rate | false_alarm_rate | binary_brier_score | deviation_mae_bps | valid_json_rate | avg_latency_seconds | total_estimated_cost_usd |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| always_stable | 0.8698 | 0.3101 | 0.3333 | 0.0000 | 1.0000 | 0.0000 | 0.0059 | 20.1696 | 1.0000 | 0.0000 | 0.0000 |
| historical_persistence | 0.6726 | 0.3867 | 0.4500 | 0.3333 | 0.6667 | 0.1488 | 0.1116 | 52.6647 | 1.0000 | 0.0000 | 0.0000 |
| threshold_rule | 0.6450 | 0.3763 | 0.4461 | 0.3333 | 1.0000 | 0.0952 | 0.0926 | 52.6885 | 1.0000 | 0.0000 | 0.0000 |
| simple_ml_softmax_logistic | 0.6410 | 0.4019 | 0.4930 | 0.3810 | 1.0000 | 0.0774 | 0.0673 | 17.0667 | 1.0000 | 0.0000 | 0.0000 |
| nanobot_qwen_507_raw | 0.3550 | 0.2232 | 0.3888 | 0.0000 | 1.0000 | 0.0020 | 0.0226 | 30.2416 | 1.0000 | 28.4315 | 1.4710 |
| nanobot_qwen_507_calibrated | 0.3945 | 0.2874 | 0.4275 | 0.0952 | 1.0000 | 0.0020 | 0.0226 | 30.2416 | 1.0000 | 28.4315 | 1.4710 |

Nanobot calibrated beats always-stable on balanced accuracy (0.4275 vs 0.3333) but not on accuracy or Macro-F1. It does not beat the simple ML/logistic baseline on Macro-F1 or balanced accuracy.

## 8. Confusion Matrix Summary

Raw Nanobot:

```csv
,stable,watch,stress,invalid
stable,142,298,1,0
watch,7,38,0,0
stress,2,19,0,0
```

Calibrated Nanobot:

```csv
,stable,watch,stress,invalid
stable,161,275,5,0
watch,7,37,1,0
stress,4,15,2,0
```

Nanobot is watch-heavy on the natural-distribution set. Calibration recovers 2 of 21 stress-label cases, but sustained-depeg detection remains weak under the binary severe-depeg probability metric.

## 9. Cost, Token, and Runtime Summary

- Total prompt tokens: 3944382
- Total completion tokens: 127566
- Total tokens: 4071948
- Total latency seconds: 14414.748
- Mean latency seconds/case: 28.431
- Total estimated cost USD: 1.471004
- Cost per case USD: 0.002901
- Valid JSON rate: 1.0000
- Failure rate: 0.0000

## 10. Paper Interpretation

The 507-case natural-distribution scaling check reinforces that ordinary accuracy is misleading under stable-dominant class imbalance: always-stable reaches 0.8698 accuracy while having zero watch and stress recall. Nanobot produces valid structured outputs at scale and shows high watch recall, but its calibrated result remains modest and does not solve rare stress detection. This supports the paper's trustworthiness framing: current agentic systems can run the structured protocol reliably, but reliability of severe-risk recognition remains limited.

This result should be described as an additional 507-case natural-distribution scaling check for baselines plus Nanobot, preferably in the appendix or as a short robustness subsection. It should not be described as scaling the full six-agent benchmark.

## 11. Failed Cases and Caveats

- Final failed cases: none
- Corrupted records: none
- Duplicate case IDs: none
- Missing case IDs: none
- Caveat: one transient OpenRouter upstream provider error occurred and was recovered by retry.
- Caveat: only Nanobot was run on 507; no six-agent 507 benchmark was performed.
- Caveat: partial32 metrics remain historical diagnostic output and should not be used as final results.

## 12. Exact Files Created or Used for Final Outputs

A detailed artifact manifest is saved at `results/stableeval_507_natural/metadata/nanobot_qwen_507_completion_artifact_manifest.csv`.

Key created artifacts:

- `scripts/run_agents/stableeval_507_natural/run_nanobot_qwen_507_resume_safe.py`
- `results/stableeval_507_natural/metadata/nanobot_qwen_507_completed_case_ids_before_continuation.csv`
- `results/stableeval_507_natural/metadata/nanobot_qwen_507_remaining_case_ids_before_continuation.csv`
- `results/stableeval_507_natural/metadata/nanobot_qwen_507_continuation_plan.json`
- `results/stableeval_507_natural/raw_outputs/nanobot_qwen_507_continuation/nanobot_predictions_continuation.jsonl`
- `results/stableeval_507_natural/raw_outputs/nanobot_qwen_507_continuation/nanobot_predictions_retry_log.csv`
- `results/stableeval_507_natural/raw_outputs/nanobot_qwen_507_continuation/nanobot_predictions_batch_log.csv`
- `results/stableeval_507_natural/raw_outputs/nanobot_qwen_507_continuation/nanobot_predictions_runtime_log.csv`
- `results/stableeval_507_natural/raw_outputs/nanobot_qwen_507_complete/nanobot_predictions_507_complete.jsonl`
- `results/stableeval_507_natural/raw_outputs/nanobot_qwen_507_complete/nanobot_predictions.jsonl`
- `results/stableeval_507_natural/raw_outputs/nanobot_qwen_507_complete_calibrated/nanobot_predictions.jsonl`
- `results/stableeval_507_natural/metadata/nanobot_qwen_507_merge_report.md`
- `results/stableeval_507_natural/metadata/nanobot_qwen_507_merge_report.json`
- `results/stableeval_507_natural/parsed_predictions/nanobot_qwen_507_raw_predictions.csv`
- `results/stableeval_507_natural/parsed_predictions/nanobot_qwen_507_calibrated_predictions.csv`
- `results/stableeval_507_natural/metrics/nanobot_qwen_507_prediction_quality.csv`
- `results/stableeval_507_natural/metrics/scaling_507_baselines_plus_nanobot_quality.csv`
- `results/stableeval_507_natural/tables/scaling_507_natural_distribution_leaderboard.csv`
- `results/stableeval_507_natural/tables/scaling_507_summary_metrics.csv`
- `results/stableeval_507_natural/costs/nanobot_qwen_507_cost_report.csv`
- `results/stableeval_507_natural/confusion_matrices/nanobot_qwen_507_raw_confusion_matrix.csv`
- `results/stableeval_507_natural/confusion_matrices/nanobot_qwen_507_calibrated_confusion_matrix.csv`
- `results/stableeval_507_natural/confusion_matrices/nanobot_qwen_507_raw_confusion_matrix.png`
- `results/stableeval_507_natural/confusion_matrices/nanobot_qwen_507_calibrated_confusion_matrix.png`
- `results/stableeval_507_natural/metadata/freeze_120_integrity_after_nanobot_completion.json`
- `results/stableeval_507_natural/metadata/FREEZE_120_INTEGRITY_AFTER_NANOBOT_COMPLETION.md`

## 13. Recommended Next Step

Use this completed 507 result to revise the Results/Discussion framing. Emphasize natural-distribution class imbalance, valid-output scalability, cost, and the trustworthiness gap in rare stress/severe-depeg detection. After that, decide whether to run a separate OpenClaw/NanoClaw native feasibility audit; do not mix that with this completed 507 Nanobot result.
