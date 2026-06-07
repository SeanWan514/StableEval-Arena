#!/usr/bin/env bash
set -euo pipefail

# Prepared run script only. Do not execute until the user explicitly approves.

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PARENT="$(cd "$ROOT/.." && pwd)"
CORE_PY="$PARENT/envs/core-py312/bin/python"
AGENT_PY="$PARENT/envs/nanobot-ai-py312/bin/python"

export PYTHONPATH="$ROOT/src"
export NO_PROXY="${NO_PROXY:-*}"
export no_proxy="${no_proxy:-*}"
cd "$ROOT"

if [[ -z "${OPENROUTER_API_KEY:-}" ]]; then
  echo "OPENROUTER_API_KEY is required. Export it in the shell; do not write it into project files." >&2
  exit 1
fi

OUT_DIR="results/stableeval_507_natural/build_metadata"
RAW_DIR="$OUT_DIR/nanobot_predictions_base_raw"
CAL_DIR="$OUT_DIR/nanobot_predictions_base_calibrated"
LOG_DIR="$OUT_DIR/logs"
mkdir -p "$RAW_DIR" "$CAL_DIR" "$LOG_DIR"

"$CORE_PY" scripts/build_cases/build_stableeval_507_natural_packets.py --root .

MODEL="$("$CORE_PY" - <<'PY'
import json
from pathlib import Path
print(json.loads(Path("results/stableeval_507_natural/build_metadata/model_backend.json").read_text())["selected_model_id"])
PY
)"

"$AGENT_PY" src/agents/run_platform.py \
  --platform nanobot \
  --input data/benchmark/stableeval_507_natural/prompt_packets.jsonl \
  --system-prompt prompts/templates/risk_sensitive_agent_prompt.md \
  --output "$RAW_DIR/nanobot_predictions.jsonl" \
  --model "$MODEL" \
  --temperature 0 \
  --max-tokens 1600 \
  --max-cases 0 \
  --max-estimated-cost-usd "${STABLEEVAL_FULL_507_MAX_COST_USD:-5.00}" \
  --label-calibration none \
  --resume \
  > "$LOG_DIR/nanobot_base_raw.log" 2>&1

"$CORE_PY" scripts/evaluate/apply_calibration.py \
  --input-dir "$RAW_DIR" \
  --output-dir "$CAL_DIR"

"$CORE_PY" scripts/evaluate/evaluate_predictions.py \
  --root . \
  --pred-dir "$RAW_DIR" \
  --labels data/benchmark/stableeval_507_natural/labels.csv \
  --pilot-labels "$OUT_DIR/full_507_case_list.csv" \
  --packets data/benchmark/stableeval_507_natural/prompt_packets.jsonl \
  --adapter-metadata results/stableeval_120_enriched/agent_execution_metadata.csv \
  --selected-model-json "$OUT_DIR/model_backend.json" \
  --out-dir "$OUT_DIR/evaluation_nanobot_base_raw"

"$CORE_PY" scripts/evaluate/evaluate_predictions.py \
  --root . \
  --pred-dir "$CAL_DIR" \
  --labels data/benchmark/stableeval_507_natural/labels.csv \
  --pilot-labels "$OUT_DIR/full_507_case_list.csv" \
  --packets data/benchmark/stableeval_507_natural/prompt_packets.jsonl \
  --adapter-metadata results/stableeval_120_enriched/agent_execution_metadata.csv \
  --selected-model-json "$OUT_DIR/model_backend.json" \
  --out-dir "$OUT_DIR/evaluation_nanobot_base_calibrated"

echo "Full 507 Nanobot frozen-protocol run complete: $ROOT/$OUT_DIR"
