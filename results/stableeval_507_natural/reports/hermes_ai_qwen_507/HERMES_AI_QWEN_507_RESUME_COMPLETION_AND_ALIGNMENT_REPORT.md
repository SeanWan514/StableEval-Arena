# Hermes AI Qwen 507 Resume Completion and Alignment Report

## Executive Summary

PASS: Hermes AI completed 507/507 cases safely. No additional API call was needed during the final resume check because the existing resume-safe runner had already completed the remaining cases and saved them.

## Resume Summary

- Dry-run records: 5
- Continuation records: 502
- Final merged records: 507
- Missing case IDs: 0
- Duplicate case IDs: 0
- Corrupt JSONL lines: 0
- Failed cases: 0
- Valid JSON rate: 1.0000

## Protocol Identity

The only intended experimental difference from LangGraph remains: agent = Hermes AI. Backend, prompt packets, output schema, calibration, and evaluator metric definitions are unchanged.

## Main Calibrated Metrics

- Accuracy: 0.4083
- Macro-F1: 0.3011
- Balanced accuracy: 0.4328
- Stable recall: 0.3810
- Watch recall: 0.8222
- Stress recall: 0.0952
- Missed-depeg rate: 1.0000
- Brier score: 0.0193
- MaxDev MAE: 34.3748

## Cost and Runtime

- Total estimated cost: $1.473841
- Cost per case: $0.002907
- Total tokens: 4079805
- Mean latency: 25.5968 seconds

## Alignment Verdict

PASS: Hermes AI is comparable to the frozen 120-case Hermes result under the same protocol. The full 507 result should be presented as a natural-distribution scaling check, not a replacement for the stress-enriched 120-case six-agent validation.

## Paper-Ready Interpretation

Hermes AI completed the 507-case natural-distribution scaling check with 100% valid structured outputs under the same Qwen/OpenRouter protocol. Its results should be interpreted as operationally successful but scientifically cautious: natural-distribution accuracy is influenced by stable-case dominance, while rare severe-risk detection remains the more important trustworthiness signal.

## Exact Key Files

- Complete raw: `results/stableeval_507_natural/raw_outputs/hermes_ai_qwen_507_complete/hermes_ai_predictions_507_complete.jsonl`
- Calibrated raw: `results/stableeval_507_natural/raw_outputs/hermes_ai_qwen_507_complete_calibrated/hermes_ai_predictions.jsonl`
- Hermes metrics: `results/stableeval_507_natural/metrics/hermes_ai_qwen_507/hermes_ai_507_prediction_quality.csv`
- Hermes table: `results/stableeval_507_natural/tables/hermes_ai_qwen_507/hermes_ai_507_results.csv`
- v3 leaderboard: `results/stableeval_507_natural/tables/scaling_507_progress_leaderboard_v3_verified_with_hermes.csv`
- Alignment audit: `results/stableeval_507_natural/reports/hermes_ai_qwen_507/HERMES_AI_120_VS_507_ALIGNMENT_AUDIT.md`
