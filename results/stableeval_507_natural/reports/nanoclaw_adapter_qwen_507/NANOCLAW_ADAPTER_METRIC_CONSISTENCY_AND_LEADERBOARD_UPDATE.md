# NanoClaw adapter Metric Consistency and Leaderboard Update

## Status

PASS: NanoClaw adapter was evaluated on the same 507 case IDs and labels as the existing baselines, Nanobot, LangGraph, Hermes AI, and EvoAgentX. Raw and calibrated outputs are separated, calibration uses `risk_sensitive_v1_posthoc_frozen`, and execution-mode grouping marks NanoClaw as a StableEval adapter extension rather than native CMDOP execution.

The known simple-ML indexing caveat from earlier 507 evaluation does not affect NanoClaw adapter agent scoring here because these metrics are recomputed directly from saved NanoClaw adapter predictions and the 507 labels using the same metric formulas.

## New Leaderboard

- `results/stableeval_507_natural/tables/scaling_507_progress_leaderboard_v6_verified_with_nanoclaw_adapter.csv`

## NanoClaw adapter Result Files

- `results/stableeval_507_natural/metrics/nanoclaw_adapter_qwen_507/nanoclaw_adapter_507_prediction_quality.csv`
- `results/stableeval_507_natural/tables/nanoclaw_adapter_qwen_507/nanoclaw_adapter_507_results.csv`

## Cross-Agent Diagnostics

- `results/stableeval_507_natural/metrics/nanoclaw_adapter_qwen_507/agents_pairwise_agreement_with_nanoclaw_adapter.csv`
- `results/stableeval_507_natural/metrics/nanoclaw_adapter_qwen_507/agents_stress_case_audit_with_nanoclaw_adapter.csv`
- `results/stableeval_507_natural/metrics/nanoclaw_adapter_qwen_507/agents_top_cross_agent_disagreements_with_nanoclaw_adapter.csv`
