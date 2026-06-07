# Hermes AI Metric Consistency and Leaderboard Update

## Status

PASS: Hermes AI was evaluated on the same 507 case IDs and labels as the existing baselines, Nanobot, and LangGraph. Raw and calibrated outputs are separated, and calibration uses `risk_sensitive_v1_posthoc_frozen`.

The known simple-ML indexing caveat from earlier 507 evaluation does not affect Hermes agent scoring here because these metrics are recomputed directly from saved Hermes predictions and the 507 labels using the same metric formulas.

## New Leaderboard

- `results/stableeval_507_natural/tables/scaling_507_progress_leaderboard_v3_verified_with_hermes.csv`

## Hermes Result Files

- `results/stableeval_507_natural/metrics/hermes_ai_qwen_507/hermes_ai_507_prediction_quality.csv`
- `results/stableeval_507_natural/tables/hermes_ai_qwen_507/hermes_ai_507_results.csv`
