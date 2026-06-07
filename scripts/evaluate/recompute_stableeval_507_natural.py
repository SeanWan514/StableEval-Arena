#!/usr/bin/env python3
"""Recompute StableEval-507-Natural saved-output metrics without API calls.

This release verifier reads the cleaned 507 labels, baseline predictions, and
six-system raw/calibrated JSONL outputs. It writes recomputed tables to an
output directory only; it never overwrites canonical repository results.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any


CLASS_ORDER = ["stable", "watch", "stress"]
LEADERBOARD_COLUMNS = [
    "system",
    "agent_type",
    "system_type",
    "execution_mode",
    "output_variant",
    "cases",
    "accuracy",
    "macro_f1",
    "balanced_accuracy",
    "stable_recall",
    "watch_recall",
    "stress_recall",
    "missed_depeg_rate",
    "false_alarm_rate",
    "brier_score",
    "maxdev_mae_bps",
    "maxdev_rmse_bps",
    "valid_json_rate",
    "failure_rate",
    "total_cost_usd",
    "cost_per_case_usd",
    "mean_latency_seconds",
    "notes",
    "execution_group",
]
NUMERIC_COLUMNS = [
    "cases",
    "accuracy",
    "macro_f1",
    "balanced_accuracy",
    "stable_recall",
    "watch_recall",
    "stress_recall",
    "missed_depeg_rate",
    "false_alarm_rate",
    "brier_score",
    "maxdev_mae_bps",
    "maxdev_rmse_bps",
    "valid_json_rate",
    "failure_rate",
    "total_cost_usd",
    "cost_per_case_usd",
    "mean_latency_seconds",
]


def as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def as_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def safe_div(num: float, den: float) -> float:
    return float(num / den) if den else 0.0


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in columns})


def load_labels(path: Path) -> dict[str, dict[str, Any]]:
    labels: dict[str, dict[str, Any]] = {}
    for row in read_csv(path):
        labels[str(row["case_id"])] = {
            "stablecoin": row["stablecoin"],
            "label": row["enhanced_stability_label"],
            "strict_depeg": as_bool(row["enhanced_severe_depeg_100bps_3h"]),
            "maxdev_bps": as_float(row["horizon_max_abs_deviation_bps"]),
        }
    return labels


def prediction_from_record(record: dict[str, Any]) -> dict[str, Any]:
    prediction = record.get("parsed_json") or record.get("prediction") or {}
    if isinstance(prediction, str):
        try:
            prediction = json.loads(prediction)
        except json.JSONDecodeError:
            prediction = {}
    return prediction if isinstance(prediction, dict) else {}


def load_agent_records(path: Path, labels: dict[str, dict[str, Any]], system: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            record = json.loads(line)
            case_id = str(record.get("case_id") or "")
            actual = labels.get(case_id)
            if actual is None:
                continue
            prediction = prediction_from_record(record)
            valid = bool(record.get("valid_json") or record.get("valid_output"))
            error = str(record.get("error_message") or record.get("error") or "")
            rows.append(
                {
                    "system": system,
                    "case_id": case_id,
                    "actual_label": actual["label"],
                    "actual_strict_depeg": actual["strict_depeg"],
                    "actual_maxdev_bps": actual["maxdev_bps"],
                    "predicted_label": prediction.get("price_stability_next_7d"),
                    "predicted_probability": as_float(prediction.get("p_depeg_next_7d")),
                    "predicted_maxdev_bps": as_float(prediction.get("predicted_max_abs_deviation_bps")),
                    "valid_json": valid,
                    "failure": (not valid) or bool(error),
                    "estimated_cost_usd": as_float(record.get("estimated_cost_usd")),
                    "latency_seconds": as_float(record.get("latency_seconds")),
                    "execution_mode": record.get("execution_mode") or record.get("framework_execution_mode") or "",
                }
            )
    return rows


def load_baseline_records(path: Path) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in read_csv(path):
        system = row["system"]
        grouped.setdefault(system, []).append(
            {
                "system": system,
                "case_id": row["case_id"],
                "actual_label": row["actual_label"],
                "actual_strict_depeg": as_bool(row["actual_sustained_depeg"]),
                "actual_maxdev_bps": as_float(row["actual_max_abs_deviation_bps"]),
                "predicted_label": row["predicted_label"],
                "predicted_probability": as_float(row["predicted_probability"]),
                "predicted_maxdev_bps": as_float(row["predicted_max_abs_deviation_bps"]),
                "valid_json": as_bool(row["valid_json"]),
                "failure": as_bool(row["failure"]),
                "estimated_cost_usd": as_float(row["estimated_cost_usd"]),
                "latency_seconds": as_float(row["latency_seconds"]),
                "execution_mode": row["execution_mode"],
            }
        )
    return grouped


def multiclass_metrics(rows: list[dict[str, Any]]) -> dict[str, float]:
    recalls = []
    f1s = []
    output: dict[str, float] = {}
    correct = 0
    for label in CLASS_ORDER:
        tp = sum(1 for row in rows if row["actual_label"] == label and row["predicted_label"] == label)
        actual_total = sum(1 for row in rows if row["actual_label"] == label)
        pred_total = sum(1 for row in rows if row["predicted_label"] == label)
        precision = safe_div(tp, pred_total)
        recall = safe_div(tp, actual_total)
        f1 = safe_div(2 * precision * recall, precision + recall)
        recalls.append(recall)
        f1s.append(f1)
        output[f"{label}_recall"] = recall
    correct = sum(1 for row in rows if row["actual_label"] == row["predicted_label"])
    output["accuracy"] = safe_div(correct, len(rows))
    output["macro_f1"] = sum(f1s) / len(f1s)
    output["balanced_accuracy"] = sum(recalls) / len(recalls)
    return output


def binary_metrics(rows: list[dict[str, Any]]) -> dict[str, float]:
    tp = tn = fp = fn = 0
    brier_total = 0.0
    for row in rows:
        actual = 1 if row["actual_strict_depeg"] else 0
        score = max(0.0, min(1.0, as_float(row["predicted_probability"])))
        pred = 1 if score >= 0.5 else 0
        brier_total += (score - actual) ** 2
        if actual and pred:
            tp += 1
        elif actual and not pred:
            fn += 1
        elif not actual and pred:
            fp += 1
        else:
            tn += 1
    return {
        "missed_depeg_rate": safe_div(fn, fn + tp),
        "false_alarm_rate": safe_div(fp, fp + tn),
        "brier_score": safe_div(brier_total, len(rows)),
    }


def deviation_metrics(rows: list[dict[str, Any]]) -> dict[str, float]:
    errors = [as_float(row["predicted_maxdev_bps"]) - as_float(row["actual_maxdev_bps"]) for row in rows]
    abs_errors = [abs(error) for error in errors]
    return {
        "maxdev_mae_bps": safe_div(sum(abs_errors), len(abs_errors)),
        "maxdev_rmse_bps": math.sqrt(safe_div(sum(error * error for error in errors), len(errors))),
    }


def score_rows(rows: list[dict[str, Any]], metadata: dict[str, str]) -> dict[str, Any]:
    total_cost = sum(as_float(row["estimated_cost_usd"]) for row in rows)
    result: dict[str, Any] = {
        "system": metadata["system"],
        "agent_type": metadata["agent_type"],
        "system_type": metadata["system_type"],
        "execution_mode": metadata["execution_mode"] or (rows[0]["execution_mode"] if rows else ""),
        "output_variant": metadata["output_variant"],
        "cases": len(rows),
        "valid_json_rate": safe_div(sum(1 for row in rows if row["valid_json"]), len(rows)),
        "failure_rate": safe_div(sum(1 for row in rows if row["failure"]), len(rows)),
        "total_cost_usd": total_cost,
        "cost_per_case_usd": safe_div(total_cost, len(rows)),
        "mean_latency_seconds": safe_div(sum(as_float(row["latency_seconds"]) for row in rows), len(rows)),
        "notes": metadata["notes"],
        "execution_group": metadata["execution_group"],
    }
    result.update(multiclass_metrics(rows))
    result.update(binary_metrics(rows))
    result.update(deviation_metrics(rows))
    return result


def canonical_metadata(path: Path) -> tuple[list[str], dict[str, dict[str, str]]]:
    rows = read_csv(path)
    order = [row["system"] for row in rows]
    metadata = {
        row["system"]: {
            "system": row["system"],
            "agent_type": row["agent_type"],
            "system_type": row["system_type"],
            "execution_mode": row["execution_mode"],
            "output_variant": row["output_variant"],
            "notes": row["notes"],
            "execution_group": row["execution_group"],
        }
        for row in rows
    }
    return order, metadata


def agent_prediction_files(root: Path) -> list[tuple[Path, str]]:
    files: list[tuple[Path, str]] = []
    raw_root = root / "results/stableeval_507_natural/raw_predictions"
    cal_root = root / "results/stableeval_507_natural/calibrated_predictions"
    for system_dir in sorted(raw_root.iterdir()):
        if system_dir.is_dir():
            matches = sorted(system_dir.glob("*_complete.jsonl"))
            if matches:
                files.append((matches[0], f"{system_dir.name}_raw"))
    for system_dir in sorted(cal_root.iterdir()):
        if system_dir.is_dir():
            matches = sorted(system_dir.glob("*_predictions.jsonl"))
            if matches:
                files.append((matches[0], f"{system_dir.name}_calibrated"))
    return files


def compare_tables(
    recomputed: list[dict[str, Any]],
    canonical_path: Path,
    tolerance: float,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    canonical = {row["system"]: row for row in read_csv(canonical_path)}
    recomputed_by_system = {row["system"]: row for row in recomputed}
    deltas: list[dict[str, Any]] = []
    missing = sorted(set(canonical) - set(recomputed_by_system))
    extra = sorted(set(recomputed_by_system) - set(canonical))
    max_abs_delta = 0.0
    for system, row in recomputed_by_system.items():
        if system not in canonical:
            continue
        for column in NUMERIC_COLUMNS:
            actual = as_float(row[column])
            expected = as_float(canonical[system][column])
            delta = actual - expected
            max_abs_delta = max(max_abs_delta, abs(delta))
            if abs(delta) > tolerance:
                deltas.append(
                    {
                        "system": system,
                        "column": column,
                        "recomputed": actual,
                        "canonical": expected,
                        "delta": delta,
                    }
                )
    summary = {
        "canonical_path": str(canonical_path),
        "systems_recomputed": len(recomputed_by_system),
        "systems_in_canonical": len(canonical),
        "missing_systems": missing,
        "extra_systems": extra,
        "numeric_tolerance": tolerance,
        "max_abs_numeric_delta": max_abs_delta,
        "deltas_over_tolerance": len(deltas),
        "passed": not missing and not extra and not deltas,
    }
    return summary, deltas


def stress_audit(rows_by_system: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    output = []
    for system, rows in sorted(rows_by_system.items()):
        stress_rows = [row for row in rows if row["actual_label"] == "stress"]
        detected = sum(1 for row in stress_rows if row["predicted_label"] == "stress")
        output.append(
            {
                "system": system,
                "stress_cases": len(stress_rows),
                "stress_detected": detected,
                "stress_missed": len(stress_rows) - detected,
                "stress_recall": safe_div(detected, len(stress_rows)),
            }
        )
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument(
        "--out",
        default="/tmp/stableeval_release_audit/stableeval_507_natural_recompute",
        help="Output directory for recomputed artifacts; canonical result files are never overwritten.",
    )
    parser.add_argument(
        "--canonical-leaderboard",
        default="results/stableeval_507_natural/final_tables/stableeval_507_natural_v6_leaderboard.csv",
    )
    parser.add_argument("--tolerance", type=float, default=1e-9)
    parser.add_argument("--no-compare", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    out_dir = Path(args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    labels = load_labels(root / "data/benchmark/stableeval_507_natural/labels.csv")
    canonical_path = root / args.canonical_leaderboard
    order, metadata = canonical_metadata(canonical_path)

    rows_by_system: dict[str, list[dict[str, Any]]] = {}
    for system, rows in load_baseline_records(root / "results/stableeval_507_natural/baselines/raw_predictions.csv").items():
        rows_by_system[system] = rows

    for path, system in agent_prediction_files(root):
        rows_by_system[system] = load_agent_records(path, labels, system)

    recomputed = []
    for system in order:
        if system not in rows_by_system:
            continue
        recomputed.append(score_rows(rows_by_system[system], metadata[system]))

    write_csv(out_dir / "stableeval_507_natural_v6_recomputed.csv", recomputed, LEADERBOARD_COLUMNS)
    write_csv(
        out_dir / "stableeval_507_natural_stress_audit.csv",
        stress_audit(rows_by_system),
        ["system", "stress_cases", "stress_detected", "stress_missed", "stress_recall"],
    )
    write_csv(
        out_dir / "stableeval_507_natural_cost_reliability.csv",
        recomputed,
        ["system", "cases", "valid_json_rate", "failure_rate", "total_cost_usd", "cost_per_case_usd", "mean_latency_seconds"],
    )

    if args.no_compare:
        summary = {"passed": None, "comparison": "skipped"}
        deltas: list[dict[str, Any]] = []
    else:
        summary, deltas = compare_tables(recomputed, canonical_path, args.tolerance)
    write_csv(out_dir / "stableeval_507_natural_v6_deltas.csv", deltas, ["system", "column", "recomputed", "canonical", "delta"])
    (out_dir / "comparison_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({"out_dir": str(out_dir), **summary}, indent=2))
    if summary.get("passed") is False:
        raise SystemExit("Recomputed 507 metrics differ from the canonical leaderboard; inspect output deltas.")


if __name__ == "__main__":
    main()
