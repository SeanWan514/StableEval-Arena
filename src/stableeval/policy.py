"""Shared deterministic policy used when no LLM API key is available.

The policy is intentionally conservative. It is not presented as an LLM result;
it is an executable, reproducible backend that lets every platform adapter run
against the same prompt packets when model-provider credentials are absent.
"""

from __future__ import annotations

import json
import math
import re
from typing import Any


def number(value: Any, default: float = 0.0) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return default
    if math.isnan(out) or math.isinf(out):
        return default
    return out


def token_count_approx(text: str) -> int:
    return len(re.findall(r"\w+|[^\w\s]", text, flags=re.UNICODE))


def prompt_text(system_prompt: str, packet: dict[str, Any]) -> str:
    return system_prompt.strip() + "\n\nFrozen evidence packet:\n" + json.dumps(
        packet, sort_keys=True, ensure_ascii=False
    )


def generate_prediction(packet: dict[str, Any], platform: str = "deterministic") -> dict[str, Any]:
    evidence = packet.get("evidence", {})
    latest = evidence.get("latest_observation", {})
    lookback = evidence.get("lookback_summary", {})
    context = evidence.get("context", {})

    last_dev_bps = abs(number(latest.get("close_deviation_bps")))
    signed_last_dev_bps = number(latest.get("close_deviation_bps"))
    max_abs_bps = number(lookback.get("max_abs_close_deviation_bps"))
    mean_abs_bps = number(lookback.get("mean_abs_close_deviation_bps"))
    max_period_bps = number(lookback.get("max_period_deviation_bps"))
    vol_7d = number(lookback.get("volatility_7d"))
    vol_30d = number(lookback.get("volatility_30d"))
    volume_change = number(lookback.get("volume_change_7d"))
    market_cap_change = number(lookback.get("market_cap_change_7d"))
    supply_change = number(lookback.get("supply_change_7d"))
    btc_7d_return = number(context.get("btc_7d_return"))
    eth_7d_return = number(context.get("eth_7d_return"))
    peg_mechanism = str(latest.get("peg_mechanism") or "").lower()

    risk = 0.005
    risk += min(max_abs_bps / 100.0, 1.0) * 0.025
    risk += min(mean_abs_bps / 35.0, 1.0) * 0.035
    risk += min(last_dev_bps / 50.0, 1.0) * 0.025
    risk += min(max(vol_7d, vol_30d) * 90.0, 0.05)
    if max_period_bps >= 250 and max_abs_bps >= 75:
        risk += 0.015
    if volume_change > 1.0:
        risk += 0.02
    if market_cap_change < -0.03 or supply_change < -0.03:
        risk += 0.05
    if market_cap_change < -0.08 or supply_change < -0.08:
        risk += 0.08
    if "crypto" in peg_mechanism:
        risk += 0.02
    if btc_7d_return < -0.10 or eth_7d_return < -0.10:
        risk += 0.03
    if max_abs_bps >= 150 and mean_abs_bps >= 25:
        risk += 0.06
    p_depeg = max(0.001, min(risk, 0.85))

    predicted_max_bps = max(
        2.5,
        0.18 * max_abs_bps
        + 0.04 * max_period_bps
        + 1.8 * mean_abs_bps
        + 0.7 * last_dev_bps
        + 25000.0 * max(vol_7d, vol_30d),
    )
    predicted_max_bps = min(predicted_max_bps, 500.0)

    if p_depeg >= 0.30 or predicted_max_bps >= 150 or (max_abs_bps >= 200 and mean_abs_bps >= 40):
        status = "stress"
    elif p_depeg >= 0.12 or predicted_max_bps >= 75 or mean_abs_bps >= 15 or last_dev_bps >= 25:
        status = "watch"
    else:
        status = "stable"

    if abs(signed_last_dev_bps) >= 10:
        direction = "below_peg" if signed_last_dev_bps < 0 else "above_peg"
    elif max_abs_bps < 25:
        direction = "two_sided_or_no_meaningful"
    else:
        direction = "two_sided_or_no_meaningful"

    confidence = 0.55
    if max_abs_bps < 25 and abs(market_cap_change) < 0.02:
        confidence += 0.12
    if max_abs_bps >= 100 or abs(market_cap_change) > 0.05:
        confidence -= 0.08
    confidence = max(0.30, min(confidence, 0.85))

    rationale_parts = [
        f"30-day max close deviation was {max_abs_bps:.1f} bps",
        f"latest close deviation was {signed_last_dev_bps:.1f} bps",
        f"7-day market-cap change was {market_cap_change:.2%}",
    ]
    if btc_7d_return or eth_7d_return:
        rationale_parts.append(f"BTC/ETH 7-day returns were {btc_7d_return:.2%}/{eth_7d_return:.2%}")

    return {
        "price_stability_next_7d": status,
        "p_depeg_next_7d": round(p_depeg, 4),
        "predicted_max_abs_deviation_bps": round(predicted_max_bps, 2),
        "predicted_direction": direction,
        "confidence": round(confidence, 3),
        "rationale": "; ".join(rationale_parts) + ".",
        "evidence_used": [
            "price deviation",
            "volatility",
            "volume",
            "market structure",
            "BTC/ETH context",
        ],
        "backend": "deterministic_conservative_policy_no_llm_key",
        "platform_adapter": platform,
    }
