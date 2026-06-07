#!/usr/bin/env python3
"""Build the 120-case StableEval-120-Enriched validation set and packets."""

from __future__ import annotations

import argparse
import copy
import json
import re
from pathlib import Path
from typing import Any

import pandas as pd
import stableeval_packet_builder as packet_builder


MODEL_ID = "qwen/qwen-2.5-72b-instruct"
TARGET_CASES = 120
ANONYMIZATION_CASES = 12
LABEL_ORDER = ["stress", "watch", "stable"]
COIN_ALIAS = {
    "USDT": "Stablecoin A",
    "USDC": "Stablecoin B",
    "DAI": "Stablecoin C",
    "Tether": "Stablecoin A",
    "USD Coin": "Stablecoin B",
    "Dai": "Stablecoin C",
}


def load_improvement_module(root: Path) -> Any:
    return packet_builder


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle]


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for item in records:
            handle.write(json.dumps(item, ensure_ascii=False) + "\n")


def round_robin_by_coin(frame: pd.DataFrame, n: int) -> pd.DataFrame:
    groups = {
        coin: group.sort_values("observation_time").reset_index(drop=True)
        for coin, group in frame.groupby("stablecoin", sort=True)
    }
    rows = []
    pos = 0
    while len(rows) < n and groups:
        progressed = False
        for coin in sorted(list(groups)):
            group = groups[coin]
            if pos < len(group):
                rows.append(group.iloc[pos])
                progressed = True
                if len(rows) >= n:
                    break
        if not progressed:
            break
        pos += 1
    return pd.DataFrame(rows).reset_index(drop=True)


