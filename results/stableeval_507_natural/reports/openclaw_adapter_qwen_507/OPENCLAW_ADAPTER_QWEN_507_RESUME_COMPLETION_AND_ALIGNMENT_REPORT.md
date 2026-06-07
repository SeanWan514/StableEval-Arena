# OpenClaw adapter Qwen 507 Resume Completion and Alignment Report

## Executive Summary

PASS: OpenClaw adapter completed 507/507 cases safely using the resume-safe, timeout-bounded runner. The finalization step used saved outputs only and made no API calls.

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

The only intended experimental difference from the previous completed 507 runs remains: agent = OpenClaw under StableEval adapter execution. Backend, prompt packets, output schema, calibration, and evaluator metric definitions are unchanged. Native CMDOP execution was not verified and is not claimed.

## Main Calibrated Metrics

- Accuracy: 0.3531
- Macro-F1: 0.2485
- Balanced accuracy: 0.4032
- Stable recall: 0.3175
- Watch recall: 0.8444
- Stress recall: 0.0476
- Missed-depeg rate: 1.0000
- Brier score: 0.0229
- MaxDev MAE: 34.6548

## Cost and Runtime

- Total estimated cost: $2.545288
- Cost per case: $0.005020
- Total tokens: 7047309
- Mean latency: 23.5969 seconds

## Alignment Verdict

PARTIAL PASS: OpenClaw adapter is comparable to the frozen 120-case OpenClaw adapter result under the same protocol. The full 507 result should be presented as a natural-distribution scaling check, not a replacement for the stress-enriched 120-case six-agent validation.

## Cross-Agent Stress Diagnostic

- True stress cases in 507: 21
- Stress cases missed by all completed agents including OpenClaw adapter: 19
- Stress cases caught by at least one completed agent including OpenClaw adapter: 2
- Unique OpenClaw adapter stress detections: 0

## Paper-Ready Interpretation

OpenClaw adapter completed the 507-case natural-distribution scaling check with 100% valid structured outputs under the same Qwen/OpenRouter protocol. Its results should be interpreted as operationally successful but scientifically cautious: natural-distribution accuracy is influenced by stable-case dominance, while rare severe-risk detection remains the more important trustworthiness signal.

## Exact Key Files

- Complete raw: `results/stableeval_507_natural/raw_outputs/openclaw_adapter_qwen_507_complete/openclaw_adapter_predictions_507_complete.jsonl`
- Calibrated raw: `results/stableeval_507_natural/raw_outputs/openclaw_adapter_qwen_507_complete_calibrated/openclaw_adapter_predictions.jsonl`
- OpenClaw adapter metrics: `results/stableeval_507_natural/metrics/openclaw_adapter_qwen_507/openclaw_adapter_507_prediction_quality.csv`
- OpenClaw adapter table: `results/stableeval_507_natural/tables/openclaw_adapter_qwen_507/openclaw_adapter_507_results.csv`
- v5 leaderboard: `results/stableeval_507_natural/tables/scaling_507_progress_leaderboard_v5_verified_with_openclaw_adapter.csv`
- Alignment audit: `results/stableeval_507_natural/reports/openclaw_adapter_qwen_507/OPENCLAW_ADAPTER_120_VS_507_ALIGNMENT_AUDIT.md`
