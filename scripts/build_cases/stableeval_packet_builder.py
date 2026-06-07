"""Shared packet builder for the StableEval release protocol."""

from __future__ import annotations

import copy
from typing import Any

import pandas as pd


def _num(value: Any, default: float = 0.0) -> float:
    try:
        value = float(value)
    except (TypeError, ValueError):
        return default
    if pd.isna(value):
        return default
    return value


def _pct_change(new: float, old: float) -> float:
    if old == 0 or pd.isna(old):
        return 0.0
    return (new - old) / abs(old)


def _max_consecutive(mask: pd.Series) -> int:
    best = cur = 0
    for item in mask.astype(bool).tolist():
        if item:
            cur += 1
            best = max(best, cur)
        else:
            cur = 0
    return int(best)


def _mechanism_note(stablecoin: str) -> str:
    notes = {
        "USDT": "Centralized issuer-backed stablecoin; sensitive to issuer liquidity, redemption confidence, exchange liquidity, and market confidence risk.",
        "USDC": "Centralized issuer-backed stablecoin; sensitive to reserve, redemption, banking confidence, and liquidity stress.",
        "DAI": "Collateralized/decentralized stablecoin; sensitive to DeFi collateral conditions, USDC exposure, ETH/BTC stress, and on-chain liquidity.",
    }
    return notes.get(stablecoin, "Dollar-referenced stablecoin; evaluate peg stability, liquidity, volume, and market stress evidence.")


