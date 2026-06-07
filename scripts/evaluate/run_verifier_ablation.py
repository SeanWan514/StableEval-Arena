#!/usr/bin/env python3
"""Run the StableEval risk-auditor layer from saved first-pass predictions."""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from agents.run_platform import (  # noqa: E402
    OpenRouterClient,
    RISK_VERIFIER_PROMPT,
    fetch_model_pricing,
    packet_hash,
    parse_prediction_with_repair,
    record_case_id,
    record_stablecoin,
    token_count_approx,
    visible_packet,
)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def base_prediction_map(base_dir: Path) -> dict[tuple[str, str], dict[str, Any]]:
    out: dict[tuple[str, str], dict[str, Any]] = {}
    for path in sorted(base_dir.glob("*_predictions.jsonl")):
        for row in load_jsonl(path):
            out[(str(row.get("platform")), str(row.get("case_id")))] = row
    return out


def verifier_task(
    *,
    packet: dict[str, Any],
    base_record: dict[str, Any],
    platform: str,
    model: str,
    temperature: float,
    max_tokens: int,
    api_key: str,
) -> dict[str, Any]:
    client = OpenRouterClient(api_key=api_key, model=model, temperature=temperature, max_tokens=max_tokens)
    first_prediction = base_record.get("parsed_json") or base_record.get("prediction") or {}
    messages = [
        {"role": "system", "content": RISK_VERIFIER_PROMPT},
        {
            "role": "user",
            "content": json.dumps(
                {
                    "packet": visible_packet(packet),
                    "first_prediction": first_prediction,
                    "first_execution_mode": base_record.get("execution_mode")
                    or base_record.get("framework_execution_mode"),
                },
                sort_keys=True,
                ensure_ascii=False,
            ),
        },
    ]
    start = time.perf_counter()
    error = ""
    prediction: dict[str, Any] | None = None
    calls = []
    raw_text = ""
    metadata: dict[str, Any] = {
        "risk_verifier_applied": True,
        "base_prediction": first_prediction,
        "base_raw_agent_output": str(base_record.get("raw_agent_output", ""))[:2400],
    }
    try:
        call = client.chat(messages, max_tokens=min(max_tokens, 1200), json_mode=True)
        raw_text = call.content
        prediction, repair_calls, repair_meta = parse_prediction_with_repair(raw_text, platform, call.model, client)
        calls = [call] + repair_calls
        metadata.update(repair_meta)
    except Exception as exc:
        error = repr(exc)

    latency = time.perf_counter() - start
    prompt_tokens = sum(call.prompt_tokens for call in calls)
    completion_tokens = sum(call.completion_tokens for call in calls)
    total_tokens = sum(call.total_tokens for call in calls)
    verifier_cost = sum(call.cost_usd for call in calls)
    prompt_fallback = token_count_approx(json.dumps(messages, ensure_ascii=False))
    completion_fallback = token_count_approx(raw_text)
    pricing = fetch_model_pricing(model)
    if prompt_tokens <= 0:
        prompt_tokens = prompt_fallback
    if completion_tokens <= 0:
        completion_tokens = completion_fallback
    if total_tokens <= 0:
        total_tokens = prompt_tokens + completion_tokens
    if verifier_cost <= 0:
        verifier_cost = pricing.estimate(prompt_tokens, completion_tokens)

    base_prompt = int(base_record.get("prompt_tokens_approx") or 0)
    base_completion = int(base_record.get("completion_tokens_approx") or 0)
    base_total = int(base_record.get("total_tokens_approx") or 0)
    base_cost = float(base_record.get("estimated_cost_usd") or 0.0)
    base_latency = float(base_record.get("latency_seconds") or 0.0)
    execution_mode = f"{base_record.get('execution_mode') or base_record.get('framework_execution_mode')}+risk_auditor_verifier"
    model_backend = f"openrouter/{model}"
    if prediction:
        prediction.update(
            {
                "case_id": record_case_id(packet),
                "platform": platform,
                "model_backend": model_backend,
                "execution_mode": execution_mode,
            }
        )

    return {
        "case_id": record_case_id(packet),
        "stablecoin": record_stablecoin(packet),
        "observation_time": packet.get("_stableeval_observation_time") or packet["observation_time"],
        "platform": platform,
        "framework_execution_mode": execution_mode,
        "execution_mode": execution_mode,
        "provider_key_present": True,
        "model_backend": model_backend,
        "backend": prediction.get("backend") if prediction else "",
        "input_packet_hash": packet_hash(packet),
        "raw_agent_output": raw_text,
        "parsed_json": prediction,
        "valid_json": bool(prediction),
        "error_message": error,
        "prediction": prediction,
        "valid_output": bool(prediction),
        "error": error,
        "latency_seconds": base_latency + latency,
        "prompt_tokens_approx": base_prompt + prompt_tokens,
        "completion_tokens_approx": base_completion + completion_tokens,
        "total_tokens_approx": base_total + total_tokens,
        "estimated_cost_usd": base_cost + verifier_cost,
        "cost_note": "OpenRouter LLM-backed first pass plus risk-auditor verifier.",
        "llm_call_count": int(base_record.get("llm_call_count") or 0) + len(calls),
        "adapter_metadata": metadata,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--base-pred-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--max-tokens", type=int, default=1600)
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--platforms", nargs="*")
    args = parser.parse_args()

    api_key = os.getenv("OPENROUTER_API_KEY") or ""
    if not api_key:
        raise SystemExit("OPENROUTER_API_KEY is required for verifier LLM calls.")

    packets = load_jsonl(Path(args.input))
    base = base_prediction_map(Path(args.base_pred_dir))
    platforms = sorted({platform for platform, _ in base})
    if args.platforms:
        requested = set(args.platforms)
        platforms = [platform for platform in platforms if platform in requested]
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    total = 0
    for platform in platforms:
        output_path = output_dir / f"{platform}_predictions.jsonl"
        if output_path.exists():
            existing = load_jsonl(output_path)
            if len(existing) >= len(packets):
                print(json.dumps({"platform": platform, "skipped_existing_records": len(existing)}, indent=2))
                total += len(existing)
                continue
        tasks = []
        for idx, packet in enumerate(packets):
            case_id = record_case_id(packet)
            base_record = base.get((platform, case_id))
            if not base_record:
                raise RuntimeError(f"Missing base prediction for {platform}/{case_id}")
            tasks.append((idx, packet, base_record))

        rows_by_index: dict[int, dict[str, Any]] = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
            future_map = {
                pool.submit(
                    verifier_task,
                    packet=packet,
                    base_record=base_record,
                    platform=platform,
                    model=args.model,
                    temperature=args.temperature,
                    max_tokens=args.max_tokens,
                    api_key=api_key,
                ): idx
                for idx, packet, base_record in tasks
            }
            for future in concurrent.futures.as_completed(future_map):
                idx = future_map[future]
                rows_by_index[idx] = future.result()
        rows = [rows_by_index[idx] for idx in sorted(rows_by_index)]
        write_jsonl(output_path, rows)
        total += len(rows)
        print(json.dumps({"platform": platform, "verifier_records": len(rows)}, indent=2))

    print(json.dumps({"verifier_records": total, "output_dir": str(output_dir)}, indent=2))


if __name__ == "__main__":
    main()
