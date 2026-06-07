# Nanobot 120 vs 507 Alignment Audit

Generated: 2026-06-04T00:48:34

## Executive Summary
Verdict: PARTIAL PASS. The completed 507-case Nanobot run is protocol-aligned with the frozen 120-case Nanobot run and is usable as a natural-distribution scaling check. It does not reveal a protocol-breaking contradiction. However, same-case rerun agreement is not perfect, and full-507 stress detection remains weak, so the result should be framed as robustness plus trustworthiness evidence, not as a stronger prediction-performance claim.

## Artifact Inventory
| artifact | path | exists | role |
| --- | --- | --- | --- |
| case_120 | results/stableeval_120_enriched/validation_case_list.csv | True | 120 case list |
| case_507 | results/stableeval_507_natural/case_ids/natural_distribution_507_case_list.csv | True | 507 case list |
| prompt_120 | results/stableeval_120_enriched/prompt_packets_120.jsonl | True | 120 prompt packets |
| prompt_507 | results/stableeval_507_natural/prompt_packets/natural_distribution_507_prompt_packets.jsonl | True | 507 prompt packets |
| raw_120_dir | results/stableeval_120_enriched/predictions_base_raw | True | 120 raw Nanobot predictions directory |
| cal_120_dir | results/stableeval_120_enriched/predictions_base_calibrated | True | 120 calibrated Nanobot predictions directory |
| raw_507_dir | results/stableeval_507_natural/raw_outputs/nanobot_qwen_507_complete | True | 507 raw Nanobot predictions directory |
| cal_507_dir | results/stableeval_507_natural/raw_outputs/nanobot_qwen_507_complete_calibrated | True | 507 calibrated Nanobot predictions directory |
| backend_120 | results/stableeval_120_enriched/model_backend.json | True | 120 backend config |
| backend_507 | results/stableeval_507_natural/metadata/model_backend.json | True | 507 backend config |
| cal_rule_120 | results/stableeval_120_enriched/calibration_rule.md | True | 120 calibration rule |
| cal_rule_507 | results/stableeval_507_natural/metadata/calibration_rule.md | True | 507 calibration rule |
| integrity_after_507 | results/stableeval_507_natural/metadata/freeze_120_integrity_after_nanobot_completion.json | True | post-507 freeze integrity |
| leaderboard_507 | results/stableeval_507_natural/tables/scaling_507_natural_distribution_leaderboard.csv | True | 507 leaderboard |
| completion_report_507 | results/stableeval_507_natural/reports/NANOBOT_QWEN_507_COMPLETION_REPORT.md | True | 507 completion report |
| artifact_manifest_507 | results/stableeval_507_natural/metadata/nanobot_qwen_507_completion_artifact_manifest.csv | True | 507 artifact manifest |
| evaluator | scripts/evaluate/evaluate_predictions.py | True | frozen evaluator script |

## Protocol Consistency
| component | same_different_unclear | evidence_path | concern_level | notes |
| --- | --- | --- | --- | --- |
| Case IDs | same | results/stableeval_120_enriched/validation_case_list.csv; results/stableeval_507_natural/case_ids/natural_distribution_507_case_list.csv | No concern | All 120 validation case IDs are contained in the 507 pool; 507 has 387 additional natural-distribution cases. |
| Case labels / hidden outcomes for overlapping 120 cases | same | case list column comparison | No concern | No mismatches in common label/outcome columns. |
| Prompt packets for overlapping 120 cases | same | results/stableeval_120_enriched/prompt_packets_120.jsonl; results/stableeval_507_natural/prompt_packets/natural_distribution_507_prompt_packets.jsonl | No concern | 120/120 overlapping prompt packet hashes match; missing=0 malformed120=0 malformed507=0. |
| Backend model | same | results/stableeval_120_enriched/model_backend.json; results/stableeval_507_natural/metadata/model_backend.json | No concern | 120=qwen/qwen-2.5-72b-instruct; 507=qwen/qwen-2.5-72b-instruct. |
| Temperature / decoding | same | results/stableeval_120_enriched/model_backend.json; results/stableeval_507_natural/metadata/model_backend.json | No concern | Both backend selection records document qwen/qwen-2.5-72b-instruct at temperature 0 in the frozen selection reason. |
| Calibration rule | same | results/stableeval_120_enriched/calibration_rule.md; results/stableeval_507_natural/metadata/calibration_rule.md | No concern | Frozen post-hoc risk-sensitive rule text matches exactly. |
| Evaluator / metric definitions | same | scripts/evaluate/evaluate_predictions.py | No concern | Audit reproduces the same local evaluator formulas for class order, binary threshold, Brier, ECE, and deviation errors. |
| Output schema | same | prediction JSONL files and protocol snapshot | No concern | Both contain predicted label, probability, max-deviation, direction, confidence, rationale, backend metadata, and cost/latency/token fields. |
| Frozen 120 artifact safety after 507 | same | results/stableeval_507_natural/metadata/freeze_120_integrity_after_nanobot_completion.json | No concern | {"changed_files": [], "checked_at_utc": "2026-06-03T15:23:21.464236+00:00", "checked_files": 325, "manifest": "results/freeze_120_audit/FREEZE_120_MANIFEST.csv", "missing_files": [], "verdict": "PASS"} |

