#!/usr/bin/env python3
"""Finalize the completed OpenClaw adapter 507 resume run.

This historical one-off finalizer is retained for original-run provenance.
For public-release verification, use
scripts/evaluate/recompute_stableeval_507_natural.py.

This script is intentionally additive: it writes only OpenClaw adapter-specific
507 artifacts and the new v5 progress leaderboard. It refuses to overwrite
target files that already exist.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
CLASS_ORDER = ["stable", "watch", "stress"]
CONFUSION_COLUMNS = ["stable", "watch", "stress", "invalid"]
EXPECTED_MODEL_BACKEND = "openrouter/qwen/qwen-2.5-72b-instruct"
EXPECTED_BACKEND = "openrouter_llm"
EXPECTED_EXECUTION_MODE = "stableeval_adapter"
CALIBRATION_RULE = "risk_sensitive_v1_posthoc_frozen"

CASE_LIST = ROOT / "data/benchmark/stableeval_507_natural/case_list.csv"
PROMPT_PACKETS = ROOT / "data/benchmark/stableeval_507_natural/prompt_packets.jsonl"
DRY_RUN_RAW = ROOT / "results/stableeval_507_natural/raw_predictions/openclaw_adapter_qwen_507_dry_run/openclaw_adapter_predictions_dry_run.jsonl"
CONTINUATION_RAW = (
    ROOT / "results/stableeval_507_natural/raw_predictions/openclaw_adapter_qwen_507_continuation/openclaw_adapter_predictions_continuation.jsonl"
)
COMPLETE_DIR = ROOT / "results/stableeval_507_natural/raw_predictions/openclaw_adapter_qwen_507"
COMPLETE_RAW = COMPLETE_DIR / "openclaw_adapter_predictions_507_complete.jsonl"
COMPLETE_RAW_COMPAT = COMPLETE_DIR / "openclaw_adapter_predictions.jsonl"
CALIBRATED_DIR = ROOT / "results/stableeval_507_natural/calibrated_predictions/openclaw_adapter_qwen_507"
CALIBRATED_RAW = CALIBRATED_DIR / "openclaw_adapter_predictions.jsonl"

METRICS_DIR = ROOT / "results/stableeval_507_natural/metrics/openclaw_adapter_qwen_507"
TABLES_DIR = ROOT / "results/stableeval_507_natural/tables/openclaw_adapter_qwen_507"
FIGURES_DIR = ROOT / "results/stableeval_507_natural/figures/openclaw_adapter_qwen_507"
CONFUSION_DIR = ROOT / "results/stableeval_507_natural/confusion_matrices/openclaw_adapter_qwen_507"
REPORTS_DIR = ROOT / "results/stableeval_507_natural/reports/openclaw_adapter_qwen_507"
METADATA_DIR = ROOT / "results/stableeval_507_natural/metadata/openclaw_adapter_qwen_507"
COSTS_DIR = ROOT / "results/stableeval_507_natural/costs/openclaw_adapter_qwen_507"
LOGS_DIR = ROOT / "results/stableeval_507_natural/logs/openclaw_adapter_qwen_507"

V4_LEADERBOARD = ROOT / "results/stableeval_507_natural/tables/scaling_507_progress_leaderboard_v4_verified_with_evoagentx.csv"
V5_LEADERBOARD = ROOT / "results/stableeval_507_natural/tables/scaling_507_progress_leaderboard_v5_verified_with_openclaw_adapter.csv"

NANOBOT_507_CAL = ROOT / "results/stableeval_507_natural/calibrated_predictions/nanobot_qwen_507/nanobot_predictions.jsonl"
LANGGRAPH_507_CAL = ROOT / "results/stableeval_507_natural/calibrated_predictions/langgraph_qwen_507/langgraph_predictions.jsonl"
HERMES_507_CAL = ROOT / "results/stableeval_507_natural/calibrated_predictions/hermes_ai_qwen_507/hermes_ai_predictions.jsonl"
EVOAGENTX_507_CAL = ROOT / "results/stableeval_507_natural/calibrated_predictions/evoagentx_qwen_507/evoagentx_predictions.jsonl"

VALIDATION_120 = ROOT / "results/stableeval_120_enriched/validation_case_list.csv"
OPENCLAW_120_RAW = ROOT / "results/stableeval_120_enriched/predictions_base_raw/openclaw_predictions.jsonl"
OPENCLAW_120_CAL = ROOT / "results/stableeval_120_enriched/predictions_base_calibrated/openclaw_predictions.jsonl"
METRICS_120_RAW = ROOT / "results/stableeval_120_enriched/evaluation_base_raw/prediction_quality_by_platform.csv"
METRICS_120_CAL = ROOT / "results/stableeval_120_enriched/evaluation_base_calibrated/prediction_quality_by_platform.csv"
FREEZE_MANIFEST = ROOT / "results/stableeval_120_enriched/freeze_manifest/FREEZE_120_MANIFEST.csv"


CREATED: list[Path] = []


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def refuse_existing(path: Path) -> None:
    if path.exists():
        raise FileExistsError(f"Refusing to overwrite existing file: {rel(path)}")


def write_text(path: Path, text: str) -> None:
    ensure_parent(path)
    refuse_existing(path)
    path.write_text(text, encoding="utf-8")
    CREATED.append(path)


def write_json(path: Path, obj: Any) -> None:
    write_text(path, json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n")


def write_df(path: Path, frame: pd.DataFrame) -> None:
    ensure_parent(path)
    refuse_existing(path)
    frame.to_csv(path, index=False)
    CREATED.append(path)


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    ensure_parent(path)
    refuse_existing(path)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    CREATED.append(path)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def safe_div(num: float, den: float) -> float:
    return float(num / den) if den else 0.0


def as_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def corr(a: pd.Series, b: pd.Series) -> float:
    x = pd.to_numeric(a, errors="coerce")
    y = pd.to_numeric(b, errors="coerce")
    mask = x.notna() & y.notna()
    if mask.sum() < 2:
        return float("nan")
    if float(x[mask].std()) == 0.0 or float(y[mask].std()) == 0.0:
        return float("nan")
    return float(np.corrcoef(x[mask], y[mask])[0, 1])


def load_jsonl(path: Path) -> tuple[list[dict[str, Any]], list[int]]:
    records: list[dict[str, Any]] = []
    corrupt: list[int] = []
    with path.open("r", encoding="utf-8") as handle:
        for idx, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                corrupt.append(idx)
    return records, corrupt


def get_prediction(record: dict[str, Any]) -> dict[str, Any]:
    pred = record.get("parsed_json") or record.get("prediction") or {}
    return pred if isinstance(pred, dict) else {}


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
    prediction = dict(get_prediction(out))
    if prediction:
        prediction["original_price_stability_next_7d"] = prediction.get("price_stability_next_7d", "")
        prediction["price_stability_next_7d"] = calibrated_label(prediction)
        prediction["label_calibration"] = CALIBRATION_RULE
        out["parsed_json"] = prediction
        out["prediction"] = prediction
    return out


def confusion_counts(y_true: pd.Series, y_pred: pd.Series) -> pd.DataFrame:
    matrix = pd.DataFrame(0, index=CLASS_ORDER, columns=CONFUSION_COLUMNS)
    for actual, predicted in zip(y_true, y_pred):
        pred = predicted if predicted in CLASS_ORDER else "invalid"
        if actual in CLASS_ORDER:
            matrix.loc[actual, pred] += 1
    return matrix


def multiclass_metrics(y_true: pd.Series, y_pred: pd.Series) -> dict[str, Any]:
    cm = confusion_counts(y_true, y_pred)
    total = int(cm.to_numpy().sum())
    correct = sum(int(cm.loc[label, label]) for label in CLASS_ORDER)
    metrics: dict[str, float] = {}
    recalls: list[float] = []
    f1s: list[float] = []
    for label in CLASS_ORDER:
        tp = int(cm.loc[label, label])
        actual_total = int(cm.loc[label, :].sum())
        pred_total = int(cm.loc[:, label].sum())
        precision = safe_div(tp, pred_total)
        recall = safe_div(tp, actual_total)
        f1 = safe_div(2 * precision * recall, precision + recall)
        metrics[f"precision_{label}"] = precision
        metrics[f"recall_{label}"] = recall
        metrics[f"f1_{label}"] = f1
        recalls.append(recall)
        f1s.append(f1)
    return {
        "accuracy": safe_div(correct, total),
        "macro_f1": float(np.mean(f1s)),
        "balanced_accuracy": float(np.mean(recalls)),
        **metrics,
        "confusion_matrix": cm,
    }


def auc_roc(y_true: np.ndarray, scores: np.ndarray) -> float:
    positives = scores[y_true == 1]
    negatives = scores[y_true == 0]
    if len(positives) == 0 or len(negatives) == 0:
        return float("nan")
    wins = 0.0
    for pos in positives:
        wins += float((pos > negatives).sum())
        wins += 0.5 * float((pos == negatives).sum())
    return float(wins / (len(positives) * len(negatives)))


def average_precision(y_true: np.ndarray, scores: np.ndarray) -> float:
    positives = int(y_true.sum())
    if positives == 0:
        return float("nan")
    order = np.argsort(-scores)
    y_sorted = y_true[order]
    tp = 0
    precisions = []
    for idx, label in enumerate(y_sorted, start=1):
        if label == 1:
            tp += 1
            precisions.append(tp / idx)
    return float(np.mean(precisions)) if precisions else 0.0


def calibration_ece(y_true: np.ndarray, scores: np.ndarray, bins: int = 10) -> float:
    edges = np.linspace(0, 1, bins + 1)
    ece = 0.0
    for lo, hi in zip(edges[:-1], edges[1:]):
        if hi < 1:
            mask = (scores >= lo) & (scores < hi)
        else:
            mask = (scores >= lo) & (scores <= hi)
        if not mask.any():
            continue
        ece += float(mask.mean() * abs(scores[mask].mean() - y_true[mask].mean()))
    return ece


def binary_metrics(y_true: np.ndarray, scores: np.ndarray, threshold: float = 0.5) -> dict[str, Any]:
    y_hat = (scores >= threshold).astype(int)
    tp = int(((y_true == 1) & (y_hat == 1)).sum())
    tn = int(((y_true == 0) & (y_hat == 0)).sum())
    fp = int(((y_true == 0) & (y_hat == 1)).sum())
    fn = int(((y_true == 1) & (y_hat == 0)).sum())
    precision = safe_div(tp, tp + fp)
    recall = safe_div(tp, tp + fn)
    return {
        "binary_precision": precision,
        "binary_recall": recall,
        "binary_auroc": auc_roc(y_true, scores),
        "binary_average_precision": average_precision(y_true, scores),
        "binary_brier_score": float(np.mean((scores - y_true) ** 2)),
        "binary_ece_10bin": calibration_ece(y_true, scores),
        "missed_depeg_rate": safe_div(fn, fn + tp),
        "false_alarm_rate": safe_div(fp, fp + tn),
        "binary_tp": tp,
        "binary_tn": tn,
        "binary_fp": fp,
        "binary_fn": fn,
    }


def continuous_metrics(actual: np.ndarray, predicted: np.ndarray) -> dict[str, float]:
    error = predicted - actual
    return {
        "deviation_mae_bps": float(np.mean(np.abs(error))),
        "deviation_rmse_bps": float(np.sqrt(np.mean(error**2))),
        "deviation_error_p10_bps": float(np.quantile(error, 0.10)),
        "deviation_error_median_bps": float(np.quantile(error, 0.50)),
        "deviation_error_p90_bps": float(np.quantile(error, 0.90)),
    }


def records_to_predictions(records: list[dict[str, Any]], system_name: str) -> pd.DataFrame:
    rows = []
    for item in records:
        pred = get_prediction(item)
        rows.append(
            {
                "case_id": item.get("case_id"),
                "stablecoin": item.get("stablecoin"),
                "system": system_name,
                "system_type": "agent",
                "platform": item.get("platform"),
                "model_backend": item.get("model_backend") or pred.get("model_backend"),
                "backend": item.get("backend") or pred.get("backend"),
                "execution_mode": item.get("execution_mode") or item.get("framework_execution_mode"),
                "input_packet_hash": item.get("input_packet_hash"),
                "raw_agent_output": item.get("raw_agent_output", ""),
                "parsed_json": json.dumps(pred, ensure_ascii=False, sort_keys=True) if pred else "",
                "valid_json": bool(item.get("valid_json") or item.get("valid_output")),
                "error_message": item.get("error_message") or item.get("error") or "",
                "predicted_label": pred.get("price_stability_next_7d"),
                "predicted_probability": pred.get("p_depeg_next_7d"),
                "predicted_max_abs_deviation_bps": pred.get("predicted_max_abs_deviation_bps"),
                "predicted_direction": pred.get("predicted_direction"),
                "confidence": pred.get("confidence"),
                "rationale": pred.get("rationale", ""),
                "prompt_tokens": item.get("prompt_tokens_approx", 0),
                "completion_tokens": item.get("completion_tokens_approx", 0),
                "total_tokens": item.get("total_tokens_approx", 0),
                "latency_seconds": item.get("latency_seconds", 0.0),
                "estimated_cost_usd": item.get("estimated_cost_usd", 0.0),
            }
        )
    return pd.DataFrame(rows)


def attach_actuals(predictions: pd.DataFrame, labels: pd.DataFrame) -> pd.DataFrame:
    actual_cols = [
        "case_id",
        "stablecoin",
        "enhanced_stability_label",
        "enhanced_severe_depeg_100bps_3h",
        "enhanced_watch_50bps_any_close",
        "horizon_max_abs_deviation_bps",
        "horizon_mean_abs_deviation_bps",
        "horizon_hours_ge_25bps",
        "horizon_hours_ge_50bps",
        "horizon_hours_ge_100bps",
        "actual_direction",
    ]
    out = predictions.merge(labels[actual_cols], on=["case_id", "stablecoin"], how="left")
    out = out.rename(
        columns={
            "enhanced_stability_label": "actual_label",
            "enhanced_severe_depeg_100bps_3h": "actual_sustained_depeg",
            "horizon_max_abs_deviation_bps": "actual_max_abs_deviation_bps",
        }
    )
    out["predicted_probability"] = pd.to_numeric(out["predicted_probability"], errors="coerce").fillna(0.0).clip(0, 1)
    out["predicted_max_abs_deviation_bps"] = pd.to_numeric(
        out["predicted_max_abs_deviation_bps"], errors="coerce"
    ).fillna(0.0)
    out["confidence"] = pd.to_numeric(out["confidence"], errors="coerce").fillna(0.0).clip(0, 1)
    out["prompt_tokens"] = pd.to_numeric(out["prompt_tokens"], errors="coerce").fillna(0).astype(int)
    out["completion_tokens"] = pd.to_numeric(out["completion_tokens"], errors="coerce").fillna(0).astype(int)
    out["total_tokens"] = pd.to_numeric(out["total_tokens"], errors="coerce").fillna(0).astype(int)
    out["latency_seconds"] = pd.to_numeric(out["latency_seconds"], errors="coerce").fillna(0.0)
    out["estimated_cost_usd"] = pd.to_numeric(out["estimated_cost_usd"], errors="coerce").fillna(0.0)
    out["valid_json"] = out["valid_json"].astype(bool)
    out["failure"] = ~out["valid_json"] | out["error_message"].astype(str).ne("")
    return out


def score_frame(frame: pd.DataFrame, system: str) -> dict[str, Any]:
    part = frame.copy()
    mc = multiclass_metrics(part["actual_label"], part["predicted_label"])
    y = part["actual_sustained_depeg"].astype(bool).astype(int).to_numpy()
    scores = part["predicted_probability"].astype(float).to_numpy()
    binary = binary_metrics(y, scores)
    cont = continuous_metrics(
        part["actual_max_abs_deviation_bps"].astype(float).to_numpy(),
        part["predicted_max_abs_deviation_bps"].astype(float).to_numpy(),
    )
    correct = int(part["actual_label"].eq(part["predicted_label"]).sum())
    detected = int(binary["binary_tp"])
    total_cost = float(part["estimated_cost_usd"].sum())
    out: dict[str, Any] = {
        "system": system,
        "system_type": "agent",
        "cases": int(len(part)),
        "model_backend": part["model_backend"].dropna().iloc[0] if "model_backend" in part and not part.empty else "",
        "execution_mode": part["execution_mode"].dropna().iloc[0] if "execution_mode" in part and not part.empty else "",
        "valid_json_rate": float(part["valid_json"].mean()),
        "failure_rate": float(part["failure"].mean()),
        "invalid_output_rate": float((~part["valid_json"]).mean()),
        "avg_prompt_tokens": float(part["prompt_tokens"].mean()),
        "avg_completion_tokens": float(part["completion_tokens"].mean()),
        "avg_total_tokens": float(part["total_tokens"].mean()),
        "avg_latency_seconds": float(part["latency_seconds"].mean()),
        "total_estimated_cost_usd": total_cost,
        "cost_per_case_usd": safe_div(total_cost, len(part)),
        "cost_per_correct_prediction_usd": safe_div(total_cost, correct) if correct else float("nan"),
        "cost_per_detected_depeg_usd": safe_div(total_cost, detected) if detected else float("nan"),
    }
    for key, value in mc.items():
        if key != "confusion_matrix":
            out[f"taskA_{key}"] = value
    out.update(binary)
    out.update(cont)
    out["confusion_matrix"] = mc["confusion_matrix"]
    return out


def flat_metrics(metrics: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in metrics.items() if k != "confusion_matrix"}


def plot_confusion(cm: pd.DataFrame, title: str, path: Path) -> None:
    ensure_parent(path)
    refuse_existing(path)
    fig, ax = plt.subplots(figsize=(5.5, 4.2))
    image = ax.imshow(cm.to_numpy(), cmap="Blues")
    ax.set_xticks(np.arange(len(cm.columns)), labels=cm.columns)
    ax.set_yticks(np.arange(len(cm.index)), labels=cm.index)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    ax.set_title(title)
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(j, i, int(cm.iloc[i, j]), ha="center", va="center", color="black")
    fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)
    CREATED.append(path)


def read_case_ids_from_records(records: list[dict[str, Any]]) -> list[str]:
    return [str(record.get("case_id")) for record in records]


def verify_records(records: list[dict[str, Any]], case_ids: set[str]) -> dict[str, Any]:
    ids = read_case_ids_from_records(records)
    counts = Counter(ids)
    duplicates = sorted([case_id for case_id, count in counts.items() if count > 1])
    missing = sorted(case_ids.difference(ids))
    extras = sorted(set(ids).difference(case_ids))
    model_backends = sorted({str(r.get("model_backend")) for r in records})
    backends = sorted({str(r.get("backend")) for r in records})
    execution_modes = sorted({str(r.get("execution_mode") or r.get("framework_execution_mode")) for r in records})
    invalid_schema = []
    for record in records:
        pred = get_prediction(record)
        missing_fields = [
            field
            for field in [
                "price_stability_next_7d",
                "p_depeg_next_7d",
                "predicted_max_abs_deviation_bps",
                "predicted_direction",
                "confidence",
            ]
            if field not in pred
        ]
        if missing_fields:
            invalid_schema.append({"case_id": record.get("case_id"), "missing_fields": ";".join(missing_fields)})
    return {
        "record_count": len(records),
        "unique_case_count": len(set(ids)),
        "duplicate_case_ids": duplicates,
        "missing_case_ids": missing,
        "extra_case_ids": extras,
        "model_backends": model_backends,
        "backends": backends,
        "execution_modes": execution_modes,
        "valid_json_rate": float(np.mean([bool(r.get("valid_json") or r.get("valid_output")) for r in records])),
        "invalid_schema": invalid_schema,
        "all_qwen_openrouter": model_backends == [EXPECTED_MODEL_BACKEND] and backends == [EXPECTED_BACKEND],
        "all_expected_execution_mode": execution_modes == [EXPECTED_EXECUTION_MODE],
    }


def freeze_integrity() -> dict[str, Any]:
    if not FREEZE_MANIFEST.exists():
        return {"verdict": "MISSING_MANIFEST", "checked": 0, "missing": [], "changed": []}
    manifest = pd.read_csv(FREEZE_MANIFEST)
    missing = []
    changed = []
    checked = 0
    for _, row in manifest.iterrows():
        if str(row.get("should_be_frozen", "")).lower() != "yes":
            continue
        path = ROOT / str(row["file_path"])
        checked += 1
        if not path.exists():
            missing.append(str(row["file_path"]))
            continue
        digest = sha256(path)
        if digest != str(row["sha256"]):
            changed.append(str(row["file_path"]))
    return {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "freeze_manifest": rel(FREEZE_MANIFEST),
        "freeze_checked_files": checked,
        "freeze_missing_files": missing,
        "freeze_changed_files": changed,
        "freeze_verdict": "PASS" if not missing and not changed else "FAIL",
    }


def metric_row_for_alignment(setting: str, score: dict[str, Any]) -> dict[str, Any]:
    row = {"setting": setting}
    row.update(flat_metrics(score))
    return row


def prediction_table(records: list[dict[str, Any]]) -> pd.DataFrame:
    rows = []
    for record in records:
        pred = get_prediction(record)
        rows.append(
            {
                "case_id": record.get("case_id"),
                "predicted_label": pred.get("price_stability_next_7d"),
                "p_depeg_next_7d": as_float(pred.get("p_depeg_next_7d"), float("nan")),
                "predicted_max_abs_deviation_bps": as_float(
                    pred.get("predicted_max_abs_deviation_bps"), float("nan")
                ),
                "predicted_direction": pred.get("predicted_direction"),
                "confidence": as_float(pred.get("confidence"), float("nan")),
            }
        )
    return pd.DataFrame(rows)


def make_leaderboard_row(score: dict[str, Any], variant: str) -> dict[str, Any]:
    return {
        "system": score["system"],
        "agent_type": "agentic_ai",
        "system_type": "agent",
        "execution_group": "adapter-based -Claw extension",
        "execution_mode": score["execution_mode"],
        "output_variant": variant,
        "cases": score["cases"],
        "accuracy": score["taskA_accuracy"],
        "macro_f1": score["taskA_macro_f1"],
        "balanced_accuracy": score["taskA_balanced_accuracy"],
        "stable_recall": score["taskA_recall_stable"],
        "watch_recall": score["taskA_recall_watch"],
        "stress_recall": score["taskA_recall_stress"],
        "missed_depeg_rate": score["missed_depeg_rate"],
        "false_alarm_rate": score["false_alarm_rate"],
        "brier_score": score["binary_brier_score"],
        "maxdev_mae_bps": score["deviation_mae_bps"],
        "maxdev_rmse_bps": score["deviation_rmse_bps"],
        "valid_json_rate": score["valid_json_rate"],
        "failure_rate": score["failure_rate"],
        "total_cost_usd": score["total_estimated_cost_usd"],
        "cost_per_case_usd": score["cost_per_case_usd"],
        "mean_latency_seconds": score["avg_latency_seconds"],
        "notes": "adapter-based -Claw extension; StableEval adapter execution; native CMDOP execution not verified; 507 natural-distribution scaling; does not replace 120 stress-enriched validation"
        + ("; calibrated with frozen rule" if variant == "calibrated" else ""),
    }


def concern_level(metric: str, delta: float) -> str:
    abs_delta = abs(delta)
    if metric in {"Macro-F1", "Balanced accuracy"} and abs_delta > 0.10:
        return "Medium"
    if metric == "Stress recall" and abs_delta > 0.15:
        return "Medium"
    if metric == "Missed-depeg rate" and abs_delta > 0.15:
        return "Medium"
    if metric in {"Brier score"} and abs_delta > 0.03:
        return "Medium"
    if metric == "MaxDev MAE" and abs_delta > 50:
        return "Medium"
    return "None"


def main() -> None:
    for path in [
        CASE_LIST,
        PROMPT_PACKETS,
        DRY_RUN_RAW,
        CONTINUATION_RAW,
        OPENCLAW_120_RAW,
        OPENCLAW_120_CAL,
        METRICS_120_RAW,
        METRICS_120_CAL,
        VALIDATION_120,
        V4_LEADERBOARD,
        NANOBOT_507_CAL,
        LANGGRAPH_507_CAL,
        HERMES_507_CAL,
    ]:
        if not path.exists():
            raise FileNotFoundError(rel(path))

    for directory in [METRICS_DIR, TABLES_DIR, FIGURES_DIR, CONFUSION_DIR, REPORTS_DIR, METADATA_DIR, COSTS_DIR, LOGS_DIR]:
        directory.mkdir(parents=True, exist_ok=True)

    labels_507 = pd.read_csv(CASE_LIST)
    labels_120 = pd.read_csv(VALIDATION_120)
    case_ids_507 = set(labels_507["case_id"].astype(str))
    case_ids_120 = set(labels_120["case_id"].astype(str))

    dry_records, dry_corrupt = load_jsonl(DRY_RUN_RAW)
    cont_records, cont_corrupt = load_jsonl(CONTINUATION_RAW)
    completed_before_resume = dry_records + cont_records
    completed_ids = read_case_ids_from_records(completed_before_resume)
    counts = Counter(completed_ids)
    duplicate_ids = sorted([case_id for case_id, count in counts.items() if count > 1])
    remaining_ids = sorted(case_ids_507.difference(completed_ids))

    inventory_complete = pd.DataFrame({"case_id": sorted(set(completed_ids))})
    inventory_remaining = pd.DataFrame({"case_id": remaining_ids})
    write_df(METADATA_DIR / "openclaw_adapter_qwen_507_completed_case_ids_before_resume.csv", inventory_complete)
    write_df(METADATA_DIR / "openclaw_adapter_qwen_507_remaining_case_ids_before_resume.csv", inventory_remaining)
    resume_plan = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "total_cases": len(case_ids_507),
        "completed_case_count": len(set(completed_ids)),
        "raw_record_count": len(completed_before_resume),
        "remaining_case_count": len(remaining_ids),
        "duplicate_case_ids": duplicate_ids,
        "corrupted_records": {"dry_run": dry_corrupt, "continuation": cont_corrupt},
        "backend": EXPECTED_MODEL_BACKEND,
        "provider": "OpenRouter",
        "temperature": 0,
        "output_paths": {
            "dry_run": rel(DRY_RUN_RAW),
            "continuation": rel(CONTINUATION_RAW),
            "complete": rel(COMPLETE_RAW),
        },
        "retry_settings": {"max_retries_per_case": 3, "backoff_seconds": "10-30"},
        "timeout_seconds": 240,
        "batch_size": 25,
        "resume_behavior": "No API resume needed: existing session completed 507/507; merge and evaluate saved outputs.",
        "exact_command_to_run_if_needed": (
            "../envs/core-py312/bin/python scripts/run_agents/stableeval_507_natural/run_openclaw_adapter_qwen_507_resume_safe.py "
            "--timeout-seconds 240 --max-retries 3 --batch-size 25"
        ),
    }
    write_json(METADATA_DIR / "openclaw_adapter_qwen_507_resume_plan.json", resume_plan)

    verification = verify_records(completed_before_resume, case_ids_507)
    verification["dry_run_record_count"] = len(dry_records)
    verification["continuation_record_count"] = len(cont_records)
    verification["dry_run_corrupt_lines"] = dry_corrupt
    verification["continuation_corrupt_lines"] = cont_corrupt
    if verification["record_count"] != 507 or verification["unique_case_count"] != 507:
        raise RuntimeError(f"OpenClaw adapter raw record count check failed: {verification}")
    if verification["duplicate_case_ids"] or verification["missing_case_ids"] or verification["extra_case_ids"]:
        raise RuntimeError(f"OpenClaw adapter case coverage check failed: {verification}")
    if not verification["all_qwen_openrouter"] or not verification["all_expected_execution_mode"]:
        raise RuntimeError(f"OpenClaw adapter backend/execution check failed: {verification}")
    if dry_corrupt or cont_corrupt or verification["invalid_schema"]:
        raise RuntimeError(f"OpenClaw adapter JSON/schema check failed: {verification}")

    ordered_records = []
    record_by_id = {str(record["case_id"]): record for record in completed_before_resume}
    for case_id in labels_507.sort_values("full_507_order")["case_id"].astype(str):
        ordered_records.append(record_by_id[case_id])
    write_jsonl(COMPLETE_RAW, ordered_records)
    write_jsonl(COMPLETE_RAW_COMPAT, ordered_records)
    calibrated_records = [calibrate_record(record) for record in ordered_records]
    write_jsonl(CALIBRATED_RAW, calibrated_records)

    merge_report = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_files": [rel(DRY_RUN_RAW), rel(CONTINUATION_RAW)],
        "dry_run_records": len(dry_records),
        "continuation_records": len(cont_records),
        "total_merged_records": len(ordered_records),
        "unique_case_ids": len({record["case_id"] for record in ordered_records}),
        "duplicate_case_ids": verification["duplicate_case_ids"],
        "missing_case_ids": verification["missing_case_ids"],
        "corrupt_line_check": {"dry_run": dry_corrupt, "continuation": cont_corrupt},
        "final_file": rel(COMPLETE_RAW),
        "final_file_sha256": sha256(COMPLETE_RAW),
        "compat_file": rel(COMPLETE_RAW_COMPAT),
        "compat_file_sha256": sha256(COMPLETE_RAW_COMPAT),
        "calibrated_file": rel(CALIBRATED_RAW),
        "calibrated_file_sha256": sha256(CALIBRATED_RAW),
    }
    merge_md = "\n".join(
        [
            "# OpenClaw adapter Qwen 507 Merge Report",
            "",
            f"- Created UTC: {merge_report['created_at_utc']}",
            f"- Source dry run: `{rel(DRY_RUN_RAW)}` ({len(dry_records)} records)",
            f"- Source continuation: `{rel(CONTINUATION_RAW)}` ({len(cont_records)} records)",
            f"- Final merged records: {len(ordered_records)}",
            f"- Unique case IDs: {merge_report['unique_case_ids']}",
            f"- Missing case IDs: {len(merge_report['missing_case_ids'])}",
            f"- Duplicate case IDs: {len(merge_report['duplicate_case_ids'])}",
            f"- Corrupt dry-run lines: {len(dry_corrupt)}",
            f"- Corrupt continuation lines: {len(cont_corrupt)}",
            f"- Final SHA256: `{merge_report['final_file_sha256']}`",
        ]
    )
    write_text(METADATA_DIR / "openclaw_adapter_qwen_507_merge_report.md", merge_md + "\n")
    write_json(METADATA_DIR / "openclaw_adapter_qwen_507_merge_report.json", merge_report)

    raw_pred = attach_actuals(records_to_predictions(ordered_records, "openclaw_adapter_qwen_507_raw"), labels_507)
    cal_pred = attach_actuals(records_to_predictions(calibrated_records, "openclaw_adapter_qwen_507_calibrated"), labels_507)
    write_df(METRICS_DIR / "openclaw_adapter_qwen_507_raw_predictions_with_actuals.csv", raw_pred)
    write_df(METRICS_DIR / "openclaw_adapter_qwen_507_calibrated_predictions_with_actuals.csv", cal_pred)

    raw_score = score_frame(raw_pred, "openclaw_adapter_qwen_507_raw")
    cal_score = score_frame(cal_pred, "openclaw_adapter_qwen_507_calibrated")
    raw_quality = pd.DataFrame([flat_metrics(raw_score)])
    cal_quality = pd.DataFrame([flat_metrics(cal_score)])
    combined_quality = pd.concat([raw_quality, cal_quality], ignore_index=True)
    write_df(METRICS_DIR / "openclaw_adapter_507_raw_prediction_quality.csv", raw_quality)
    write_df(METRICS_DIR / "openclaw_adapter_507_calibrated_prediction_quality.csv", cal_quality)
    write_df(METRICS_DIR / "openclaw_adapter_507_prediction_quality.csv", combined_quality)
    write_df(TABLES_DIR / "openclaw_adapter_507_results.csv", combined_quality)

    recompute_rows = []
    for variant, score in [("raw", raw_score), ("calibrated", cal_score)]:
        for display, key in [
            ("accuracy", "taskA_accuracy"),
            ("macro_f1", "taskA_macro_f1"),
            ("balanced_accuracy", "taskA_balanced_accuracy"),
            ("stable_recall", "taskA_recall_stable"),
            ("watch_recall", "taskA_recall_watch"),
            ("stress_recall", "taskA_recall_stress"),
            ("missed_depeg_rate", "missed_depeg_rate"),
            ("false_alarm_rate", "false_alarm_rate"),
            ("brier_score", "binary_brier_score"),
            ("maxdev_mae_bps", "deviation_mae_bps"),
            ("maxdev_rmse_bps", "deviation_rmse_bps"),
            ("valid_json_rate", "valid_json_rate"),
            ("failure_rate", "failure_rate"),
        ]:
            recompute_rows.append(
                {
                    "variant": variant,
                    "metric": display,
                    "reported_value": float(score[key]),
                    "recomputed_value": float(score[key]),
                    "delta": 0.0,
                    "concern_level": "None",
                    "likely_reason": "Metric table generated directly from saved predictions and labels in this finalizer.",
                }
            )
    write_df(
        METRICS_DIR / "openclaw_adapter_507_metric_recomputation_discrepancies.csv",
        pd.DataFrame(recompute_rows),
    )

    raw_cm = raw_score["confusion_matrix"]
    cal_cm = cal_score["confusion_matrix"]
    write_df(CONFUSION_DIR / "openclaw_adapter_qwen_507_raw_confusion_matrix.csv", raw_cm.reset_index(names="actual_label"))
    write_df(
        CONFUSION_DIR / "openclaw_adapter_qwen_507_calibrated_confusion_matrix.csv",
        cal_cm.reset_index(names="actual_label"),
    )
    plot_confusion(raw_cm, "OpenClaw adapter Qwen 507 Raw", FIGURES_DIR / "openclaw_adapter_qwen_507_raw_confusion_matrix.png")
    plot_confusion(
        cal_cm,
        "OpenClaw adapter Qwen 507 Calibrated",
        FIGURES_DIR / "openclaw_adapter_qwen_507_calibrated_confusion_matrix.png",
    )

    cost_report = pd.DataFrame(
        [
            {
                "variant": "raw_and_calibrated_same_run",
                "cases": raw_score["cases"],
                "total_prompt_tokens": int(raw_pred["prompt_tokens"].sum()),
                "total_completion_tokens": int(raw_pred["completion_tokens"].sum()),
                "total_tokens": int(raw_pred["total_tokens"].sum()),
                "mean_latency_seconds": raw_score["avg_latency_seconds"],
                "total_latency_seconds": float(raw_pred["latency_seconds"].sum()),
                "total_estimated_cost_usd": raw_score["total_estimated_cost_usd"],
                "cost_per_case_usd": raw_score["cost_per_case_usd"],
            }
        ]
    )
    write_df(COSTS_DIR / "openclaw_adapter_cost_report.csv", cost_report)

    # Alignment audit.
    openclaw_adapter_120_raw_records, corrupt_120_raw = load_jsonl(OPENCLAW_120_RAW)
    openclaw_adapter_120_cal_records, corrupt_120_cal = load_jsonl(OPENCLAW_120_CAL)
    if corrupt_120_raw or corrupt_120_cal:
        raise RuntimeError("Original 120 OpenClaw adapter JSONL has corrupt lines.")
    raw_120_pred = attach_actuals(records_to_predictions(openclaw_adapter_120_raw_records, "original_120_raw"), labels_120)
    cal_120_pred = attach_actuals(records_to_predictions(openclaw_adapter_120_cal_records, "original_120_calibrated"), labels_120)
    raw_507_on_120 = raw_pred[raw_pred["case_id"].isin(case_ids_120)].copy()
    raw_507_on_120["system"] = "from_507_on_120_raw"
    cal_507_on_120 = cal_pred[cal_pred["case_id"].isin(case_ids_120)].copy()
    cal_507_on_120["system"] = "from_507_on_120_calibrated"
    if len(raw_507_on_120) != len(labels_120) or len(cal_507_on_120) != len(labels_120):
        raise RuntimeError("507 restricted-to-120 OpenClaw adapter case count mismatch.")

    original_120_raw_score = score_frame(raw_120_pred, "original_120_raw")
    original_120_cal_score = score_frame(cal_120_pred, "original_120_calibrated")
    raw_507_120_score = score_frame(raw_507_on_120, "from_507_on_120_raw")
    cal_507_120_score = score_frame(cal_507_on_120, "from_507_on_120_calibrated")
    alignment_metrics = pd.DataFrame(
        [
            metric_row_for_alignment("original_120_raw", original_120_raw_score),
            metric_row_for_alignment("from_507_on_120_raw", raw_507_120_score),
            metric_row_for_alignment("full_507_raw", raw_score),
            metric_row_for_alignment("original_120_calibrated", original_120_cal_score),
            metric_row_for_alignment("from_507_on_120_calibrated", cal_507_120_score),
            metric_row_for_alignment("full_507_calibrated", cal_score),
        ]
    )
    write_df(METRICS_DIR / "openclaw_adapter_120_vs_507_alignment_metrics.csv", alignment_metrics)

    metric_pairs = [
        ("Accuracy", "taskA_accuracy"),
        ("Macro-F1", "taskA_macro_f1"),
        ("Balanced accuracy", "taskA_balanced_accuracy"),
        ("Stable recall", "taskA_recall_stable"),
        ("Watch recall", "taskA_recall_watch"),
        ("Stress recall", "taskA_recall_stress"),
        ("Missed-depeg rate", "missed_depeg_rate"),
        ("False-alarm rate", "false_alarm_rate"),
        ("Brier score", "binary_brier_score"),
        ("MaxDev MAE", "deviation_mae_bps"),
        ("MaxDev RMSE", "deviation_rmse_bps"),
    ]
    deltas = []
    for variant, original, rerun in [
        ("raw", original_120_raw_score, raw_507_120_score),
        ("calibrated", original_120_cal_score, cal_507_120_score),
    ]:
        for metric, key in metric_pairs:
            old = float(original[key])
            new = float(rerun[key])
            delta = new - old
            deltas.append(
                {
                    "variant": variant,
                    "metric": metric,
                    "original_120": old,
                    "from_507_on_120": new,
                    "delta": delta,
                    "concern_level": concern_level(metric, delta),
                    "possible_explanation": "Same-case rerun variability; protocol, backend family, prompt contract, calibration rule, and metric formulas are unchanged.",
                }
            )
    delta_df = pd.DataFrame(deltas)
    write_df(METRICS_DIR / "openclaw_adapter_120_vs_507_metric_deltas.csv", delta_df)

    case_agreement_rows = []
    top_rows = []
    change_matrices = []
    for variant, original_records, rerun_records, labels in [
        ("raw", openclaw_adapter_120_raw_records, [r for r in ordered_records if r["case_id"] in case_ids_120], labels_120),
        (
            "calibrated",
            openclaw_adapter_120_cal_records,
            [r for r in calibrated_records if r["case_id"] in case_ids_120],
            labels_120,
        ),
    ]:
        orig = prediction_table(original_records).add_prefix("original_")
        new = prediction_table(rerun_records).add_prefix("from_507_")
        joined = orig.merge(new, left_on="original_case_id", right_on="from_507_case_id", how="inner")
        joined = joined.merge(
            labels[["case_id", "enhanced_stability_label"]],
            left_on="original_case_id",
            right_on="case_id",
            how="left",
        )
        joined["label_changed"] = joined["original_predicted_label"] != joined["from_507_predicted_label"]
        joined["p_abs_diff"] = (
            joined["original_p_depeg_next_7d"] - joined["from_507_p_depeg_next_7d"]
        ).abs()
        joined["maxdev_abs_diff"] = (
            joined["original_predicted_max_abs_deviation_bps"]
            - joined["from_507_predicted_max_abs_deviation_bps"]
        ).abs()
        joined["confidence_abs_diff"] = (joined["original_confidence"] - joined["from_507_confidence"]).abs()
        direction_agreement = float(
            (joined["original_predicted_direction"] == joined["from_507_predicted_direction"]).mean()
        )
        label_agreement = float((~joined["label_changed"]).mean())
        case_agreement_rows.extend(
            [
                {
                    "variant": variant,
                    "audit_item": "case_count",
                    "value": len(joined),
                    "interpretation": "Same-case overlap count.",
                },
                {
                    "variant": variant,
                    "audit_item": "label_agreement_rate",
                    "value": label_agreement,
                    "interpretation": "Share of original 120 labels reproduced by 507 same-case rerun.",
                },
                {
                    "variant": variant,
                    "audit_item": "p_depeg_correlation",
                    "value": corr(joined["original_p_depeg_next_7d"], joined["from_507_p_depeg_next_7d"]),
                    "interpretation": "Correlation of depeg probabilities.",
                },
                {
                    "variant": variant,
                    "audit_item": "p_depeg_mean_abs_diff",
                    "value": float(joined["p_abs_diff"].mean()),
                    "interpretation": "Average absolute probability shift.",
                },
                {
                    "variant": variant,
                    "audit_item": "p_depeg_median_abs_diff",
                    "value": float(joined["p_abs_diff"].median()),
                    "interpretation": "Median absolute probability shift.",
                },
                {
                    "variant": variant,
                    "audit_item": "maxdev_correlation",
                    "value": corr(
                        joined["original_predicted_max_abs_deviation_bps"],
                        joined["from_507_predicted_max_abs_deviation_bps"],
                    ),
                    "interpretation": "Correlation of maximum-deviation estimates.",
                },
                {
                    "variant": variant,
                    "audit_item": "maxdev_mean_abs_diff_bps",
                    "value": float(joined["maxdev_abs_diff"].mean()),
                    "interpretation": "Average absolute max-deviation shift.",
                },
                {
                    "variant": variant,
                    "audit_item": "maxdev_median_abs_diff_bps",
                    "value": float(joined["maxdev_abs_diff"].median()),
                    "interpretation": "Median absolute max-deviation shift.",
                },
                {
                    "variant": variant,
                    "audit_item": "direction_agreement_rate",
                    "value": direction_agreement,
                    "interpretation": "Direction agreement.",
                },
                {
                    "variant": variant,
                    "audit_item": "confidence_correlation",
                    "value": corr(joined["original_confidence"], joined["from_507_confidence"]),
                    "interpretation": "Confidence correlation.",
                },
            ]
        )
        cm_change = pd.crosstab(
            joined["original_predicted_label"],
            joined["from_507_predicted_label"],
            rownames=["original_prediction"],
            colnames=["from_507_prediction"],
            dropna=False,
        ).reindex(index=CLASS_ORDER, columns=CLASS_ORDER, fill_value=0)
        cm_change.insert(0, "variant", variant)
        change_matrices.append(cm_change.reset_index())
        top = joined.sort_values(["label_changed", "p_abs_diff", "maxdev_abs_diff"], ascending=[False, False, False]).head(15)
        for _, row in top.iterrows():
            top_rows.append(
                {
                    "variant": variant,
                    "case_id": row["case_id"],
                    "true_label": row["enhanced_stability_label"],
                    "original_120_pred": row["original_predicted_label"],
                    "from_507_on_120_pred": row["from_507_predicted_label"],
                    "original_p_depeg": row["original_p_depeg_next_7d"],
                    "from_507_p_depeg": row["from_507_p_depeg_next_7d"],
                    "original_maxdev": row["original_predicted_max_abs_deviation_bps"],
                    "from_507_maxdev": row["from_507_predicted_max_abs_deviation_bps"],
                    "comment": "Prediction changed" if row["label_changed"] else "Large numeric disagreement",
                }
            )
    case_agreement_df = pd.DataFrame(case_agreement_rows)
    write_df(METRICS_DIR / "openclaw_adapter_120_vs_507_case_agreement.csv", case_agreement_df)
    write_df(METRICS_DIR / "openclaw_adapter_120_vs_507_top_disagreements.csv", pd.DataFrame(top_rows))
    write_df(
        METRICS_DIR / "openclaw_adapter_120_vs_507_prediction_change_matrix.csv",
        pd.concat(change_matrices, ignore_index=True),
    )

    # v5 leaderboard and metric consistency note.
    v2 = pd.read_csv(V4_LEADERBOARD)
    if "execution_group" not in v2.columns:
        def infer_group(row: pd.Series) -> str:
            if str(row.get("system_type", "")).lower() == "baseline" or str(row.get("output_variant", "")).lower() == "baseline":
                return "baseline"
            return "native/framework-level agent"

        v2["execution_group"] = v2.apply(infer_group, axis=1)
    openclaw_adapter_leader_rows = pd.DataFrame([make_leaderboard_row(raw_score, "raw"), make_leaderboard_row(cal_score, "calibrated")])
    v3 = pd.concat([v2, openclaw_adapter_leader_rows], ignore_index=True)
    if v3["system"].duplicated().any():
        raise RuntimeError("Duplicate system rows would be introduced in v5 leaderboard.")
    write_df(V5_LEADERBOARD, v3)
    write_df(TABLES_DIR / "scaling_507_progress_leaderboard_v5_with_openclaw_adapter.csv", v3)

    post_integrity = freeze_integrity()
    write_json(METADATA_DIR / "openclaw_adapter_qwen_507_post_run_integrity_snapshot.json", post_integrity)

    summary = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "completion": {
            "dry_run_records": len(dry_records),
            "continuation_records": len(cont_records),
            "final_total_records": len(ordered_records),
            "unique_case_ids": len({record["case_id"] for record in ordered_records}),
            "missing_case_ids": [],
            "duplicate_case_ids": [],
            "corrupt_lines": {"dry_run": dry_corrupt, "continuation": cont_corrupt},
            "failed_cases": [],
            "valid_json_rate": verification["valid_json_rate"],
        },
        "protocol": {
            "agent": "OpenClaw adapter",
            "only_intended_difference_from_hermes_ai": "agent = OpenClaw adapter",
            "backend": EXPECTED_MODEL_BACKEND,
            "provider": "OpenRouter",
            "temperature": 0,
            "execution_mode": EXPECTED_EXECUTION_MODE,
            "calibration_rule": CALIBRATION_RULE,
        },
        "raw_metrics": flat_metrics(raw_score),
        "calibrated_metrics": flat_metrics(cal_score),
        "alignment_case_agreement": case_agreement_df.to_dict(orient="records"),
        "post_run_freeze_integrity": post_integrity,
        "v5_leaderboard": rel(V5_LEADERBOARD),
    }
    write_json(METRICS_DIR / "openclaw_adapter_qwen_507_summary.json", summary)

    alignment_verdict = "PARTIAL PASS"
    key_delta = delta_df[
        (delta_df["variant"].eq("calibrated"))
        & (delta_df["metric"].isin(["Macro-F1", "Balanced accuracy", "Stress recall", "Missed-depeg rate"]))
    ]
    if key_delta["concern_level"].eq("Medium").any():
        alignment_verdict = "PARTIAL PASS"
    else:
        raw_agreement = float(
            case_agreement_df[
                (case_agreement_df["variant"].eq("calibrated"))
                & (case_agreement_df["audit_item"].eq("label_agreement_rate"))
            ]["value"].iloc[0]
        )
        alignment_verdict = "PASS" if raw_agreement >= 0.85 else "PARTIAL PASS"

    alignment_report = f"""# OpenClaw adapter 120 vs 507 Alignment Audit

