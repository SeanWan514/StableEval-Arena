# EvoAgentX Metric Consistency and Leaderboard Update

## Status

PASS: EvoAgentX was evaluated on the same 507 case IDs and labels as the existing baselines, Nanobot, LangGraph, and Hermes AI. Raw and calibrated outputs are separated, and calibration uses `risk_sensitive_v1_posthoc_frozen`.

The known simple-ML indexing caveat from earlier 507 evaluation does not affect EvoAgentX agent scoring here because these metrics are recomputed directly from saved EvoAgentX predictions and the 507 labels using the same metric formulas.

## New Leaderboard

- `results/stableeval_507_natural/tables/scaling_507_progress_leaderboard_v4_verified_with_evoagentx.csv`

## EvoAgentX Result Files

- `results/stableeval_507_natural/metrics/evoagentx_qwen_507/evoagentx_507_prediction_quality.csv`
- `results/stableeval_507_natural/tables/evoagentx_qwen_507/evoagentx_507_results.csv`

## Cross-Agent Diagnostics

- `results/stableeval_507_natural/metrics/evoagentx_qwen_507/native_agents_pairwise_agreement_with_evoagentx.csv`
- `results/stableeval_507_natural/metrics/evoagentx_qwen_507/native_agents_stress_case_audit_with_evoagentx.csv`
- `results/stableeval_507_natural/metrics/evoagentx_qwen_507/native_agents_top_cross_agent_disagreements_with_evoagentx.csv`