## Raw Nanobot Alignment Metrics
| setting | cases | taskA_accuracy | taskA_macro_f1 | taskA_balanced_accuracy | taskA_recall_stable | taskA_recall_watch | taskA_recall_stress | missed_depeg_rate | binary_brier_score | deviation_mae_bps | valid_json_rate | failure_rate | total_estimated_cost_usd | cost_per_case_usd |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| original_120_raw | 120 | 0.4000 | 0.2660 | 0.3432 | 0.1852 | 0.8444 | 0.0000 | 1.0000 | 0.0469 | 56.6167 | 1.0000 | 0.0000 | 0.3454 | 0.0029 |
| from_507_on_120_raw | 120 | 0.4333 | 0.3009 | 0.3679 | 0.2593 | 0.8444 | 0.0000 | 1.0000 | 0.0464 | 56.5500 | 1.0000 | 0.0000 | 0.3483 | 0.0029 |
| full_507_raw | 507 | 0.3550 | 0.2232 | 0.3888 | 0.3220 | 0.8444 | 0.0000 | 1.0000 | 0.0226 | 30.2416 | 1.0000 | 0.0000 | 1.4710 | 0.0029 |

## Calibrated Nanobot Alignment Metrics
| setting | cases | taskA_accuracy | taskA_macro_f1 | taskA_balanced_accuracy | taskA_recall_stable | taskA_recall_watch | taskA_recall_stress | missed_depeg_rate | binary_brier_score | deviation_mae_bps | valid_json_rate | failure_rate | total_estimated_cost_usd | cost_per_case_usd |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| original_120_calibrated | 120 | 0.4417 | 0.3505 | 0.3935 | 0.2407 | 0.8444 | 0.0952 | 1.0000 | 0.0469 | 56.6167 | 1.0000 | 0.0000 | 0.3454 | 0.0029 |
| from_507_on_120_calibrated | 120 | 0.4583 | 0.3684 | 0.4046 | 0.2963 | 0.8222 | 0.0952 | 1.0000 | 0.0464 | 56.5500 | 1.0000 | 0.0000 | 0.3483 | 0.0029 |
| full_507_calibrated | 507 | 0.3945 | 0.2874 | 0.4275 | 0.3651 | 0.8222 | 0.0952 | 1.0000 | 0.0226 | 30.2416 | 1.0000 | 0.0000 | 1.4710 | 0.0029 |

## Case-Level Agreement Summary
| variant | audit_item | value | interpretation |
| --- | --- | --- | --- |
| raw | label_agreement_rate | 0.8333 | Prediction-label consistency between original 120 run and 507 rerun on the same 120 case IDs. |
| raw | changed_prediction_count | 20.0000 | Count of case-level label changes across reruns. |
| raw | p_depeg_correlation | 0.3962 | Correlation of predicted depeg probabilities across reruns. |
| raw | p_depeg_mean_abs_diff | 0.0392 | Average absolute probability drift across reruns. |
| raw | p_depeg_median_abs_diff | 0.0000 | Median absolute probability drift across reruns. |
| raw | maxdev_correlation | 0.0911 | Correlation of predicted max-deviation estimates across reruns. |
| raw | maxdev_mean_abs_diff_bps | 22.5167 | Average absolute max-deviation drift across reruns. |
| raw | maxdev_median_abs_diff_bps | 0.0000 | Median absolute max-deviation drift across reruns. |
| raw | direction_agreement_rate | 0.8583 | Agreement of predicted deviation direction across reruns. |
| raw | confidence_correlation | 0.3938 | Correlation of reported confidence across reruns. |
| raw | confidence_mean_abs_diff | 0.0358 | Average absolute confidence drift across reruns. |
| raw | input_packet_hash_agreement_rate | 0.0000 | Whether predictions report the same input packet hashes for same case IDs. |
| calibrated | label_agreement_rate | 0.8417 | Prediction-label consistency between original 120 run and 507 rerun on the same 120 case IDs. |
| calibrated | changed_prediction_count | 19.0000 | Count of case-level label changes across reruns. |
| calibrated | p_depeg_correlation | 0.3962 | Correlation of predicted depeg probabilities across reruns. |
| calibrated | p_depeg_mean_abs_diff | 0.0392 | Average absolute probability drift across reruns. |
| calibrated | p_depeg_median_abs_diff | 0.0000 | Median absolute probability drift across reruns. |
| calibrated | maxdev_correlation | 0.0911 | Correlation of predicted max-deviation estimates across reruns. |
| calibrated | maxdev_mean_abs_diff_bps | 22.5167 | Average absolute max-deviation drift across reruns. |
| calibrated | maxdev_median_abs_diff_bps | 0.0000 | Median absolute max-deviation drift across reruns. |
| calibrated | direction_agreement_rate | 0.8583 | Agreement of predicted deviation direction across reruns. |
| calibrated | confidence_correlation | 0.3938 | Correlation of reported confidence across reruns. |
| calibrated | confidence_mean_abs_diff | 0.0358 | Average absolute confidence drift across reruns. |
| calibrated | input_packet_hash_agreement_rate | 0.0000 | Whether predictions report the same input packet hashes for same case IDs. |

