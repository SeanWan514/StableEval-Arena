#!/usr/bin/env python3
"""Evaluate the StableEval paper pilot with baselines, costs, and paper tables."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


CLASS_ORDER = ["stable", "watch", "stress"]
CONFUSION_COLUMNS = ["stable", "watch", "stress", "invalid"]
CLASS_TO_INT = {label: idx for idx, label in enumerate(CLASS_ORDER)}
PLATFORMS = ["nanobot", "langgraph", "hermes_ai", "evoagentx", "openclaw", "nanoclaw"]


def safe_div(num: float, den: float) -> float:
    return float(num / den) if den else 0.0


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
    per_class: dict[str, float] = {}
    recalls = []
    f1s = []
    precisions = []
    for label in CLASS_ORDER:
        tp = int(cm.loc[label, label])
        actual_total = int(cm.loc[label, :].sum())
        pred_total = int(cm.loc[:, label].sum())
        precision = safe_div(tp, pred_total)
        recall = safe_div(tp, actual_total)
        f1 = safe_div(2 * precision * recall, precision + recall)
        per_class[f"precision_{label}"] = precision
        per_class[f"recall_{label}"] = recall
        precisions.append(precision)
        recalls.append(recall)
        f1s.append(f1)
    return {
        "accuracy": safe_div(correct, total),
        "macro_f1": float(np.mean(f1s)),
        "balanced_accuracy": float(np.mean(recalls)),
        **per_class,
        "confusion_matrix": cm,
    }


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


def packet_hashless_features(packet: dict[str, Any]) -> dict[str, float]:
    evidence = packet.get("evidence", {})
    latest = evidence.get("latest_observation", {})
    lookback = evidence.get("lookback_summary", {})
    context = evidence.get("context", {})
    last_48 = evidence.get("last_48_hourly_observations", []) or []
    abs_48 = np.array([float(row.get("abs_close_deviation") or 0.0) * 10000 for row in last_48], dtype=float)
    period_48 = np.array([float(row.get("max_period_deviation") or 0.0) * 10000 for row in last_48], dtype=float)
    features = {
        "latest_close_deviation_bps": float(latest.get("close_deviation_bps") or 0.0),
        "latest_market_share": float(latest.get("stablecoin_market_share") or 0.0),
        "latest_chain_count": float(latest.get("chain_count") or 0.0),
        "latest_top_chain_share": float(latest.get("top_chain_share") or 0.0),
        "lookback_mean_abs_close_deviation_bps": float(lookback.get("mean_abs_close_deviation_bps") or 0.0),
        "lookback_max_abs_close_deviation_bps": float(lookback.get("max_abs_close_deviation_bps") or 0.0),
        "lookback_max_period_deviation_bps": float(lookback.get("max_period_deviation_bps") or 0.0),
        "lookback_volatility_7d": float(lookback.get("volatility_7d") or 0.0),
        "lookback_volatility_30d": float(lookback.get("volatility_30d") or 0.0),
        "lookback_volume_change_7d": float(lookback.get("volume_change_7d") or 0.0),
        "lookback_market_cap_change_7d": float(lookback.get("market_cap_change_7d") or 0.0),
        "lookback_supply_change_7d": float(lookback.get("supply_change_7d") or 0.0),
        "btc_7d_return": float(context.get("btc_7d_return") or 0.0),
        "eth_7d_return": float(context.get("eth_7d_return") or 0.0),
        "btc_7d_volatility": float(context.get("btc_7d_volatility") or 0.0),
        "eth_7d_volatility": float(context.get("eth_7d_volatility") or 0.0),
        "last48_max_abs_close_deviation_bps": float(abs_48.max() if len(abs_48) else 0.0),
        "last48_mean_abs_close_deviation_bps": float(abs_48.mean() if len(abs_48) else 0.0),
        "last48_hours_ge_25bps": float((abs_48 >= 25).sum() if len(abs_48) else 0.0),
        "last48_hours_ge_50bps": float((abs_48 >= 50).sum() if len(abs_48) else 0.0),
        "last48_max_period_deviation_bps": float(period_48.max() if len(period_48) else 0.0),
        "coin_USDT": 1.0 if packet.get("stablecoin") == "USDT" else 0.0,
        "coin_USDC": 1.0 if packet.get("stablecoin") == "USDC" else 0.0,
        "coin_DAI": 1.0 if packet.get("stablecoin") == "DAI" else 0.0,
    }
    return features


def load_packets(path: Path) -> dict[str, dict[str, Any]]:
    packets = {}
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            packet = json.loads(line)
            packets[packet["case_id"]] = packet
    return packets


def rule_direction(packet: dict[str, Any]) -> str:
    latest = packet.get("evidence", {}).get("latest_observation", {})
    deviation = float(latest.get("close_deviation_bps") or 0.0)
    if deviation <= -10:
        return "below_peg"
    if deviation >= 10:
        return "above_peg"
    return "two_sided_or_no_meaningful"


def baseline_records(
    labels: pd.DataFrame,
    packets: dict[str, dict[str, Any]],
    baseline_name: str,
) -> pd.DataFrame:
    rows = []
    for _, label in labels.iterrows():
        case_id = label["case_id"]
        packet = packets[case_id]
        features = packet_hashless_features(packet)
        lb_max = features["lookback_max_abs_close_deviation_bps"]
        lb_mean = features["lookback_mean_abs_close_deviation_bps"]
        lb_vol = features["lookback_volatility_30d"]
        last48_max = features["last48_max_abs_close_deviation_bps"]
        if baseline_name == "always_stable":
            pred_label = "stable"
            p = 0.01
            pred_bps = 10.0
        elif baseline_name == "historical_persistence":
            pred_bps = max(lb_max, last48_max)
            if pred_bps >= 100 or lb_mean >= 25:
                pred_label = "stress"
            elif pred_bps >= 50 or lb_mean >= 10:
                pred_label = "watch"
            else:
                pred_label = "stable"
            p = min(0.95, max(0.01, pred_bps / 200.0))
        elif baseline_name == "threshold_rule":
            pred_bps = max(lb_max, last48_max, lb_mean * 3.0)
            if lb_max >= 100 or lb_mean >= 20 or last48_max >= 75 or lb_vol >= 0.003:
                pred_label = "stress"
            elif lb_max >= 50 or lb_mean >= 8 or last48_max >= 25 or lb_vol >= 0.001:
                pred_label = "watch"
            else:
                pred_label = "stable"
            p = min(0.95, max(0.01, 0.01 + pred_bps / 250.0 + 20.0 * lb_vol))
        else:
            raise ValueError(baseline_name)
        rows.append(
            {
                "case_id": case_id,
                "stablecoin": label["stablecoin"],
                "system": baseline_name,
                "system_type": "baseline",
                "platform": baseline_name,
                "model_backend": "baseline",
                "execution_mode": "deterministic_baseline",
                "predicted_label": pred_label,
                "predicted_probability": p,
                "predicted_max_abs_deviation_bps": pred_bps,
                "predicted_direction": rule_direction(packet),
                "confidence": 1.0,
                "valid_json": True,
                "failure": False,
                "latency_seconds": 0.0,
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
                "estimated_cost_usd": 0.0,
                "raw_agent_output": "",
                "parsed_json": "",
                "error_message": "",
                "rationale": f"{baseline_name} baseline",
            }
        )
    return pd.DataFrame(rows)


def feature_matrix(labels: pd.DataFrame, packets: dict[str, dict[str, Any]]) -> tuple[np.ndarray, list[str]]:
    rows = [packet_hashless_features(packets[case_id]) for case_id in labels["case_id"]]
    feature_names = sorted(rows[0].keys())
    X = np.array([[row.get(name, 0.0) for name in feature_names] for row in rows], dtype=float)
    X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
    return X, feature_names


def standardize(train: np.ndarray, test: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    mean = train.mean(axis=0)
    std = train.std(axis=0)
    std[std < 1e-8] = 1.0
    return (train - mean) / std, (test - mean) / std


def softmax(z: np.ndarray) -> np.ndarray:
    z = z - z.max(axis=1, keepdims=True)
    ez = np.exp(z)
    return ez / ez.sum(axis=1, keepdims=True)


def train_softmax(X: np.ndarray, y: np.ndarray, classes: int = 3, steps: int = 1200) -> np.ndarray:
    Xb = np.column_stack([np.ones(len(X)), X])
    W = np.zeros((Xb.shape[1], classes))
    counts = np.bincount(y, minlength=classes).astype(float)
    weights = len(y) / np.maximum(counts, 1.0)
    lr = 0.04
    reg = 0.001
    Y = np.eye(classes)[y]
    for _ in range(steps):
        P = softmax(Xb @ W)
        sample_weights = weights[y][:, None]
        grad = Xb.T @ ((P - Y) * sample_weights) / len(Xb) + reg * W
        W -= lr * grad
    return W


def predict_softmax(W: np.ndarray, X: np.ndarray) -> np.ndarray:
    Xb = np.column_stack([np.ones(len(X)), X])
    return softmax(Xb @ W)


def train_logistic(X: np.ndarray, y: np.ndarray, steps: int = 1200) -> np.ndarray:
    Xb = np.column_stack([np.ones(len(X)), X])
    w = np.zeros(Xb.shape[1])
    pos = max(float(y.sum()), 1.0)
    neg = max(float((1 - y).sum()), 1.0)
    weights = np.where(y == 1, len(y) / pos, len(y) / neg)
    lr = 0.04
    reg = 0.001
    for _ in range(steps):
        z = Xb @ w
        p = 1.0 / (1.0 + np.exp(-np.clip(z, -50, 50)))
        grad = Xb.T @ ((p - y) * weights) / len(Xb) + reg * w
        w -= lr * grad
    return w


def predict_logistic(w: np.ndarray, X: np.ndarray) -> np.ndarray:
    Xb = np.column_stack([np.ones(len(X)), X])
    z = Xb @ w
    return 1.0 / (1.0 + np.exp(-np.clip(z, -50, 50)))


def train_ridge(X: np.ndarray, y: np.ndarray, ridge: float = 1.0) -> np.ndarray:
    Xb = np.column_stack([np.ones(len(X)), X])
    eye = np.eye(Xb.shape[1])
    eye[0, 0] = 0.0
    return np.linalg.pinv(Xb.T @ Xb + ridge * eye) @ Xb.T @ np.log1p(np.maximum(y, 0))


def predict_ridge(w: np.ndarray, X: np.ndarray) -> np.ndarray:
    Xb = np.column_stack([np.ones(len(X)), X])
    return np.maximum(0.0, np.expm1(Xb @ w))


def fit_ml_predict(train_labels: pd.DataFrame, test_labels: pd.DataFrame, packets: dict[str, dict[str, Any]]) -> pd.DataFrame:
    train_X, _ = feature_matrix(train_labels, packets)
    test_X, _ = feature_matrix(test_labels, packets)
    train_Xs, test_Xs = standardize(train_X, test_X)
    y_multi = train_labels["enhanced_stability_label"].map(CLASS_TO_INT).to_numpy(dtype=int)
    y_binary = train_labels["enhanced_severe_depeg_100bps_3h"].astype(int).to_numpy()
    y_bps = train_labels["horizon_max_abs_deviation_bps"].astype(float).to_numpy()
    W = train_softmax(train_Xs, y_multi)
    w_bin = train_logistic(train_Xs, y_binary)
    w_bps = train_ridge(train_Xs, y_bps)
    probs = predict_softmax(W, test_Xs)
    binary_probs = predict_logistic(w_bin, test_Xs)
    pred_bps = predict_ridge(w_bps, test_Xs)
    labels = [CLASS_ORDER[int(idx)] for idx in probs.argmax(axis=1)]
    rows = []
    for idx, (_, label) in enumerate(test_labels.iterrows()):
        rows.append(
            {
                "case_id": label["case_id"],
                "stablecoin": label["stablecoin"],
                "system": "simple_ml_softmax_logistic",
                "system_type": "baseline",
                "platform": "simple_ml_softmax_logistic",
                "model_backend": "baseline_numpy_softmax_logistic",
                "execution_mode": "supervised_baseline_train_non_test_cases",
                "predicted_label": labels[idx],
                "predicted_probability": float(binary_probs[idx]),
                "predicted_max_abs_deviation_bps": float(pred_bps[idx]),
                "predicted_direction": "two_sided_or_no_meaningful",
                "confidence": float(probs[idx].max()),
                "valid_json": True,
                "failure": False,
                "latency_seconds": 0.0,
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
                "estimated_cost_usd": 0.0,
                "raw_agent_output": "",
                "parsed_json": "",
                "error_message": "",
                "rationale": "Numpy softmax/logistic baseline trained on non-test cases using only lookback features.",
            }
        )
    return pd.DataFrame(rows)


def ml_pilot_predictions(all_labels: pd.DataFrame, pilot_labels: pd.DataFrame, packets: dict[str, dict[str, Any]]) -> pd.DataFrame:
    train = all_labels[~all_labels["case_id"].isin(set(pilot_labels["case_id"]))].reset_index(drop=True)
    return fit_ml_predict(train, pilot_labels.reset_index(drop=True), packets)


def ml_cv_predictions(all_labels: pd.DataFrame, packets: dict[str, dict[str, Any]], folds: int = 5) -> pd.DataFrame:
    labels = all_labels.reset_index(drop=True).copy()
    labels["fold"] = -1
    for _, group in labels.groupby("enhanced_stability_label"):
        ordered = group.sort_values("case_id").index.to_list()
        for pos, idx in enumerate(ordered):
            labels.loc[idx, "fold"] = pos % folds
    outputs = []
    for fold in range(folds):
        train = labels[labels["fold"] != fold].drop(columns=["fold"]).reset_index(drop=True)
        test = labels[labels["fold"] == fold].drop(columns=["fold"]).reset_index(drop=True)
        outputs.append(fit_ml_predict(train, test, packets))
    return pd.concat(outputs, ignore_index=True)


def load_agent_predictions(pred_dir: Path, labels: pd.DataFrame) -> pd.DataFrame:
    rows = []
    label_case_ids = set(labels["case_id"])
    for path in sorted(pred_dir.glob("*_predictions.jsonl")):
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                item = json.loads(line)
                if item.get("case_id") not in label_case_ids:
                    continue
                pred = item.get("parsed_json") or item.get("prediction") or {}
                rows.append(
                    {
                        "case_id": item.get("case_id"),
                        "stablecoin": item.get("stablecoin"),
                        "system": item.get("platform"),
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
    out["failure"] = ~out["valid_json"].astype(bool) | out["error_message"].astype(str).ne("")
    return out


def score_system(frame: pd.DataFrame, system: str) -> dict[str, Any]:
    part = frame[frame["system"].eq(system)].copy()
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
    output: dict[str, Any] = {
        "system": system,
        "system_type": part["system_type"].iloc[0],
        "cases": int(len(part)),
        "model_backend": part["model_backend"].iloc[0] if "model_backend" in part else "",
        "execution_mode": part["execution_mode"].iloc[0] if "execution_mode" in part else "",
        "valid_json_rate": float(part["valid_json"].mean()),
        "failure_rate": float(part["failure"].mean()),
        "invalid_output_rate": float((~part["valid_json"].astype(bool)).mean()),
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
            output[f"taskA_{key}"] = value
    output.update(binary)
    output.update(cont)
    output["confusion_matrix"] = mc["confusion_matrix"]
    return output


def dataframe_without_matrices(rows: list[dict[str, Any]]) -> pd.DataFrame:
    cleaned = []
    for row in rows:
        copy = {k: v for k, v in row.items() if k != "confusion_matrix"}
        cleaned.append(copy)
    return pd.DataFrame(cleaned)


def markdown_table(frame: pd.DataFrame, columns: list[str] | None = None) -> str:
    if columns is not None:
        frame = frame[columns]
    if frame.empty:
        return ""
    text = frame.copy()
    for col in text.columns:
        if pd.api.types.is_numeric_dtype(text[col]):
            text[col] = text[col].map(lambda x: "" if pd.isna(x) else f"{float(x):.4g}")
        else:
            text[col] = text[col].astype(str)
    lines = [
        "| " + " | ".join(text.columns) + " |",
        "| " + " | ".join(["---"] * len(text.columns)) + " |",
    ]
    for _, row in text.iterrows():
        lines.append("| " + " | ".join(str(row[col]).replace("\n", " ") for col in text.columns) + " |")
    return "\n".join(lines)


def plot_confusion(cm: pd.DataFrame, title: str, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(5.2, 4.2))
    values = cm.to_numpy()
    ax.imshow(values, cmap="Blues")
    ax.set_xticks(range(len(cm.columns)), cm.columns, rotation=35, ha="right")
    ax.set_yticks(range(len(cm.index)), cm.index)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    ax.set_title(title)
    vmax = values.max() if values.size else 0
    for i in range(values.shape[0]):
        for j in range(values.shape[1]):
            ax.text(j, i, int(values[i, j]), ha="center", va="center", color="white" if values[i, j] > vmax / 2 else "black")
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def write_figures(out_dir: Path, pilot_labels: pd.DataFrame, quality: pd.DataFrame, cost: pd.DataFrame) -> None:
    fig_dir = out_dir / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)

    counts = pilot_labels["enhanced_stability_label"].value_counts().reindex(CLASS_ORDER).fillna(0)
    fig, ax = plt.subplots(figsize=(5, 3.4))
    ax.bar(counts.index, counts.values, color=["#4b8bbe", "#d9a441", "#c44e52"])
    ax.set_ylabel("Cases")
    ax.set_title("Evaluation Label Distribution")
    fig.tight_layout()
    fig.savefig(fig_dir / "pilot_label_distribution.png", dpi=180)
    plt.close(fig)

    plot_quality = quality.sort_values("taskA_macro_f1", ascending=True)
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.barh(plot_quality["system"], plot_quality["taskA_macro_f1"], color="#4b8bbe")
    ax.set_xlabel("Macro-F1")
    ax.set_title("3-Class Prediction Quality")
    fig.tight_layout()
    fig.savefig(fig_dir / "prediction_quality_by_platform.png", dpi=180)
    plt.close(fig)

    cost_plot = cost[cost["system_type"].eq("agent")].sort_values("cost_per_case_usd", ascending=True)
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.barh(cost_plot["system"], cost_plot["cost_per_case_usd"], color="#6f8f72")
    ax.set_xlabel("Estimated USD per case")
    ax.set_title("Computational Cost")
    fig.tight_layout()
    fig.savefig(fig_dir / "computational_cost_by_platform.png", dpi=180)
    plt.close(fig)


def write_summary(
    out_dir: Path,
    case_count: int,
    quality: pd.DataFrame,
    cost: pd.DataFrame,
    baseline_comparison: pd.DataFrame,
    adapter_metadata: pd.DataFrame,
    natural_baselines: pd.DataFrame,
    selected_model: str,
) -> None:
    agents = quality[quality["system_type"].eq("agent")].sort_values("taskA_macro_f1", ascending=False)
    baselines = quality[quality["system_type"].eq("baseline")].sort_values("taskA_macro_f1", ascending=False)
    best_agent = agents.iloc[0] if len(agents) else None
    best_baseline = baselines.iloc[0] if len(baselines) else None
    beats = (
        bool(best_agent["taskA_macro_f1"] > best_baseline["taskA_macro_f1"])
        if best_agent is not None and best_baseline is not None
        else False
    )
    lines = [
        "# StableEval Arena Paper Pilot Evaluation",
        "",
        f"Selected model backend: `{selected_model}`",
        "",
        f"This evaluation covers {case_count} historical-replay cases. Each case contains only a frozen 30-day lookback window; the hidden next-7-day horizon is used only by the evaluator.",
        "",
        "## Main Evaluation Results",
        "",
        markdown_table(
            quality.sort_values(["system_type", "taskA_macro_f1"], ascending=[True, False]),
            [
                "system",
                "system_type",
                "cases",
                "taskA_accuracy",
                "taskA_macro_f1",
                "taskA_balanced_accuracy",
                "binary_recall",
                "binary_auroc",
                "binary_average_precision",
                "deviation_mae_bps",
                "valid_json_rate",
                "failure_rate",
            ],
        ),
        "",
        "## Baseline Comparison",
        "",
        markdown_table(
            baseline_comparison.sort_values("taskA_macro_f1", ascending=False),
            [
                "system",
                "system_type",
                "taskA_accuracy",
                "taskA_macro_f1",
                "taskA_balanced_accuracy",
                "missed_depeg_rate",
                "false_alarm_rate",
                "deviation_mae_bps",
                "total_estimated_cost_usd",
            ],
        ),
        "",
        "## Computational Cost",
        "",
        markdown_table(
            cost.sort_values(["system_type", "cost_per_case_usd"], ascending=[True, True]),
            [
                "system",
                "system_type",
                "avg_prompt_tokens",
                "avg_completion_tokens",
                "avg_total_tokens",
                "avg_latency_seconds",
                "total_estimated_cost_usd",
                "cost_per_case_usd",
                "cost_per_correct_prediction_usd",
                "cost_per_detected_depeg_usd",
            ],
        ),
        "",
        "## Adapter Truthfulness",
        "",
        markdown_table(adapter_metadata),
        "",
        "## Natural-Distribution Baseline Results",
        "",
        "Agent results are not reported on all 507 cases yet because the user requested no full scaling run in this step. Natural-distribution results below are for baselines only and show what the full benchmark distribution looks like before final scaling.",
        "",
        markdown_table(
            natural_baselines.sort_values("taskA_macro_f1", ascending=False),
            [
                "system",
                "cases",
                "taskA_accuracy",
                "taskA_macro_f1",
                "taskA_balanced_accuracy",
                "missed_depeg_rate",
                "false_alarm_rate",
                "deviation_mae_bps",
            ],
        ),
        "",
        "## Simple Interpretation",
        "",
        (
            "In this pilot, the best agent did outperform the best baseline on macro-F1."
            if beats
            else "In this pilot, the best agent did not outperform the best baseline on macro-F1."
        ),
        "For this workshop target, the important contribution is not only accuracy: the benchmark records reliability, structured-output validity, latency, tokens, estimated cost, false alarms, and missed depeg events.",
        "",
    ]
    (out_dir / "evaluation_summary.md").write_text("\n".join(lines), encoding="utf-8")


def write_interpretation(
    out_dir: Path,
    case_count: int,
    quality: pd.DataFrame,
    adapter_metadata: pd.DataFrame,
    selected_model: str,
) -> None:
    agents = quality[quality["system_type"].eq("agent")]
    baselines = quality[quality["system_type"].eq("baseline")]
    best_agent = agents.sort_values("taskA_macro_f1", ascending=False).iloc[0] if len(agents) else None
    best_baseline = baselines.sort_values("taskA_macro_f1", ascending=False).iloc[0] if len(baselines) else None
    adapter_platforms = adapter_metadata[
        adapter_metadata["execution_mode"].astype(str).eq("stableeval_adapter")
    ]["platform"].tolist()
    native_platforms = adapter_metadata[
        ~adapter_metadata["execution_mode"].astype(str).eq("stableeval_adapter")
    ]["platform"].tolist()
    lines = [
        "# Paper Interpretation: StableEval Arena Pilot",
        "",
        "## What Was Run",
        "",
        f"We ran a {case_count}-case historical-replay evaluation using `{selected_model}` through OpenRouter at temperature 0. Each agent received the same frozen 30-day lookback packet, in the same case order, with no web search and no future horizon labels or prices.",
        "",
        "## Platforms Compared",
        "",
        "The evaluated platforms were Nanobot, LangGraph, Hermes AI, EvoAgentX, OpenClaw, and NanoClaw.",
        "",
        f"Native or framework-level execution verified: {', '.join(native_platforms) if native_platforms else 'none recorded'}.",
        f"Adapter-based execution: {', '.join(adapter_platforms) if adapter_platforms else 'none recorded'}.",
        "",
        "OpenClaw and NanoClaw are reported as adapter-based unless a local CMDOP runtime is actually verified. This avoids presenting wrapper execution as native agent execution.",
        "",
        "## Label and Deviation Design",
        "",
        "Dollar-peg deviation is measured from hourly close price as `abs(close_price - 1.00) * 10000` basis points. Stable means no meaningful next-7-day deviation. Watch means mild but meaningful instability, including any close deviation around 50 bps. Stress means large, persistent, or operationally meaningful instability, including sustained 100 bps deviation for at least 3 consecutive hours or near-stress duration/intensity signals.",
        "",
        "## Evaluation, Trustworthy, Agentic",
        "",
        "Evaluation: all platforms use the same data windows, model route, temperature, prompt schema, case order, and hidden-label evaluator, with rule and ML baselines.",
        "",
        "Trustworthy: the evaluator reports missed-depeg risk, false-alarm rate, Brier score, valid JSON rate, failure rate, latency, token usage, inference cost, cost per case, cost per correct prediction, and cost per detected stress case.",
        "",
        "Agentic: the run logs platform execution mode, raw outputs, parsed JSON, adapter metadata, and failure modes, so the comparison measures workflow reliability and cost behavior in addition to final labels.",
        "",
        "## Result Takeaway",
        "",
    ]
    if best_agent is not None and best_baseline is not None:
        lines.append(
            f"The best agent by macro-F1 was `{best_agent['system']}` ({best_agent['taskA_macro_f1']:.3f}); the best baseline was `{best_baseline['system']}` ({best_baseline['taskA_macro_f1']:.3f})."
        )
    lines.extend(
        [
            "",
            "A false alarm can create business opportunity cost by reducing stablecoin exposure, liquidity, or payment/trading availability unnecessarily. A missed stress event can create public or systemic cost by giving false reassurance, delaying risk response, and underestimating stablecoin fragility. Computational cost determines whether agentic monitoring is practical beyond a small benchmark.",
            "",
            "## Remaining Scaling Step",
            "",
            "The remaining scaling step is to run the selected frozen protocol on all 507 cases after the validation gate is accepted.",
        ]
    )
    (out_dir / "paper_interpretation.md").write_text("\n".join(lines), encoding="utf-8")


def write_latex_skeleton(out_dir: Path) -> None:
    text = r"""\section{StableEval Arena}
