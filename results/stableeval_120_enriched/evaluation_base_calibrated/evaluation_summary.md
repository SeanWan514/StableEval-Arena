# StableEval Arena Paper Pilot Evaluation

Selected model backend: `qwen/qwen-2.5-72b-instruct`

This evaluation covers 120 historical-replay cases. Each case contains only a frozen 30-day lookback window; the hidden next-7-day horizon is used only by the evaluator.

## Main Evaluation Results

| system | system_type | cases | taskA_accuracy | taskA_macro_f1 | taskA_balanced_accuracy | binary_recall | binary_auroc | binary_average_precision | deviation_mae_bps | valid_json_rate | failure_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nanobot | agent | 120 | 0.4417 | 0.3505 | 0.3935 | 0 | 0.5142 | 0.03097 | 56.62 | 1 | 0 |
| langgraph | agent | 120 | 0.4417 | 0.3372 | 0.3813 | 0 | 0.4744 | 0.03279 | 58.68 | 1 | 0 |
| nanoclaw | agent | 120 | 0.4417 | 0.3278 | 0.385 | 0 | 0.4316 | 0.02418 | 66.36 | 1 | 0 |
| hermes_ai | agent | 120 | 0.425 | 0.3213 | 0.369 | 0 | 0.2863 | 0.02247 | 57.86 | 1 | 0 |
| openclaw | agent | 120 | 0.4083 | 0.3176 | 0.3675 | 0 | 0.49 | 0.0286 | 62 | 1 | 0 |
| evoagentx | agent | 120 | 0.3917 | 0.2719 | 0.348 | 0 | 0.4245 | 0.02283 | 66.92 | 1 | 0 |
| historical_persistence | baseline | 120 | 0.2917 | 0.2854 | 0.3 | 0.3333 | 0.3761 | 0.02661 | 148.9 | 1 | 0 |
| threshold_rule | baseline | 120 | 0.2833 | 0.2779 | 0.2951 | 0 | 0.3504 | 0.02503 | 148.9 | 1 | 0 |
| always_stable | baseline | 120 | 0.45 | 0.2069 | 0.3333 | 0 | 0.5 | 0.02765 | 63.91 | 1 | 0 |
| simple_ml_softmax_logistic | baseline | 120 | 0.45 | 0.2069 | 0.3333 | 0 | 0.3376 | 0.02434 | 113.5 | 1 | 0 |

## Baseline Comparison

| system | system_type | taskA_accuracy | taskA_macro_f1 | taskA_balanced_accuracy | missed_depeg_rate | false_alarm_rate | deviation_mae_bps | total_estimated_cost_usd |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nanobot | agent | 0.4417 | 0.3505 | 0.3935 | 1 | 0.008547 | 56.62 | 0.3454 |
| langgraph | agent | 0.4417 | 0.3372 | 0.3813 | 1 | 0.008547 | 58.68 | 1.212 |
| nanoclaw | agent | 0.4417 | 0.3278 | 0.385 | 1 | 0.01709 | 66.36 | 0.6272 |
| hermes_ai | agent | 0.425 | 0.3213 | 0.369 | 1 | 0.01709 | 57.86 | 0.3481 |
| openclaw | agent | 0.4083 | 0.3176 | 0.3675 | 1 | 0.01709 | 62 | 0.6248 |
| historical_persistence | baseline | 0.2917 | 0.2854 | 0.3 | 0.6667 | 0.3761 | 148.9 | 0 |
| threshold_rule | baseline | 0.2833 | 0.2779 | 0.2951 | 1 | 0.2821 | 148.9 | 0 |
| evoagentx | agent | 0.3917 | 0.2719 | 0.348 | 1 | 0.01709 | 66.92 | 0.6111 |
| always_stable | baseline | 0.45 | 0.2069 | 0.3333 | 1 | 0 | 63.91 | 0 |
| simple_ml_softmax_logistic | baseline | 0.45 | 0.2069 | 0.3333 | 1 | 0 | 113.5 | 0 |

## Computational Cost

