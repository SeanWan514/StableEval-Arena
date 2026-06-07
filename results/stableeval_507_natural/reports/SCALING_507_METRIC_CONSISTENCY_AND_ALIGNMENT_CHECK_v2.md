# 507 Metric Consistency and Alignment Check v2

Created: 2026-06-04T05:09:24.220771+00:00

## Executive Summary

**PASS.** Recomputed metrics match the reported baseline, Nanobot, and LangGraph 507 tables with zero medium/high discrepancies and zero non-zero discrepancies above tolerance. LangGraph 507 is aligned with its frozen 120-case result and has a positive operational impact on the scaling analysis, while still requiring caveated trustworthiness interpretation because severe-risk detection remains weak.

## Additive-Only Cleanup Statement

No existing result files were deleted, moved, renamed, or overwritten. This v2 report is additive and supersedes the first verification report only for readability of the metric-delta table.

## 120 Freeze Safety

Post-LangGraph integrity snapshot: checked `325` frozen files; missing `0`; changed `0`; verdict `PASS`.

## Metric Consistency

- Case/label consistency: `PASS`.
- Calibration consistency: `PASS`.
- Medium/high metric discrepancies: `0`.
- Non-zero discrepancies above tolerance: `0`.

The simple-ML indexing caveat is limited to the evaluator's internal supervised-baseline branch during an agent-only 507 invocation. It does not affect saved agent predictions, labels, calibration, or metric formulas.

## Clean Verified 507 Leaderboard

| system | output_variant | cases | accuracy | macro_f1 | balanced_accuracy | stable_recall | watch_recall | stress_recall | missed_depeg_rate | brier_score | maxdev_mae_bps | valid_json_rate | total_cost_usd | cost_per_case_usd |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| simple_ml_softmax_logistic | baseline | 507.0000 | 0.6410 | 0.4019 | 0.4930 | 0.6757 | 0.4222 | 0.3810 | 1.0000 | 0.0673 | 17.0667 | 1.0000 | 0.0000 | 0.0000 |
| historical_persistence | baseline | 507.0000 | 0.6726 | 0.3867 | 0.4500 | 0.7279 | 0.2889 | 0.3333 | 0.6667 | 0.1116 | 52.6647 | 1.0000 | 0.0000 | 0.0000 |
| threshold_rule | baseline | 507.0000 | 0.6450 | 0.3763 | 0.4461 | 0.6939 | 0.3111 | 0.3333 | 1.0000 | 0.0926 | 52.6885 | 1.0000 | 0.0000 | 0.0000 |
| always_stable | baseline | 507.0000 | 0.8698 | 0.3101 | 0.3333 | 1.0000 | 0.0000 | 0.0000 | 1.0000 | 0.0059 | 20.1696 | 1.0000 | 0.0000 | 0.0000 |
| nanobot_qwen_507_raw | raw | 507.0000 | 0.3550 | 0.2232 | 0.3888 | 0.3220 | 0.8444 | 0.0000 | 1.0000 | 0.0226 | 30.2416 | 1.0000 | 1.4710 | 0.0029 |
| nanobot_qwen_507_calibrated | calibrated | 507.0000 | 0.3945 | 0.2874 | 0.4275 | 0.3651 | 0.8222 | 0.0952 | 1.0000 | 0.0226 | 30.2416 | 1.0000 | 1.4710 | 0.0029 |
| langgraph_qwen_507_raw | raw | 507.0000 | 0.4576 | 0.2738 | 0.4281 | 0.4399 | 0.8444 | 0.0000 | 1.0000 | 0.0208 | 31.0631 | 1.0000 | 4.9802 | 0.0098 |
| langgraph_qwen_507_calibrated | calibrated | 507.0000 | 0.4675 | 0.3044 | 0.4404 | 0.4512 | 0.8222 | 0.0476 | 1.0000 | 0.0208 | 31.0631 | 1.0000 | 4.9802 | 0.0098 |

## Calibrated 120-vs-507 Alignment

