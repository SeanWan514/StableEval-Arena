# Verifier Ablation Report

The verifier/risk-auditor receives the same lookback packet and the first prediction. It may revise labels or probabilities only from lookback-window evidence.

## Base vs Verifier Delta

| comparison | system | system_type | macro_f1_delta | balanced_accuracy_delta | stress_recall_delta | missed_depeg_delta | false_alarm_delta | brier_delta | cost_delta_usd |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| evaluation_base_raw -> evaluation_verifier_raw | langgraph | agent | -0.02869 | -0.02734 | 0.04762 | 0 | 0.008547 | 0.008157 | 0.6282 |
| evaluation_base_raw -> evaluation_verifier_raw | nanoclaw | agent | -0.01452 | -0.02875 | 0.09524 | 0 | 0 | 0.004146 | 0.6301 |
| evaluation_base_raw -> evaluation_verifier_raw | hermes_ai | agent | -0.02065 | -0.01499 | 0.04762 | 0 | 0 | 0.003729 | 0.6338 |
| evaluation_base_raw -> evaluation_verifier_raw | openclaw | agent | -0.04036 | -0.03827 | 0 | 0 | 0 | 0.004583 | 0.6284 |
| evaluation_base_raw -> evaluation_verifier_raw | nanobot | agent | -0.01276 | -0.007584 | 0.04762 | 0 | 0.008547 | 0.005416 | 0.633 |
| evaluation_base_raw -> evaluation_verifier_raw | evoagentx | agent | 0.02528 | 0.01199 | 0.09524 | 0 | 0 | 0.003312 | 0.6354 |
| evaluation_base_raw -> evaluation_verifier_raw | historical_persistence | baseline | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| evaluation_base_raw -> evaluation_verifier_raw | threshold_rule | baseline | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| evaluation_base_raw -> evaluation_verifier_raw | always_stable | baseline | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| evaluation_base_raw -> evaluation_verifier_raw | simple_ml_softmax_logistic | baseline | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| evaluation_base_calibrated -> evaluation_verifier_calibrated | nanobot | agent | -0.001378 | -0.005115 | 0.04762 | 0 | 0.008547 | 0.005416 | 0.633 |
| evaluation_base_calibrated -> evaluation_verifier_calibrated | langgraph | agent | -0.02514 | -0.03968 | 0.04762 | 0 | 0.008547 | 0.008157 | 0.6282 |
| evaluation_base_calibrated -> evaluation_verifier_calibrated | nanoclaw | agent | -0.01267 | -0.0261 | 0.04762 | 0 | 0 | 0.004146 | 0.6301 |
| evaluation_base_calibrated -> evaluation_verifier_calibrated | hermes_ai | agent | 0.02632 | 0.01076 | 0.09524 | 0 | 0 | 0.003729 | 0.6338 |
| evaluation_base_calibrated -> evaluation_verifier_calibrated | openclaw | agent | -0.04017 | -0.04198 | 0 | 0 | 0 | 0.004583 | 0.6284 |
| evaluation_base_calibrated -> evaluation_verifier_calibrated | evoagentx | agent | -0.005431 | -0.01993 | 0.04762 | 0 | 0 | 0.003312 | 0.6354 |
| evaluation_base_calibrated -> evaluation_verifier_calibrated | historical_persistence | baseline | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| evaluation_base_calibrated -> evaluation_verifier_calibrated | threshold_rule | baseline | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| evaluation_base_calibrated -> evaluation_verifier_calibrated | always_stable | baseline | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| evaluation_base_calibrated -> evaluation_verifier_calibrated | simple_ml_softmax_logistic | baseline | 0 | 0 | 0 | 0 | 0 | 0 | 0 |