# OpenClaw adapter Metric Consistency and Leaderboard Update

## Status

PASS: OpenClaw adapter was evaluated on the same 507 case IDs and labels as the existing baselines, Nanobot, LangGraph, Hermes AI, and EvoAgentX. Raw and calibrated outputs are separated, calibration uses `risk_sensitive_v1_posthoc_frozen`, and execution-mode grouping marks OpenClaw as a StableEval adapter extension rather than native CMDOP execution.

The known simple-ML indexing caveat from earlier 507 evaluation does not affect OpenClaw adapter agent scoring here because these metrics are recomputed directly from saved OpenClaw adapter predictions and the 507 labels using the same metric formulas.

## New Leaderboard

- `results/stableeval_507_natural/tables/scaling_507_progress_leaderboard_v5_verified_with_openclaw_adapter.csv`

## OpenClaw adapter Result Files

- `results/stableeval_507_natural/metrics/openclaw_adapter_qwen_507/openclaw_adapter_507_prediction_quality.csv`
- `results/stableeval_507_natural/tables/openclaw_adapter_qwen_507/openclaw_adapter_507_results.csv`

## Cross-Agent Diagnostics

- `results/stableeval_507_natural/metrics/openclaw_adapter_qwen_507/agents_pairwise_agreement_with_openclaw_adapter.csv`
- `results/stableeval_507_natural/metrics/openclaw_adapter_qwen_507/agents_stress_case_audit_with_openclaw_adapter.csv`
- `results/stableeval_507_natural/metrics/openclaw_adapter_qwen_507/agents_top_cross_agent_disagreements_with_openclaw_adapter.csv`
