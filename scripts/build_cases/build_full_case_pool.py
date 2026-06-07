#!/usr/bin/env python3
"""Build the StableEval Arena hourly frozen-window benchmark dataset.

Data sources:
- CryptoCompare histohour endpoint for hourly OHLCV in USD.
- DeFiLlama stablecoin endpoints for historical circulating supply, sector
  supply, and chain-distribution metadata.

The benchmark uses frozen 30-day lookback windows and seven-day forecast
horizons. Agents receive only the lookback summary and compact within-window
evidence. Labels are stored separately from prompt packets.
"""

from __future__ import annotations

import argparse
import json
import math
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


CRYPTOCOMPARE_HISTOHOUR = "https://min-api.cryptocompare.com/data/v2/histohour"
DEFILLAMA_STABLECOINS = "https://stablecoins.llama.fi/stablecoins?includePrices=true"
DEFILLAMA_STABLECOIN = "https://stablecoins.llama.fi/stablecoin/{stablecoin_id}"
DEFILLAMA_SECTOR = "https://stablecoins.llama.fi/stablecoincharts/all"
USER_AGENT = "StableEvalArena/0.2 academic reproducibility script"


@dataclass(frozen=True)
class StablecoinSpec:
    symbol: str
    name: str
    defillama_id: str
    gecko_id: str


STABLECOINS = [
    StablecoinSpec("USDT", "Tether", "1", "tether"),
    StablecoinSpec("USDC", "USD Coin", "2", "usd-coin"),
    StablecoinSpec("DAI", "Dai", "5", "dai"),
]

CONTEXT_SYMBOLS = ["BTC", "ETH"]


def utc_dt(text: str, end_of_day: bool = False) -> datetime:
    base = datetime.fromisoformat(text).replace(tzinfo=timezone.utc)
    if end_of_day:
        return base + timedelta(hours=23)
    return base


def fetch_json(url: str, timeout: int = 45, retries: int = 3) -> Any:
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=timeout) as response:
                return json.load(response)
        except Exception as exc:  # pragma: no cover - network failures are runtime details.
            last_error = exc
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"failed to fetch {url}: {last_error}")


def fetch_cryptocompare_histohour(symbol: str, start: datetime, end: datetime) -> pd.DataFrame:
    start_ts = int(start.timestamp())
    to_ts = int(end.timestamp())
    rows: list[dict[str, Any]] = []
    seen_min: int | None = None

    while True:
        params = {
            "fsym": symbol,
            "tsym": "USD",
            "limit": 2000,
            "toTs": to_ts,
        }
        url = f"{CRYPTOCOMPARE_HISTOHOUR}?{urllib.parse.urlencode(params)}"
        payload = fetch_json(url)
        if payload.get("Response") != "Success":
            raise RuntimeError(f"CryptoCompare failed for {symbol}: {payload.get('Message')}")

        batch = payload.get("Data", {}).get("Data", [])
        if not batch:
            break
        rows.extend(batch)

        min_time = min(int(item["time"]) for item in batch)
        if min_time <= start_ts or min_time == seen_min:
            break
        seen_min = min_time
        to_ts = min_time - 3600
        time.sleep(0.25)

    frame = pd.DataFrame(rows).drop_duplicates(subset=["time"]).sort_values("time")
    frame = frame[(frame["time"] >= start_ts) & (frame["time"] <= int(end.timestamp()))].copy()
    frame["timestamp"] = pd.to_datetime(frame["time"], unit="s", utc=True)
    frame["symbol"] = symbol
    frame.rename(columns={"volumefrom": "volume_base", "volumeto": "volume_usd"}, inplace=True)
    keep = [
        "timestamp",
        "symbol",
        "open",
        "high",
        "low",
        "close",
        "volume_base",
        "volume_usd",
        "conversionType",
        "conversionSymbol",
    ]
    return frame[keep]


