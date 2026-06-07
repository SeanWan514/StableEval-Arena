# Methodology And Reference Map

This file maps major benchmark decisions to supporting references. It is intentionally explicit so that the paper can defend the experimental design.

## 1. Historical Replay And Frozen Windows

Decision:

Each case is a historical replay sample. The agent receives only information from a frozen 30-day lookback window ending at observation time `t`, then predicts the next seven days.

Why:

This follows the same broad evaluation logic as Prediction Arena: agents make repeated decisions under a time-indexed historical or live market setting, and are scored later against objective outcomes. Freezing the evidence packet prevents future leakage.

References:

| Reference | Use |
|---|---|
| Prediction Arena: Benchmarking AI Models on Real-World Prediction Markets | Closest benchmark framing: repeated agent decisions, objective financial outcomes, token/time cost. |
| Gneiting and Raftery (2007) | Forecast evaluation should compare probabilistic forecasts to realized outcomes using proper scoring rules. |

## 2. Stablecoin Price Stability And Peg Deviation

Decision:

The benchmark measures deviation from the target peg of 1.00 USD using close prices. It stores high/low deviations as evidence but uses sustained close-price deviations for depeg labels.

Why:

Stablecoin literature evaluates whether tokens remain close to their intended peg and studies deviation, volatility, arbitrage, redemption, and stabilization mechanisms. Close-price sustained labels avoid turning isolated high/low wicks into false depeg events.

References:

| Reference | Use |
|---|---|
| Lyons and Viswanath-Natraj, "What Keeps Stablecoins Stable?" | Stablecoin peg stability, arbitrage, and price-deviation framing. |
| Baur and Hoang, "The Stable in Stablecoins" | Empirical treatment of stablecoins as assets expected to stay close to one dollar. |
| Gorton and Zhang, "Taming Wildcat Stablecoins" | Stablecoin fragility and run-risk framing. |
| DeFiLlama stablecoin data | Supply, peg mechanism, and market-structure context. |

## 3. Conservative And Graded Depeg Definition

Decision:

Strict sustained-depeg label:

`abs(close - 1.00) >= 0.01` for at least three consecutive hourly closes during the seven-day horizon.

Watch signal:

`abs(close - 1.00) >= 0.005` for any hourly close during the seven-day horizon.

Main three-class label:

- `stable`: no meaningful hidden-horizon instability.
- `watch`: mild but meaningful instability, including close-deviation or duration signals.
- `stress`: strict sustained depeg or operationally meaningful near-stress, including 100 bps close deviation, repeated 50 bps hours, or high average absolute deviation.

Why:

Prof. Zhang's warning is methodologically important: stablecoins should not be labeled as depegged too easily. A one-hour high/low wick is weaker evidence than sustained close-price deviation. The 1% threshold is a clear operational definition for a material dollar-peg break; the three-hour persistence rule reduces false positives from transient data artifacts.

The current build confirms this conservatism: only 3 of 507 cases, or 0.59%, are labeled as strict sustained 1% depeg. The broader enhanced stress class contains 21 cases so the validation can test rare-event behavior without pretending every 50 bps fluctuation is a full depeg.

## 4. Feature Set

Decision:

The dataset includes:

| Layer | Features |
|---|---|
| Price/volume | OHLCV, close deviation, absolute deviation, hourly range, returns, rolling volatility. |
| Market structure | Market cap, circulating supply, stablecoin market share, chain count, top-chain concentration. |
| Context | BTC/ETH seven-day return and volatility. |

Why:

Price alone is not enough for stablecoin risk. A token can remain near 1.00 USD while supply contraction, market share loss, or chain concentration changes reveal stress. BTC/ETH context helps distinguish isolated stablecoin stress from general crypto-market turbulence.

References:

| Reference | Use |
|---|---|
| CryptoCompare histohour API | Reproducible hourly OHLCV source. |
| DeFiLlama stablecoin endpoints | Reproducible supply, peg mechanism, and chain-balance source. |
| Stablecoin empirical papers above | Justification for focusing on peg deviation, volatility, and stabilization mechanisms. |

## 5. Prediction Metrics

Decision:

The benchmark reports classification, probabilistic, calibration, directional, continuous-error, and reliability metrics.

References:

| Metric | Reference |
|---|---|
| Brier score | Brier (1950); Gneiting and Raftery (2007). |
| Calibration / ECE | Guo et al. (2017). |
| AUROC | Fawcett (2006). |
| Average precision / PR under imbalance | Davis and Goadrich (2006); Saito and Rehmsmeier (2015). |
| MAE / RMSE | Standard forecast-error metrics; included for continuous maximum-deviation forecasts. |
| Precision, recall, F1 | Standard classification metrics, especially useful under rare-event imbalance. |

## 6. Computational Cost And Failure Modes

Decision:

The benchmark tracks:

| Cost/reliability field | Meaning |
|---|---|
| prompt_tokens_approx | Input size proxy. |
| completion_tokens_approx | Output size proxy. |
| total_tokens_approx | Total token-cost proxy. |
| latency_seconds | Runtime cost. |
| estimated_cost_usd | Provider API spend. |
| valid_json_rate | Automation-readiness. |
| failure_rate | Platform reliability. |

Why:

The paper's title is cost-aware, so prediction quality alone is insufficient. Prediction Arena explicitly motivates measuring token usage and processing time as part of agentic prediction-market evaluation. StableEval Arena adapts that logic to stablecoin-risk prediction.

## 7. LLM-Backed Experiment Requirement

The earlier full report was an offline pilot because no LLM provider key was available in the shell. That pilot proved the data and scoring pipeline, but it did not compare agentic AI systems.

The current runner fixes that limitation:

1. `src/agents/run_platform.py` now requires `OPENROUTER_API_KEY` by default.
2. Each prediction row records `model_backend`, `llm_call_count`, token usage, latency, cost, and adapter metadata.
3. The deterministic policy can only run through the explicit `--allow-deterministic-fallback` flag.
4. The StableEval-120-Enriched validation under `results/stableeval_120_enriched/` verifies all six systems on the same case list, model backend, prompt schema, and evaluator.

For final full-benchmark results, rerun the frozen 507-case protocol with the same funded OpenRouter model across platforms. The current release does not claim that the full 507-case scaling step has been completed.