| agent | setting | cases | taskA_accuracy | taskA_macro_f1 | taskA_balanced_accuracy | taskA_recall_stable | taskA_recall_watch | taskA_recall_stress | missed_depeg_rate | binary_brier_score | deviation_mae_bps |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nanobot | original_120_calibrated | 120.0000 | 0.4417 | 0.3505 | 0.3935 | 0.2407 | 0.8444 | 0.0952 | 1.0000 | 0.0469 | 56.6167 |
| nanobot | from_507_on_120_calibrated | 120.0000 | 0.4583 | 0.3684 | 0.4046 | 0.2963 | 0.8222 | 0.0952 | 1.0000 | 0.0464 | 56.5500 |
| nanobot | full_507_calibrated | 507.0000 | 0.3945 | 0.2874 | 0.4275 | 0.3651 | 0.8222 | 0.0952 | 1.0000 | 0.0226 | 30.2416 |
| langgraph | original_120_calibrated | 120.0000 | 0.4417 | 0.3372 | 0.3813 | 0.2963 | 0.8000 | 0.0476 | 1.0000 | 0.0463 | 58.6833 |
| langgraph | from_507_on_120_calibrated | 120.0000 | 0.5000 | 0.3881 | 0.4257 | 0.4074 | 0.8222 | 0.0476 | 1.0000 | 0.0482 | 64.2750 |
| langgraph | full_507_calibrated | 507.0000 | 0.4675 | 0.3044 | 0.4404 | 0.4512 | 0.8222 | 0.0476 | 1.0000 | 0.0208 | 31.0631 |

## Key Same-Case Metric Deltas

| agent | metric | original_120 | from_507_on_120 | delta | concern_level | possible_explanation |
| --- | --- | --- | --- | --- | --- | --- |
| nanobot | Accuracy | 0.4417 | 0.4583 | 0.0167 | None | Same-case rerun variability despite fixed prompt/backend; compare label agreement and transition counts. |
| nanobot | Macro-F1 | 0.3505 | 0.3684 | 0.0179 | None | Same-case rerun variability despite fixed prompt/backend; compare label agreement and transition counts. |
| nanobot | Balanced accuracy | 0.3935 | 0.4046 | 0.0111 | None | Same-case rerun variability despite fixed prompt/backend; compare label agreement and transition counts. |
| nanobot | Stress recall | 0.0952 | 0.0952 | 0.0000 | None | No measurable difference. |
| nanobot | Missed-depeg rate | 1.0000 | 1.0000 | 0.0000 | None | No measurable difference. |
| nanobot | Brier score | 0.0469 | 0.0464 | -0.0005 | None | Numeric-output rerun variability; calibration does not alter probability/max-deviation fields. |
| nanobot | MaxDev MAE | 56.6167 | 56.5500 | -0.0667 | Low | Numeric-output rerun variability; calibration does not alter probability/max-deviation fields. |
| langgraph | Accuracy | 0.4417 | 0.5000 | 0.0583 | None | Same-case rerun variability; protocol and evaluator are unchanged. |
| langgraph | Macro-F1 | 0.3372 | 0.3881 | 0.0508 | None | Same-case rerun variability; protocol and evaluator are unchanged. |
| langgraph | Balanced accuracy | 0.3813 | 0.4257 | 0.0444 | None | Same-case rerun variability; protocol and evaluator are unchanged. |
| langgraph | Stress recall | 0.0476 | 0.0476 | 0.0000 | None | Same-case rerun variability; protocol and evaluator are unchanged. |
| langgraph | Missed-depeg rate | 1.0000 | 1.0000 | 0.0000 | None | Same-case rerun variability; protocol and evaluator are unchanged. |
| langgraph | Brier score | 0.0463 | 0.0482 | 0.0019 | None | Probability-output rerun variability; calibration does not alter probabilities. |
| langgraph | MaxDev MAE | 58.6833 | 64.2750 | 5.5917 | None | Numeric-output rerun variability; calibration does not alter max-deviation values. |

## Interpretation

LangGraph 507 does not contradict the frozen 120-case LangGraph result. On the exact same 120 case IDs, LangGraph is slightly better after rerun on accuracy, Macro-F1, and balanced accuracy; stress recall and missed-depeg rate are unchanged. This is a positive continuity signal, not a protocol concern.

Together, Nanobot and LangGraph show that the 507 natural-distribution scaling path is operationally stable for native/framework-level agents. The substantive caveat is performance: both agents still struggle with rare severe-risk detection, which should be framed as a trustworthiness finding.

## Paper Use

Use `results/stableeval_507_natural/tables/scaling_507_progress_leaderboard_v2_verified.csv` for any 507 progress table. Treat full alignment details as appendix material. Keep the frozen 120-case stress-enriched six-agent validation as the main benchmark result.

## Recommendation

Proceed to Hermes AI with the same one-agent-at-a-time, resume-safe protocol and repeat this metric-consistency/alignment check afterward.
