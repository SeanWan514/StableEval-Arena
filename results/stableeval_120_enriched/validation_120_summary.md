# Intermediate Validation Summary

Validation cases: 120.

## Label Distribution

| label | cases |
| --- | --- |
| stable | 54 |
| watch | 45 |
| stress | 21 |

## Main Variants

- `evaluation_base_raw`: first-pass agent labels exactly as generated.
- `evaluation_base_calibrated`: first-pass outputs with frozen post-hoc probability/max-deviation label mapping.
- `evaluation_verifier_raw`: second-pass risk-auditor labels exactly as generated.
- `evaluation_verifier_calibrated`: second-pass outputs with the same frozen calibration mapping.

## Baselines only

| system | system_type | cases | taskA_accuracy | taskA_macro_f1 | taskA_balanced_accuracy | taskA_recall_stress | missed_depeg_rate | false_alarm_rate | binary_brier_score | deviation_mae_bps | valid_json_rate | failure_rate | total_estimated_cost_usd |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| historical_persistence | baseline | 120 | 0.2917 | 0.2854 | 0.3 | 0.3333 | 0.6667 | 0.3761 | 0.2761 | 148.9 | 1 | 0 | 0 |
| threshold_rule | baseline | 120 | 0.2833 | 0.2779 | 0.2951 | 0.3333 | 1 | 0.2821 | 0.2444 | 148.9 | 1 | 0 | 0 |
| always_stable | baseline | 120 | 0.45 | 0.2069 | 0.3333 | 0 | 1 | 0 | 0.0246 | 63.91 | 1 | 0 | 0 |
| simple_ml_softmax_logistic | baseline | 120 | 0.45 | 0.2069 | 0.3333 | 0 | 1 | 0 | 0.02438 | 113.5 | 1 | 0 | 0 |

## Base raw

| system | system_type | cases | taskA_accuracy | taskA_macro_f1 | taskA_balanced_accuracy | taskA_recall_stress | missed_depeg_rate | false_alarm_rate | binary_brier_score | deviation_mae_bps | valid_json_rate | failure_rate | total_estimated_cost_usd |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| langgraph | agent | 120 | 0.4333 | 0.3009 | 0.3679 | 0 | 1 | 0.008547 | 0.04633 | 58.68 | 1 | 0 | 1.212 |
| nanoclaw | agent | 120 | 0.425 | 0.2858 | 0.3642 | 0 | 1 | 0.01709 | 0.04983 | 66.36 | 1 | 0 | 0.6272 |
| hermes_ai | agent | 120 | 0.425 | 0.2815 | 0.3654 | 0 | 1 | 0.01709 | 0.04746 | 57.86 | 1 | 0 | 0.3481 |
| openclaw | agent | 120 | 0.4167 | 0.281 | 0.3568 | 0 | 1 | 0.01709 | 0.04825 | 62 | 1 | 0 | 0.6248 |
| nanobot | agent | 120 | 0.4 | 0.266 | 0.3432 | 0 | 1 | 0.008547 | 0.04692 | 56.62 | 1 | 0 | 0.3454 |
| evoagentx | agent | 120 | 0.3833 | 0.237 | 0.3333 | 0 | 1 | 0.01709 | 0.04973 | 66.92 | 1 | 0 | 0.6111 |
| historical_persistence | baseline | 120 | 0.2917 | 0.2854 | 0.3 | 0.3333 | 0.6667 | 0.3761 | 0.2761 | 148.9 | 1 | 0 | 0 |
| threshold_rule | baseline | 120 | 0.2833 | 0.2779 | 0.2951 | 0.3333 | 1 | 0.2821 | 0.2444 | 148.9 | 1 | 0 | 0 |
| always_stable | baseline | 120 | 0.45 | 0.2069 | 0.3333 | 0 | 1 | 0 | 0.0246 | 63.91 | 1 | 0 | 0 |
| simple_ml_softmax_logistic | baseline | 120 | 0.45 | 0.2069 | 0.3333 | 0 | 1 | 0 | 0.02438 | 113.5 | 1 | 0 | 0 |

## Base calibrated

| system | system_type | cases | taskA_accuracy | taskA_macro_f1 | taskA_balanced_accuracy | taskA_recall_stress | missed_depeg_rate | false_alarm_rate | binary_brier_score | deviation_mae_bps | valid_json_rate | failure_rate | total_estimated_cost_usd |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nanobot | agent | 120 | 0.4417 | 0.3505 | 0.3935 | 0.09524 | 1 | 0.008547 | 0.04692 | 56.62 | 1 | 0 | 0.3454 |
| langgraph | agent | 120 | 0.4417 | 0.3372 | 0.3813 | 0.04762 | 1 | 0.008547 | 0.04633 | 58.68 | 1 | 0 | 1.212 |
| nanoclaw | agent | 120 | 0.4417 | 0.3278 | 0.385 | 0.04762 | 1 | 0.01709 | 0.04983 | 66.36 | 1 | 0 | 0.6272 |
| hermes_ai | agent | 120 | 0.425 | 0.3213 | 0.369 | 0.04762 | 1 | 0.01709 | 0.04746 | 57.86 | 1 | 0 | 0.3481 |
| openclaw | agent | 120 | 0.4083 | 0.3176 | 0.3675 | 0.09524 | 1 | 0.01709 | 0.04825 | 62 | 1 | 0 | 0.6248 |
| evoagentx | agent | 120 | 0.3917 | 0.2719 | 0.348 | 0.04762 | 1 | 0.01709 | 0.04973 | 66.92 | 1 | 0 | 0.6111 |
| historical_persistence | baseline | 120 | 0.2917 | 0.2854 | 0.3 | 0.3333 | 0.6667 | 0.3761 | 0.2761 | 148.9 | 1 | 0 | 0 |
| threshold_rule | baseline | 120 | 0.2833 | 0.2779 | 0.2951 | 0.3333 | 1 | 0.2821 | 0.2444 | 148.9 | 1 | 0 | 0 |
| always_stable | baseline | 120 | 0.45 | 0.2069 | 0.3333 | 0 | 1 | 0 | 0.0246 | 63.91 | 1 | 0 | 0 |
| simple_ml_softmax_logistic | baseline | 120 | 0.45 | 0.2069 | 0.3333 | 0 | 1 | 0 | 0.02438 | 113.5 | 1 | 0 | 0 |