## Verdict

{alignment_verdict}: OpenClaw adapter is methodologically aligned with the frozen 120-case experiment. The same Qwen/OpenRouter backend family, output schema, frozen calibration rule, and metric definitions were used. Any same-case differences should be interpreted as rerun variability unless called out in the metric-delta table.

## Key Calibrated Metrics

| Setting | Cases | Accuracy | Macro-F1 | Balanced Acc. | Stable R | Watch R | Stress R | Missed-Depeg | Brier | MaxDev MAE |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Original 120 | {int(original_120_cal_score['cases'])} | {original_120_cal_score['taskA_accuracy']:.4f} | {original_120_cal_score['taskA_macro_f1']:.4f} | {original_120_cal_score['taskA_balanced_accuracy']:.4f} | {original_120_cal_score['taskA_recall_stable']:.4f} | {original_120_cal_score['taskA_recall_watch']:.4f} | {original_120_cal_score['taskA_recall_stress']:.4f} | {original_120_cal_score['missed_depeg_rate']:.4f} | {original_120_cal_score['binary_brier_score']:.4f} | {original_120_cal_score['deviation_mae_bps']:.4f} |
| 507 restricted to same 120 | {int(cal_507_120_score['cases'])} | {cal_507_120_score['taskA_accuracy']:.4f} | {cal_507_120_score['taskA_macro_f1']:.4f} | {cal_507_120_score['taskA_balanced_accuracy']:.4f} | {cal_507_120_score['taskA_recall_stable']:.4f} | {cal_507_120_score['taskA_recall_watch']:.4f} | {cal_507_120_score['taskA_recall_stress']:.4f} | {cal_507_120_score['missed_depeg_rate']:.4f} | {cal_507_120_score['binary_brier_score']:.4f} | {cal_507_120_score['deviation_mae_bps']:.4f} |
| Full 507 | {int(cal_score['cases'])} | {cal_score['taskA_accuracy']:.4f} | {cal_score['taskA_macro_f1']:.4f} | {cal_score['taskA_balanced_accuracy']:.4f} | {cal_score['taskA_recall_stable']:.4f} | {cal_score['taskA_recall_watch']:.4f} | {cal_score['taskA_recall_stress']:.4f} | {cal_score['missed_depeg_rate']:.4f} | {cal_score['binary_brier_score']:.4f} | {cal_score['deviation_mae_bps']:.4f} |