\paragraph{Benchmark Overview.}
StableEval Arena is a cost-aware historical-replay benchmark for evaluating whether agentic AI systems can act as stablecoin price-stability prediction agents.

\paragraph{Data Construction.}
Each case contains a frozen 30-day lookback window and a hidden 7-day forecast horizon. Dollar-peg deviation is measured from hourly close price as $\lvert p_t - 1.00\rvert \times 10{,}000$ basis points. We report a balanced 30-case pilot and reserve the 507-case natural distribution for scaling.

\paragraph{Agent Platforms.}
We compare Nanobot, LangGraph, Hermes AI, EvoAgentX, OpenClaw, and NanoClaw under one shared OpenRouter backend, temperature 0, identical prompt packets, identical output schema, and reset memory between cases. OpenClaw and NanoClaw are reported as adapter-based unless native CMDOP execution is verified.

\paragraph{Evaluation Protocol.}
Agents output strict JSON containing the predicted stability class, sustained-depeg probability, maximum absolute deviation forecast, direction, confidence, and rationale. We evaluate 3-class stability prediction, binary sustained-depeg prediction, continuous deviation prediction, reliability, and computational cost.

\paragraph{Trustworthiness Metrics.}
We report missed-depeg rate, false-alarm rate, Brier score, valid JSON rate, failure rate, latency, token usage, estimated cost, cost per case, cost per correct prediction, and cost per detected stress case. These metrics connect technical performance to business opportunity cost, public/systemic cost, and deployment feasibility.

