# LangGraph Qwen 507 Completion and Alignment Report

## Executive Summary

PASS: LangGraph completed 507/507 natural-distribution scaling cases with 100% valid JSON and no final failed cases. The only intended experimental change from the completed Nanobot 507 run was `agent = LangGraph`; cases, prompt packets, Qwen/OpenRouter backend, temperature, output schema, calibration rule, and metric definitions were kept fixed.

## 120 Freeze Safety

Freeze integrity verdict after the LangGraph run: **PASS**. Checked frozen files: 325; missing: 0; changed: 0.

## Run Completion

- Dry-run records: 5
- Continuation records: 502
- Final merged records: 507
- Missing cases: 0
- Duplicate cases: 0
- Corrupt JSONL lines: 0
- Valid JSON rate: 1.0000
- Retry-log failed attempts: 9; all resolved without final failed cases.
- Successful records show `openrouter/qwen/qwen-2.5-72b-instruct`, temperature 0. Retry logs include transient OpenRouter upstream provider-route errors, but no non-Qwen model was used.

## LangGraph 507 Results

| system | cases | taskA_accuracy | taskA_macro_f1 | taskA_balanced_accuracy | taskA_recall_stable | taskA_recall_watch | taskA_recall_stress | missed_depeg_rate | binary_brier_score | deviation_mae_bps | total_estimated_cost_usd |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| langgraph_qwen_507_raw | 507 | 0.4576 | 0.2738 | 0.4281 | 0.4399 | 0.8444 | 0.0000 | 1.0000 | 0.0208 | 31.0631 | 4.9802 |
| langgraph_qwen_507_calibrated | 507 | 0.4675 | 0.3044 | 0.4404 | 0.4512 | 0.8222 | 0.0476 | 1.0000 | 0.0208 | 31.0631 | 4.9802 |

## Baseline and Nanobot Comparison

| system | cases | taskA_accuracy | taskA_macro_f1 | taskA_balanced_accuracy | taskA_recall_stable | taskA_recall_watch | taskA_recall_stress | missed_depeg_rate | binary_brier_score | deviation_mae_bps | total_estimated_cost_usd |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| always_stable | 507 | 0.8698 | 0.3101 | 0.3333 | 1.0000 | 0.0000 | 0.0000 | 1.0000 | 0.0059 | 20.1696 | 0.0000 |
| historical_persistence | 507 | 0.6726 | 0.3867 | 0.4500 | 0.7279 | 0.2889 | 0.3333 | 0.6667 | 0.1116 | 52.6647 | 0.0000 |
| threshold_rule | 507 | 0.6450 | 0.3763 | 0.4461 | 0.6939 | 0.3111 | 0.3333 | 1.0000 | 0.0926 | 52.6885 | 0.0000 |
| simple_ml_softmax_logistic | 507 | 0.6410 | 0.4019 | 0.4930 | 0.6757 | 0.4222 | 0.3810 | 1.0000 | 0.0673 | 17.0667 | 0.0000 |
| nanobot_qwen_507_raw | 507 | 0.3550 | 0.2232 | 0.3888 | 0.3220 | 0.8444 | 0.0000 | 1.0000 | 0.0226 | 30.2416 | 1.4710 |
| nanobot_qwen_507_calibrated | 507 | 0.3945 | 0.2874 | 0.4275 | 0.3651 | 0.8222 | 0.0952 | 1.0000 | 0.0226 | 30.2416 | 1.4710 |
| nanobot_qwen_507_raw | 507 | 0.3550 | 0.2232 | 0.3888 | 0.3220 | 0.8444 | 0.0000 | 1.0000 | 0.0226 | 30.2416 | 1.4710 |
| nanobot_qwen_507_calibrated | 507 | 0.3945 | 0.2874 | 0.4275 | 0.3651 | 0.8222 | 0.0952 | 1.0000 | 0.0226 | 30.2416 | 1.4710 |
| langgraph_qwen_507_raw | 507 | 0.4576 | 0.2738 | 0.4281 | 0.4399 | 0.8444 | 0.0000 | 1.0000 | 0.0208 | 31.0631 | 4.9802 |
| langgraph_qwen_507_calibrated | 507 | 0.4675 | 0.3044 | 0.4404 | 0.4512 | 0.8222 | 0.0476 | 1.0000 | 0.0208 | 31.0631 | 4.9802 |

## 120-vs-507 Alignment

Alignment verdict: **PASS**.

| setting | cases | taskA_accuracy | taskA_macro_f1 | taskA_balanced_accuracy | taskA_recall_stable | taskA_recall_watch | taskA_recall_stress | missed_depeg_rate | binary_brier_score | deviation_mae_bps | total_estimated_cost_usd |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| original_120_raw | 120 | 0.4333 | 0.3009 | 0.3679 | 0.2593 | 0.8444 | 0.0000 | 1.0000 | 0.0463 | 58.6833 | 1.2122 |
| from_507_on_120_raw | 120 | 0.4833 | 0.3497 | 0.4049 | 0.3704 | 0.8444 | 0.0000 | 1.0000 | 0.0482 | 64.2750 | 1.1941 |
| full_507_raw | 507 | 0.4576 | 0.2738 | 0.4281 | 0.4399 | 0.8444 | 0.0000 | 1.0000 | 0.0208 | 31.0631 | 4.9802 |
| original_120_calibrated | 120 | 0.4417 | 0.3372 | 0.3813 | 0.2963 | 0.8000 | 0.0476 | 1.0000 | 0.0463 | 58.6833 | 1.2122 |
| from_507_on_120_calibrated | 120 | 0.5000 | 0.3881 | 0.4257 | 0.4074 | 0.8222 | 0.0476 | 1.0000 | 0.0482 | 64.2750 | 1.1941 |
| full_507_calibrated | 507 | 0.4675 | 0.3044 | 0.4404 | 0.4512 | 0.8222 | 0.0476 | 1.0000 | 0.0208 | 31.0631 | 4.9802 |

Case-level label agreement: raw=0.9083, calibrated=0.9083.

## Interpretation

LangGraph is operationally reliable on the full 507 natural-distribution scaling check. Its prediction-quality results should be interpreted as a robustness and trustworthiness finding, not as proof that agentic systems solve stablecoin risk prediction. The result is directly comparable to Nanobot because the protocol was held fixed except for the agent system.

The 507 setting is stable-dominant, so ordinary accuracy can be misleading. Macro-F1, balanced accuracy, stress recall, missed-depeg rate, Brier score, valid JSON, latency, and cost are the more reviewer-relevant signals.

## Caveats

The frozen evaluator script failed when invoked directly for this 507 agent-only run because its internal simple-ML baseline branch received an empty training split under this label/prompt invocation. I did not modify the evaluator. Metrics here are computed with the same metric formulas from `scripts/evaluate/evaluate_predictions.py` and are saved separately under LangGraph-specific paths.

## Recommended Next Step

Proceed to Hermes AI one agent at a time using the same protocol, then repeat the same completion and 120-vs-507 alignment audit. Keep OpenClaw/NanoClaw for a separate native-feasibility audit.
