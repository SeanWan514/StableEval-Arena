#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PARENT="$(cd "$ROOT/.." && pwd)"

CORE_PY="${STABLEEVAL_CORE_PY:-$PARENT/envs/core-py312/bin/python}"
NANOBOT_PY="${STABLEEVAL_NANOBOT_PY:-$PARENT/envs/nanobot-ai-py312/bin/python}"
LANGGRAPH_PY="${STABLEEVAL_LANGGRAPH_PY:-$PARENT/envs/langgraph-py312/bin/python}"
HERMES_AI_PY="${STABLEEVAL_HERMES_AI_PY:-$PARENT/envs/hermes-ai-py312/bin/python}"
EVOAGENTX_PY="${STABLEEVAL_EVOAGENTX_PY:-$PARENT/envs/evoagentx-py312/bin/python}"
CMDOP_CLAW_PY="${STABLEEVAL_CMDOP_CLAW_PY:-$PARENT/envs/cmdop-claw-py312/bin/python}"

export PYTHONPATH="$ROOT/src"
export NO_PROXY="${NO_PROXY:-*}"
export no_proxy="${no_proxy:-*}"
cd "$ROOT"

OUT_DIR="results/stableeval_120_enriched"
LOG_DIR="$OUT_DIR/logs"
mkdir -p "$LOG_DIR"

"$CORE_PY" scripts/build_cases/build_stableeval_120_enriched.py --root .

if [[ -z "${OPENROUTER_API_KEY:-}" ]]; then
  echo "OPENROUTER_API_KEY is required for the real LLM-backed intermediate validation." >&2
  echo "The validation set and packets were built, but no LLM predictions were run." >&2
  exit 1
fi

MODEL="$("$CORE_PY" - <<'PY'
import json
from pathlib import Path
print(json.loads(Path("results/stableeval_120_enriched/model_backend.json").read_text())["selected_model_id"])
PY
)"

if [[ -f "$PARENT/scripts/patch_cmdop_claw_imports.py" ]]; then
  "$CMDOP_CLAW_PY" "$PARENT/scripts/patch_cmdop_claw_imports.py" >/dev/null 2>&1 || true
fi

run_platform_set() {
  local variant="$1"
  local input_packets="$2"
  local pred_dir="$OUT_DIR/predictions_${variant}"
  mkdir -p "$pred_dir"
  if [[ "${STABLEEVAL_RESUME:-1}" != "1" ]]; then
    rm -f "$pred_dir"/*_predictions.jsonl
  fi

  run_one() {
    local platform="$1"
    local python="$2"
    "$python" src/agents/run_platform.py \
      --platform "$platform" \
      --input "$input_packets" \
      --system-prompt prompts/templates/risk_sensitive_agent_prompt.md \
      --output "$pred_dir/${platform}_predictions.jsonl" \
      --model "$MODEL" \
      --temperature 0 \
      --max-tokens 1600 \
      --max-cases 0 \
      --max-estimated-cost-usd "${STABLEEVAL_VALIDATION_MAX_COST_USD_PER_PLATFORM:-25.00}" \
      --label-calibration none \
      --resume \
      > "$LOG_DIR/${variant}_${platform}.log" 2>&1
  }

  echo "Running ${variant} with model: $MODEL"
  run_one nanobot "$NANOBOT_PY" &
  pids=("$!")
  run_one langgraph "$LANGGRAPH_PY" &
  pids+=("$!")
  run_one hermes_ai "$HERMES_AI_PY" &
  pids+=("$!")
  run_one evoagentx "$EVOAGENTX_PY" &
  pids+=("$!")
  run_one openclaw "$CMDOP_CLAW_PY" &
  pids+=("$!")
  run_one nanoclaw "$CMDOP_CLAW_PY" &
  pids+=("$!")
  status=0
  for pid in "${pids[@]}"; do
    wait "$pid" || status=1
  done
  if [[ "$status" != "0" ]]; then
    echo "One or more ${variant} platform runs failed." >&2
    exit "$status"
  fi
}

evaluate_variant() {
  local pred_dir="$1"
  local out_subdir="$2"
  local labels_file="$3"
  "$CORE_PY" scripts/evaluate/evaluate_predictions.py \
    --root . \
    --pred-dir "$pred_dir" \
    --labels data/benchmark/stableeval_507_natural/labels.csv \
    --pilot-labels "$labels_file" \
    --packets data/benchmark/stableeval_507_natural/prompt_packets.jsonl \
    --adapter-metadata results/stableeval_120_enriched/agent_execution_metadata.csv \
    --selected-model-json "$OUT_DIR/model_backend.json" \
    --out-dir "$OUT_DIR/$out_subdir"
}

mkdir -p "$OUT_DIR/baselines_only_predictions"
rm -f "$OUT_DIR/baselines_only_predictions"/*_predictions.jsonl
evaluate_variant "$OUT_DIR/baselines_only_predictions" "evaluation_baselines" "$OUT_DIR/validation_case_list.csv"

run_platform_set "base_raw" "data/benchmark/stableeval_120_enriched/prompt_packets.jsonl"
"$CORE_PY" scripts/evaluate/apply_calibration.py \
  --input-dir "$OUT_DIR/predictions_base_raw" \
  --output-dir "$OUT_DIR/predictions_base_calibrated"

evaluate_variant "$OUT_DIR/predictions_base_raw" "evaluation_base_raw" "$OUT_DIR/validation_case_list.csv"
evaluate_variant "$OUT_DIR/predictions_base_calibrated" "evaluation_base_calibrated" "$OUT_DIR/validation_case_list.csv"

rm -rf "$OUT_DIR/predictions_verifier_raw"
"$CORE_PY" scripts/evaluate/run_verifier_ablation.py \
  --input data/benchmark/stableeval_120_enriched/prompt_packets.jsonl \
  --base-pred-dir "$OUT_DIR/predictions_base_raw" \
  --output-dir "$OUT_DIR/predictions_verifier_raw" \
  --model "$MODEL" \
  --temperature 0 \
  --max-tokens 1600 \
  --workers "${STABLEEVAL_VERIFIER_WORKERS:-6}" \
  > "$LOG_DIR/verifier_from_base.log" 2>&1
"$CORE_PY" scripts/evaluate/apply_calibration.py \
  --input-dir "$OUT_DIR/predictions_verifier_raw" \
  --output-dir "$OUT_DIR/predictions_verifier_calibrated"

evaluate_variant "$OUT_DIR/predictions_verifier_raw" "evaluation_verifier_raw" "$OUT_DIR/validation_case_list.csv"
evaluate_variant "$OUT_DIR/predictions_verifier_calibrated" "evaluation_verifier_calibrated" "$OUT_DIR/validation_case_list.csv"

run_platform_set "anonymization_original" "data/benchmark/stableeval_120_enriched/anonymization_original_prompt_packets.jsonl"
run_platform_set "anonymization_anonymized" "data/benchmark/stableeval_120_enriched/anonymization_anonymized_prompt_packets.jsonl"

evaluate_variant "$OUT_DIR/predictions_anonymization_original" "evaluation_anonymization_original" "$OUT_DIR/anonymization_case_list.csv"
evaluate_variant "$OUT_DIR/predictions_anonymization_anonymized" "evaluation_anonymization_anonymized" "$OUT_DIR/anonymization_case_list.csv"

"$CORE_PY" scripts/release/finalize_stableeval_120_enriched.py --root .

echo "Intermediate validation complete. Outputs are in $ROOT/$OUT_DIR"
