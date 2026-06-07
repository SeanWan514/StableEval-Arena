# 507 Metric Consistency and Alignment Check

Created: 2026-06-04T05:07:58.817914+00:00

## Executive Summary

**PASS.** Metrics are consistent across baselines, Nanobot, and LangGraph when recomputed from saved prediction rows and the same 507 case labels. LangGraph's 507 result is aligned with the frozen 120-case LangGraph result and has a positive operational impact on the scaling analysis, with the caveat that rare severe-risk detection remains weak.

## Additive-Only Cleanup Statement

No files were deleted, moved, renamed, or overwritten by this verification step. New outputs were created under `results/stableeval_507_natural/metrics/verification/`, `results/stableeval_507_natural/tables/`, `results/stableeval_507_natural/reports/`, and the additive index file at `results/stableeval_507_natural/SCALING_507_INDEX.md`.

## Artifact Location Check

No required artifacts missing. The only missing item is the optional dedicated evaluator error log; the caveat is documented in the LangGraph report.

## 120 Freeze Safety

Post-LangGraph integrity snapshot: checked `325` frozen files; missing `0`; changed `0`; verdict `PASS`.

## Metric Consistency Check

- Case/label consistency: `PASS`.
- Calibration consistency: `PASS`.
- Medium/high metric discrepancies: `0`.
- Non-zero discrepancies above tolerance: `0`.

No discrepancies above numerical tolerance. Reported baseline, Nanobot, and LangGraph metrics reproduce from saved prediction rows.

## Evaluator / Simple-ML Indexing Caveat

The direct evaluator invocation caveat is limited to the evaluator's internal supervised simple-ML baseline branch when used in an agent-only 507 invocation. It does not affect saved Nanobot or LangGraph predictions, labels, calibration, or metric definitions. Recomputing from saved prediction rows reproduces the reported baseline, Nanobot, and LangGraph metric tables.

## Table Version Check

| path | rows | duplicate_rows_by_available_system_key | note |
| --- | --- | --- | --- |
| results/stableeval_507_natural/tables/scaling_507_native_agents_progress_leaderboard.csv | 10.0000 | 2.0000 | review before paper use |
| results/stableeval_507_natural/tables/langgraph_qwen_507/langgraph_507_baseline_nanobot_comparison.csv | 10.0000 | 2.0000 | review before paper use |
| results/stableeval_507_natural/tables/scaling_507_natural_distribution_leaderboard.csv | 6.0000 | 0.0000 | no duplicate system rows detected |

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

## Calibrated 120-vs-507 Alignment Summary

| agent | setting | cases | taskA_accuracy | taskA_macro_f1 | taskA_balanced_accuracy | taskA_recall_stable | taskA_recall_watch | taskA_recall_stress | missed_depeg_rate | binary_brier_score | deviation_mae_bps |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nanobot | original_120_calibrated | 120.0000 | 0.4417 | 0.3505 | 0.3935 | 0.2407 | 0.8444 | 0.0952 | 1.0000 | 0.0469 | 56.6167 |
| nanobot | from_507_on_120_calibrated | 120.0000 | 0.4583 | 0.3684 | 0.4046 | 0.2963 | 0.8222 | 0.0952 | 1.0000 | 0.0464 | 56.5500 |
| nanobot | full_507_calibrated | 507.0000 | 0.3945 | 0.2874 | 0.4275 | 0.3651 | 0.8222 | 0.0952 | 1.0000 | 0.0226 | 30.2416 |
| langgraph | original_120_calibrated | 120.0000 | 0.4417 | 0.3372 | 0.3813 | 0.2963 | 0.8000 | 0.0476 | 1.0000 | 0.0463 | 58.6833 |
| langgraph | from_507_on_120_calibrated | 120.0000 | 0.5000 | 0.3881 | 0.4257 | 0.4074 | 0.8222 | 0.0476 | 1.0000 | 0.0482 | 64.2750 |
| langgraph | full_507_calibrated | 507.0000 | 0.4675 | 0.3044 | 0.4404 | 0.4512 | 0.8222 | 0.0476 | 1.0000 | 0.0208 | 31.0631 |

## Metric Delta Check

| agent | variant | metric | original_120 | from_507_on_120 | delta | concern_level | possible_explanation |
| --- | --- | --- | --- | --- | --- | --- | --- |

## LangGraph Impact

LangGraph does not contradict the frozen 120-case result. On the same 120 cases inside the 507 run, calibrated accuracy, Macro-F1, and balanced accuracy are slightly higher than the original frozen 120 LangGraph result, while stress recall and missed-depeg behavior remain essentially unchanged. This supports protocol continuity and strengthens the scaling story operationally.

## Joint Nanobot + LangGraph Interpretation

Together, the two completed 507 agent runs show that the protocol can scale beyond the 120-case stress-enriched validation for native/framework-level agents while preserving structured-output reliability. They also reinforce the trustworthiness gap: both agents are operationally reliable but weak on rare severe-risk detection.

## Paper Placement

Use the 507 result as a natural-distribution scaling check. Keep the 120-case stress-enriched six-agent validation as the main benchmark result. Put the compact verified leaderboard or summary in the main paper only if space allows; put full alignment and cost details in the appendix.

## Remaining Concerns

- Existing combined 507 tables with duplicate Nanobot rows should not be used for paper tables. Use `results/stableeval_507_natural/tables/scaling_507_progress_leaderboard_v2_verified.csv` instead.
- Both completed agents still have high missed-depeg rates; this is a trustworthiness limitation to discuss, not a metric-consistency problem.

## Recommendation

Proceed to Hermes AI using the same one-agent-at-a-time resume-safe protocol and the same post-run alignment audit.
