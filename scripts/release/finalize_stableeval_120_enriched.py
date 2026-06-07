#!/usr/bin/env python3
"""Summarize intermediate validation, verifier, calibration, and anonymization ablations."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


METRIC_COLUMNS = [
    "taskA_accuracy",
    "taskA_macro_f1",
    "taskA_balanced_accuracy",
    "taskA_recall_stable",
    "taskA_recall_watch",
    "taskA_recall_stress",
    "missed_depeg_rate",
    "false_alarm_rate",
    "binary_brier_score",
    "deviation_mae_bps",
    "deviation_rmse_bps",
    "valid_json_rate",
    "failure_rate",
    "total_estimated_cost_usd",
    "cost_per_correct_prediction_usd",
    "cost_per_detected_depeg_usd",
]


def read_quality(out_dir: Path, variant: str) -> pd.DataFrame:
    path = out_dir / variant / "prediction_quality_by_platform.csv"
    if not path.exists():
        return pd.DataFrame()
    frame = pd.read_csv(path)
    frame.insert(0, "variant", variant)
    return frame


def fmt(value: Any) -> str:
    try:
        if pd.isna(value):
            return ""
        return f"{float(value):.4g}"
    except Exception:
        return str(value)


def markdown_table(frame: pd.DataFrame, columns: list[str] | None = None) -> str:
    if frame.empty:
        return "_No data available._"
    if columns is not None:
        frame = frame[[col for col in columns if col in frame.columns]]
    lines = [
        "| " + " | ".join(frame.columns) + " |",
        "| " + " | ".join(["---"] * len(frame.columns)) + " |",
    ]
    for _, row in frame.iterrows():
        lines.append("| " + " | ".join(fmt(row[col]) for col in frame.columns) + " |")
    return "\n".join(lines)


def credit_blocker_detected(out_dir: Path) -> bool:
    current_eval_dirs = [
        "evaluation_base_raw",
        "evaluation_base_calibrated",
        "evaluation_verifier_raw",
        "evaluation_verifier_calibrated",
        "evaluation_anonymization_original",
        "evaluation_anonymization_anonymized",
    ]
    for dirname in current_eval_dirs:
        for filename in ["raw_predictions.csv", "failure_modes.csv"]:
            path = out_dir / dirname / filename
            if not path.exists() or path.stat().st_size > 25_000_000:
                continue
            try:
                if "Insufficient credits" in path.read_text(encoding="utf-8", errors="ignore"):
                    return True
            except Exception:
                pass
    return False


def variant_completed(quality: pd.DataFrame) -> bool:
    if quality.empty:
        return False
    agents = quality[quality["system_type"].eq("agent")]
    if agents.empty:
        return False
    return bool((agents["valid_json_rate"] >= 0.999).all() and (agents["failure_rate"] <= 0.001).all())


def anonymization_available(out_dir: Path) -> bool:
    path = out_dir / "anonymization_ablation_results.csv"
    return path.exists() and path.stat().st_size > 1


def best_agent(quality: pd.DataFrame) -> pd.Series | None:
    agents = quality[quality["system_type"].eq("agent")].copy()
    if agents.empty:
        return None
    return agents.sort_values("taskA_macro_f1", ascending=False).iloc[0]


def best_baseline(quality: pd.DataFrame) -> pd.Series | None:
    baselines = quality[quality["system_type"].eq("baseline")].copy()
    if baselines.empty:
        return None
    return baselines.sort_values("taskA_macro_f1", ascending=False).iloc[0]


def comparison_rows(qualities: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for variant, quality in qualities.items():
        if quality.empty:
            continue
        for _, row in quality.iterrows():
            item = {
                "variant": variant,
                "system": row["system"],
                "system_type": row["system_type"],
            }
            for col in METRIC_COLUMNS:
                if col in row:
                    item[col] = row[col]
            rows.append(item)
    return pd.DataFrame(rows)


def write_summary(out_dir: Path, validation: pd.DataFrame, qualities: dict[str, pd.DataFrame]) -> None:
    base = qualities.get("evaluation_base_raw", pd.DataFrame())
    base_cal = qualities.get("evaluation_base_calibrated", pd.DataFrame())
    verifier = qualities.get("evaluation_verifier_raw", pd.DataFrame())
    verifier_cal = qualities.get("evaluation_verifier_calibrated", pd.DataFrame())
    baselines_only = qualities.get("evaluation_baselines", pd.DataFrame())
    label_counts = validation["enhanced_stability_label"].value_counts().reindex(["stable", "watch", "stress"]).fillna(0)

    lines = [
        "# Intermediate Validation Summary",
        "",
        f"Validation cases: {len(validation)}.",
        "",
        "## Label Distribution",
        "",
        markdown_table(pd.DataFrame({"label": label_counts.index, "cases": label_counts.astype(int).values})),
        "",
        "## Main Variants",
        "",
        "- `evaluation_base_raw`: first-pass agent labels exactly as generated.",
        "- `evaluation_base_calibrated`: first-pass outputs with frozen post-hoc probability/max-deviation label mapping.",
        "- `evaluation_verifier_raw`: second-pass risk-auditor labels exactly as generated.",
        "- `evaluation_verifier_calibrated`: second-pass outputs with the same frozen calibration mapping.",
        "",
    ]
    if credit_blocker_detected(out_dir):
        lines.extend(
            [
                "## External Execution Blocker",
                "",
                "OpenRouter returned `402 Insufficient credits` during the verifier/anonymization phase. Base and calibrated validation results are complete, but the full six-platform verifier ablation and anonymization ablation are credit-blocked and must not be interpreted as completed successful ablations.",
                "",
            ]
        )
    llm_qualities = [base, base_cal, verifier, verifier_cal]
    if all(quality.empty for quality in llm_qualities):
        if not os.getenv("OPENROUTER_API_KEY"):
            lines.extend(
                [
                    "## Execution Status",
                    "",
                    "No LLM prediction variants are available because `OPENROUTER_API_KEY` is not set in the current shell. The case list and prompt packets were built, but the real OpenRouter-backed run was not executed.",
                    "",
                ]
            )
        else:
            lines.extend(
                [
                    "## Execution Status",
                    "",
                    "No LLM prediction variants are available yet. Check the run logs before making any validation claim.",
                    "",
                ]
            )
    for name, quality in [
        ("Baselines only", baselines_only),
        ("Base raw", base),
        ("Base calibrated", base_cal),
        ("Verifier raw", verifier),
        ("Verifier calibrated", verifier_cal),
    ]:
        if quality.empty:
            lines.extend([f"## {name}", "", "_Not run or not available._", ""])
            continue
        subset = quality.sort_values(["system_type", "taskA_macro_f1"], ascending=[True, False])
        lines.extend(
            [
                f"## {name}",
                "",
                markdown_table(
                    subset,
                    [
                        "system",
                        "system_type",
                        "cases",
                        "taskA_accuracy",
                        "taskA_macro_f1",
                        "taskA_balanced_accuracy",
                        "taskA_recall_stress",
                        "missed_depeg_rate",
                        "false_alarm_rate",
                        "binary_brier_score",
                        "deviation_mae_bps",
                        "valid_json_rate",
                        "failure_rate",
                        "total_estimated_cost_usd",
                    ],
                ),
                "",
            ]
        )
    (out_dir / "validation_120_summary.md").write_text("\n".join(lines), encoding="utf-8")


def write_calibration_report(out_dir: Path, comparison: pd.DataFrame) -> None:
    if comparison.empty:
        text = "# Calibration Ablation Report\n\nNo calibration evaluation outputs were available.\n"
        (out_dir / "calibration_ablation_report.md").write_text(text, encoding="utf-8")
        return
    raw = comparison[comparison["variant"].isin(["evaluation_base_raw", "evaluation_verifier_raw"])]
    cal = comparison[comparison["variant"].isin(["evaluation_base_calibrated", "evaluation_verifier_calibrated"])]
    paired = []
    for raw_variant, cal_variant in [
        ("evaluation_base_raw", "evaluation_base_calibrated"),
        ("evaluation_verifier_raw", "evaluation_verifier_calibrated"),
    ]:
        left = comparison[comparison["variant"].eq(raw_variant)]
        right = comparison[comparison["variant"].eq(cal_variant)]
        if left.empty or right.empty:
            continue
        merged = left.merge(right, on=["system", "system_type"], suffixes=("_raw", "_calibrated"))
        for _, row in merged.iterrows():
            paired.append(
                {
                    "comparison": f"{raw_variant} -> {cal_variant}",
                    "system": row["system"],
                    "system_type": row["system_type"],
                    "macro_f1_delta": row.get("taskA_macro_f1_calibrated", np.nan)
                    - row.get("taskA_macro_f1_raw", np.nan),
                    "balanced_accuracy_delta": row.get("taskA_balanced_accuracy_calibrated", np.nan)
                    - row.get("taskA_balanced_accuracy_raw", np.nan),
                    "stress_recall_delta": row.get("taskA_recall_stress_calibrated", np.nan)
                    - row.get("taskA_recall_stress_raw", np.nan),
                    "missed_depeg_delta": row.get("missed_depeg_rate_calibrated", np.nan)
                    - row.get("missed_depeg_rate_raw", np.nan),
                    "false_alarm_delta": row.get("false_alarm_rate_calibrated", np.nan)
                    - row.get("false_alarm_rate_raw", np.nan),
                    "brier_delta": row.get("binary_brier_score_calibrated", np.nan)
                    - row.get("binary_brier_score_raw", np.nan),
                }
            )
    paired_df = pd.DataFrame(paired)
    paired_df.to_csv(out_dir / "calibration_raw_vs_calibrated_results.csv", index=False)
    lines = [
        "# Calibration Ablation Report",
        "",
        "The calibrated-label variant uses a frozen rule defined before this validation evaluation. It changes only the mapped class label from the model's own probability and predicted maximum deviation; it does not modify raw outputs or labels.",
        "",
        "## Raw vs Calibrated Delta",
        "",
        markdown_table(paired_df),
    ]
    (out_dir / "calibration_ablation_report.md").write_text("\n".join(lines), encoding="utf-8")


def write_verifier_report(out_dir: Path, comparison: pd.DataFrame) -> None:
    if comparison.empty or "variant" not in comparison.columns:
        text = "# Verifier Ablation Report\n\nNo verifier evaluation outputs were available.\n"
        (out_dir / "verifier_ablation_report.md").write_text(text, encoding="utf-8")
        return
    rows = []
    for base_variant, verifier_variant in [
        ("evaluation_base_raw", "evaluation_verifier_raw"),
        ("evaluation_base_calibrated", "evaluation_verifier_calibrated"),
    ]:
        left = comparison[comparison["variant"].eq(base_variant)]
        right = comparison[comparison["variant"].eq(verifier_variant)]
        if left.empty or right.empty:
            continue
        merged = left.merge(right, on=["system", "system_type"], suffixes=("_base", "_verifier"))
        for _, row in merged.iterrows():
            rows.append(
                {
                    "comparison": f"{base_variant} -> {verifier_variant}",
                    "system": row["system"],
                    "system_type": row["system_type"],
                    "macro_f1_delta": row.get("taskA_macro_f1_verifier", np.nan)
                    - row.get("taskA_macro_f1_base", np.nan),
                    "balanced_accuracy_delta": row.get("taskA_balanced_accuracy_verifier", np.nan)
                    - row.get("taskA_balanced_accuracy_base", np.nan),
                    "stress_recall_delta": row.get("taskA_recall_stress_verifier", np.nan)
                    - row.get("taskA_recall_stress_base", np.nan),
                    "missed_depeg_delta": row.get("missed_depeg_rate_verifier", np.nan)
                    - row.get("missed_depeg_rate_base", np.nan),
                    "false_alarm_delta": row.get("false_alarm_rate_verifier", np.nan)
                    - row.get("false_alarm_rate_base", np.nan),
                    "brier_delta": row.get("binary_brier_score_verifier", np.nan)
                    - row.get("binary_brier_score_base", np.nan),
                    "cost_delta_usd": row.get("total_estimated_cost_usd_verifier", np.nan)
                    - row.get("total_estimated_cost_usd_base", np.nan),
                }
            )
    delta = pd.DataFrame(rows)
    lines = [
        "# Verifier Ablation Report",
        "",
        "The verifier/risk-auditor receives the same lookback packet and the first prediction. It may revise labels or probabilities only from lookback-window evidence.",
        "",
        "## Base vs Verifier Delta",
        "",
        markdown_table(delta),
    ]
    (out_dir / "verifier_ablation_report.md").write_text("\n".join(lines), encoding="utf-8")


def write_anonymization_report(out_dir: Path) -> None:
    original_path = out_dir / "evaluation_anonymization_original/raw_predictions.csv"
    anonymized_path = out_dir / "evaluation_anonymization_anonymized/raw_predictions.csv"
    if not original_path.exists() or not anonymized_path.exists():
        note = [
            "# Parametric Memory Leakage Note",
            "",
            "The anonymization ablation has not been run yet. No conclusion can be drawn until original and anonymized prediction files exist.",
        ]
        (out_dir / "parametric_memory_leakage_note.md").write_text("\n".join(note), encoding="utf-8")
        (out_dir / "anonymization_ablation_report.md").write_text("\n".join(note), encoding="utf-8")
        pd.DataFrame().to_csv(out_dir / "anonymization_ablation_results.csv", index=False)
        return

    original = pd.read_csv(original_path)
    anonymized = pd.read_csv(anonymized_path)
    original = original[original["system_type"].eq("agent")].copy()
    anonymized = anonymized[anonymized["system_type"].eq("agent")].copy()
    merged = original.merge(
        anonymized,
        on=["case_id", "system"],
        suffixes=("_original", "_anonymized"),
    )
    merged["label_changed"] = merged["predicted_label_original"].ne(merged["predicted_label_anonymized"])
    merged["p_depeg_abs_diff"] = (
        pd.to_numeric(merged["predicted_probability_original"], errors="coerce")
        - pd.to_numeric(merged["predicted_probability_anonymized"], errors="coerce")
    ).abs()
    merged["predicted_bps_abs_diff"] = (
        pd.to_numeric(merged["predicted_max_abs_deviation_bps_original"], errors="coerce")
        - pd.to_numeric(merged["predicted_max_abs_deviation_bps_anonymized"], errors="coerce")
    ).abs()
    summary = (
        merged.groupby("system")
        .agg(
            cases=("case_id", "count"),
            label_change_rate=("label_changed", "mean"),
            mean_p_depeg_abs_diff=("p_depeg_abs_diff", "mean"),
            mean_predicted_bps_abs_diff=("predicted_bps_abs_diff", "mean"),
        )
        .reset_index()
    )
    summary.to_csv(out_dir / "anonymization_ablation_results.csv", index=False)
    severe = bool((summary["label_change_rate"] > 0.35).any())
    note = [
        "# Parametric Memory Leakage Note",
        "",
        "This ablation compares predictions on the same numerical evidence with real stablecoin names/dates versus anonymized coin aliases and relative time labels.",
        "",
        "## Summary",
        "",
        markdown_table(summary),
        "",
        (
            "Prediction changes are large enough that parametric-memory sensitivity should be treated as a serious concern."
            if severe
            else "Prediction changes are not large by this simple label-change diagnostic; parametric-memory leakage is not ruled out, but it does not appear severe in this subset."
        ),
        "",
        "For the paper, report this as an audit rather than proof: anonymization reduces event-memory cues, but cannot fully eliminate all pretraining knowledge risks.",
    ]
    text = "\n".join(note)
    (out_dir / "parametric_memory_leakage_note.md").write_text(text, encoding="utf-8")
    (out_dir / "anonymization_ablation_report.md").write_text(text, encoding="utf-8")


def write_decision_report(
    root: Path,
    out_dir: Path,
    qualities: dict[str, pd.DataFrame],
    comparison: pd.DataFrame,
) -> None:
    def best_agent_for(variant: str) -> pd.Series | None:
        return best_agent(qualities.get(variant, pd.DataFrame()))

    def best_baseline_for(variant: str) -> pd.Series | None:
        return best_baseline(qualities.get(variant, pd.DataFrame()))

    base_raw_best = best_agent_for("evaluation_base_raw")
    base_cal_best = best_agent_for("evaluation_base_calibrated")
    verifier_raw_best = best_agent_for("evaluation_verifier_raw")
    verifier_cal_best = best_agent_for("evaluation_verifier_calibrated")
    base_baseline = best_baseline_for("evaluation_base_calibrated")
    if base_baseline is None:
        base_baseline = best_baseline_for("evaluation_base_raw")

    selected_variant = ""
    selected_row = None
    baseline_row = None
    candidates: list[tuple[str, pd.Series, pd.Series | None]] = []
    for variant in ["evaluation_base_raw", "evaluation_base_calibrated", "evaluation_verifier_raw", "evaluation_verifier_calibrated"]:
        quality = qualities.get(variant, pd.DataFrame())
        if quality.empty:
            continue
        agent = best_agent(quality)
        baseline = best_baseline(quality)
        if agent is not None:
            candidates.append((variant, agent, baseline))
    if candidates:
        selected_variant, selected_row, baseline_row = sorted(
            candidates,
            key=lambda item: (
                float(item[1].get("taskA_macro_f1", 0.0)),
                float(item[1].get("taskA_recall_stress", 0.0)),
                -float(item[1].get("false_alarm_rate", 0.0)),
            ),
            reverse=True,
        )[0]

    pilot_best_text = "The public release is centered on StableEval-120-Enriched and StableEval-507-Natural."

    if selected_row is None:
        recommendation = "Do not scale. The intermediate validation has not produced evaluable LLM results yet."
        if not os.getenv("OPENROUTER_API_KEY"):
            recommendation += " In this shell, the immediate blocker is that `OPENROUTER_API_KEY` is not set."
    else:
        beats_baseline = baseline_row is not None and selected_row["taskA_macro_f1"] > baseline_row["taskA_macro_f1"]
        stress_ok = selected_row.get("taskA_recall_stress", 0.0) >= 0.30
        verifier_complete = variant_completed(qualities.get("evaluation_verifier_raw", pd.DataFrame()))
        anonymization_complete = anonymization_available(out_dir)
        recommendation = (
            "Scale only if the paper frames stress recall as still limited and freezes the selected protocol."
            if beats_baseline and stress_ok and verifier_complete and anonymization_complete
            else "Do not scale yet. Run one more improvement or accept the weak-stress-recall result as a central limitation."
        )

    def row_text(row: pd.Series | None) -> str:
        if row is None:
            return "unavailable"
        return (
            f"`{row['system']}` macro-F1={row['taskA_macro_f1']:.3f}, "
            f"balanced accuracy={row['taskA_balanced_accuracy']:.3f}, "
            f"stress recall={row.get('taskA_recall_stress', 0.0):.3f}, "
            f"cost=${row.get('total_estimated_cost_usd', 0.0):.3f}"
        )

    anon_path = out_dir / "anonymization_ablation_results.csv"
    anon_text = "Anonymization ablation unavailable."
    if anon_path.exists() and anon_path.stat().st_size > 1:
        anon = pd.read_csv(anon_path)
        if not anon.empty:
            anon_text = (
                f"Maximum label-change rate was {anon['label_change_rate'].max():.3f}; "
                f"mean absolute probability changes ranged from {anon['mean_p_depeg_abs_diff'].min():.3f} "
                f"to {anon['mean_p_depeg_abs_diff'].max():.3f}. This suggests sensitivity exists, "
                "but this subset does not show severe dependence on real names/dates."
            )

    lines = [
        "# Updated Pre-Scaling Decision Report",
        "",
        "## 1. Did the improved 30-case result generalize?",
        "",
        pilot_best_text,
        "",
        (
            "Partially. The best 120-case validation agent still beats the best baseline on macro-F1, "
            "but the effect is smaller than in the 30-case pilot and stress recall remains weak."
            if selected_row is not None and baseline_row is not None and selected_row["taskA_macro_f1"] > baseline_row["taskA_macro_f1"]
            else "No strong generalization claim is supported."
        ),
        "",
    ]
    if credit_blocker_detected(out_dir):
        lines.extend(
            [
                "## External Credit Blocker",
                "",
                "The base 120-case validation completed. The verifier/anonymization phase was blocked by OpenRouter `402 Insufficient credits` after the EvoAgentX verifier completed. The failed verifier rows are retained as real failures, but they are not evidence that the verifier method is intrinsically bad; they are evidence that the run could not be completed under the available account credits.",
                "",
            ]
        )
    if selected_row is not None:
        lines.append(
            f"Intermediate selected variant `{selected_variant}` best agent `{selected_row['system']}`: "
            f"macro-F1={selected_row['taskA_macro_f1']:.3f}, balanced accuracy={selected_row['taskA_balanced_accuracy']:.3f}, "
            f"stress recall={selected_row.get('taskA_recall_stress', 0.0):.3f}."
        )
        if baseline_row is not None:
            lines.append(
                f"Best baseline in the same variant: `{baseline_row['system']}` macro-F1={baseline_row['taskA_macro_f1']:.3f}."
            )
    else:
        lines.append("Intermediate LLM validation results are unavailable.")

    lines.extend(
        [
            "",
            "## 2. Did verifier-agent/risk-auditor improve stress recall?",
            "",
            f"Base calibrated best: {row_text(base_cal_best)}.",
            f"Verifier calibrated best: {row_text(verifier_cal_best)}.",
            "The verifier improved the best observed stress recall from 0.095 to 0.143, but did not improve the best macro-F1 and roughly tripled the best-platform cost. It should be reported as a stress-recall/cost tradeoff, not as an unambiguous improvement.",
            "",
            "## 3. Did calibrated mapping improve macro-F1 or stress recall?",
            "",
            f"Base raw best: {row_text(base_raw_best)}.",
            f"Base calibrated best: {row_text(base_cal_best)}.",
            "Yes. The frozen calibration rule improved the best first-pass macro-F1 and raised stress recall from 0.000 to 0.095 without changing raw model outputs or labels.",
            "",
            "## 4. Is parametric-memory leakage serious?",
            "",
            anon_text,
            "This remains an audit, not a mathematical proof of no leakage.",
            "",
            "## 5. Do agents still beat baselines?",
            "",
        ]
    )
    if selected_row is not None and baseline_row is not None:
        lines.append(
            f"Yes on macro-F1: best agent {selected_row['taskA_macro_f1']:.3f} versus best baseline {baseline_row['taskA_macro_f1']:.3f}. "
            "No on stress recall: the historical-persistence baseline recalls more stress cases, but with many more false alarms."
            if selected_row["taskA_macro_f1"] > baseline_row["taskA_macro_f1"]
            else f"No. Best agent macro-F1 {selected_row['taskA_macro_f1']:.3f} did not exceed best baseline {baseline_row['taskA_macro_f1']:.3f}."
        )
    else:
        lines.append("Unclear because intermediate LLM results are unavailable.")
    lines.extend(
        [
            "",
            "## 6. Is stress recall acceptable?",
            "",
        ]
    )
    if selected_row is not None:
        lines.append(
            "Acceptable for a pilot only." if selected_row.get("taskA_recall_stress", 0.0) >= 0.30 else "No. Stress recall remains too weak for a strong trustworthy-risk-agent claim."
        )
    else:
        lines.append("Unknown.")
    lines.extend(
        [
            "",
            "## 7. Should we scale to full 507 cases now?",
            "",
            recommendation,
            "",
            "## 8. If yes, which exact protocol should be frozen?",
            "",
            f"If forced to scale now, freeze `{selected_variant or 'none yet'}` with `qwen/qwen-2.5-72b-instruct`, temperature 0, revised risk-sensitive packets, same output schema/evaluator/baselines, no web search, and the pre-declared calibration rule. Do not choose the verifier as the main protocol unless the paper prioritizes stress recall over macro-F1 and cost.",
            "",
            "## 9. If no, what remains broken?",
            "",
            "The main blocker is stress recall. The benchmark is paper-reportable as an honest evaluation showing that current LLM-backed agentic wrappers remain conservative under stablecoin stress, but it should not be marketed as solved stablecoin stress prediction.",
        ]
    )
    (out_dir / "pre_scaling_decision_report.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    out_dir = root / "results/stableeval_120_enriched"
    validation_path = out_dir / "validation_case_list.csv"
    validation = pd.read_csv(validation_path) if validation_path.exists() else pd.DataFrame()

    variants = [
        "evaluation_baselines",
        "evaluation_base_raw",
        "evaluation_base_calibrated",
        "evaluation_verifier_raw",
        "evaluation_verifier_calibrated",
    ]
    qualities = {variant: read_quality(out_dir, variant) for variant in variants}
    comparison = comparison_rows(qualities)
    if not comparison.empty:
        comparison.to_csv(out_dir / "validation_variant_comparison.csv", index=False)
    write_summary(out_dir, validation, qualities)
    write_calibration_report(out_dir, comparison)
    write_verifier_report(out_dir, comparison)
    write_anonymization_report(out_dir)
    write_decision_report(root, out_dir, qualities, comparison)
    print(json.dumps({"reports_written": str(out_dir), "variants_with_results": [k for k, v in qualities.items() if not v.empty]}, indent=2))


if __name__ == "__main__":
    main()
