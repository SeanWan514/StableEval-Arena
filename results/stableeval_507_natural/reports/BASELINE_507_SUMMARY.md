# 507 Baseline Evaluation Summary

No LLM API calls were used. Outputs are under `results/stableeval_507_natural/`.

| system | cases | taskA_accuracy | taskA_macro_f1 | taskA_balanced_accuracy | taskA_recall_stable | taskA_recall_watch | taskA_recall_stress | missed_depeg_rate | false_alarm_rate | binary_brier_score | deviation_mae_bps | deviation_rmse_bps |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| simple_ml_softmax_logistic | 507 | 0.641 | 0.4019 | 0.493 | 0.6757 | 0.4222 | 0.381 | 1 | 0.07738 | 0.06727 | 17.07 | 72.33 |
| historical_persistence | 507 | 0.6726 | 0.3867 | 0.45 | 0.7279 | 0.2889 | 0.3333 | 0.6667 | 0.1488 | 0.1116 | 52.66 | 154.3 |
| threshold_rule | 507 | 0.645 | 0.3763 | 0.4461 | 0.6939 | 0.3111 | 0.3333 | 1 | 0.09524 | 0.09257 | 52.69 | 154.3 |
| always_stable | 507 | 0.8698 | 0.3101 | 0.3333 | 1 | 0 | 0 | 1 | 0 | 0.005899 | 20.17 | 72.67 |
