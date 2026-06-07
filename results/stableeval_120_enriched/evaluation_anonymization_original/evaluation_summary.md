# StableEval Arena Paper Pilot Evaluation

Selected model backend: `qwen/qwen-2.5-72b-instruct`

This evaluation covers 12 historical-replay cases. Each case contains only a frozen 30-day lookback window; the hidden next-7-day horizon is used only by the evaluator.

## Main Evaluation Results

| system | system_type | cases | taskA_accuracy | taskA_macro_f1 | taskA_balanced_accuracy | binary_recall | binary_auroc | binary_average_precision | deviation_mae_bps | valid_json_rate | failure_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| langgraph | agent | 12 | 0.5 | 0.4167 | 0.5 | 0 | 0.4444 | 0.2758 | 184.8 | 1 | 0 |
| nanobot | agent | 12 | 0.5 | 0.4127 | 0.5 | 0 | 0.4074 | 0.231 | 185.7 | 1 | 0 |
| nanoclaw | agent | 12 | 0.5 | 0.3956 | 0.5 | 0 | 0.4074 | 0.2611 | 190.3 | 1 | 0 |
| hermes_ai | agent | 12 | 0.4167 | 0.3111 | 0.4167 | 0 | 0.4259 | 0.2574 | 189.1 | 1 | 0 |
| evoagentx | agent | 12 | 0.3333 | 0.254 | 0.3333 | 0 | 0.6111 | 0.2758 | 191.6 | 1 | 0 |
| openclaw | agent | 12 | 0.3333 | 0.1778 | 0.3333 | 0 | 0.5 | 0.5119 | 191.2 | 1 | 0 |
| simple_ml_softmax_logistic | baseline | 12 | 0.25 | 0.2545 | 0.25 | 0 | 0.5556 | 0.3313 | 231.7 | 1 | 0 |
| always_stable | baseline | 12 | 0.3333 | 0.1667 | 0.3333 | 0 | 0.5 | 0.6389 | 206.7 | 1 | 0 |
| historical_persistence | baseline | 12 | 0.1667 | 0.1333 | 0.1667 | 0.3333 | 0.2407 | 0.2242 | 283.8 | 1 | 0 |
| threshold_rule | baseline | 12 | 0.1667 | 0.1333 | 0.1667 | 0 | 0.2222 | 0.2131 | 283.8 | 1 | 0 |

## Baseline Comparison

| system | system_type | taskA_accuracy | taskA_macro_f1 | taskA_balanced_accuracy | missed_depeg_rate | false_alarm_rate | deviation_mae_bps | total_estimated_cost_usd |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| langgraph | agent | 0.5 | 0.4167 | 0.5 | 1 | 0 | 184.8 | 0.1196 |
| nanobot | agent | 0.5 | 0.4127 | 0.5 | 1 | 0 | 185.7 | 0.03477 |
| nanoclaw | agent | 0.5 | 0.3956 | 0.5 | 1 | 0 | 190.3 | 0.06112 |
| hermes_ai | agent | 0.4167 | 0.3111 | 0.4167 | 1 | 0 | 189.1 | 0.03481 |
| simple_ml_softmax_logistic | baseline | 0.25 | 0.2545 | 0.25 | 1 | 0 | 231.7 | 0 |
| evoagentx | agent | 0.3333 | 0.254 | 0.3333 | 1 | 0 | 191.6 | 0.06058 |
| openclaw | agent | 0.3333 | 0.1778 | 0.3333 | 1 | 0 | 191.2 | 0.06217 |
| always_stable | baseline | 0.3333 | 0.1667 | 0.3333 | 1 | 0 | 206.7 | 0 |
| historical_persistence | baseline | 0.1667 | 0.1333 | 0.1667 | 0.6667 | 0.5556 | 283.8 | 0 |
| threshold_rule | baseline | 0.1667 | 0.1333 | 0.1667 | 1 | 0.2222 | 283.8 | 0 |

## Computational Cost

| system | system_type | avg_prompt_tokens | avg_completion_tokens | avg_total_tokens | avg_latency_seconds | total_estimated_cost_usd | cost_per_case_usd | cost_per_correct_prediction_usd | cost_per_detected_depeg_usd |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nanobot | agent | 7787 | 236.2 | 8023 | 27.57 | 0.03477 | 0.002898 | 0.005795 |  |
| hermes_ai | agent | 7787 | 244.7 | 8031 | 26.99 | 0.03481 | 0.002901 | 0.006962 |  |
| evoagentx | agent | 1.354e+04 | 439.9 | 1.398e+04 | 27.08 | 0.06058 | 0.005049 | 0.01515 |  |
| nanoclaw | agent | 1.353e+04 | 387 | 1.392e+04 | 25.54 | 0.06112 | 0.005094 | 0.01019 |  |
| openclaw | agent | 1.354e+04 | 375.9 | 1.391e+04 | 25.57 | 0.06217 | 0.005181 | 0.01554 |  |
| langgraph | agent | 2.661e+04 | 689.5 | 2.73e+04 | 42.72 | 0.1196 | 0.00997 | 0.01994 |  |
| simple_ml_softmax_logistic | baseline | 0 | 0 | 0 | 0 | 0 | 0 | 0 |  |
| always_stable | baseline | 0 | 0 | 0 | 0 | 0 | 0 | 0 |  |
| historical_persistence | baseline | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| threshold_rule | baseline | 0 | 0 | 0 | 0 | 0 | 0 | 0 |  |

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