\paragraph{Pilot Results.}
Table~\ref{tab:pilot-quality} reports prediction quality. Table~\ref{tab:pilot-cost} reports computational cost. Table~\ref{tab:baselines} compares agentic systems against simple rules and a supervised ML baseline.

\paragraph{Limitations and Scaling Plan.}
This evaluation is designed to validate the full paper-ready protocol before scaling. The remaining step is to run the selected frozen protocol over all 507 historical-replay cases.
"""
    (out_dir / "overleaf_methodology_results_skeleton.tex").write_text(text, encoding="utf-8")


def write_failure_modes(out_dir: Path, raw: pd.DataFrame) -> pd.DataFrame:
    failures = raw[raw["failure"]].copy()
    if failures.empty:
        failure_modes = pd.DataFrame(
            columns=["system", "case_id", "failure_category", "error_message", "execution_mode", "model_backend"]
        )
    else:
        failures["failure_category"] = np.where(
            ~failures["valid_json"].astype(bool),
            "invalid_json",
            np.where(failures["error_message"].astype(str).str.len() > 0, "runtime_error", "unknown_failure"),
        )
        failure_modes = failures[
            ["system", "case_id", "failure_category", "error_message", "execution_mode", "model_backend"]
        ]
    failure_modes.to_csv(out_dir / "failure_modes.csv", index=False)
    return failure_modes


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--pred-dir", default="results/stableeval_120_enriched/predictions_base_raw")
    parser.add_argument("--labels", default="data/benchmark/stableeval_507_natural/labels.csv")
    parser.add_argument("--pilot-labels", default="results/stableeval_120_enriched/validation_case_list.csv")
    parser.add_argument("--packets", default="data/benchmark/stableeval_507_natural/prompt_packets.jsonl")
    parser.add_argument("--adapter-metadata", default="results/stableeval_120_enriched/agent_execution_metadata.csv")
    parser.add_argument("--selected-model-json", default="results/stableeval_120_enriched/model_backend.json")
    parser.add_argument("--out-dir", default="results/stableeval_120_enriched/evaluation_base_raw")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    out_dir = root / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    confusion_dir = out_dir / "confusion_matrices"
    confusion_dir.mkdir(parents=True, exist_ok=True)

    all_labels = pd.read_csv(root / args.labels)
    pilot_labels = pd.read_csv(root / args.pilot_labels)
    packets = load_packets(root / args.packets)
    selected = json.loads((root / args.selected_model_json).read_text(encoding="utf-8"))
    selected_model = selected.get("selected_model_id", "")

    agent_preds = load_agent_predictions(root / args.pred_dir, pilot_labels)
    baseline_frames = [
        baseline_records(pilot_labels, packets, "always_stable"),
        baseline_records(pilot_labels, packets, "historical_persistence"),
        baseline_records(pilot_labels, packets, "threshold_rule"),
        ml_pilot_predictions(all_labels, pilot_labels, packets),
    ]
    pilot_predictions = pd.concat([agent_preds, *baseline_frames], ignore_index=True)
    raw = attach_actuals(pilot_predictions, pilot_labels)
    raw.to_json(out_dir / "raw_predictions.jsonl", orient="records", lines=True, force_ascii=False)
    raw.to_csv(out_dir / "raw_predictions.csv", index=False)

    rows = [score_system(raw, system) for system in sorted(raw["system"].dropna().unique())]
    for row in rows:
        safe_name = str(row["system"]).replace("/", "_")
        cm = row["confusion_matrix"]
        cm.to_csv(confusion_dir / f"{safe_name}_confusion_matrix.csv")
        plot_confusion(cm, f"{row['system']} Confusion Matrix", confusion_dir / f"{safe_name}_confusion_matrix.png")

    quality = dataframe_without_matrices(rows)
    quality = quality.sort_values(["system_type", "taskA_macro_f1"], ascending=[True, False]).reset_index(drop=True)
    quality.to_csv(out_dir / "prediction_quality_by_platform.csv", index=False)
    cost_cols = [
        "system",
        "system_type",
        "cases",
        "avg_prompt_tokens",
        "avg_completion_tokens",
        "avg_total_tokens",
        "avg_latency_seconds",
        "total_estimated_cost_usd",
        "cost_per_case_usd",
        "cost_per_correct_prediction_usd",
        "cost_per_detected_depeg_usd",
        "valid_json_rate",
        "failure_rate",
        "invalid_output_rate",
    ]
    cost = quality[cost_cols].copy()
    cost.to_csv(out_dir / "computational_cost_by_platform.csv", index=False)
    cost.to_csv(out_dir / "cost_report.csv", index=False)
    baseline_comparison = quality[
        [
            "system",
            "system_type",
            "cases",
            "taskA_accuracy",
            "taskA_macro_f1",
            "taskA_balanced_accuracy",
            "binary_precision",
            "binary_recall",
            "binary_auroc",
            "binary_average_precision",
            "binary_brier_score",
            "missed_depeg_rate",
            "false_alarm_rate",
            "deviation_mae_bps",
            "deviation_rmse_bps",
            "total_estimated_cost_usd",
        ]
    ].copy()
    baseline_comparison.to_csv(out_dir / "baseline_comparison.csv", index=False)
    write_failure_modes(out_dir, raw)

    natural_baselines = pd.concat(
        [
            attach_actuals(baseline_records(all_labels, packets, "always_stable"), all_labels),
            attach_actuals(baseline_records(all_labels, packets, "historical_persistence"), all_labels),
            attach_actuals(baseline_records(all_labels, packets, "threshold_rule"), all_labels),
            attach_actuals(ml_cv_predictions(all_labels, packets), all_labels),
        ],
        ignore_index=True,
    )
    natural_rows = [score_system(natural_baselines, system) for system in sorted(natural_baselines["system"].unique())]
    natural_quality = dataframe_without_matrices(natural_rows)
    natural_quality.to_csv(out_dir / "natural_distribution_baseline_comparison.csv", index=False)

    adapter_path = root / args.adapter_metadata
    adapter_metadata = pd.read_csv(adapter_path) if adapter_path.exists() else pd.DataFrame()
    write_figures(out_dir, pilot_labels, quality, cost)
    write_summary(out_dir, len(pilot_labels), quality, cost, baseline_comparison, adapter_metadata, natural_quality, selected_model)
    write_interpretation(out_dir, len(pilot_labels), quality, adapter_metadata, selected_model)
    write_latex_skeleton(out_dir)
    print(quality[["system", "system_type", "taskA_accuracy", "taskA_macro_f1", "deviation_mae_bps", "total_estimated_cost_usd"]].to_string(index=False))


if __name__ == "__main__":
    main()