## Metric Deltas
| variant | metric | original_120 | from_507_on_120 | delta | concern_level | possible_explanation |
| --- | --- | --- | --- | --- | --- | --- |
| raw | Accuracy | 0.4000 | 0.4333 | 0.0333 | NA | Same-case rerun variability despite fixed prompt/backend; compare label agreement and transition counts. |
| raw | Macro-F1 | 0.2660 | 0.3009 | 0.0348 | Low | Same-case rerun variability despite fixed prompt/backend; compare label agreement and transition counts. |
| raw | Balanced accuracy | 0.3432 | 0.3679 | 0.0247 | NA | Same-case rerun variability despite fixed prompt/backend; compare label agreement and transition counts. |
| raw | Stable precision | 0.5263 | 0.6087 | 0.0824 | NA | Rerun/model-output variability under same protocol. |
| raw | Stable recall | 0.1852 | 0.2593 | 0.0741 | NA | Rerun/model-output variability under same protocol. |
| raw | Stable F1 | 0.2740 | 0.3636 | 0.0897 | NA | Rerun/model-output variability under same protocol. |
| raw | Watch precision | 0.3800 | 0.3958 | 0.0158 | NA | Rerun/model-output variability under same protocol. |
| raw | Watch recall | 0.8444 | 0.8444 | 0.0000 | NA | No measurable difference. |
| raw | Watch F1 | 0.5241 | 0.5390 | 0.0149 | NA | Rerun/model-output variability under same protocol. |
| raw | Stress precision | 0.0000 | 0.0000 | 0.0000 | NA | No measurable difference. |
| raw | Stress recall | 0.0000 | 0.0000 | 0.0000 | NA | No measurable difference. |
| raw | Stress F1 | 0.0000 | 0.0000 | 0.0000 | NA | No measurable difference. |
| raw | Missed-depeg rate | 1.0000 | 1.0000 | 0.0000 | NA | No measurable difference. |
| raw | False-alarm rate | 0.0085 | 0.0085 | 0.0000 | NA | No measurable difference. |
| raw | Brier score | 0.0469 | 0.0464 | -0.0005 | NA | Numeric-output rerun variability; calibration does not alter probability/max-deviation fields. |
| raw | MaxDev MAE | 56.6167 | 56.5500 | -0.0667 | Low | Numeric-output rerun variability; calibration does not alter probability/max-deviation fields. |
| raw | MaxDev RMSE | 167.1716 | 165.0895 | -2.0821 | NA | Numeric-output rerun variability; calibration does not alter probability/max-deviation fields. |
| raw | Valid JSON rate | 1.0000 | 1.0000 | 0.0000 | NA | No measurable difference. |
| raw | Failure rate | 0.0000 | 0.0000 | 0.0000 | NA | No measurable difference. |
| raw | Cost per case | 0.0029 | 0.0029 | 0.0000 | NA | Rerun/model-output variability under same protocol. |
| calibrated | Accuracy | 0.4417 | 0.4583 | 0.0167 | NA | Same-case rerun variability despite fixed prompt/backend; compare label agreement and transition counts. |
| calibrated | Macro-F1 | 0.3505 | 0.3684 | 0.0179 | NA | Same-case rerun variability despite fixed prompt/backend; compare label agreement and transition counts. |
| calibrated | Balanced accuracy | 0.3935 | 0.4046 | 0.0111 | NA | Same-case rerun variability despite fixed prompt/backend; compare label agreement and transition counts. |
| calibrated | Stable precision | 0.5909 | 0.5926 | 0.0017 | NA | Rerun/model-output variability under same protocol. |
| calibrated | Stable recall | 0.2407 | 0.2963 | 0.0556 | NA | Rerun/model-output variability under same protocol. |
| calibrated | Stable F1 | 0.3421 | 0.3951 | 0.0530 | NA | Rerun/model-output variability under same protocol. |
| calibrated | Watch precision | 0.4000 | 0.4205 | 0.0205 | NA | Rerun/model-output variability under same protocol. |
| calibrated | Watch recall | 0.8444 | 0.8222 | -0.0222 | NA | Rerun/model-output variability under same protocol. |
| calibrated | Watch F1 | 0.5429 | 0.5564 | 0.0135 | NA | Rerun/model-output variability under same protocol. |
| calibrated | Stress precision | 0.6667 | 0.4000 | -0.2667 | NA | Rerun/model-output variability under same protocol. |
| calibrated | Stress recall | 0.0952 | 0.0952 | 0.0000 | NA | No measurable difference. |
| calibrated | Stress F1 | 0.1667 | 0.1538 | -0.0128 | NA | Rerun/model-output variability under same protocol. |
| calibrated | Missed-depeg rate | 1.0000 | 1.0000 | 0.0000 | NA | No measurable difference. |
| calibrated | False-alarm rate | 0.0085 | 0.0085 | 0.0000 | NA | No measurable difference. |
| calibrated | Brier score | 0.0469 | 0.0464 | -0.0005 | NA | Numeric-output rerun variability; calibration does not alter probability/max-deviation fields. |
| calibrated | MaxDev MAE | 56.6167 | 56.5500 | -0.0667 | Low | Numeric-output rerun variability; calibration does not alter probability/max-deviation fields. |
| calibrated | MaxDev RMSE | 167.1716 | 165.0895 | -2.0821 | NA | Numeric-output rerun variability; calibration does not alter probability/max-deviation fields. |
| calibrated | Valid JSON rate | 1.0000 | 1.0000 | 0.0000 | NA | No measurable difference. |
| calibrated | Failure rate | 0.0000 | 0.0000 | 0.0000 | NA | No measurable difference. |
| calibrated | Cost per case | 0.0029 | 0.0029 | 0.0000 | NA | Rerun/model-output variability under same protocol. |