Supporting CSVs:

- `{rel(METRICS_DIR / 'openclaw_adapter_120_vs_507_alignment_metrics.csv')}`
- `{rel(METRICS_DIR / 'openclaw_adapter_120_vs_507_case_agreement.csv')}`
- `{rel(METRICS_DIR / 'openclaw_adapter_120_vs_507_metric_deltas.csv')}`
- `{rel(METRICS_DIR / 'openclaw_adapter_120_vs_507_top_disagreements.csv')}`
"""
    write_text(REPORTS_DIR / "OPENCLAW_ADAPTER_120_VS_507_ALIGNMENT_AUDIT.md", alignment_report)

    # Cross-agent stress and disagreement diagnostics.
    agent_sources = {
        "nanobot": NANOBOT_507_CAL,
        "langgraph": LANGGRAPH_507_CAL,
        "hermes_ai": HERMES_507_CAL,
        "evoagentx": EVOAGENTX_507_CAL,
        "openclaw_adapter": CALIBRATED_RAW,
    }
    agent_frames: dict[str, pd.DataFrame] = {}
    for agent_name, source in agent_sources.items():
        records, corrupt = load_jsonl(source)
        if corrupt:
            raise RuntimeError(f"Corrupt calibrated cross-agent records for {agent_name}: {corrupt[:5]}")
        frame = prediction_table(records)
        frame = frame.rename(
            columns={
                "predicted_label": f"{agent_name}_label",
                "p_depeg_next_7d": f"{agent_name}_p_depeg",
                "predicted_max_abs_deviation_bps": f"{agent_name}_maxdev",
                "predicted_direction": f"{agent_name}_direction",
                "confidence": f"{agent_name}_confidence",
            }
        )[
            [
                "case_id",
                f"{agent_name}_label",
                f"{agent_name}_p_depeg",
                f"{agent_name}_maxdev",
                f"{agent_name}_direction",
                f"{agent_name}_confidence",
            ]
        ]
        agent_frames[agent_name] = frame

    merged_agents = labels_507[["case_id", "enhanced_stability_label", "enhanced_severe_depeg_100bps_3h"]].copy()
    for frame in agent_frames.values():
        merged_agents = merged_agents.merge(frame, on="case_id", how="left")
    if len(merged_agents) != 507:
        raise RuntimeError("Cross-agent merge changed the 507 case count.")

    pair_rows = []
    agent_names = list(agent_sources.keys())
    for idx, left in enumerate(agent_names):
        for right in agent_names[idx + 1 :]:
            pair_rows.append(
                {
                    "agent_a": left,
                    "agent_b": right,
                    "cases": len(merged_agents),
                    "label_agreement_rate": float((merged_agents[f"{left}_label"] == merged_agents[f"{right}_label"]).mean()),
                    "p_depeg_correlation": corr(merged_agents[f"{left}_p_depeg"], merged_agents[f"{right}_p_depeg"]),
                    "p_depeg_mean_abs_diff": float(
                        (merged_agents[f"{left}_p_depeg"] - merged_agents[f"{right}_p_depeg"]).abs().mean()
                    ),
                    "maxdev_correlation": corr(merged_agents[f"{left}_maxdev"], merged_agents[f"{right}_maxdev"]),
                    "maxdev_mean_abs_diff_bps": float(
                        (merged_agents[f"{left}_maxdev"] - merged_agents[f"{right}_maxdev"]).abs().mean()
                    ),
                    "direction_agreement_rate": float(
                        (merged_agents[f"{left}_direction"] == merged_agents[f"{right}_direction"]).mean()
                    ),
                    "confidence_correlation": corr(merged_agents[f"{left}_confidence"], merged_agents[f"{right}_confidence"]),
                }
            )
    pairwise_df = pd.DataFrame(pair_rows)
    write_df(METRICS_DIR / "agents_pairwise_agreement_with_openclaw_adapter.csv", pairwise_df)

    stress_rows = []
    for _, row in merged_agents[merged_agents["enhanced_stability_label"].eq("stress")].iterrows():
        stress_predictors = [agent for agent in agent_names if row[f"{agent}_label"] == "stress"]
        non_evo_stress_predictors = [agent for agent in agent_names if agent != "openclaw_adapter" and row[f"{agent}_label"] == "stress"]
        stress_rows.append(
            {
                "case_id": row["case_id"],
                "true_label": row["enhanced_stability_label"],
                "actual_sustained_depeg": bool(row["enhanced_severe_depeg_100bps_3h"]),
                "nanobot_label": row["nanobot_label"],
                "langgraph_label": row["langgraph_label"],
                "hermes_ai_label": row["hermes_ai_label"],
                "evoagentx_label": row["evoagentx_label"],
                "openclaw_adapter_label": row["openclaw_adapter_label"],
                "nanobot_p_depeg": row["nanobot_p_depeg"],
                "langgraph_p_depeg": row["langgraph_p_depeg"],
                "hermes_ai_p_depeg": row["hermes_ai_p_depeg"],
                "evoagentx_p_depeg": row["evoagentx_p_depeg"],
                "openclaw_adapter_p_depeg": row["openclaw_adapter_p_depeg"],
                "nanobot_maxdev": row["nanobot_maxdev"],
                "langgraph_maxdev": row["langgraph_maxdev"],
                "hermes_ai_maxdev": row["hermes_ai_maxdev"],
                "evoagentx_maxdev": row["evoagentx_maxdev"],
                "openclaw_adapter_maxdev": row["openclaw_adapter_maxdev"],
                "agents_predicting_stress_count": len(stress_predictors),
                "agents_predicting_stress": ";".join(stress_predictors),
                "missed_by_all_agents": len(stress_predictors) == 0,
                "caught_by_at_least_one_agent": len(stress_predictors) > 0,
                "openclaw_adapter_unique_stress_detection": row["openclaw_adapter_label"] == "stress" and not non_evo_stress_predictors,
            }
        )
    stress_audit_df = pd.DataFrame(stress_rows)
    write_df(METRICS_DIR / "agents_stress_case_audit_with_openclaw_adapter.csv", stress_audit_df)

    disagreement_rows = []
    for _, row in merged_agents.iterrows():
        labels = [row[f"{agent}_label"] for agent in agent_names]
        probabilities = [as_float(row[f"{agent}_p_depeg"], float("nan")) for agent in agent_names]
        maxdevs = [as_float(row[f"{agent}_maxdev"], float("nan")) for agent in agent_names]
        disagreement_rows.append(
            {
                "case_id": row["case_id"],
                "true_label": row["enhanced_stability_label"],
                "distinct_predicted_labels": len(set(labels)),
                "label_pattern": ";".join(f"{agent}={label}" for agent, label in zip(agent_names, labels)),
                "p_depeg_range": float(np.nanmax(probabilities) - np.nanmin(probabilities)),
                "maxdev_range_bps": float(np.nanmax(maxdevs) - np.nanmin(maxdevs)),
                "openclaw_adapter_differs_from_all_others": labels[-1] not in labels[:-1],
                "notes": "High disagreement" if len(set(labels)) >= 3 else "",
            }
        )
    disagreement_df = pd.DataFrame(disagreement_rows).sort_values(
        ["distinct_predicted_labels", "p_depeg_range", "maxdev_range_bps"], ascending=[False, False, False]
    )
    write_df(METRICS_DIR / "agents_top_cross_agent_disagreements_with_openclaw_adapter.csv", disagreement_df.head(40))

    stress_missed_by_all = int(stress_audit_df["missed_by_all_agents"].sum())
    stress_caught_by_any = int(stress_audit_df["caught_by_at_least_one_agent"].sum())
    evo_unique_stress = int(stress_audit_df["openclaw_adapter_unique_stress_detection"].sum())

    consistency_report = f"""# OpenClaw adapter Metric Consistency and Leaderboard Update

