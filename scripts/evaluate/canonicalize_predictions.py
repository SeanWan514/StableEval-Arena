#!/usr/bin/env python3
"""Create one-row-per-platform-case prediction directories for evaluation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd


PLATFORMS = ["nanobot", "langgraph", "hermes_ai", "evoagentx", "openclaw", "nanoclaw"]


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def row_is_valid(row: dict[str, Any]) -> bool:
    return bool(row.get("valid_json") or row.get("valid_output")) and not (
        row.get("error_message") or row.get("error")
    )


def better(candidate: dict[str, Any], current: dict[str, Any] | None) -> bool:
    if current is None:
        return True
    candidate_valid = row_is_valid(candidate)
    current_valid = row_is_valid(current)
    if candidate_valid != current_valid:
        return candidate_valid
    return str(candidate.get("_stableeval_source_file", "")) > str(current.get("_stableeval_source_file", ""))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case-list", required=True)
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--require-valid", action="store_true")
    parser.add_argument("--platforms", nargs="*", default=PLATFORMS)
    args = parser.parse_args()

    cases = pd.read_csv(args.case_list)["case_id"].astype(str).tolist()
    case_set = set(cases)
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    if output_dir.exists():
        for path in output_dir.glob("*_predictions.jsonl"):
            path.unlink()
    output_dir.mkdir(parents=True, exist_ok=True)

    chosen: dict[tuple[str, str], dict[str, Any]] = {}
    for path in sorted(input_dir.glob("*_predictions.jsonl")):
        for row in load_jsonl(path):
            platform = str(row.get("platform") or "")
            case_id = str(row.get("case_id") or "")
            if platform not in args.platforms or case_id not in case_set:
                continue
            item = dict(row)
            item["_stableeval_source_file"] = path.name
            key = (platform, case_id)
            if better(item, chosen.get(key)):
                chosen[key] = item

    manifest = []
    errors = []
    for platform in args.platforms:
        rows = []
        for case_id in cases:
            row = chosen.get((platform, case_id))
            if row is None:
                errors.append(f"missing row: {platform}/{case_id}")
                continue
            if args.require_valid and not row_is_valid(row):
                errors.append(f"invalid row: {platform}/{case_id}: {row.get('error_message') or row.get('error')}")
            row = dict(row)
            row.pop("_stableeval_source_file", None)
            rows.append(row)
        write_jsonl(output_dir / f"{platform}_predictions.jsonl", rows)
        manifest.append(
            {
                "platform": platform,
                "rows": len(rows),
                "valid_rows": sum(1 for row in rows if row_is_valid(row)),
            }
        )

    manifest_path = output_dir / "canonical_manifest.json"
    manifest_path.write_text(json.dumps({"manifest": manifest, "errors": errors[:20]}, indent=2), encoding="utf-8")
    print(json.dumps({"output_dir": str(output_dir), "manifest": manifest, "error_count": len(errors)}, indent=2))
    if errors:
        raise SystemExit(f"Canonicalization found {len(errors)} missing/invalid rows; see {manifest_path}")


if __name__ == "__main__":
    main()