## Verifier raw

| system | system_type | cases | taskA_accuracy | taskA_macro_f1 | taskA_balanced_accuracy | taskA_recall_stress | missed_depeg_rate | false_alarm_rate | binary_brier_score | deviation_mae_bps | valid_json_rate | failure_rate | total_estimated_cost_usd |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| langgraph | agent | 120 | 0.3833 | 0.2722 | 0.3406 | 0.04762 | 1 | 0.01709 | 0.05449 | 65.44 | 1 | 0 | 1.84 |
| nanoclaw | agent | 120 | 0.3667 | 0.2712 | 0.3354 | 0.09524 | 1 | 0.01709 | 0.05398 | 71.16 | 1 | 0 | 1.257 |
| evoagentx | agent | 120 | 0.375 | 0.2623 | 0.3453 | 0.09524 | 1 | 0.01709 | 0.05304 | 69.22 | 1 | 0 | 1.246 |
| hermes_ai | agent | 120 | 0.3917 | 0.2608 | 0.3504 | 0.04762 | 1 | 0.01709 | 0.05119 | 60.61 | 1 | 0 | 0.9819 |
| nanobot | agent | 120 | 0.375 | 0.2533 | 0.3356 | 0.04762 | 1 | 0.01709 | 0.05233 | 59.99 | 1 | 0 | 0.9785 |
| openclaw | agent | 120 | 0.3667 | 0.2406 | 0.3185 | 0 | 1 | 0.01709 | 0.05283 | 70.85 | 1 | 0 | 1.253 |
| historical_persistence | baseline | 120 | 0.2917 | 0.2854 | 0.3 | 0.3333 | 0.6667 | 0.3761 | 0.2761 | 148.9 | 1 | 0 | 0 |
| threshold_rule | baseline | 120 | 0.2833 | 0.2779 | 0.2951 | 0.3333 | 1 | 0.2821 | 0.2444 | 148.9 | 1 | 0 | 0 |
| always_stable | baseline | 120 | 0.45 | 0.2069 | 0.3333 | 0 | 1 | 0 | 0.0246 | 63.91 | 1 | 0 | 0 |
| simple_ml_softmax_logistic | baseline | 120 | 0.45 | 0.2069 | 0.3333 | 0 | 1 | 0 | 0.02438 | 113.5 | 1 | 0 | 0 |

## Verifier calibrated

| system | system_type | cases | taskA_accuracy | taskA_macro_f1 | taskA_balanced_accuracy | taskA_recall_stress | missed_depeg_rate | false_alarm_rate | binary_brier_score | deviation_mae_bps | valid_json_rate | failure_rate | total_estimated_cost_usd |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nanobot | agent | 120 | 0.425 | 0.3492 | 0.3884 | 0.1429 | 1 | 0.01709 | 0.05233 | 59.99 | 1 | 0 | 0.9785 |
| hermes_ai | agent | 120 | 0.4167 | 0.3477 | 0.3797 | 0.1429 | 1 | 0.01709 | 0.05119 | 60.61 | 1 | 0 | 0.9819 |
| nanoclaw | agent | 120 | 0.4 | 0.3151 | 0.3589 | 0.09524 | 1 | 0.01709 | 0.05398 | 71.16 | 1 | 0 | 1.257 |
| langgraph | agent | 120 | 0.3833 | 0.3121 | 0.3416 | 0.09524 | 1 | 0.01709 | 0.05449 | 65.44 | 1 | 0 | 1.84 |
| openclaw | agent | 120 | 0.3583 | 0.2774 | 0.3256 | 0.09524 | 1 | 0.01709 | 0.05283 | 70.85 | 1 | 0 | 1.253 |
| evoagentx | agent | 120 | 0.3583 | 0.2665 | 0.328 | 0.09524 | 1 | 0.01709 | 0.05304 | 69.22 | 1 | 0 | 1.246 |
| historical_persistence | baseline | 120 | 0.2917 | 0.2854 | 0.3 | 0.3333 | 0.6667 | 0.3761 | 0.2761 | 148.9 | 1 | 0 | 0 |
| threshold_rule | baseline | 120 | 0.2833 | 0.2779 | 0.2951 | 0.3333 | 1 | 0.2821 | 0.2444 | 148.9 | 1 | 0 | 0 |
| always_stable | baseline | 120 | 0.45 | 0.2069 | 0.3333 | 0 | 1 | 0 | 0.0246 | 63.91 | 1 | 0 | 0 |
| simple_ml_softmax_logistic | baseline | 120 | 0.45 | 0.2069 | 0.3333 | 0 | 1 | 0 | 0.02438 | 113.5 | 1 | 0 | 0 |
