# StableEval Arena Paper Pilot Evaluation

Selected model backend: `qwen/qwen-2.5-72b-instruct`

This evaluation covers 120 historical-replay cases. Each case contains only a frozen 30-day lookback window; the hidden next-7-day horizon is used only by the evaluator.

## Main Evaluation Results

| system | system_type | cases | taskA_accuracy | taskA_macro_f1 | taskA_balanced_accuracy | binary_recall | binary_auroc | binary_average_precision | deviation_mae_bps | valid_json_rate | failure_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| historical_persistence | baseline | 120 | 0.2917 | 0.2854 | 0.3 | 0.3333 | 0.3761 | 0.02661 | 148.9 | 1 | 0 |
| threshold_rule | baseline | 120 | 0.2833 | 0.2779 | 0.2951 | 0 | 0.3504 | 0.02503 | 148.9 | 1 | 0 |
| always_stable | baseline | 120 | 0.45 | 0.2069 | 0.3333 | 0 | 0.5 | 0.02765 | 63.91 | 1 | 0 |
| simple_ml_softmax_logistic | baseline | 120 | 0.45 | 0.2069 | 0.3333 | 0 | 0.3376 | 0.02434 | 113.5 | 1 | 0 |

## Baseline Comparison

| system | system_type | taskA_accuracy | taskA_macro_f1 | taskA_balanced_accuracy | missed_depeg_rate | false_alarm_rate | deviation_mae_bps | total_estimated_cost_usd |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| historical_persistence | baseline | 0.2917 | 0.2854 | 0.3 | 0.6667 | 0.3761 | 148.9 | 0 |
| threshold_rule | baseline | 0.2833 | 0.2779 | 0.2951 | 1 | 0.2821 | 148.9 | 0 |
| always_stable | baseline | 0.45 | 0.2069 | 0.3333 | 1 | 0 | 63.91 | 0 |
| simple_ml_softmax_logistic | baseline | 0.45 | 0.2069 | 0.3333 | 1 | 0 | 113.5 | 0 |

## Computational Cost

| system | system_type | avg_prompt_tokens | avg_completion_tokens | avg_total_tokens | avg_latency_seconds | total_estimated_cost_usd | cost_per_case_usd | cost_per_correct_prediction_usd | cost_per_detected_depeg_usd |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
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

In this pilot, the best agent did not outperform the best baseline on macro-F1.
For this workshop target, the important contribution is not only accuracy: the benchmark records reliability, structured-output validity, latency, tokens, estimated cost, false alarms, and missed depeg events.