def select_validation_cases(labels: pd.DataFrame, pilot_ids: set[str], target: int) -> pd.DataFrame:
    labels = labels.copy()
    labels["severity_score"] = (
        labels["horizon_max_abs_deviation_bps"].astype(float)
        + 0.15 * labels["horizon_hours_ge_25bps"].astype(float)
        + 0.75 * labels["horizon_hours_ge_50bps"].astype(float)
        + 2.0 * labels["horizon_hours_ge_100bps"].astype(float)
        + 20.0 * labels["enhanced_severe_depeg_100bps_3h"].astype(int)
    )
    labels["in_30_case_pilot"] = labels["case_id"].isin(pilot_ids)

    stress = labels[labels["enhanced_stability_label"].eq("stress")].copy()
    stress["selection_bucket"] = "all_stress_cases"
    stress["inclusion_reason"] = "All enhanced stress cases are included; this also includes all strict sustained-depeg cases."

    watch = labels[labels["enhanced_stability_label"].eq("watch")].copy()
    watch["selection_bucket"] = "all_watch_cases"
    watch["inclusion_reason"] = "All watch cases are included to test mild but meaningful instability."

    selected_ids = set(stress["case_id"]) | set(watch["case_id"])
    remaining = target - len(selected_ids)
    if remaining <= 0:
        out = pd.concat([stress, watch], ignore_index=True).head(target)
    else:
        stable = labels[
            labels["enhanced_stability_label"].eq("stable") & ~labels["case_id"].isin(selected_ids)
        ].copy()
        stable["near_stress_stable"] = (
            stable["enhanced_near_stress"].astype(bool)
            | stable["horizon_max_abs_deviation_bps"].ge(35)
            | stable["horizon_hours_ge_25bps"].ge(1)
        )

        near_n = min(max(remaining // 2, 1), int(stable["near_stress_stable"].sum()))
        near_stable = (
            stable[stable["near_stress_stable"]]
            .sort_values(["in_30_case_pilot", "severity_score", "observation_time"], ascending=[True, False, True])
            .head(near_n)
            .copy()
        )
        near_stable["selection_bucket"] = "near_stress_stable_controls"
        near_stable["inclusion_reason"] = (
            "Stable label, but close to watch/stress thresholds or with nonzero 25 bps duration."
        )

        selected_ids |= set(near_stable["case_id"])
        natural_needed = remaining - len(near_stable)
        natural_pool = stable[~stable["case_id"].isin(selected_ids)].copy()
        natural_pool = natural_pool.sort_values(["in_30_case_pilot", "stablecoin", "observation_time"])
        natural_stable = round_robin_by_coin(natural_pool, natural_needed).copy()
        natural_stable["selection_bucket"] = "natural_stable_controls"
        natural_stable["inclusion_reason"] = (
            "Chronological, cross-coin stable controls retained to test realistic deployment behavior."
        )

        out = pd.concat([stress, watch, near_stable, natural_stable], ignore_index=True)

    out = out.sort_values(["observation_time", "stablecoin", "case_id"]).reset_index(drop=True)
    out["validation_order"] = range(1, len(out) + 1)
    return out


def build_improved_packets(
    root: Path,
    validation: pd.DataFrame,
    improvement: Any,
) -> list[dict[str, Any]]:
    hourly = pd.read_csv(root / "data/benchmark/stableeval_507_natural/full_hourly_windows.csv.gz")
    packet_by_case = {packet["case_id"]: packet for packet in load_jsonl(root / "data/benchmark/stableeval_507_natural/prompt_packets_base.jsonl")}
    packets = []
    for case_id in validation["case_id"]:
        group = hourly[(hourly["case_id"].eq(case_id)) & (hourly["period"].eq("lookback"))].copy()
        packet = packet_by_case[case_id]
        risk = improvement.build_risk_features(group, packet)
        packets.append(improvement.improved_packet(packet, risk))
    return packets


def replace_coin_names(value: str) -> str:
    out = value
    for source, target in COIN_ALIAS.items():
        out = re.sub(rf"\b{re.escape(source)}\b", target, out)
    out = re.sub(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:Z|\+00:00)?", "Relative Time", out)
    out = re.sub(r"\d{4}-\d{2}-\d{2}", "Relative Day", out)
    return out


def anonymize_obj(obj: Any) -> Any:
    if isinstance(obj, dict):
        out = {}
        for key, value in obj.items():
            if key in {"stablecoin", "stablecoin_name"}:
                out[key] = replace_coin_names(str(value))
            elif key == "observation_time":
                out[key] = "Day 0, final lookback hour"
            elif key == "lookback_window":
                out[key] = {"start": "Day -30", "end": "Day 0", "hours_observed": value.get("hours_observed", 720)}
            elif key == "forecast_horizon":
                out[key] = {"start": "Day +1", "end": "Day +7", "hours": value.get("hours", 168)}
            elif key in {"timestamp", "day", "date", "time", "start", "end", "horizon_start", "horizon_end"}:
                out[key] = "Relative Time"
            elif key == "mechanism_note":
                out[key] = replace_coin_names(str(value))
            else:
                out[key] = anonymize_obj(value)
        return out
    if isinstance(obj, list):
        return [anonymize_obj(item) for item in obj]
    if isinstance(obj, str):
        return replace_coin_names(obj)
    return obj


def anonymize_packets(packets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    anon = []
    for idx, packet in enumerate(packets, start=1):
        item = anonymize_obj(copy.deepcopy(packet))
        item["_stableeval_case_id"] = packet["case_id"]
        item["_stableeval_stablecoin"] = packet["stablecoin"]
        item["_stableeval_observation_time"] = packet["observation_time"]
        item["case_id"] = f"anonymized_case_{idx:03d}"
        item["anonymization_note"] = (
            "Stablecoin names and calendar dates are replaced by aliases and relative time labels; numerical evidence is unchanged."
        )
        anon.append(item)
    return anon


def write_selection_report(
    out_dir: Path,
    validation: pd.DataFrame,
    all_labels: pd.DataFrame,
    pilot_ids: set[str],
) -> None:
    def simple_table(frame: pd.DataFrame) -> str:
        text = frame.reset_index()
        text.columns = [str(col) for col in text.columns]
        lines = [
            "| " + " | ".join(text.columns) + " |",
            "| " + " | ".join(["---"] * len(text.columns)) + " |",
        ]
        for _, row in text.iterrows():
            lines.append("| " + " | ".join(str(row[col]) for col in text.columns) + " |")
        return "\n".join(lines)

    label_counts = validation["enhanced_stability_label"].value_counts().reindex(["stable", "watch", "stress"]).fillna(0).astype(int)
    bucket_counts = validation["selection_bucket"].value_counts()
    strict_total = int(all_labels["enhanced_severe_depeg_100bps_3h"].sum())
    strict_included = int(validation["enhanced_severe_depeg_100bps_3h"].sum())
    stress_total = int(all_labels["enhanced_stability_label"].eq("stress").sum())
    stress_included = int(validation["enhanced_stability_label"].eq("stress").sum())
    overlap = int(validation["case_id"].isin(pilot_ids).sum())
    non_pilot = len(validation) - overlap
    lines = [
        "# Intermediate Validation Case Selection Report",
        "",
        f"Target size: {TARGET_CASES} cases.",
        f"Actual size: {len(validation)} cases.",
        "",
        "## Label Mix",
        "",
        simple_table(label_counts.to_frame("cases")),
        "",
        "## Selection Buckets",
        "",
        simple_table(bucket_counts.to_frame("cases")),
        "",
        "## Stress Inclusion",
        "",
        f"All enhanced stress cases included: {stress_included}/{stress_total}.",
        f"All strict sustained-depeg cases included: {strict_included}/{strict_total}.",
        "",
        "## Near-Stress Definition",
        "",
        "Near-stress controls are stable-labeled cases with at least one of: `enhanced_near_stress = true`, hidden-horizon max absolute deviation at or above 35 bps, or at least one hidden-horizon hour above 25 bps. These labels are used only for validation-set sampling; agents do not receive hidden-horizon values.",
        "",
        "## Relation To 30-Case Pilot",
        "",
        f"Cases overlapping the prior 30-case pilot: {overlap}.",
        f"Cases outside the prior 30-case pilot: {non_pilot}.",
        "The set is more reliable than the 30-case pilot because it contains every stress case in the dataset, all watch cases, near-stress stable controls, and a larger chronological cross-coin stable-control slice. It therefore tests both rare-event detection and more realistic deployment behavior without moving to the full 507-case benchmark.",
        "",
        "## Leakage Control",
        "",
        "Hidden labels and horizon statistics are used only for selecting and evaluating the validation set. The saved prompt packets contain only 30-day lookback evidence and do not include future prices, future labels, or horizon outcomes.",
    ]
    (out_dir / "validation_case_selection_report.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--target-cases", type=int, default=TARGET_CASES)
    parser.add_argument("--anonymization-cases", type=int, default=ANONYMIZATION_CASES)
    args = parser.parse_args()

    root = Path(args.root).resolve()
    out_dir = root / "results/stableeval_120_enriched"
    out_dir.mkdir(parents=True, exist_ok=True)
    benchmark_dir = root / "data/benchmark/stableeval_120_enriched"
    benchmark_dir.mkdir(parents=True, exist_ok=True)

    improvement = load_improvement_module(root)
    labels = pd.read_csv(root / "data/benchmark/stableeval_507_natural/labels.csv")
    pilot_ids: set[str] = set()
    validation = select_validation_cases(labels, pilot_ids, args.target_cases)
    validation.to_csv(out_dir / "validation_case_list.csv", index=False)
    write_selection_report(out_dir, validation, labels, pilot_ids)

    packets = build_improved_packets(root, validation, improvement)
    write_jsonl(benchmark_dir / "prompt_packets.jsonl", packets)

    subset_parts = []
    for label in LABEL_ORDER:
        part = validation[validation["enhanced_stability_label"].eq(label)].head(max(1, args.anonymization_cases // 3))
        subset_parts.append(part)
    anon_cases = pd.concat(subset_parts, ignore_index=True).head(args.anonymization_cases)
    anon_cases.to_csv(out_dir / "anonymization_case_list.csv", index=False)
    anon_ids = set(anon_cases["case_id"])
    original_subset = [packet for packet in packets if packet["case_id"] in anon_ids]
    write_jsonl(benchmark_dir / "anonymization_original_prompt_packets.jsonl", original_subset)
    write_jsonl(benchmark_dir / "anonymization_anonymized_prompt_packets.jsonl", anonymize_packets(original_subset))

    selected_model = {
        "selected_model_id": MODEL_ID,
        "selection_reason": (
            "Frozen intermediate-validation backend inherited from the improved 30-case pilot: reliable six-platform "
            "OpenRouter execution with qwen/qwen-2.5-72b-instruct at temperature 0."
        ),
    }
    (out_dir / "model_backend.json").write_text(json.dumps(selected_model, indent=2), encoding="utf-8")
    (out_dir / "calibration_rule.md").write_text(
        "\n".join(
            [
                "# Calibration Rule",
                "",
                "This rule is frozen before intermediate validation evaluation and is inherited from the improved pilot.",
                "",
                "- Stress if `predicted_max_abs_deviation_bps >= 100`.",
                "- Stress if `p_depeg_next_7d >= 0.35` and `predicted_max_abs_deviation_bps >= 75`.",
                "- Watch if `p_depeg_next_7d >= 0.15` or `predicted_max_abs_deviation_bps >= 40`.",
                "- Stable otherwise.",
                "",
                "The rule uses only model outputs generated from lookback-window evidence. It does not use validation labels, future prices, or hidden horizon outcomes.",
            ]
        ),
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "validation_cases": len(validation),
                "label_counts": validation["enhanced_stability_label"].value_counts().to_dict(),
                "prompt_packets": str(root / "data/benchmark/stableeval_120_enriched/prompt_packets.jsonl"),
                "outputs": str(out_dir),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
