#!/usr/bin/env python3
"""Recompute StableEval-120-Enriched saved-output metrics without APIs.

This release verifier reads saved predictions and labels from the cleaned
two-block repository tree and writes recomputed artifacts only to --out. It does
not overwrite canonical result files.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from evaluate_predictions import (  # noqa: E402
    attach_actuals,
    baseline_records,
    dataframe_without_matrices,
    load_agent_predictions,
    load_packets,
    ml_pilot_predictions,
    score_system,
)


DEFAULT_OUT = Path("/tmp/stableeval_release_audit/stableeval_120_enriched_recompute")
COMPARE_COLUMNS = [
    "cases",
    "valid_json_rate",
    "failure_rate",
    "invalid_output_rate",
    "total_estimated_cost_usd",
    "taskA_accuracy",
    "taskA_macro_f1",
    "taskA_balanced_accuracy",
    "taskA_recall_stress",
    "binary_precision",
    "binary_recall",
    "binary_auroc",
    "binary_average_precision",
    "binary_brier_score",
    "missed_depeg_rate",
    "false_alarm_rate",
    "deviation_mae_bps",
    "deviation_rmse_bps",
]


def rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def finite_delta(left: Any, right: Any) -> float | None:
    a = pd.to_numeric(pd.Series([left]), errors="coerce").iloc[0]
    b = pd.to_numeric(pd.Series([right]), errors="coerce").iloc[0]
    if pd.isna(a) and pd.isna(b):
        return 0.0
    if pd.isna(a) or pd.isna(b):
        return None
    return float(a) - float(b)


def compare_tables(recomputed: pd.DataFrame, canonical: pd.DataFrame, tolerance: float) -> tuple[pd.DataFrame, dict[str, Any]]:
    recomputed = recomputed.set_index("system", drop=False)
    canonical = canonical.set_index("system", drop=False)
    missing = sorted(set(canonical.index) - set(recomputed.index))
    extra = sorted(set(recomputed.index) - set(canonical.index))
    rows: list[dict[str, Any]] = []
    max_abs_delta = 0.0
    deltas_over_tolerance = 0
    for system in sorted(set(canonical.index) & set(recomputed.index)):
        for column in COMPARE_COLUMNS:
            if column not in canonical.columns or column not in recomputed.columns:
                continue
            delta = finite_delta(recomputed.at[system, column], canonical.at[system, column])
            if delta is None:
                status = "non_numeric_or_one_missing"
                abs_delta = math.nan
            else:
                abs_delta = abs(delta)
                max_abs_delta = max(max_abs_delta, abs_delta)
                status = "PASS" if abs_delta <= tolerance else "FAIL"
                if status == "FAIL":
                    deltas_over_tolerance += 1
            rows.append(
                {
                    "system": system,
                    "column": column,
                    "recomputed": recomputed.at[system, column],
                    "canonical": canonical.at[system, column],
                    "delta": delta,
                    "abs_delta": abs_delta,
                    "status": status,
                }
            )
    summary = {
        "systems_recomputed": int(len(recomputed)),
        "systems_in_canonical": int(len(canonical)),
        "missing_systems": missing,
        "extra_systems": extra,
        "numeric_tolerance": tolerance,
        "max_abs_numeric_delta": max_abs_delta,
        "deltas_over_tolerance": deltas_over_tolerance,
        "passed": not missing and not extra and deltas_over_tolerance == 0,
    }
    return pd.DataFrame(rows), summary


def build_recomputed(root: Path, labels: Path, pilot_labels: Path, packets: Path, pred_dir: Path) -> pd.DataFrame:
    all_labels = pd.read_csv(labels)
    selected = pd.read_csv(pilot_labels)
    selected_ids = set(selected["case_id"])
    pilot = all_labels[all_labels["case_id"].isin(selected_ids)].reset_index(drop=True)
    packet_map = load_packets(packets)

    prediction_frames = [
        attach_actuals(baseline_records(pilot, packet_map, "always_stable"), pilot),
        attach_actuals(baseline_records(pilot, packet_map, "historical_persistence"), pilot),
        attach_actuals(baseline_records(pilot, packet_map, "threshold_rule"), pilot),
        attach_actuals(ml_pilot_predictions(all_labels, pilot, packet_map), pilot),
        attach_actuals(load_agent_predictions(pred_dir, pilot), pilot),
    ]
    raw = pd.concat(prediction_frames, ignore_index=True)
    rows = [score_system(raw, system) for system in sorted(raw["system"].dropna().unique())]
    quality = dataframe_without_matrices(rows)
    return quality.sort_values(["system_type", "taskA_macro_f1"], ascending=[True, False]).reset_index(drop=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--labels", default="data/benchmark/stableeval_507_natural/labels.csv")
    parser.add_argument("--pilot-labels", default="results/stableeval_120_enriched/validation_case_list.csv")
    parser.add_argument("--packets", default="data/benchmark/stableeval_507_natural/prompt_packets.jsonl")
    parser.add_argument("--pred-dir", default="results/stableeval_120_enriched/predictions_base_calibrated")
    parser.add_argument(
        "--canonical-quality",
        default="results/stableeval_120_enriched/evaluation_base_calibrated/prediction_quality_by_platform.csv",
    )
    parser.add_argument("--tolerance", type=float, default=1e-3)
    args = parser.parse_args()

    root = Path(args.root).resolve()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)

    quality = build_recomputed(
        root=root,
        labels=root / args.labels,
        pilot_labels=root / args.pilot_labels,
        packets=root / args.packets,
        pred_dir=root / args.pred_dir,
    )
    quality_path = out / "stableeval_120_enriched_recomputed_prediction_quality.csv"
    quality.to_csv(quality_path, index=False)

    canonical_path = root / args.canonical_quality
    canonical = pd.read_csv(canonical_path)
    deltas, summary = compare_tables(quality, canonical, args.tolerance)
    deltas.to_csv(out / "stableeval_120_enriched_metric_deltas.csv", index=False)
    summary.update(
        {
            "out_dir": str(out),
            "recomputed_quality": rel(quality_path, root),
            "canonical_quality": rel(canonical_path, root),
        }
    )
    (out / "comparison_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    if not summary["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