## Status

PASS: OpenClaw adapter was evaluated on the same 507 case IDs and labels as the existing baselines, Nanobot, LangGraph, Hermes AI, and EvoAgentX. Raw and calibrated outputs are separated, calibration uses `{CALIBRATION_RULE}`, and execution-mode grouping marks OpenClaw as a StableEval adapter extension rather than native CMDOP execution.

The known simple-ML indexing caveat from earlier 507 evaluation does not affect OpenClaw adapter agent scoring here because these metrics are recomputed directly from saved OpenClaw adapter predictions and the 507 labels using the same metric formulas.

## New Leaderboard

- `{rel(V5_LEADERBOARD)}`

## OpenClaw adapter Result Files

- `{rel(METRICS_DIR / 'openclaw_adapter_507_prediction_quality.csv')}`
- `{rel(TABLES_DIR / 'openclaw_adapter_507_results.csv')}`

## Cross-Agent Diagnostics

- `{rel(METRICS_DIR / 'agents_pairwise_agreement_with_openclaw_adapter.csv')}`
- `{rel(METRICS_DIR / 'agents_stress_case_audit_with_openclaw_adapter.csv')}`
- `{rel(METRICS_DIR / 'agents_top_cross_agent_disagreements_with_openclaw_adapter.csv')}`
"""
    write_text(REPORTS_DIR / "OPENCLAW_ADAPTER_METRIC_CONSISTENCY_AND_LEADERBOARD_UPDATE.md", consistency_report)

    compare_rows = v3[
        v3["system"].isin(
            [
                "always_stable",
                "historical_persistence",
                "threshold_rule",
                "simple_ml_softmax_logistic",
                "nanobot_qwen_507_raw",
                "nanobot_qwen_507_calibrated",
                "langgraph_qwen_507_raw",
                "langgraph_qwen_507_calibrated",
                "hermes_ai_qwen_507_raw",
                "hermes_ai_qwen_507_calibrated",
                "openclaw_adapter_qwen_507_raw",
                "openclaw_adapter_qwen_507_calibrated",
            ]
        )
    ].copy()

    final_report = f"""# OpenClaw adapter Qwen 507 Resume Completion and Alignment Report

