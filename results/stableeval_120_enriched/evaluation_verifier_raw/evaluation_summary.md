# StableEval Arena Paper Pilot Evaluation

Selected model backend: `qwen/qwen-2.5-72b-instruct`

This evaluation covers 120 historical-replay cases. Each case contains only a frozen 30-day lookback window; the hidden next-7-day horizon is used only by the evaluator.

## Main Evaluation Results

| system | system_type | cases | taskA_accuracy | taskA_macro_f1 | taskA_balanced_accuracy | binary_recall | binary_auroc | binary_average_precision | deviation_mae_bps | valid_json_rate | failure_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| langgraph | agent | 120 | 0.3833 | 0.2722 | 0.3406 | 0 | 0.4103 | 0.03191 | 65.44 | 1 | 0 |
| nanoclaw | agent | 120 | 0.3667 | 0.2712 | 0.3354 | 0 | 0.4444 | 0.02558 | 71.16 | 1 | 0 |
| evoagentx | agent | 120 | 0.375 | 0.2623 | 0.3453 | 0 | 0.3832 | 0.02256 | 69.22 | 1 | 0 |
| hermes_ai | agent | 120 | 0.3917 | 0.2608 | 0.3504 | 0 | 0.2436 | 0.02344 | 60.61 | 1 | 0 |
| nanobot | agent | 120 | 0.375 | 0.2533 | 0.3356 | 0 | 0.4687 | 0.02815 | 59.99 | 1 | 0 |
| openclaw | agent | 120 | 0.3667 | 0.2406 | 0.3185 | 0 | 0.4345 | 0.02952 | 70.85 | 1 | 0 |
| historical_persistence | baseline | 120 | 0.2917 | 0.2854 | 0.3 | 0.3333 | 0.3761 | 0.02661 | 148.9 | 1 | 0 |
| threshold_rule | baseline | 120 | 0.2833 | 0.2779 | 0.2951 | 0 | 0.3504 | 0.02503 | 148.9 | 1 | 0 |
| always_stable | baseline | 120 | 0.45 | 0.2069 | 0.3333 | 0 | 0.5 | 0.02765 | 63.91 | 1 | 0 |
| simple_ml_softmax_logistic | baseline | 120 | 0.45 | 0.2069 | 0.3333 | 0 | 0.3376 | 0.02434 | 113.5 | 1 | 0 |

## Baseline Comparison

| system | system_type | taskA_accuracy | taskA_macro_f1 | taskA_balanced_accuracy | missed_depeg_rate | false_alarm_rate | deviation_mae_bps | total_estimated_cost_usd |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| historical_persistence | baseline | 0.2917 | 0.2854 | 0.3 | 0.6667 | 0.3761 | 148.9 | 0 |
| threshold_rule | baseline | 0.2833 | 0.2779 | 0.2951 | 1 | 0.2821 | 148.9 | 0 |
| langgraph | agent | 0.3833 | 0.2722 | 0.3406 | 1 | 0.01709 | 65.44 | 1.84 |
| nanoclaw | agent | 0.3667 | 0.2712 | 0.3354 | 1 | 0.01709 | 71.16 | 1.257 |
| evoagentx | agent | 0.375 | 0.2623 | 0.3453 | 1 | 0.01709 | 69.22 | 1.246 |
| hermes_ai | agent | 0.3917 | 0.2608 | 0.3504 | 1 | 0.01709 | 60.61 | 0.9819 |
| nanobot | agent | 0.375 | 0.2533 | 0.3356 | 1 | 0.01709 | 59.99 | 0.9785 |
| openclaw | agent | 0.3667 | 0.2406 | 0.3185 | 1 | 0.01709 | 70.85 | 1.253 |
| always_stable | baseline | 0.45 | 0.2069 | 0.3333 | 1 | 0 | 63.91 | 0 |
| simple_ml_softmax_logistic | baseline | 0.45 | 0.2069 | 0.3333 | 1 | 0 | 113.5 | 0 |

## Computational Cost

| system | system_type | avg_prompt_tokens | avg_completion_tokens | avg_total_tokens | avg_latency_seconds | total_estimated_cost_usd | cost_per_case_usd | cost_per_correct_prediction_usd | cost_per_detected_depeg_usd |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nanobot | agent | 2.152e+04 | 687.7 | 2.221e+04 | 63.96 | 0.9785 | 0.008154 | 0.02174 |  |
| hermes_ai | agent | 2.157e+04 | 730 | 2.23e+04 | 68.1 | 0.9819 | 0.008183 | 0.02089 |  |
| evoagentx | agent | 2.748e+04 | 904.5 | 2.839e+04 | 83.59 | 1.246 | 0.01039 | 0.0277 |  |
| openclaw | agent | 2.732e+04 | 800 | 2.812e+04 | 68.12 | 1.253 | 0.01044 | 0.02848 |  |
| nanoclaw | agent | 2.742e+04 | 783.5 | 2.82e+04 | 63.65 | 1.257 | 0.01048 | 0.02858 |  |
| langgraph | agent | 4.055e+04 | 1099 | 4.165e+04 | 97.86 | 1.84 | 0.01534 | 0.04001 |  |
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
