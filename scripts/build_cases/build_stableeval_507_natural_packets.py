#!/usr/bin/env python3
"""Build frozen improved prompt packets for the full 507-case benchmark."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd
import stableeval_packet_builder as packet_builder


MODEL_ID = "qwen/qwen-2.5-72b-instruct"


def load_improvement_module(root: Path) -> Any:
    return packet_builder


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for item in records:
            handle.write(json.dumps(item, ensure_ascii=False) + "\n")


def markdown_table(frame: pd.DataFrame) -> str:
    lines = [
        "| " + " | ".join(frame.columns.astype(str)) + " |",
        "| " + " | ".join(["---"] * len(frame.columns)) + " |",
    ]
    for _, row in frame.iterrows():
        lines.append("| " + " | ".join(str(row[col]) for col in frame.columns) + " |")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--out-dir", default="results/stableeval_507_natural/build_metadata")
    parser.add_argument("--packets-out", default="data/benchmark/stableeval_507_natural/prompt_packets.jsonl")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    out_dir = root / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    improvement = load_improvement_module(root)
    labels = pd.read_csv(root / "data/benchmark/stableeval_507_natural/labels.csv").sort_values(
        ["observation_time", "stablecoin", "case_id"]
    )
    hourly = pd.read_csv(root / "data/benchmark/stableeval_507_natural/full_hourly_windows.csv.gz")
    base_packets = {packet["case_id"]: packet for packet in load_jsonl(root / "data/benchmark/stableeval_507_natural/prompt_packets_base.jsonl")}

    packets = []
    missing = []
    for case_id in labels["case_id"]:
        packet = base_packets.get(case_id)
        if packet is None:
            missing.append(case_id)
            continue
        group = hourly[(hourly["case_id"].eq(case_id)) & (hourly["period"].eq("lookback"))].copy()
        if group.empty:
            missing.append(case_id)
            continue
        risk = improvement.build_risk_features(group, packet)
        packets.append(improvement.improved_packet(packet, risk))

    if missing:
        raise RuntimeError(f"Missing packets/lookback rows for {len(missing)} cases: {missing[:10]}")

    full_case_list = labels.copy()
    full_case_list["full_507_order"] = range(1, len(full_case_list) + 1)
    full_case_list.to_csv(out_dir / "full_507_case_list.csv", index=False)
    write_jsonl(root / args.packets_out, packets)

    selected_model = {
        "selected_model_id": MODEL_ID,
        "selection_reason": (
            "Frozen MVP full-distribution backend inherited from the 120-case validation: "
            "qwen/qwen-2.5-72b-instruct via OpenRouter at temperature 0."
        ),
    }
    (out_dir / "model_backend.json").write_text(json.dumps(selected_model, indent=2), encoding="utf-8")

    counts = (
        full_case_list["enhanced_stability_label"]
        .value_counts()
        .reindex(["stable", "watch", "stress"])
        .fillna(0)
        .astype(int)
        .reset_index()
    )
    counts.columns = ["label", "cases"]
    report = [
        "# Full 507 Frozen Packet Build Report",
        "",
        f"Cases: {len(full_case_list)}.",
        f"Prompt packets: `{args.packets_out}`.",
        "",
        "## Label Distribution",
        "",
        markdown_table(counts),
        "",
        "## Protocol",
        "",
        "- 30-day frozen lookback only.",
        "- Hidden next-7-day labels are not included in packets.",
        "- Model backend for planned run: `qwen/qwen-2.5-72b-instruct`.",
        "- Temperature: 0.",
        "- Calibration is applied after raw prediction generation as a separate frozen step.",
    ]
    (out_dir / "full_507_build_report.md").write_text("\n".join(report), encoding="utf-8")
    print(json.dumps({"cases": len(full_case_list), "packets": len(packets), "out_dir": str(out_dir)}, indent=2))


if __name__ == "__main__":
    main()