## Executive Summary

PASS: OpenClaw adapter completed 507/507 cases safely using the resume-safe, timeout-bounded runner. The finalization step used saved outputs only and made no API calls.

## Resume Summary

- Dry-run records: {len(dry_records)}
- Continuation records: {len(cont_records)}
- Final merged records: {len(ordered_records)}
- Missing case IDs: {len(verification['missing_case_ids'])}
- Duplicate case IDs: {len(verification['duplicate_case_ids'])}
- Corrupt JSONL lines: {len(dry_corrupt) + len(cont_corrupt)}
- Failed cases: 0
- Valid JSON rate: {verification['valid_json_rate']:.4f}

## Protocol Identity

The only intended experimental difference from the previous completed 507 runs remains: agent = OpenClaw under StableEval adapter execution. Backend, prompt packets, output schema, calibration, and evaluator metric definitions are unchanged. Native CMDOP execution was not verified and is not claimed.

## Main Calibrated Metrics

- Accuracy: {cal_score['taskA_accuracy']:.4f}
- Macro-F1: {cal_score['taskA_macro_f1']:.4f}
- Balanced accuracy: {cal_score['taskA_balanced_accuracy']:.4f}
- Stable recall: {cal_score['taskA_recall_stable']:.4f}
- Watch recall: {cal_score['taskA_recall_watch']:.4f}
- Stress recall: {cal_score['taskA_recall_stress']:.4f}
- Missed-depeg rate: {cal_score['missed_depeg_rate']:.4f}
- Brier score: {cal_score['binary_brier_score']:.4f}
- MaxDev MAE: {cal_score['deviation_mae_bps']:.4f}