| system | system_type | avg_prompt_tokens | avg_completion_tokens | avg_total_tokens | avg_latency_seconds | total_estimated_cost_usd | cost_per_case_usd | cost_per_correct_prediction_usd | cost_per_detected_depeg_usd |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nanobot | agent | 7730 | 238.9 | 7969 | 34.29 | 0.3454 | 0.002878 | 0.006517 |  |
| hermes_ai | agent | 7790 | 241 | 8031 | 33.2 | 0.3481 | 0.002901 | 0.006826 |  |
| evoagentx | agent | 1.366e+04 | 431.9 | 1.41e+04 | 54.25 | 0.6111 | 0.005092 | 0.013 |  |
| openclaw | agent | 1.361e+04 | 376.8 | 1.399e+04 | 30.74 | 0.6248 | 0.005207 | 0.01275 |  |
| nanoclaw | agent | 1.367e+04 | 364.5 | 1.403e+04 | 29.35 | 0.6272 | 0.005226 | 0.01183 |  |
| langgraph | agent | 2.687e+04 | 657.2 | 2.753e+04 | 72.56 | 1.212 | 0.0101 | 0.02287 |  |
| historical_persistence | baseline | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| threshold_rule | baseline | 0 | 0 | 0 | 0 | 0 | 0 | 0 |  |
| always_stable | baseline | 0 | 0 | 0 | 0 | 0 | 0 | 0 |  |
| simple_ml_softmax_logistic | baseline | 0 | 0 | 0 | 0 | 0 | 0 | 0 |  |

## Adapter Truthfulness

| platform | package_version | import_verified | llm_smoke_verified | native_runtime_verified | execution_mode | caveat |
| --- | --- | --- | --- | --- | --- | --- |
| nanobot | nanobot-ai==0.2.0 | 1 | 1 | 1 | nanobot_sdk_openrouter_agent_loop | Real local Nanobot SDK framework path executed with OpenRouter LLM backend. |
| langgraph | langgraph==1.2.0 | 1 | 1 | 1 | langgraph_two_node_stategraph_openrouter_llm | Real local LangGraph StateGraph framework path executed with OpenRouter LLM backend. |
| hermes_ai | hermes-ai==0.3.20 | 1 | 1 | 1 | hermes_agent_llamaindex_achat_openrouter_llm | Real local Hermes Agent framework path executed with OpenRouter LLM backend. |
| evoagentx | evoagentx==0.1.0 | 1 | 1 | 1 | evoagentx_openrouterllm_adapter | Real local EvoAgentX OpenRouterLLM framework path executed with OpenRouter LLM backend. |
| openclaw | openclaw==2026.3.20 | 1 | 1 | 0 | stableeval_adapter | CMDOP local runtime was not available; StableEval used an LLM-backed adapter, not native CMDOP execution. Native check: AgentNotRunningError: No cmdop agent found. Start with: cmdop agent start |
| nanoclaw | nanoclaw==2026.3.20 | 1 | 1 | 0 | stableeval_adapter | CMDOP local runtime was not available; StableEval used an LLM-backed adapter, not native CMDOP execution. Native check: AgentNotRunningError: No cmdop agent found. Start with: cmdop agent start |

## Natural-Distribution Baseline Results

Agent results are not reported on all 507 cases yet because the user requested no full scaling run in this step. Natural-distribution results below are for baselines only and show what the full benchmark distribution looks like before final scaling.

| system | cases | taskA_accuracy | taskA_macro_f1 | taskA_balanced_accuracy | missed_depeg_rate | false_alarm_rate | deviation_mae_bps |
| --- | --- | --- | --- | --- | --- | --- | --- |
| simple_ml_softmax_logistic | 507 | 0.641 | 0.4019 | 0.493 | 1 | 0.07738 | 17.07 |
| historical_persistence | 507 | 0.6726 | 0.3867 | 0.45 | 0.6667 | 0.1488 | 52.66 |
| threshold_rule | 507 | 0.645 | 0.3763 | 0.4461 | 1 | 0.09524 | 52.69 |
| always_stable | 507 | 0.8698 | 0.3101 | 0.3333 | 1 | 0 | 20.17 |

## Simple Interpretation

In this pilot, the best agent did outperform the best baseline on macro-F1.
For this workshop target, the important contribution is not only accuracy: the benchmark records reliability, structured-output validity, latency, tokens, estimated cost, false alarms, and missed depeg events.