## Medium/High Concern Deltas
No medium/high metric deltas under the diagnostic thresholds.

## Top Disagreements
| variant | case_id | true_label | original_120_pred | from_507_pred | original_p_depeg | from_507_p_depeg | original_maxdev_bps | from_507_maxdev_bps | comment |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| raw | DAI_2023031323 | stable | stress | watch | 0.8500 | 0.2000 | 1082.00 | 100.0000 | prediction label changed |
| raw | USDC_2023031323 | stable | watch | stress | 0.3000 | 0.8500 | 50.0000 | 978.0000 | prediction label changed |
| raw | USDT_2023040323 | stable | stable | watch | 0.0500 | 0.1500 | 10.0000 | 50.0000 | prediction label changed |
| raw | USDT_2023042423 | stable | stable | watch | 0.0500 | 0.1500 | 10.0000 | 50.0000 | prediction label changed |
| raw | USDC_2023021323 | stable | watch | stable | 0.1000 | 0.0500 | 50.0000 | 12.0000 | prediction label changed |
| raw | DAI_2023021323 | stable | watch | stable | 0.1500 | 0.0500 | 50.0000 | 14.0000 | prediction label changed |
| raw | DAI_2025100623 | stress | stable | watch | 0.0500 | 0.1500 | 15.0000 | 50.0000 | prediction label changed |
| raw | USDC_2023030623 | stress | watch | stable | 0.2000 | 0.0500 | 50.0000 | 20.0000 | prediction label changed |
| raw | USDT_2023052223 | stable | watch | stable | 0.1500 | 0.0500 | 50.0000 | 20.0000 | prediction label changed |
| raw | USDT_2023060523 | stable | watch | stable | 0.1500 | 0.0500 | 50.0000 | 20.0000 | prediction label changed |
| raw | DAI_2023030623 | stress | watch | stable | 0.1000 | 0.0500 | 40.0000 | 20.0000 | prediction label changed |
| raw | USDT_2023041023 | stable | stable | watch | 0.0500 | 0.1500 | 10.0000 | 25.0000 | prediction label changed |
| raw | USDC_2023022723 | stable | watch | stable | 0.1500 | 0.0500 | 25.0000 | 12.0000 | prediction label changed |
| raw | USDC_2023013023 | stable | watch | stable | 0.1000 | 0.0500 | 30.0000 | 20.0000 | prediction label changed |
| raw | DAI_2023062623 | watch | watch | stable | 0.1000 | 0.0500 | 30.0000 | 20.0000 | prediction label changed |
| calibrated | USDC_2023031323 | stable | watch | stress | 0.3000 | 0.8500 | 50.0000 | 978.0000 | prediction label changed |
| calibrated | DAI_2023031323 | stable | stress | stress | 0.8500 | 0.2000 | 1082.00 | 100.0000 | largest numeric output drift without label change |
| calibrated | DAI_2026040623 | watch | watch | stress | 0.1500 | 0.1500 | 50.0000 | 117.0000 | prediction label changed |
| calibrated | USDT_2023040323 | stable | stable | watch | 0.0500 | 0.1500 | 10.0000 | 50.0000 | prediction label changed |
| calibrated | USDT_2023042423 | stable | stable | watch | 0.0500 | 0.1500 | 10.0000 | 50.0000 | prediction label changed |