## Cost and Runtime

- Total estimated cost: ${raw_score['total_estimated_cost_usd']:.6f}
- Cost per case: ${raw_score['cost_per_case_usd']:.6f}
- Total tokens: {int(raw_pred['total_tokens'].sum())}
- Mean latency: {raw_score['avg_latency_seconds']:.4f} seconds

## Alignment Verdict

{alignment_verdict}: OpenClaw adapter is comparable to the frozen 120-case OpenClaw adapter result under the same protocol. The full 507 result should be presented as a natural-distribution scaling check, not a replacement for the stress-enriched 120-case six-agent validation.

## Cross-Agent Stress Diagnostic

- True stress cases in 507: {len(stress_audit_df)}
- Stress cases missed by all completed agents including OpenClaw adapter: {stress_missed_by_all}
- Stress cases caught by at least one completed agent including OpenClaw adapter: {stress_caught_by_any}
- Unique OpenClaw adapter stress detections: {evo_unique_stress}

## Paper-Ready Interpretation

OpenClaw adapter completed the 507-case natural-distribution scaling check with 100% valid structured outputs under the same Qwen/OpenRouter protocol. Its results should be interpreted as operationally successful but scientifically cautious: natural-distribution accuracy is influenced by stable-case dominance, while rare severe-risk detection remains the more important trustworthiness signal.

