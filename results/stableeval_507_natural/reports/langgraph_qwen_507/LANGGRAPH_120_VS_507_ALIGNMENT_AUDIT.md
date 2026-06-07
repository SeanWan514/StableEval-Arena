# LangGraph 120 vs 507 Alignment Audit

## Verdict

PASS: LangGraph is methodologically aligned between the frozen 120-case validation and the 507-case natural-distribution scaling run. The comparison requires caveated interpretation where same-case rerun predictions differ, but no protocol-breaking inconsistency was found.

## Protocol Consistency

- Cases: all 120 validation case IDs are present in the 507 pool.
- Backend: successful records show `openrouter/qwen/qwen-2.5-72b-instruct`, temperature 0.
- Prompt/output/calibration: same prompt contract and frozen calibration rule.
- Evaluator: same metric formulas; direct evaluator invocation failed on the internal ML baseline branch, so this audit computes the formulas directly.

## Metric Alignment

| setting | cases | taskA_accuracy | taskA_macro_f1 | taskA_balanced_accuracy | taskA_recall_stable | taskA_recall_watch | taskA_recall_stress | missed_depeg_rate | binary_brier_score | deviation_mae_bps | total_estimated_cost_usd |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| original_120_raw | 120 | 0.4333 | 0.3009 | 0.3679 | 0.2593 | 0.8444 | 0.0000 | 1.0000 | 0.0463 | 58.6833 | 1.2122 |
| from_507_on_120_raw | 120 | 0.4833 | 0.3497 | 0.4049 | 0.3704 | 0.8444 | 0.0000 | 1.0000 | 0.0482 | 64.2750 | 1.1941 |
| full_507_raw | 507 | 0.4576 | 0.2738 | 0.4281 | 0.4399 | 0.8444 | 0.0000 | 1.0000 | 0.0208 | 31.0631 | 4.9802 |
| original_120_calibrated | 120 | 0.4417 | 0.3372 | 0.3813 | 0.2963 | 0.8000 | 0.0476 | 1.0000 | 0.0463 | 58.6833 | 1.2122 |
| from_507_on_120_calibrated | 120 | 0.5000 | 0.3881 | 0.4257 | 0.4074 | 0.8222 | 0.0476 | 1.0000 | 0.0482 | 64.2750 | 1.1941 |
| full_507_calibrated | 507 | 0.4675 | 0.3044 | 0.4404 | 0.4512 | 0.8222 | 0.0476 | 1.0000 | 0.0208 | 31.0631 | 4.9802 |

## Case-Level Agreement

- Raw label agreement: 0.9083
- Calibrated label agreement: 0.9083

See `langgraph_120_vs_507_case_agreement.csv`, `langgraph_120_vs_507_prediction_change_matrix.csv`, and `langgraph_120_vs_507_top_disagreements.csv` for case-level details.

## Misalignment Risk

Metric deltas are saved in `langgraph_120_vs_507_metric_deltas.csv`. The audit found 0 medium/high delta rows under diagnostic thresholds.

## Paper Guidance

Use LangGraph 507 as a natural-distribution scaling check for a second native/framework-level agent. Do not claim all six agents have been scaled. Emphasize operational reliability and the continued need for trustworthiness-focused evaluation under class imbalance and rare stress events.
