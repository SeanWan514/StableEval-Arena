# Dataset Card

## Dataset Name

StableEval Arena hourly frozen-window stablecoin benchmark.

## Purpose

The dataset evaluates stablecoin-risk agents under historical replay. Each benchmark case contains one stablecoin, one observation time, one frozen 30-day lookback window, and one seven-day prediction horizon.

## Sources

| Source | URL | Use |
|---|---|---|
| CryptoCompare histohour | https://min-api.cryptocompare.com/documentation?cat=dataHistohour&key=Historical | Hourly OHLCV in USD for USDT, USDC, DAI, BTC, and ETH. |
| DeFiLlama stablecoins current endpoint | https://stablecoins.llama.fi/stablecoins?includePrices=true | Stablecoin metadata and IDs. |
| DeFiLlama per-stablecoin endpoint | https://stablecoins.llama.fi/stablecoin/1 | Historical stablecoin supply and chain balances. IDs 1, 2, and 5 are USDT, USDC, and DAI. |
| DeFiLlama stablecoin sector chart | https://stablecoins.llama.fi/stablecoincharts/all | Historical total stablecoin sector supply / market cap. |

## License And Redistribution Notice

Repository code, scripts, prompts, and documentation are licensed under Apache-2.0 unless otherwise stated. The benchmark artifacts under `data/benchmark/` and the saved result artifacts under `results/` may include processed or derived market-data artifacts from upstream providers such as CryptoCompare and DeFiLlama, plus LLM-generated prediction outputs. These artifacts are included to support academic reproducibility, but redistribution and reuse may remain subject to original provider terms. Raw provider/vendor snapshots are not redistributed in this release.

## Time Window

Source period: `2023-01-01 00:00 UTC` to `2026-05-01 23:00 UTC`.

The script interprets `2026-05-01` as the full UTC calendar day ending at `2026-05-01 23:00 UTC`.

## Assets

Stablecoins:

| Symbol | DeFiLlama ID | Mechanism |
|---|---:|---|
| USDT | 1 | Fiat-backed |
| USDC | 2 | Fiat-backed |
| DAI | 5 | Crypto-backed |

Context:

| Symbol | Purpose |
|---|---|
| BTC | Broad crypto market context. |
| ETH | Broad crypto market context and DAI collateral-market context. |

## Raw Fields

Hourly price and volume:

| Field |
|---|
| timestamp |
| stablecoin |
| open |
| high |
| low |
| close |
| volume_base |
| volume_usd |

Market structure:

| Field |
|---|
| stablecoin_market_cap_usd |
| stablecoin_total_supply_usd |
| stablecoin_market_share |
| chain_count |
| top_chain |
| top_chain_share |
| peg_type |
| peg_mechanism |

Context:

| Field |
|---|
| btc_7d_return |
| eth_7d_return |
| btc_7d_volatility |
| eth_7d_volatility |

## Constructed Features

| Feature | Definition |
|---|---|
| close_deviation | `close - 1.0` |
| abs_close_deviation | `abs(close - 1.0)` |
| max_period_deviation | `max(abs(high - 1.0), abs(low - 1.0))` for the hourly bar |
| hourly_range | `high - low` |
| return_1h | `close_t / close_t-1 - 1` |
| rolling_volatility_7d | Rolling 168-hour standard deviation of hourly returns |
| rolling_volatility_30d | Rolling 720-hour standard deviation of hourly returns |
| rolling_7d_abs_deviation_mean | Rolling 168-hour mean absolute close deviation |
| rolling_7d_abs_deviation_max | Rolling 168-hour max absolute close deviation |
| rolling_30d_abs_deviation_max | Rolling 720-hour max absolute close deviation |
| rolling_7d_volume_change | Current 168-hour volume sum divided by previous 168-hour sum, minus 1 |
| rolling_7d_market_cap_change | Current market cap divided by market cap 168 hours prior, minus 1 |

## Frozen Windows

Main experiment:

| Parameter | Value |
|---|---:|
| Lookback | 30 days / 720 hours |
| Horizon | 7 days / 168 hours |
| Stride | 7 days |
| Cases | 507 |

For each case, the agent receives a compact prompt packet with:

| Prompt component | Included |
|---|---|
| Latest observation | Yes |
| 30-day summary | Yes |
| BTC/ETH context | Yes |
| 30 daily aggregates | Yes |
| Last 48 hourly bars | Yes |
| Future labels | No |

The complete expanded lookback and horizon rows are stored in:

`data/benchmark/stableeval_507_natural/full_hourly_windows.csv.gz`

## Labels

Dollar-peg deviation is measured from hourly close price:

`deviation_bps = abs(close - 1.0) * 10000`

Strict sustained-depeg label:

`label_depeg_100bps_sustained_3h`

True if the hourly close price deviates from 1.00 USD by at least 100 bps for at least three consecutive hours during the forecast horizon.

Watch signal:

`label_stress_50bps_any_close`

True if any hourly close price deviates from 1.00 USD by at least 50 bps during the forecast horizon.

Main evaluation label:

`enhanced_stability_label`

| Status | Definition |
|---|---|
| stable | No meaningful next-7-day instability under the enhanced label rule. |
| watch | Mild but meaningful instability, including 50 bps close deviations or persistent lower-grade deviation. |
| stress | Large, persistent, or operationally meaningful instability, including strict sustained depeg, 100 bps close deviation, repeated 50 bps hours, or high average absolute deviation. |

Additional horizon statistics used by the evaluator include maximum absolute deviation, average absolute deviation, deviation volatility, hours above 25/50/100 bps, maximum consecutive hours above 100 bps, and direction.

## Current Label Distribution

| Label | Count in full 507-case pool |
|---|---:|
| stable | 441 |
| watch | 45 |
| stress | 21 |

Only three cases satisfy the strict sustained 100 bps depeg criterion. The broader `stress` class also includes near-stress cases with operationally meaningful intensity or duration. This distinction is important: strict sustained depegs are rare, but a trustworthy monitoring benchmark should also test high-risk near-stress behavior.

## Known Limitations

The benchmark uses price, volume, supply, market share, chain distribution, and BTC/ETH market context. It does not yet include issuer reserve disclosures, centralized exchange order books, DEX pool liquidity, oracle feeds, news, regulatory announcements, or bank-run event data.

The release results include the completed `StableEval-120-Enriched` validation under `results/stableeval_120_enriched/` and the completed `StableEval-507-Natural` scaling block under `results/stableeval_507_natural/`. The runner requires `OPENROUTER_API_KEY` by default for new LLM-backed runs; deterministic fallback is available only through the explicit `--allow-deterministic-fallback` flag and is not a paper-reported agent result.