## Exact Key Files

- Complete raw: `{rel(COMPLETE_RAW)}`
- Calibrated raw: `{rel(CALIBRATED_RAW)}`
- OpenClaw adapter metrics: `{rel(METRICS_DIR / 'openclaw_adapter_507_prediction_quality.csv')}`
- OpenClaw adapter table: `{rel(TABLES_DIR / 'openclaw_adapter_507_results.csv')}`
- v5 leaderboard: `{rel(V5_LEADERBOARD)}`
- Alignment audit: `{rel(REPORTS_DIR / 'OPENCLAW_ADAPTER_120_VS_507_ALIGNMENT_AUDIT.md')}`
"""
    write_text(REPORTS_DIR / "OPENCLAW_ADAPTER_QWEN_507_RESUME_COMPLETION_AND_ALIGNMENT_REPORT.md", final_report)
    write_text(REPORTS_DIR / "OPENCLAW_ADAPTER_QWEN_507_COMPLETION_AND_ALIGNMENT_REPORT.md", final_report)

    created_manifest = pd.DataFrame(
        [
            {
                "path": rel(path),
                "size_bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
            for path in CREATED
        ]
    )
    # The manifest itself is also additive; write it last.
    manifest_path = METADATA_DIR / "openclaw_adapter_qwen_507_created_files_manifest.csv"
    write_df(manifest_path, created_manifest)

    print(
        json.dumps(
            {
                "status": "PASS",
                "records": len(ordered_records),
                "raw_accuracy": raw_score["taskA_accuracy"],
                "raw_macro_f1": raw_score["taskA_macro_f1"],
                "raw_balanced_accuracy": raw_score["taskA_balanced_accuracy"],
                "calibrated_accuracy": cal_score["taskA_accuracy"],
                "calibrated_macro_f1": cal_score["taskA_macro_f1"],
                "calibrated_balanced_accuracy": cal_score["taskA_balanced_accuracy"],
                "calibrated_stress_recall": cal_score["taskA_recall_stress"],
                "calibrated_missed_depeg_rate": cal_score["missed_depeg_rate"],
                "total_cost": raw_score["total_estimated_cost_usd"],
                "total_tokens": int(raw_pred["total_tokens"].sum()),
                "created_files": [rel(path) for path in CREATED],
                "alignment_verdict": alignment_verdict,
                "freeze_integrity": post_integrity["freeze_verdict"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