## 507 Baseline Comparison Context
| system | cases | taskA_accuracy | taskA_macro_f1 | taskA_balanced_accuracy | taskA_recall_stable | taskA_recall_watch | taskA_recall_stress | missed_depeg_rate | binary_brier_score | deviation_mae_bps |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| always_stable | 507 | 0.8698 | 0.3101 | 0.3333 | 1.0000 | 0.0000 | 0.0000 | 1.0000 | 0.0059 | 20.1696 |
| historical_persistence | 507 | 0.6726 | 0.3867 | 0.4500 | 0.7279 | 0.2889 | 0.3333 | 0.6667 | 0.1116 | 52.6647 |
| threshold_rule | 507 | 0.6450 | 0.3763 | 0.4461 | 0.6939 | 0.3111 | 0.3333 | 1.0000 | 0.0926 | 52.6885 |
| simple_ml_softmax_logistic | 507 | 0.6410 | 0.4019 | 0.4930 | 0.6757 | 0.4222 | 0.3810 | 1.0000 | 0.0673 | 17.0667 |
| nanobot_qwen_507_raw | 507 | 0.3550 | 0.2232 | 0.3888 | 0.3220 | 0.8444 | 0.0000 | 1.0000 | 0.0226 | 30.2416 |
| nanobot_qwen_507_calibrated | 507 | 0.3945 | 0.2874 | 0.4275 | 0.3651 | 0.8222 | 0.0952 | 1.0000 | 0.0226 | 30.2416 |

## Interpretation
- Protocol alignment is strong: the overlapping case IDs, labels, prompt packet content, backend model, temperature, calibration rule, and evaluator definitions are consistent.
- The 507 result should not replace the frozen 120-case six-agent validation. It is best described as a 507-case natural-distribution scaling check for baselines plus Nanobot.
- The 507 pool is stable-dominant, so always-stable accuracy is high but not trustworthy for rare-risk monitoring. Macro-F1, balanced accuracy, stress recall, and missed-depeg behavior are more informative.
- Nanobot remains watch-heavy and stress-conservative. This supports the trustworthiness interpretation: current agentic systems can produce valid structured outputs at scale, but rare severe-risk detection remains unreliable.
- The same-case rerun differences are a paper-framing issue and possible model variability issue, not a protocol-breaking issue, because prompts, labels, backend, calibration, and evaluator align.

## Recommendation
Proceed to other agents one at a time only if needed, starting with native/framework agents such as LangGraph, Hermes AI, and EvoAgentX. Repeat this same alignment audit after each 507 run. OpenClaw and NanoClaw should remain paused until a native-execution feasibility audit is complete.

## Files Created
- `results/stableeval_507_natural/metrics/nanobot_120_vs_507_alignment_metrics.csv`
- `results/stableeval_507_natural/metrics/nanobot_120_vs_507_case_agreement.csv`
- `results/stableeval_507_natural/metrics/nanobot_120_vs_507_metric_deltas.csv`
- `results/stableeval_507_natural/metrics/nanobot_120_vs_507_top_disagreements.csv`
- `results/stableeval_507_natural/metrics/nanobot_120_vs_507_protocol_consistency.csv`
- `results/stableeval_507_natural/metrics/nanobot_120_vs_507_artifact_inventory.csv`
- `results/stableeval_507_natural/reports/NANOBOT_120_VS_507_ALIGNMENT_AUDIT.md`