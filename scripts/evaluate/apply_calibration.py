#!/usr/bin/env python3
"""Create calibrated prediction JSONL files from raw StableEval prediction files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def calibrated_label(prediction: dict[str, Any]) -> str:
    p = max(0.0, min(1.0, as_float(prediction.get("p_depeg_next_7d"))))
    bps = max(0.0, as_float(prediction.get("predicted_max_abs_deviation_bps")))
    if bps >= 100 or (p >= 0.35 and bps >= 75):
        return "stress"
    if p >= 0.15 or bps >= 40:
        return "watch"
    return "stable"


def calibrate_record(record: dict[str, Any]) -> dict[str, Any]:
    out = dict(record)
    prediction = dict(out.get("parsed_json") or out.get("prediction") or {})
    if prediction:
        original = prediction.get("price_stability_next_7d", "")
        prediction["original_price_stability_next_7d"] = original
        prediction["price_stability_next_7d"] = calibrated_label(prediction)
        prediction["label_calibration"] = "risk_sensitive_v1_posthoc_frozen"
        out["parsed_json"] = prediction
        out["prediction"] = prediction
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    for stale in output_dir.glob("*_predictions.jsonl"):
        stale.unlink()

    count = 0
    for path in sorted(input_dir.glob("*_predictions.jsonl")):
        output_path = output_dir / path.name
        with path.open("r", encoding="utf-8") as src, output_path.open("w", encoding="utf-8") as dst:
            for line in src:
                if not line.strip():
                    continue
                dst.write(json.dumps(calibrate_record(json.loads(line)), ensure_ascii=False) + "\n")
                count += 1
    print(json.dumps({"calibrated_records": count, "output_dir": str(output_dir)}, indent=2))


if __name__ == "__main__":
    main()
