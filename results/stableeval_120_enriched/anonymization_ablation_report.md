# Parametric Memory Leakage Note

This ablation compares predictions on the same numerical evidence with real stablecoin names/dates versus anonymized coin aliases and relative time labels.

## Summary

| system | cases | label_change_rate | mean_p_depeg_abs_diff | mean_predicted_bps_abs_diff |
| --- | --- | --- | --- | --- |
| evoagentx | 12 | 0.1667 | 0.01667 | 7.917 |
| hermes_ai | 12 | 0.08333 | 0.02917 | 4.583 |
| langgraph | 12 | 0.3333 | 0.0625 | 8.417 |
| nanobot | 12 | 0.25 | 0.04167 | 8.5 |
| nanoclaw | 12 | 0.25 | 0.05 | 14.17 |
| openclaw | 12 | 0.08333 | 0.02917 | 8.333 |

Prediction changes are not large by this simple label-change diagnostic; parametric-memory leakage is not ruled out, but it does not appear severe in this subset.

For the paper, report this as an audit rather than proof: anonymization reduces event-memory cues, but cannot fully eliminate all pretraining knowledge risks.