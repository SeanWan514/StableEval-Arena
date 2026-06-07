# Reproducibility

This guide explains how to reproduce the release-facing StableEval Arena artifacts. Saved-output checks do not call model APIs and should write to a temporary output folder. Real agent reruns are optional and require an OpenRouter credential.

## Environment

Install the core dependencies for saved-output recomputation:

```bash
pip install -r requirements-core.txt
```

`requirements-evoagentx-extra.txt` is optional and only needed for EvoAgentX-backed reruns. If a clean environment cannot reach PyPI or a package mirror, use an equivalent Python environment with the core scientific stack listed in `requirements-core.txt`.

Do not write API keys into repository files.

## No-API Saved-Output Checks

Create a temporary verification directory:

```bash
mkdir -p /tmp/stableeval_release_audit
```

### StableEval-120-Enriched

Canonical inputs and outputs:

```text
data/benchmark/stableeval_120_enriched/prompt_packets.jsonl
results/stableeval_120_enriched/validation_case_list.csv
results/stableeval_120_enriched/predictions_base_raw/
results/stableeval_120_enriched/predictions_base_calibrated/
results/stableeval_120_enriched/evaluation_base_calibrated/
results/stableeval_120_enriched/freeze_manifest/
```

Recompute the main 120-case evaluation from saved calibrated predictions:

```bash
python scripts/evaluate/recompute_stableeval_120_enriched.py \
  --root . \
  --out /tmp/stableeval_release_audit/stableeval_120_enriched_recompute
```

The command writes a recomputed `prediction_quality_by_platform` table and a comparison summary under `/tmp/stableeval_release_audit/` and does not overwrite committed canonical files. The default tolerance is `1e-3` to avoid failing on tiny tie-order differences in non-primary average-precision values. Use `scripts/evaluate/evaluate_predictions.py` only when you want to regenerate the fuller local report bundle with figures and auxiliary tables.

### StableEval-507-Natural

Canonical inputs and outputs:

```text
data/benchmark/stableeval_507_natural/case_list.csv
data/benchmark/stableeval_507_natural/labels.csv
data/benchmark/stableeval_507_natural/prompt_packets.jsonl
results/stableeval_507_natural/baselines/
results/stableeval_507_natural/raw_predictions/
results/stableeval_507_natural/calibrated_predictions/
results/stableeval_507_natural/metrics/
results/stableeval_507_natural/reports/
results/stableeval_507_natural/final_tables/stableeval_507_natural_v6_leaderboard.csv
```

Verify the final 507 v6 leaderboard, stress-case audit, and cost/reliability summary from saved outputs:

```bash
python scripts/evaluate/recompute_stableeval_507_natural.py \
  --root . \
  --out /tmp/stableeval_release_audit/stableeval_507_natural_recompute
```

This script reads labels, baselines, raw predictions, calibrated predictions, and cost logs from the cleaned two-block tree. It writes recomputed CSV/JSON files only to the requested output directory and compares the recomputed leaderboard with `results/stableeval_507_natural/final_tables/stableeval_507_natural_v6_leaderboard.csv`.

## Case And Prompt Rebuilds

Rebuilding the full processed pool may fetch upstream market data and should be treated separately from saved-output verification:

```bash
python scripts/build_cases/build_full_case_pool.py \
  --start 2023-01-01 \
  --end 2026-05-01 \
  --lookback-days 30 \
  --horizon-days 7 \
  --stride-days 7

python scripts/build_cases/build_stableeval_120_enriched.py --root .
python scripts/build_cases/build_stableeval_507_natural_packets.py --root .
```

Raw provider/vendor snapshots are not redistributed. The release includes processed benchmark artifacts and enough saved predictions/results to verify the paper-facing metrics without refetching raw data.

## Optional API-Backed Reruns

Real LLM-backed reruns call OpenRouter and may spend API credits:

```bash
export OPENROUTER_API_KEY="..."
./scripts/run_agents/stableeval_120_enriched/run_stableeval_120_enriched_experiments.sh
```

The 507 runner scripts under `scripts/run_agents/stableeval_507_natural/` are optional rerun helpers for the six-system extension. They use the cleaned prompt path `data/benchmark/stableeval_507_natural/prompt_packets.jsonl` and write under `results/stableeval_507_natural/` when run. Platform-specific Python interpreters can be supplied through the documented environment variables in the runner scripts if the default local environments are unavailable.

Historical one-off finalizers in `scripts/run_agents/stableeval_507_natural/finalize_*.py` are retained for provenance from the original run sequence. Use `scripts/evaluate/recompute_stableeval_507_natural.py` for public-release verification.

## Final Tables And Manifests

The final v6 507 leaderboard is the canonical 507 table:

```text
results/stableeval_507_natural/final_tables/stableeval_507_natural_v6_leaderboard.csv
```

`FILE_MANIFEST.md` lists release-facing files and checksums. Some historical manifests or created-file manifests may preserve pre-cleanup path names for audit provenance; they are not the active public paths.

## Hugging Face Package Draft

Prepare a local package draft after the GitHub tree is final:

```bash
python scripts/release/prepare_huggingface_dataset.py --root . --out /tmp/stableeval_hf_package
python /tmp/stableeval_hf_package/scripts/validate_local_package.py
```

Raw provider snapshots are intentionally excluded from the package by default.
