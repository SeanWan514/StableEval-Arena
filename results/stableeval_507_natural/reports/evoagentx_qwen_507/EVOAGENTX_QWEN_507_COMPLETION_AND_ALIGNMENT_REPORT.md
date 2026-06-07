# EvoAgentX Qwen 507 Resume Completion and Alignment Report

## Executive Summary

PASS: EvoAgentX completed 507/507 cases safely using the resume-safe, timeout-bounded runner. The finalization step used saved outputs only and made no API calls.

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

The only intended experimental difference from Hermes AI remains: agent = EvoAgentX. Backend, prompt packets, output schema, calibration, and evaluator metric definitions are unchanged.

## Main Calibrated Metrics

- Accuracy: 0.3807
- Macro-F1: 0.2626
- Balanced accuracy: 0.4138
- Stable recall: 0.3492
- Watch recall: 0.8444
- Stress recall: 0.0476
- Missed-depeg rate: 1.0000
- Brier score: 0.0224
- MaxDev MAE: 32.6805

## Cost and Runtime

- Total estimated cost: $2.551741
- Cost per case: $0.005033
- Total tokens: 7063441
- Mean latency: 27.7197 seconds

## Alignment Verdict

PASS: EvoAgentX is comparable to the frozen 120-case EvoAgentX result under the same protocol. The full 507 result should be presented as a natural-distribution scaling check, not a replacement for the stress-enriched 120-case six-agent validation.

## Cross-Agent Stress Diagnostic

- True stress cases in 507: 21
- Stress cases missed by all four completed native/framework-level agents: 19
- Stress cases caught by at least one completed native/framework-level agent: 2
- Unique EvoAgentX stress detections: 0

## Paper-Ready Interpretation

EvoAgentX completed the 507-case natural-distribution scaling check with 100% valid structured outputs under the same Qwen/OpenRouter protocol. Its results should be interpreted as operationally successful but scientifically cautious: natural-distribution accuracy is influenced by stable-case dominance, while rare severe-risk detection remains the more important trustworthiness signal.

## Exact Key Files

- Complete raw: `results/stableeval_507_natural/raw_outputs/evoagentx_qwen_507_complete/evoagentx_predictions_507_complete.jsonl`
- Calibrated raw: `results/stableeval_507_natural/raw_outputs/evoagentx_qwen_507_complete_calibrated/evoagentx_predictions.jsonl`
- EvoAgentX metrics: `results/stableeval_507_natural/metrics/evoagentx_qwen_507/evoagentx_507_prediction_quality.csv`
- EvoAgentX table: `results/stableeval_507_natural/tables/evoagentx_qwen_507/evoagentx_507_results.csv`
- v4 leaderboard: `results/stableeval_507_natural/tables/scaling_507_progress_leaderboard_v4_verified_with_evoagentx.csv`
- Alignment audit: `results/stableeval_507_natural/reports/evoagentx_qwen_507/EVOAGENTX_120_VS_507_ALIGNMENT_AUDIT.md`