def build_risk_features(group: pd.DataFrame, packet: dict[str, Any]) -> dict[str, Any]:
    """Compute lookback-only risk features used by the revised prompt packet."""
    if group.empty:
        raise ValueError("Cannot build risk features from an empty lookback group.")

    group = group.copy().sort_values("timestamp")
    last7 = group.tail(168)
    prior7 = group.iloc[-336:-168] if len(group) >= 336 else group.iloc[:0]
    last24 = group.tail(24)
    prior7_for_trend = group.iloc[-192:-24] if len(group) >= 192 else group.iloc[:0]

    close_dev_bps = group["close_deviation"].astype(float) * 10000.0
    abs_dev_bps = group["abs_close_deviation"].astype(float) * 10000.0
    abs_dev_7d = last7["abs_close_deviation"].astype(float) * 10000.0
    close_dev_7d = last7["close_deviation"].astype(float) * 10000.0
    period_range_7d = last7["max_period_deviation"].astype(float) * 10000.0

    latest = group.iloc[-1]
    latest_close = _num(latest.get("close"))
    latest_dev = _num(latest.get("close_deviation")) * 10000.0
    latest_abs = abs(latest_dev)

    volume_7d = float(last7["volume_usd"].fillna(0).sum())
    prior_volume_7d = float(prior7["volume_usd"].fillna(0).sum()) if not prior7.empty else 0.0
    volume_30d_avg_7d = float(group["volume_usd"].fillna(0).sum()) / max(len(group) / 168.0, 1.0)

    cap_first_7d = _num(last7["stablecoin_market_cap_usd"].dropna().iloc[0]) if last7["stablecoin_market_cap_usd"].notna().any() else 0.0
    cap_last = _num(last7["stablecoin_market_cap_usd"].dropna().iloc[-1]) if last7["stablecoin_market_cap_usd"].notna().any() else 0.0
    supply_first_7d = _num(last7["stablecoin_total_supply_usd"].dropna().iloc[0]) if last7["stablecoin_total_supply_usd"].notna().any() else 0.0
    supply_last = _num(last7["stablecoin_total_supply_usd"].dropna().iloc[-1]) if last7["stablecoin_total_supply_usd"].notna().any() else 0.0
    cap_first_30d = _num(group["stablecoin_market_cap_usd"].dropna().iloc[0]) if group["stablecoin_market_cap_usd"].notna().any() else 0.0
    supply_first_30d = _num(group["stablecoin_total_supply_usd"].dropna().iloc[0]) if group["stablecoin_total_supply_usd"].notna().any() else 0.0

    trend_last24 = float((last24["close_deviation"].astype(float).abs() * 10000.0).mean()) if not last24.empty else 0.0
    trend_prior = float((prior7_for_trend["close_deviation"].astype(float).abs() * 10000.0).mean()) if not prior7_for_trend.empty else 0.0

    stablecoin = str(packet.get("stablecoin", latest.get("stablecoin", "")))
    btc_ret = _num(latest.get("btc_7d_return"))
    eth_ret = _num(latest.get("eth_7d_return"))
    btc_vol = _num(latest.get("btc_7d_volatility"))
    eth_vol = _num(latest.get("eth_7d_volatility"))

    risk = {
        "protocol_note": "All values in this risk summary are computed only from the 30-day lookback window.",
        "latest_close_price": latest_close,
        "latest_deviation_bps": latest_dev,
        "latest_abs_deviation_bps": latest_abs,
        "lookback_7d_max_abs_deviation_bps": float(abs_dev_7d.max()),
        "lookback_30d_max_abs_deviation_bps": float(abs_dev_bps.max()),
        "lookback_7d_mean_abs_deviation_bps": float(abs_dev_7d.mean()),
        "lookback_30d_mean_abs_deviation_bps": float(abs_dev_bps.mean()),
        "lookback_7d_hours_above_25bps": int((abs_dev_7d >= 25).sum()),
        "lookback_7d_hours_above_50bps": int((abs_dev_7d >= 50).sum()),
        "lookback_7d_hours_above_100bps": int((abs_dev_7d >= 100).sum()),
        "lookback_30d_hours_above_25bps": int((abs_dev_bps >= 25).sum()),
        "lookback_30d_hours_above_50bps": int((abs_dev_bps >= 50).sum()),
        "lookback_30d_hours_above_100bps": int((abs_dev_bps >= 100).sum()),
        "lookback_7d_max_consecutive_above_50bps": _max_consecutive(abs_dev_7d >= 50),
        "lookback_30d_max_consecutive_above_100bps": _max_consecutive(abs_dev_bps >= 100),
        "lookback_7d_deviation_volatility_bps": float(close_dev_7d.std(ddof=0)),
        "lookback_30d_deviation_volatility_bps": float(close_dev_bps.std(ddof=0)),
        "recent_deviation_trend_bps_last24_minus_prior7d": trend_last24 - trend_prior,
        "recent_high_low_range_max_bps_7d": float(period_range_7d.max()),
        "recent_high_low_range_mean_bps_7d": float(period_range_7d.mean()),
        "volume_usd_change_7d_vs_prior7d": _pct_change(volume_7d, prior_volume_7d),
        "volume_usd_change_7d_vs_30d_average": _pct_change(volume_7d, volume_30d_avg_7d),
        "market_cap_change_7d": _pct_change(cap_last, cap_first_7d),
        "supply_change_7d": _pct_change(supply_last, supply_first_7d),
        "market_cap_change_30d": _pct_change(cap_last, cap_first_30d),
        "supply_change_30d": _pct_change(supply_last, supply_first_30d),
        "btc_7d_return": btc_ret,
        "eth_7d_return": eth_ret,
        "btc_7d_volatility": btc_vol,
        "eth_7d_volatility": eth_vol,
        "mechanism_note": _mechanism_note(stablecoin),
    }
    risk["risk_flags"] = {
        "recent_close_deviation_ge_25bps": bool(latest_abs >= 25),
        "lookback_7d_any_50bps_close_deviation": bool(risk["lookback_7d_hours_above_50bps"] > 0),
        "lookback_30d_any_100bps_close_deviation": bool(risk["lookback_30d_hours_above_100bps"] > 0),
        "lookback_7d_repeated_25bps_close_deviation": bool(risk["lookback_7d_hours_above_25bps"] >= 3),
        "high_recent_range": bool(risk["recent_high_low_range_max_bps_7d"] >= 100),
        "rising_recent_deviation": bool(risk["recent_deviation_trend_bps_last24_minus_prior7d"] >= 5),
        "large_volume_shift": bool(abs(risk["volume_usd_change_7d_vs_prior7d"]) >= 0.5),
        "large_supply_or_market_cap_shift": bool(
            abs(risk["market_cap_change_7d"]) >= 0.03 or abs(risk["supply_change_7d"]) >= 0.03
        ),
        "btc_or_eth_stress": bool(btc_ret <= -0.10 or eth_ret <= -0.10 or btc_vol >= 0.05 or eth_vol >= 0.05),
    }
    return risk


def improved_packet(packet: dict[str, Any], risk: dict[str, Any]) -> dict[str, Any]:
    """Attach the revised risk-sensitive lookback summary to a base packet."""
    out = copy.deepcopy(packet)
    out["task"] = "Forecast seven-day stablecoin price stability and dollar-peg deviation using only this packet."
    out["risk_sensitive_evidence"] = risk
    return out
