#!/usr/bin/env python3
"""Resume-safe NanoClaw adapter/Qwen runner for the 507-case scaling check.

This script is intentionally scoped to NanoClaw adapter outputs under
results/stableeval_507_natural. It does not modify frozen 120-case validation artifacts
and does not touch Nanobot, LangGraph, Hermes AI, EvoAgentX, or OpenClaw
adapter outputs.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import random
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
SCALING_ROOT = ROOT / "results" / "stableeval_507_natural"
PROMPT_PACKETS = ROOT / "data/benchmark/stableeval_507_natural/prompt_packets.jsonl"
CASE_LIST = ROOT / "data/benchmark/stableeval_507_natural/case_list.csv"
DRY_RUN_DIR = SCALING_ROOT / "raw_predictions" / "nanoclaw_adapter_qwen_507_dry_run"
DRY_RUN_JSONL = DRY_RUN_DIR / "nanoclaw_adapter_predictions_dry_run.jsonl"
CONTINUATION_DIR = SCALING_ROOT / "raw_predictions" / "nanoclaw_adapter_qwen_507_continuation"
CONTINUATION_JSONL = CONTINUATION_DIR / "nanoclaw_adapter_predictions_continuation.jsonl"
LOG_DIR = SCALING_ROOT / "logs" / "nanoclaw_adapter_qwen_507"
COST_DIR = SCALING_ROOT / "costs" / "nanoclaw_adapter_qwen_507"
FAILED_CASES_CSV = LOG_DIR / "nanoclaw_adapter_failed_cases.csv"
RETRY_LOG_CSV = LOG_DIR / "nanoclaw_adapter_retry_log.csv"
BATCH_LOG_CSV = LOG_DIR / "nanoclaw_adapter_batch_log.csv"
RUNTIME_LOG_CSV = LOG_DIR / "nanoclaw_adapter_runtime_log.csv"
COST_LOG_CSV = COST_DIR / "nanoclaw_adapter_cost_log.csv"
CASE_INPUT_DIR = CONTINUATION_DIR / "case_inputs"
ATTEMPT_DIR = CONTINUATION_DIR / "attempt_outputs"
STDOUT_DIR = LOG_DIR / "subprocess_logs"
SYSTEM_PROMPT = ROOT / "prompts" / "templates" / "risk_sensitive_agent_prompt.md"
RUN_PLATFORM = ROOT / "src" / "agents" / "run_platform.py"
EXPECTED_MODEL = "qwen/qwen-2.5-72b-instruct"
EXPECTED_BACKEND = f"openrouter/{EXPECTED_MODEL}"
EXPECTED_EXECUTION_MODE = "stableeval_adapter"
EXPECTED_PLATFORM = "nanoclaw"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_under_scaling(path: Path) -> None:
    resolved = path.resolve()
    root = SCALING_ROOT.resolve()
    if resolved != root and root not in resolved.parents:
        raise SystemExit(f"Refusing to write outside results/stableeval_507_natural: {path}")


def append_csv(path: Path, row: dict[str, Any], fieldnames: list[str]) -> None:
    ensure_under_scaling(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.exists()
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        if not exists:
            writer.writeheader()
        writer.writerow({key: row.get(key, "") for key in fieldnames})
        handle.flush()
        os.fsync(handle.fileno())


def append_jsonl(path: Path, record: dict[str, Any]) -> None:
    ensure_under_scaling(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def read_jsonl_records(path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    records: list[dict[str, Any]] = []
    corrupt: list[dict[str, Any]] = []
    if not path.exists():
        return records, corrupt
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                records.append(json.loads(line))
            except Exception as exc:
                corrupt.append({"path": str(path), "line_no": line_no, "error": repr(exc)})
    return records, corrupt


def valid_completed_ids(records: list[dict[str, Any]]) -> set[str]:
    out: set[str] = set()
    for record in records:
        case_id = str(record.get("case_id") or "")
        if not case_id:
            continue
        if record.get("valid_json") or record.get("valid_output"):
            if str(record.get("platform") or "") != EXPECTED_PLATFORM:
                continue
            if str(record.get("model_backend")) != EXPECTED_BACKEND:
                continue
            if str(record.get("execution_mode") or "") != EXPECTED_EXECUTION_MODE:
                continue
            metadata = record.get("adapter_metadata") or {}
            if str(metadata.get("cmdop_local_agent") or "") != "unavailable":
                continue
            out.add(case_id)
    return out


def load_case_ids() -> list[str]:
    with CASE_LIST.open(newline="", encoding="utf-8") as handle:
        return [row["case_id"] for row in csv.DictReader(handle)]


def load_case_rows() -> list[dict[str, str]]:
    with CASE_LIST.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def select_stratified_dry_run_case_ids() -> list[str]:
    rows = load_case_rows()
    selected: list[str] = []
    targets = [("stable", 2), ("watch", 2), ("stress", 1)]
    for label, count in targets:
        matches = [row["case_id"] for row in rows if row.get("enhanced_stability_label") == label]
        selected.extend(matches[:count])
    if len(selected) != 5:
        raise SystemExit(f"Could not select 5 stratified dry-run cases; got {len(selected)}.")
    return selected


def load_packets() -> dict[str, dict[str, Any]]:
    packets: dict[str, dict[str, Any]] = {}
    with PROMPT_PACKETS.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            packet = json.loads(line)
            case_id = packet.get("_stableeval_case_id") or packet.get("case_id")
            packets[str(case_id)] = packet
    return packets


def write_one_case_packet(case_id: str, packet: dict[str, Any]) -> Path:
    ensure_under_scaling(CASE_INPUT_DIR)
    CASE_INPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = CASE_INPUT_DIR / f"{case_id}.jsonl"
    if not path.exists():
        path.write_text(json.dumps(packet, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def attempt_output_path(case_id: str, attempt: int) -> Path:
    ensure_under_scaling(ATTEMPT_DIR)
    ATTEMPT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    return ATTEMPT_DIR / f"{case_id}_attempt{attempt:02d}_{stamp}_predictions.jsonl"


def subprocess_log_paths(case_id: str, attempt: int) -> tuple[Path, Path]:
    ensure_under_scaling(STDOUT_DIR)
    STDOUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    return (
        STDOUT_DIR / f"{case_id}_attempt{attempt:02d}_{stamp}.stdout.log",
        STDOUT_DIR / f"{case_id}_attempt{attempt:02d}_{stamp}.stderr.log",
    )


def load_first_record(path: Path) -> tuple[dict[str, Any] | None, str]:
    records, corrupt = read_jsonl_records(path)
    if corrupt:
        return None, f"corrupt_jsonl:{corrupt[:1]}"
    if len(records) != 1:
        return None, f"expected_one_record_got_{len(records)}"
    record = records[0]
    if not (record.get("valid_json") or record.get("valid_output")):
        return None, f"invalid_output:{record.get('error_message') or record.get('error')}"
    if str(record.get("platform") or "") != EXPECTED_PLATFORM:
        return None, f"unexpected_platform:{record.get('platform')}"
    if str(record.get("model_backend")) != EXPECTED_BACKEND:
        return None, f"unexpected_backend:{record.get('model_backend')}"
    if record.get("backend") and str(record.get("backend")) != "openrouter_llm":
        return None, f"unexpected_provider_backend:{record.get('backend')}"
    if str(record.get("execution_mode") or "") != EXPECTED_EXECUTION_MODE:
        return None, f"unexpected_execution_mode:{record.get('execution_mode')}"
    metadata = record.get("adapter_metadata") or {}
    if str(metadata.get("cmdop_local_agent") or "") != "unavailable":
        return None, f"native_cmdop_claim_or_missing_adapter_status:{metadata}"
    if "native" in str(record.get("execution_mode") or "").lower():
        return None, f"native_execution_mode_claim:{record.get('execution_mode')}"
    return record, ""


def run_one_case(
    *,
    case_id: str,
    packet: dict[str, Any],
    python_bin: str,
    model: str,
    temperature: float,
    max_tokens: int,
    timeout_seconds: int,
    attempt: int,
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    packet_path = write_one_case_packet(case_id, packet)
    output_path = attempt_output_path(case_id, attempt)
    stdout_path, stderr_path = subprocess_log_paths(case_id, attempt)
    command = [
        python_bin,
        str(RUN_PLATFORM),
        "--platform",
        "nanoclaw",
        "--input",
        str(packet_path),
        "--system-prompt",
        str(SYSTEM_PROMPT),
        "--output",
        str(output_path),
        "--model",
        model,
        "--temperature",
        str(temperature),
        "--max-tokens",
        str(max_tokens),
        "--max-cases",
        "0",
        "--max-estimated-cost-usd",
        "1.00",
        "--label-calibration",
        "none",
    ]
    env = os.environ.copy()
    if not env.get("OPENROUTER_API_KEY"):
        raise SystemExit("OPENROUTER_API_KEY is not set in the environment.")
    env.pop("OPENAI_API_KEY", None)
    env.pop("ANTHROPIC_API_KEY", None)
    env.pop("GOOGLE_API_KEY", None)
    env["STABLEEVAL_OPENROUTER_RETRIES"] = "1"
    env["STABLEEVAL_SDK_CALL_TIMEOUT_SECONDS"] = str(max(30, timeout_seconds - 20))
    env["LOGURU_LEVEL"] = "ERROR"
    start = time.perf_counter()
    result: subprocess.CompletedProcess[str] | None = None
    status = "unknown"
    error = ""
    with stdout_path.open("w", encoding="utf-8") as stdout, stderr_path.open("w", encoding="utf-8") as stderr:
        try:
            result = subprocess.run(
                command,
                cwd=str(ROOT),
                env=env,
                text=True,
                stdout=stdout,
                stderr=stderr,
                timeout=timeout_seconds,
                check=False,
            )
            status = "subprocess_returned"
        except subprocess.TimeoutExpired as exc:
            status = "timeout"
            error = repr(exc)
    elapsed = time.perf_counter() - start
    record, validation_error = load_first_record(output_path) if output_path.exists() else (None, "no_output_file")
    if validation_error:
        error = error or validation_error
    if result is not None and result.returncode not in (0, None) and not record:
        error = error or f"returncode:{result.returncode}"
    log = {
        "timestamp_utc": utc_now(),
        "case_id": case_id,
        "attempt": attempt,
        "status": status,
        "returncode": "" if result is None else result.returncode,
        "elapsed_seconds": round(elapsed, 6),
        "timeout_seconds": timeout_seconds,
        "output_path": str(output_path.relative_to(ROOT)),
        "stdout_path": str(stdout_path.relative_to(ROOT)),
        "stderr_path": str(stderr_path.relative_to(ROOT)),
        "record_valid": bool(record),
        "error": error,
        "model": model,
        "temperature": temperature,
    }
    return record, log


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0, help="Run at most this many remaining cases; 0 means all.")
    parser.add_argument("--dry-run", action="store_true", help="Run the fixed 2 stable / 2 watch / 1 stress smoke test.")
    parser.add_argument("--batch-size", type=int, default=25)
    parser.add_argument("--timeout-seconds", type=int, default=240)
    parser.add_argument("--max-retries", type=int, default=3)
    parser.add_argument("--backoff-min-seconds", type=float, default=10)
    parser.add_argument("--backoff-max-seconds", type=float, default=30)
    parser.add_argument("--model", default=EXPECTED_MODEL)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--max-tokens", type=int, default=1600)
    parser.add_argument("--python-bin", default=str(ROOT.parent / "envs" / "cmdop-claw-py312" / "bin" / "python"))
    args = parser.parse_args()

    global CASE_INPUT_DIR, ATTEMPT_DIR, STDOUT_DIR
    run_mode = "dry_run" if args.dry_run else "continuation"
    run_dir = DRY_RUN_DIR if args.dry_run else CONTINUATION_DIR
    run_jsonl = DRY_RUN_JSONL if args.dry_run else CONTINUATION_JSONL
    CASE_INPUT_DIR = run_dir / "case_inputs"
    ATTEMPT_DIR = run_dir / "attempt_outputs"
    STDOUT_DIR = LOG_DIR / f"subprocess_logs_{run_mode}"

    if args.model != EXPECTED_MODEL:
        raise SystemExit(f"Refusing non-Qwen model: {args.model}")
    if abs(args.temperature) > 1e-12:
        raise SystemExit(f"Refusing nonzero temperature: {args.temperature}")
    if not str(CONTINUATION_DIR.resolve()).startswith(str(SCALING_ROOT.resolve())):
        raise SystemExit("Continuation output dir is outside stableeval_507_natural.")
    if not str(DRY_RUN_DIR.resolve()).startswith(str(SCALING_ROOT.resolve())):
        raise SystemExit("Dry-run output dir is outside stableeval_507_natural.")
    if not PROMPT_PACKETS.exists() or not CASE_LIST.exists():
        raise SystemExit("Required 507 input file is missing.")
    if not Path(args.python_bin).exists():
        raise SystemExit(f"Python executable does not exist: {args.python_bin}")

    for directory in [run_dir, CASE_INPUT_DIR, ATTEMPT_DIR, STDOUT_DIR, LOG_DIR, COST_DIR]:
        ensure_under_scaling(directory)
        directory.mkdir(parents=True, exist_ok=True)

    case_ids = load_case_ids()
    packets = load_packets()
    if len(case_ids) != 507 or len(packets) != 507 or set(case_ids) != set(packets):
        raise SystemExit("507 case list and prompt packets do not match.")

    dry_run_records, dry_run_corrupt = read_jsonl_records(DRY_RUN_JSONL)
    continuation_records, continuation_corrupt = read_jsonl_records(CONTINUATION_JSONL)
    if dry_run_corrupt or continuation_corrupt:
        raise SystemExit(
            f"Corrupt JSONL found: dry_run={dry_run_corrupt[:2]} continuation={continuation_corrupt[:2]}"
        )
    if args.dry_run:
        target_case_ids = select_stratified_dry_run_case_ids()
        completed = valid_completed_ids(dry_run_records)
        remaining = [case_id for case_id in target_case_ids if case_id not in completed]
    else:
        completed = valid_completed_ids(dry_run_records) | valid_completed_ids(continuation_records)
        remaining = [case_id for case_id in case_ids if case_id not in completed]
    if args.limit > 0:
        remaining = remaining[: args.limit]

    append_csv(
        RUNTIME_LOG_CSV,
        {
            "timestamp_utc": utc_now(),
            "event": "start",
            "run_mode": run_mode,
            "limit": args.limit,
            "completed_before": len(completed),
            "remaining_selected": len(remaining),
            "batch_size": args.batch_size,
            "timeout_seconds": args.timeout_seconds,
            "max_retries": args.max_retries,
            "model": args.model,
            "temperature": args.temperature,
            "output_jsonl": str(run_jsonl.relative_to(ROOT)),
        },
        [
            "timestamp_utc",
            "event",
            "run_mode",
            "limit",
            "completed_before",
            "remaining_selected",
            "batch_size",
            "timeout_seconds",
            "max_retries",
            "model",
            "temperature",
            "output_jsonl",
        ],
    )

    retry_fields = [
        "timestamp_utc",
        "case_id",
        "attempt",
        "status",
        "returncode",
        "elapsed_seconds",
        "timeout_seconds",
        "output_path",
        "stdout_path",
        "stderr_path",
        "record_valid",
        "error",
        "model",
        "temperature",
    ]
    failed_fields = ["timestamp_utc", "case_id", "reason", "attempts", "model", "temperature"]
    batch_fields = ["timestamp_utc", "batch_index", "batch_start", "batch_size", "case_id", "status"]
    cost_fields = [
        "timestamp_utc",
        "run_mode",
        "case_id",
        "latency_seconds",
        "prompt_tokens_approx",
        "completion_tokens_approx",
        "total_tokens_approx",
        "estimated_cost_usd",
        "model_backend",
        "execution_mode",
    ]

    successes = 0
    failures = 0
    for idx, case_id in enumerate(remaining):
        batch_index = idx // max(1, args.batch_size)
        append_csv(
            BATCH_LOG_CSV,
            {
                "timestamp_utc": utc_now(),
                "batch_index": batch_index,
                "batch_start": idx % max(1, args.batch_size) == 0,
                "batch_size": args.batch_size,
                "case_id": case_id,
                "status": "started",
            },
            batch_fields,
        )
        record: dict[str, Any] | None = None
        last_error = ""
        for attempt in range(1, args.max_retries + 1):
            record, log = run_one_case(
                case_id=case_id,
                packet=packets[case_id],
                python_bin=args.python_bin,
                model=args.model,
                temperature=args.temperature,
                max_tokens=args.max_tokens,
                timeout_seconds=args.timeout_seconds,
                attempt=attempt,
            )
            append_csv(RETRY_LOG_CSV, log, retry_fields)
            if record:
                append_jsonl(run_jsonl, record)
                append_csv(
                    COST_LOG_CSV,
                    {
                        "timestamp_utc": utc_now(),
                        "run_mode": run_mode,
                        "case_id": case_id,
                        "latency_seconds": record.get("latency_seconds", ""),
                        "prompt_tokens_approx": record.get("prompt_tokens_approx", ""),
                        "completion_tokens_approx": record.get("completion_tokens_approx", ""),
                        "total_tokens_approx": record.get("total_tokens_approx", ""),
                        "estimated_cost_usd": record.get("estimated_cost_usd", ""),
                        "model_backend": record.get("model_backend", ""),
                        "execution_mode": record.get("execution_mode", ""),
                    },
                    cost_fields,
                )
                successes += 1
                append_csv(
                    BATCH_LOG_CSV,
                    {
                        "timestamp_utc": utc_now(),
                        "batch_index": batch_index,
                        "batch_start": False,
                        "batch_size": args.batch_size,
                        "case_id": case_id,
                        "status": "completed",
                    },
                    batch_fields,
                )
                break
            last_error = str(log.get("error") or "")
            if attempt < args.max_retries:
                time.sleep(random.uniform(args.backoff_min_seconds, args.backoff_max_seconds))
        if not record:
            failures += 1
            append_csv(
                FAILED_CASES_CSV,
                {
                    "timestamp_utc": utc_now(),
                    "case_id": case_id,
                    "reason": last_error,
                    "attempts": args.max_retries,
                    "model": args.model,
                    "temperature": args.temperature,
                },
                failed_fields,
            )
            append_csv(
                BATCH_LOG_CSV,
                {
                    "timestamp_utc": utc_now(),
                    "batch_index": batch_index,
                    "batch_start": False,
                    "batch_size": args.batch_size,
                    "case_id": case_id,
                    "status": "failed_after_retries",
                },
                batch_fields,
            )

    dry_run_records, dry_run_corrupt = read_jsonl_records(DRY_RUN_JSONL)
    continuation_records, continuation_corrupt = read_jsonl_records(CONTINUATION_JSONL)
    completed_after = valid_completed_ids(dry_run_records) | valid_completed_ids(continuation_records)
    final_remaining = [case_id for case_id in case_ids if case_id not in completed_after]
    append_csv(
        RUNTIME_LOG_CSV,
        {
            "timestamp_utc": utc_now(),
            "event": "finish",
            "run_mode": run_mode,
            "limit": args.limit,
            "completed_before": len(completed),
            "remaining_selected": len(remaining),
            "batch_size": args.batch_size,
            "timeout_seconds": args.timeout_seconds,
            "max_retries": args.max_retries,
            "model": args.model,
            "temperature": args.temperature,
            "output_jsonl": str(run_jsonl.relative_to(ROOT)),
        },
        [
            "timestamp_utc",
            "event",
            "run_mode",
            "limit",
            "completed_before",
            "remaining_selected",
            "batch_size",
            "timeout_seconds",
            "max_retries",
            "model",
            "temperature",
            "output_jsonl",
        ],
    )
    print(
        json.dumps(
            {
                "selected_cases": len(remaining),
                "successes_this_run": successes,
                "failures_this_run": failures,
                "completed_total_with_dry_run": len(completed_after),
                "remaining_total_after_run": len(final_remaining),
                "dry_run_records": len(dry_run_records),
                "continuation_records": len(continuation_records),
                "continuation_corrupt_records": len(continuation_corrupt),
                "output": str(run_jsonl.relative_to(ROOT)),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
