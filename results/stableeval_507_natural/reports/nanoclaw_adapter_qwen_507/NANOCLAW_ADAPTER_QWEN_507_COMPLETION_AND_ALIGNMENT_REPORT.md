# NanoClaw adapter Qwen 507 Resume Completion and Alignment Report

## Executive Summary

PASS: NanoClaw adapter completed 507/507 cases safely using the resume-safe, timeout-bounded runner. The finalization step used saved outputs only and made no API calls.

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

The only intended experimental difference from the previous completed 507 runs remains: agent = NanoClaw under StableEval adapter execution. Backend, prompt packets, output schema, calibration, and evaluator metric definitions are unchanged. Native CMDOP execution was not verified and is not claimed.

## Main Calibrated Metrics

- Accuracy: 0.4714
- Macro-F1: 0.3041
- Balanced accuracy: 0.4352
- Stable recall: 0.4580
- Watch recall: 0.8000
- Stress recall: 0.0476
- Missed-depeg rate: 1.0000
- Brier score: 0.0205
- MaxDev MAE: 31.6724

## Cost and Runtime

- Total estimated cost: $2.541224
- Cost per case: $0.005012
- Total tokens: 7037097
- Mean latency: 21.0567 seconds

## Alignment Verdict

PASS: NanoClaw adapter is comparable to the frozen 120-case NanoClaw adapter result under the same protocol. The full 507 result should be presented as a natural-distribution scaling check, not a replacement for the stress-enriched 120-case six-agent validation.

## Cross-Agent Stress Diagnostic

- True stress cases in 507: 21
- Stress cases missed by the four native/framework-level agents: 19
- Stress cases missed by all six evaluated systems including adapter-based -Claw: 19
- Stress cases caught by at least one completed system including NanoClaw adapter: 2
- Unique NanoClaw adapter stress detections: 0

## Paper-Ready Interpretation

NanoClaw adapter completed the 507-case natural-distribution scaling check with 100% valid structured outputs under the same Qwen/OpenRouter protocol. Its results should be interpreted as operationally successful but scientifically cautious: natural-distribution accuracy is influenced by stable-case dominance, while rare severe-risk detection remains the more important trustworthiness signal.

## Exact Key Files

- Complete raw: `results/stableeval_507_natural/raw_outputs/nanoclaw_adapter_qwen_507_complete/nanoclaw_adapter_predictions_507_complete.jsonl`
- Calibrated raw: `results/stableeval_507_natural/raw_outputs/nanoclaw_adapter_qwen_507_complete_calibrated/nanoclaw_adapter_predictions.jsonl`
- NanoClaw adapter metrics: `results/stableeval_507_natural/metrics/nanoclaw_adapter_qwen_507/nanoclaw_adapter_507_prediction_quality.csv`
- NanoClaw adapter table: `results/stableeval_507_natural/tables/nanoclaw_adapter_qwen_507/nanoclaw_adapter_507_results.csv`
- v6 leaderboard: `results/stableeval_507_natural/tables/scaling_507_progress_leaderboard_v6_verified_with_nanoclaw_adapter.csv`
- Alignment audit: `results/stableeval_507_natural/reports/nanoclaw_adapter_qwen_507/NANOCLAW_ADAPTER_120_VS_507_ALIGNMENT_AUDIT.md`
