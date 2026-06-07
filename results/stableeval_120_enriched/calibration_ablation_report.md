# Calibration Ablation Report

The calibrated-label variant uses a frozen rule defined before this validation evaluation. It changes only the mapped class label from the model's own probability and predicted maximum deviation; it does not modify raw outputs or labels.

## Raw vs Calibrated Delta

| comparison | system | system_type | macro_f1_delta | balanced_accuracy_delta | stress_recall_delta | missed_depeg_delta | false_alarm_delta | brier_delta |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| evaluation_base_raw -> evaluation_base_calibrated | langgraph | agent | 0.03636 | 0.0134 | 0.04762 | 0 | 0 | 0 |
| evaluation_base_raw -> evaluation_base_calibrated | nanoclaw | agent | 0.04199 | 0.02081 | 0.04762 | 0 | 0 | 0 |
| evaluation_base_raw -> evaluation_base_calibrated | hermes_ai | agent | 0.03986 | 0.003527 | 0.04762 | 0 | 0 | 0 |
| evaluation_base_raw -> evaluation_base_calibrated | openclaw | agent | 0.03655 | 0.01076 | 0.09524 | 0 | 0 | 0 |
| evaluation_base_raw -> evaluation_base_calibrated | nanobot | agent | 0.08451 | 0.05026 | 0.09524 | 0 | 0 | 0 |
| evaluation_base_raw -> evaluation_base_calibrated | evoagentx | agent | 0.03495 | 0.01464 | 0.04762 | 0 | 0 | 0 |
| evaluation_base_raw -> evaluation_base_calibrated | historical_persistence | baseline | 0 | 0 | 0 | 0 | 0 | 0 |
| evaluation_base_raw -> evaluation_base_calibrated | threshold_rule | baseline | 0 | 0 | 0 | 0 | 0 | 0 |
| evaluation_base_raw -> evaluation_base_calibrated | always_stable | baseline | 0 | 0 | 0 | 0 | 0 | 0 |
| evaluation_base_raw -> evaluation_base_calibrated | simple_ml_softmax_logistic | baseline | 0 | 0 | 0 | 0 | 0 | 0 |
| evaluation_verifier_raw -> evaluation_verifier_calibrated | langgraph | agent | 0.03992 | 0.001058 | 0.04762 | 0 | 0 | 0 |
| evaluation_verifier_raw -> evaluation_verifier_calibrated | nanoclaw | agent | 0.04385 | 0.02346 | 0 | 0 | 0 | 0 |
| evaluation_verifier_raw -> evaluation_verifier_calibrated | evoagentx | agent | 0.004241 | -0.01728 | 0 | 0 | 0 | 0 |
| evaluation_verifier_raw -> evaluation_verifier_calibrated | hermes_ai | agent | 0.08683 | 0.02928 | 0.09524 | 0 | 0 | 0 |
| evaluation_verifier_raw -> evaluation_verifier_calibrated | nanobot | agent | 0.09589 | 0.05273 | 0.09524 | 0 | 0 | 0 |
| evaluation_verifier_raw -> evaluation_verifier_calibrated | openclaw | agent | 0.03674 | 0.007055 | 0.09524 | 0 | 0 | 0 |
| evaluation_verifier_raw -> evaluation_verifier_calibrated | historical_persistence | baseline | 0 | 0 | 0 | 0 | 0 | 0 |
| evaluation_verifier_raw -> evaluation_verifier_calibrated | threshold_rule | baseline | 0 | 0 | 0 | 0 | 0 | 0 |
| evaluation_verifier_raw -> evaluation_verifier_calibrated | always_stable | baseline | 0 | 0 | 0 | 0 | 0 | 0 |
| evaluation_verifier_raw -> evaluation_verifier_calibrated | simple_ml_softmax_logistic | baseline | 0 | 0 | 0 | 0 | 0 | 0 |