def fetch_defillama_metadata(raw_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    current = fetch_json(DEFILLAMA_STABLECOINS)
    (raw_dir / "defillama_stablecoins_current.json").write_text(
        json.dumps(current, indent=2), encoding="utf-8"
    )

    sector_payload = fetch_json(DEFILLAMA_SECTOR)
    (raw_dir / "defillama_sector_stablecoincharts_all.json").write_text(
        json.dumps(sector_payload[:5], indent=2), encoding="utf-8"
    )
    sector_rows = []
    for row in sector_payload:
        ts = pd.to_datetime(int(row["date"]), unit="s", utc=True)
        sector_rows.append(
            {
                "date": ts.date().isoformat(),
                "sector_total_supply_usd": (row.get("totalCirculating") or {}).get("peggedUSD"),
                "sector_total_market_cap_usd": (row.get("totalCirculatingUSD") or {}).get("peggedUSD"),
            }
        )
    sector = pd.DataFrame(sector_rows)

    stablecoin_rows = []
    chain_rows = []
    stablecoin_payloads: dict[str, Any] = {}
    for spec in STABLECOINS:
        payload = fetch_json(DEFILLAMA_STABLECOIN.format(stablecoin_id=spec.defillama_id))
        stablecoin_payloads[spec.symbol] = payload
        (raw_dir / f"defillama_stablecoin_{spec.symbol}.json").write_text(
            json.dumps(payload, indent=2), encoding="utf-8"
        )

        for item in payload.get("tokens", []):
            ts = pd.to_datetime(int(item["date"]), unit="s", utc=True)
            circulating = (item.get("circulating") or {}).get("peggedUSD")
            stablecoin_rows.append(
                {
                    "date": ts.date().isoformat(),
                    "stablecoin": spec.symbol,
                    "stablecoin_total_supply_usd": circulating,
                    "stablecoin_market_cap_usd": circulating,
                    "peg_type": payload.get("pegType"),
                    "peg_mechanism": payload.get("pegMechanism"),
                    "price_source": payload.get("priceSource"),
                }
            )

        for chain, chain_data in (payload.get("chainBalances") or {}).items():
            for item in chain_data.get("tokens", []):
                ts = pd.to_datetime(int(item["date"]), unit="s", utc=True)
                circulating = (item.get("circulating") or {}).get("peggedUSD")
                if circulating is None:
                    continue
                chain_rows.append(
                    {
                        "date": ts.date().isoformat(),
                        "stablecoin": spec.symbol,
                        "chain": chain,
                        "chain_supply_usd": circulating,
                    }
                )
        time.sleep(0.4)

    stablecoins = pd.DataFrame(stablecoin_rows)
    chains = pd.DataFrame(chain_rows)
    if chains.empty:
        chain_daily = pd.DataFrame(columns=["date", "stablecoin", "chain_count", "top_chain", "top_chain_share"])
    else:
        chain_sum = chains.groupby(["date", "stablecoin", "chain"], as_index=False)["chain_supply_usd"].sum()
        totals = chain_sum.groupby(["date", "stablecoin"], as_index=False)["chain_supply_usd"].sum()
        totals.rename(columns={"chain_supply_usd": "chain_supply_total_usd"}, inplace=True)
        chain_sum = chain_sum.merge(totals, on=["date", "stablecoin"], how="left")
        chain_sum["chain_share"] = chain_sum["chain_supply_usd"] / chain_sum["chain_supply_total_usd"].replace(0, np.nan)
        idx = chain_sum.groupby(["date", "stablecoin"])["chain_supply_usd"].idxmax()
        top = chain_sum.loc[idx, ["date", "stablecoin", "chain", "chain_share"]].rename(
            columns={"chain": "top_chain", "chain_share": "top_chain_share"}
        )
        counts = chain_sum.groupby(["date", "stablecoin"], as_index=False)["chain"].nunique().rename(
            columns={"chain": "chain_count"}
        )
        chain_daily = counts.merge(top, on=["date", "stablecoin"], how="left")

    stablecoins = stablecoins.merge(sector, on="date", how="left")
    stablecoins["stablecoin_market_share"] = (
        stablecoins["stablecoin_market_cap_usd"] / stablecoins["sector_total_market_cap_usd"].replace(0, np.nan)
    )
    stablecoins = stablecoins.merge(chain_daily, on=["date", "stablecoin"], how="left")
    return stablecoins, sector, stablecoin_payloads


def clean_price_rows(frame: pd.DataFrame, is_stablecoin: bool) -> pd.DataFrame:
    out = frame.copy()
    numeric = ["open", "high", "low", "close", "volume_base", "volume_usd"]
    for col in numeric:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    valid = out[numeric].notna().all(axis=1)
    valid &= (out[["open", "high", "low", "close"]] > 0).all(axis=1)
    if is_stablecoin:
        valid &= (out[["open", "high", "low", "close"]] < 1.20).all(axis=1)
        valid &= (out[["open", "high", "low", "close"]] > 0.80).all(axis=1)
    out = out[valid].copy()
    out["timestamp"] = pd.to_datetime(out["timestamp"], utc=True)
    return out.sort_values(["symbol", "timestamp"]).reset_index(drop=True)


def add_hourly_features(price: pd.DataFrame, metadata: pd.DataFrame) -> pd.DataFrame:
    df = clean_price_rows(price, is_stablecoin=True)
    df.rename(columns={"symbol": "stablecoin"}, inplace=True)
    df["date"] = df["timestamp"].dt.date.astype(str)
    df = df.merge(metadata, on=["date", "stablecoin"], how="left")
    df.sort_values(["stablecoin", "timestamp"], inplace=True)

    parts = []
    for stablecoin, group in df.groupby("stablecoin", sort=False):
        g = group.copy()
        g["close_deviation"] = g["close"] - 1.0
        g["abs_close_deviation"] = g["close_deviation"].abs()
        g["max_period_deviation"] = np.maximum((g["high"] - 1.0).abs(), (g["low"] - 1.0).abs())
        g["hourly_range"] = g["high"] - g["low"]
        g["return_1h"] = g["close"].pct_change()
        g["rolling_volatility_7d"] = g["return_1h"].rolling(168, min_periods=24).std()
        g["rolling_volatility_30d"] = g["return_1h"].rolling(720, min_periods=168).std()
        g["rolling_7d_abs_deviation_mean"] = g["abs_close_deviation"].rolling(168, min_periods=24).mean()
        g["rolling_7d_abs_deviation_max"] = g["abs_close_deviation"].rolling(168, min_periods=24).max()
        g["rolling_30d_abs_deviation_max"] = g["abs_close_deviation"].rolling(720, min_periods=168).max()
        volume_7d = g["volume_usd"].rolling(168, min_periods=24).sum()
        prev_volume_7d = volume_7d.shift(168)
        g["rolling_7d_volume_change"] = volume_7d / prev_volume_7d.replace(0, np.nan) - 1
        market_cap = pd.to_numeric(g["stablecoin_market_cap_usd"], errors="coerce")
        g["rolling_7d_market_cap_change"] = market_cap / market_cap.shift(168).replace(0, np.nan) - 1
        parts.append(g)
    return pd.concat(parts, ignore_index=True)


def add_context_features(context: pd.DataFrame) -> pd.DataFrame:
    ctx = clean_price_rows(context, is_stablecoin=False)
    out = []
    for symbol, group in ctx.groupby("symbol", sort=False):
        g = group.copy().sort_values("timestamp")
        lower = symbol.lower()
        g[f"{lower}_close"] = g["close"]
        g[f"{lower}_return_1h"] = g["close"].pct_change()
        g[f"{lower}_7d_return"] = g["close"] / g["close"].shift(168) - 1
        g[f"{lower}_7d_volatility"] = g[f"{lower}_return_1h"].rolling(168, min_periods=24).std()
        keep = ["timestamp", f"{lower}_close", f"{lower}_7d_return", f"{lower}_7d_volatility"]
        out.append(g[keep])
    merged = out[0]
    for extra in out[1:]:
        merged = merged.merge(extra, on="timestamp", how="outer")
    return merged.sort_values("timestamp")


def pct_change_safe(last: float | None, first: float | None) -> float | None:
    if first is None or last is None or not np.isfinite(first) or not np.isfinite(last) or first == 0:
        return None
    return float(last / first - 1)


def first_last_change(series: pd.Series) -> float | None:
    clean = pd.to_numeric(series, errors="coerce").dropna()
    if len(clean) < 2:
        return None
    return pct_change_safe(float(clean.iloc[-1]), float(clean.iloc[0]))


def sustained_depeg(abs_dev: pd.Series, threshold: float = 0.01, min_hours: int = 3) -> bool:
    flag = abs_dev >= threshold
    if not flag.any():
        return False
    return bool(flag.rolling(min_hours, min_periods=min_hours).sum().ge(min_hours).any())


def max_consecutive(mask: pd.Series) -> int:
    best = run = 0
    for value in mask.astype(bool).tolist():
        if value:
            run += 1
            best = max(best, run)
        else:
            run = 0
    return int(best)


def direction_from_horizon(horizon: pd.DataFrame, threshold: float = 0.0025) -> str:
    dev = horizon["close"] - 1.0
    if dev.abs().max() < threshold:
        return "two_sided_or_no_meaningful"
    max_pos = dev.max()
    max_neg = dev.min()
    return "below_peg" if abs(max_neg) >= abs(max_pos) else "above_peg"


def direction_from_signed(min_signed_bps: float, max_signed_bps: float) -> str:
    if abs(min_signed_bps) < 10 and abs(max_signed_bps) < 10:
        return "two_sided_or_no_meaningful"
    if abs(min_signed_bps) > abs(max_signed_bps) * 1.2:
        return "below_peg"
    if abs(max_signed_bps) > abs(min_signed_bps) * 1.2:
        return "above_peg"
    return "two_sided_or_no_meaningful"


def summarize_daily(window: pd.DataFrame) -> list[dict[str, Any]]:
    daily = (
        window.assign(day=window["timestamp"].dt.date.astype(str))
        .groupby("day", as_index=False)
        .agg(
            open=("open", "first"),
            high=("high", "max"),
            low=("low", "min"),
            close=("close", "last"),
            volume_usd=("volume_usd", "sum"),
            abs_close_deviation_mean=("abs_close_deviation", "mean"),
            abs_close_deviation_max=("abs_close_deviation", "max"),
            max_period_deviation=("max_period_deviation", "max"),
            stablecoin_market_cap_usd=("stablecoin_market_cap_usd", "last"),
            stablecoin_market_share=("stablecoin_market_share", "last"),
        )
    )
    for col in daily.columns:
        if col != "day":
            daily[col] = pd.to_numeric(daily[col], errors="coerce").round(10)
    return daily.to_dict("records")


def build_cases(
    features: pd.DataFrame,
    context: pd.DataFrame,
    start: datetime,
    end: datetime,
    lookback_days: int,
    horizon_days: int,
    stride_days: int,
) -> tuple[pd.DataFrame, list[dict[str, Any]], pd.DataFrame, pd.DataFrame]:
    features = features.merge(context, on="timestamp", how="left")
    lookback_hours = lookback_days * 24
    horizon_hours = horizon_days * 24
    stride = timedelta(days=stride_days)

    observation = start + timedelta(hours=lookback_hours - 1)
    latest_observation = end - timedelta(hours=horizon_hours)
    case_rows: list[dict[str, Any]] = []
    long_parts: list[pd.DataFrame] = []
    prompt_packets: list[dict[str, Any]] = []

    while observation <= latest_observation:
        lookback_start = observation - timedelta(hours=lookback_hours - 1)
        horizon_start = observation + timedelta(hours=1)
        horizon_end = observation + timedelta(hours=horizon_hours)
        for spec in STABLECOINS:
            coin = features[features["stablecoin"].eq(spec.symbol)].copy()
            window = coin[(coin["timestamp"] >= lookback_start) & (coin["timestamp"] <= observation)].copy()
            horizon = coin[(coin["timestamp"] >= horizon_start) & (coin["timestamp"] <= horizon_end)].copy()
            if len(window) < int(0.95 * lookback_hours) or len(horizon) < int(0.95 * horizon_hours):
                continue

            latest = window.iloc[-1]
            last_7d = window.tail(168)
            prev_7d = window.iloc[-336:-168] if len(window) >= 336 else pd.DataFrame()
            horizon_abs = horizon["abs_close_deviation"]
            horizon_returns = horizon["close"].pct_change().dropna()
            horizon_abs_bps = horizon_abs.astype(float) * 10000.0
            horizon_signed_bps = horizon["close_deviation"].astype(float) * 10000.0

            actual_depeg = sustained_depeg(horizon_abs, threshold=0.01, min_hours=3)
            horizon_max_abs = float(horizon_abs.max())
            status = "stress" if actual_depeg else ("watch" if horizon_max_abs >= 0.005 else "stable")
            horizon_mean_abs_bps = float(horizon_abs_bps.mean())
            horizon_max_abs_bps = float(horizon_abs_bps.max())
            horizon_vol_bps = float(horizon_abs_bps.std(ddof=0))
            horizon_hours_ge_25 = int((horizon_abs_bps >= 25).sum())
            horizon_hours_ge_50 = int((horizon_abs_bps >= 50).sum())
            horizon_hours_ge_100 = int((horizon_abs_bps >= 100).sum())
            horizon_max_consec_ge_100 = max_consecutive(horizon_abs_bps >= 100)
            enhanced_severe = horizon_max_consec_ge_100 >= 3
            enhanced_stress = (
                enhanced_severe
                or horizon_max_abs_bps >= 100
                or horizon_hours_ge_50 >= 6
                or horizon_mean_abs_bps >= 25
            )
            enhanced_watch = (
                (not enhanced_stress)
                and (
                    horizon_max_abs_bps >= 50
                    or horizon_hours_ge_25 >= 6
                    or horizon_mean_abs_bps >= 10
                )
            )
            enhanced_label = "stress" if enhanced_stress else ("watch" if enhanced_watch else "stable")
            enhanced_direction = direction_from_signed(float(horizon_signed_bps.min()), float(horizon_signed_bps.max()))
            case_id = f"{spec.symbol}_{observation.strftime('%Y%m%d%H')}"

            volume_recent = float(last_7d["volume_usd"].sum())
            volume_prev = float(prev_7d["volume_usd"].sum()) if not prev_7d.empty else np.nan
            volume_change_7d = pct_change_safe(volume_recent, volume_prev)

            case = {
                "case_id": case_id,
                "stablecoin": spec.symbol,
                "stablecoin_name": spec.name,
                "lookback_start": lookback_start.isoformat(),
                "observation_time": observation.isoformat(),
                "horizon_start": horizon_start.isoformat(),
                "horizon_end": horizon_end.isoformat(),
                "lookback_hours_observed": int(len(window)),
                "horizon_hours_observed": int(len(horizon)),
                "last_close": float(latest["close"]),
                "last_close_deviation_bps": float((latest["close"] - 1.0) * 10000),
                "lookback_min_close": float(window["close"].min()),
                "lookback_max_close": float(window["close"].max()),
                "lookback_mean_abs_close_deviation_bps": float(window["abs_close_deviation"].mean() * 10000),
                "lookback_max_abs_close_deviation_bps": float(window["abs_close_deviation"].max() * 10000),
                "lookback_max_period_deviation_bps": float(window["max_period_deviation"].max() * 10000),
                "lookback_volatility_7d": float(last_7d["return_1h"].std()),
                "lookback_volatility_30d": float(window["return_1h"].std()),
                "lookback_volume_usd_sum_30d": float(window["volume_usd"].sum()),
                "lookback_volume_change_7d": volume_change_7d,
                "lookback_market_cap_change_7d": first_last_change(last_7d["stablecoin_market_cap_usd"]),
                "lookback_supply_change_7d": first_last_change(last_7d["stablecoin_total_supply_usd"]),
                "latest_market_cap_usd": float(latest["stablecoin_market_cap_usd"]) if pd.notna(latest["stablecoin_market_cap_usd"]) else np.nan,
                "latest_circulating_supply_usd": float(latest["stablecoin_total_supply_usd"]) if pd.notna(latest["stablecoin_total_supply_usd"]) else np.nan,
                "latest_stablecoin_market_share": float(latest["stablecoin_market_share"]) if pd.notna(latest["stablecoin_market_share"]) else np.nan,
                "latest_chain_count": int(latest["chain_count"]) if pd.notna(latest["chain_count"]) else None,
                "latest_top_chain": latest["top_chain"] if pd.notna(latest["top_chain"]) else None,
                "latest_top_chain_share": float(latest["top_chain_share"]) if pd.notna(latest["top_chain_share"]) else np.nan,
                "peg_mechanism": latest["peg_mechanism"],
                "peg_type": latest["peg_type"],
                "btc_7d_return": float(latest["btc_7d_return"]) if pd.notna(latest["btc_7d_return"]) else np.nan,
                "eth_7d_return": float(latest["eth_7d_return"]) if pd.notna(latest["eth_7d_return"]) else np.nan,
                "btc_7d_volatility": float(latest["btc_7d_volatility"]) if pd.notna(latest["btc_7d_volatility"]) else np.nan,
                "eth_7d_volatility": float(latest["eth_7d_volatility"]) if pd.notna(latest["eth_7d_volatility"]) else np.nan,
                "actual_horizon_max_abs_close_deviation_bps": horizon_max_abs_bps,
                "actual_horizon_mean_abs_close_deviation_bps": horizon_mean_abs_bps,
                "actual_horizon_realized_volatility": float(horizon_returns.std()) if len(horizon_returns) else np.nan,
                "actual_horizon_min_close": float(horizon["close"].min()),
                "actual_horizon_max_close": float(horizon["close"].max()),
                "actual_direction": direction_from_horizon(horizon),
                "label_depeg_100bps_sustained_3h": bool(actual_depeg),
                "label_stress_50bps_any_close": bool(horizon_max_abs >= 0.005),
                "actual_price_stability_next_7d": status,
                "horizon_max_abs_deviation_bps": horizon_max_abs_bps,
                "horizon_mean_abs_deviation_bps": horizon_mean_abs_bps,
                "horizon_deviation_volatility_bps": horizon_vol_bps,
                "horizon_hours_ge_25bps": horizon_hours_ge_25,
                "horizon_hours_ge_50bps": horizon_hours_ge_50,
                "horizon_hours_ge_100bps": horizon_hours_ge_100,
                "horizon_max_consecutive_ge_100bps": horizon_max_consec_ge_100,
                "enhanced_direction": enhanced_direction,
                "enhanced_stability_label": enhanced_label,
                "enhanced_severe_depeg_100bps_3h": bool(enhanced_severe),
                "enhanced_watch_50bps_any_close": bool(horizon_max_abs_bps >= 50),
                "enhanced_near_stress": bool(enhanced_label == "stress" and not enhanced_severe),
            }
            case_rows.append(case)

            prompt_packets.append(
                {
                    "case_id": case_id,
                    "stablecoin": spec.symbol,
                    "stablecoin_name": spec.name,
                    "observation_time": observation.isoformat(),
                    "lookback_window": {
                        "start": lookback_start.isoformat(),
                        "end": observation.isoformat(),
                        "hours_observed": int(len(window)),
                    },
                    "forecast_horizon": {
                        "start": horizon_start.isoformat(),
                        "end": horizon_end.isoformat(),
                        "hours": horizon_hours,
                    },
                    "task": "Forecast seven-day stablecoin price stability and dollar-peg deviation using only this packet.",
                    "evidence": {
                        "peg_usd": 1.0,
                        "latest_observation": {
                            "close": case["last_close"],
                            "close_deviation_bps": case["last_close_deviation_bps"],
                            "market_cap_usd": case["latest_market_cap_usd"],
                            "circulating_supply_usd": case["latest_circulating_supply_usd"],
                            "stablecoin_market_share": case["latest_stablecoin_market_share"],
                            "chain_count": case["latest_chain_count"],
                            "top_chain": case["latest_top_chain"],
                            "top_chain_share": case["latest_top_chain_share"],
                            "peg_type": case["peg_type"],
                            "peg_mechanism": case["peg_mechanism"],
                        },
                        "lookback_summary": {
                            "min_close": case["lookback_min_close"],
                            "max_close": case["lookback_max_close"],
                            "mean_abs_close_deviation_bps": case["lookback_mean_abs_close_deviation_bps"],
                            "max_abs_close_deviation_bps": case["lookback_max_abs_close_deviation_bps"],
                            "max_period_deviation_bps": case["lookback_max_period_deviation_bps"],
                            "volatility_7d": case["lookback_volatility_7d"],
                            "volatility_30d": case["lookback_volatility_30d"],
                            "volume_usd_sum_30d": case["lookback_volume_usd_sum_30d"],
                            "volume_change_7d": case["lookback_volume_change_7d"],
                            "market_cap_change_7d": case["lookback_market_cap_change_7d"],
                            "supply_change_7d": case["lookback_supply_change_7d"],
                        },
                        "context": {
                            "btc_7d_return": case["btc_7d_return"],
                            "eth_7d_return": case["eth_7d_return"],
                            "btc_7d_volatility": case["btc_7d_volatility"],
                            "eth_7d_volatility": case["eth_7d_volatility"],
                        },
                        "daily_lookback_table": summarize_daily(window),
                        "last_48_hourly_observations": window.tail(48)[
                            [
                                "timestamp",
                                "open",
                                "high",
                                "low",
                                "close",
                                "volume_usd",
                                "abs_close_deviation",
                                "max_period_deviation",
                            ]
                        ].assign(timestamp=lambda x: x["timestamp"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")).to_dict("records"),
                    },
                }
            )
            long_cols = [
                "timestamp",
                "stablecoin",
                "open",
                "high",
                "low",
                "close",
                "volume_base",
                "volume_usd",
                "close_deviation",
                "abs_close_deviation",
                "max_period_deviation",
                "hourly_range",
                "return_1h",
                "stablecoin_market_cap_usd",
                "stablecoin_total_supply_usd",
                "stablecoin_market_share",
                "chain_count",
                "top_chain",
                "top_chain_share",
                "btc_7d_return",
                "eth_7d_return",
                "btc_7d_volatility",
                "eth_7d_volatility",
            ]
            lookback_long = window[long_cols].copy()
            lookback_long.insert(0, "case_id", case_id)
            lookback_long.insert(1, "period", "lookback")
            lookback_long.insert(2, "relative_hour", range(-len(lookback_long) + 1, 1))
            horizon_long = horizon[long_cols].copy()
            horizon_long.insert(0, "case_id", case_id)
            horizon_long.insert(1, "period", "horizon")
            horizon_long.insert(2, "relative_hour", range(1, len(horizon_long) + 1))
            long_parts.append(pd.concat([lookback_long, horizon_long], ignore_index=True))
        observation += stride

    cases = pd.DataFrame(case_rows)
    labels = cases[
        [
            "case_id",
            "stablecoin",
            "observation_time",
            "horizon_start",
            "horizon_end",
            "actual_horizon_max_abs_close_deviation_bps",
            "actual_horizon_mean_abs_close_deviation_bps",
            "actual_horizon_realized_volatility",
            "actual_horizon_min_close",
            "actual_horizon_max_close",
            "actual_direction",
            "label_depeg_100bps_sustained_3h",
            "label_stress_50bps_any_close",
            "actual_price_stability_next_7d",
            "horizon_max_abs_deviation_bps",
            "horizon_mean_abs_deviation_bps",
            "horizon_deviation_volatility_bps",
            "horizon_hours_ge_25bps",
            "horizon_hours_ge_50bps",
            "horizon_hours_ge_100bps",
            "horizon_max_consecutive_ge_100bps",
            "enhanced_direction",
            "enhanced_stability_label",
            "enhanced_severe_depeg_100bps_3h",
            "enhanced_watch_50bps_any_close",
            "enhanced_near_stress",
        ]
    ].copy()
    long_windows = pd.concat(long_parts, ignore_index=True) if long_parts else pd.DataFrame()
    return cases, prompt_packets, labels, long_windows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", default="2023-01-01")
    parser.add_argument("--end", default="2026-05-01")
    parser.add_argument("--lookback-days", type=int, default=30)
    parser.add_argument("--horizon-days", type=int, default=7)
    parser.add_argument("--stride-days", type=int, default=7)
    parser.add_argument("--data-dir", default="data")
    args = parser.parse_args()

    start = utc_dt(args.start)
    end = utc_dt(args.end, end_of_day=True)
    data_dir = Path(args.data_dir)
    raw_dir = data_dir / "raw"
    interim_dir = data_dir / "interim"
    benchmark_dir = data_dir / "benchmark"
    for directory in [raw_dir, interim_dir, benchmark_dir]:
        directory.mkdir(parents=True, exist_ok=True)

    stable_frames = []
    context_frames = []
    for spec in STABLECOINS:
        path = raw_dir / f"cryptocompare_histohour_{spec.symbol}_USD.csv"
        if path.exists():
            frame = pd.read_csv(path)
            frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)
        else:
            frame = fetch_cryptocompare_histohour(spec.symbol, start, end)
            frame.to_csv(path, index=False)
        stable_frames.append(frame)
        print(f"{spec.symbol}: {len(frame)} hourly rows")

    for symbol in CONTEXT_SYMBOLS:
        path = raw_dir / f"cryptocompare_histohour_{symbol}_USD.csv"
        if path.exists():
            frame = pd.read_csv(path)
            frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)
        else:
            frame = fetch_cryptocompare_histohour(symbol, start, end)
            frame.to_csv(path, index=False)
        context_frames.append(frame)
        print(f"{symbol}: {len(frame)} hourly rows")

    metadata_path = interim_dir / "defillama_stablecoin_daily_metadata.csv"
    sector_path = interim_dir / "defillama_sector_daily.csv"
    if metadata_path.exists() and sector_path.exists():
        stablecoin_metadata = pd.read_csv(metadata_path)
        sector = pd.read_csv(sector_path)
    else:
        stablecoin_metadata, sector, _ = fetch_defillama_metadata(raw_dir)
        stablecoin_metadata.to_csv(metadata_path, index=False)
        sector.to_csv(sector_path, index=False)

    hourly = add_hourly_features(pd.concat(stable_frames, ignore_index=True), stablecoin_metadata)
    context = add_context_features(pd.concat(context_frames, ignore_index=True))
    hourly.to_csv(interim_dir / "stablecoin_hourly_features.csv", index=False)
    context.to_csv(interim_dir / "btc_eth_hourly_context.csv", index=False)

    cases, prompt_packets, labels, long_windows = build_cases(
        hourly,
        context,
        start=start,
        end=end,
        lookback_days=args.lookback_days,
        horizon_days=args.horizon_days,
        stride_days=args.stride_days,
    )
    release_dir = benchmark_dir / "stableeval_507_natural"
    release_dir.mkdir(parents=True, exist_ok=True)

    cases.to_csv(release_dir / "full_case_pool.csv", index=False)
    labels.to_csv(release_dir / "labels.csv", index=False)
    long_windows.to_csv(release_dir / "full_hourly_windows.csv.gz", index=False, compression="gzip")
    with (release_dir / "prompt_packets_base.jsonl").open("w", encoding="utf-8") as handle:
        for packet in prompt_packets:
            handle.write(json.dumps(packet, ensure_ascii=False, default=str) + "\n")

    summary = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_start": args.start,
        "source_end": args.end,
        "frequency": "hourly price/volume; daily market-structure metadata joined by date",
        "stablecoins": [spec.symbol for spec in STABLECOINS],
        "context_symbols": CONTEXT_SYMBOLS,
        "lookback_days": args.lookback_days,
        "horizon_days": args.horizon_days,
        "stride_days": args.stride_days,
        "raw_hourly_rows_stablecoins": int(sum(len(x) for x in stable_frames)),
        "raw_hourly_rows_context": int(sum(len(x) for x in context_frames)),
        "processed_hourly_rows": int(len(hourly)),
        "frozen_window_cases": int(len(cases)),
        "depeg_100bps_sustained_3h_positive_rate": float(labels["label_depeg_100bps_sustained_3h"].mean()) if len(labels) else None,
        "stress_50bps_any_close_positive_rate": float(labels["label_stress_50bps_any_close"].mean()) if len(labels) else None,
        "enhanced_label_distribution": labels["enhanced_stability_label"].value_counts().to_dict() if len(labels) else {},
        "outputs": {
            "hourly_features": "data/interim/stablecoin_hourly_features.csv",
            "cases": "data/benchmark/stableeval_507_natural/full_case_pool.csv",
            "frozen_window_hourly_long": "data/benchmark/stableeval_507_natural/full_hourly_windows.csv.gz",
            "labels": "data/benchmark/stableeval_507_natural/labels.csv",
            "base_prompt_packets": "data/benchmark/stableeval_507_natural/prompt_packets_base.jsonl",
        },
    }
    (release_dir / "dataset_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
