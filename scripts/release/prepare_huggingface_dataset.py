#!/usr/bin/env python3
"""Prepare a Hugging Face-ready StableEval dataset folder.

This script does not upload anything. It copies reviewer-relevant processed
benchmark artifacts and result tables into a Hugging Face dataset repository
layout and writes:

- README.md dataset card with Hugging Face YAML configs
- croissant.json with core + minimal Responsible AI metadata
- LICENSE.md with mixed-source licensing caveat
- RELEASE_CHECKLIST.md
- checksums.sha256
- upload_to_huggingface.sh template

Raw vendor snapshots are intentionally excluded because redistribution rights
must be confirmed before public release.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


DATASET_SLUG = "stableeval-arena"
DATASET_TITLE = "StableEval Arena"
HF_URL_PLACEHOLDER = f"https://huggingface.co/datasets/YOUR_ORG_OR_USERNAME/{DATASET_SLUG}"


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.strip() + "\n", encoding="utf-8")


def copy(src: Path, dst: Path) -> bool:
    if not src.exists():
        return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return True


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def csv_columns(path: Path) -> list[str]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        return next(reader)


def jsonl_top_level_fields(path: Path) -> list[str]:
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                obj = json.loads(line)
                return list(obj.keys())
    return []


def data_type_for_series(series: pd.Series) -> str:
    if pd.api.types.is_bool_dtype(series):
        return "sc:Boolean"
    if pd.api.types.is_integer_dtype(series):
        return "sc:Integer"
    if pd.api.types.is_float_dtype(series):
        return "sc:Float"
    return "sc:Text"


def croissant_record_set(file_id: str, path: Path, name: str, description: str) -> dict[str, Any]:
    fields: list[dict[str, Any]] = []
    if path.suffix == ".csv":
        df = pd.read_csv(path, nrows=100)
        for col in df.columns:
            fields.append(
                {
                    "@type": "cr:Field",
                    "@id": f"{name}/{col}",
                    "name": col,
                    "description": f"Column `{col}` from `{path.name}`.",
                    "dataType": data_type_for_series(df[col]),
                    "source": {"fileObject": {"@id": file_id}, "extract": {"column": col}},
                }
            )
    elif path.suffix == ".jsonl":
        for col in jsonl_top_level_fields(path):
            fields.append(
                {
                    "@type": "cr:Field",
                    "@id": f"{name}/{col}",
                    "name": col,
                    "description": f"Top-level JSONL field `{col}` from `{path.name}`.",
                    "dataType": "sc:Text",
                    "source": {"fileObject": {"@id": file_id}, "extract": {"jsonPath": f"$.{col}"}},
                }
            )
    if not fields:
        fields.append(
            {
                "@type": "cr:Field",
                "@id": f"{name}/file",
                "name": "file",
                "description": description,
                "dataType": "sc:Text",
                "source": {"fileObject": {"@id": file_id}},
            }
        )
    return {"@type": "cr:RecordSet", "@id": name, "name": name, "description": description, "field": fields}


def build_package(root: Path, out: Path) -> None:
    if out.exists():
        shutil.rmtree(out)
    (out / "data").mkdir(parents=True)
    (out / "docs").mkdir()
    (out / "figures").mkdir()
    (out / "scripts").mkdir()
    (out / "metadata").mkdir()

    source_map = {
        "data/full_case_labels_507.csv": root / "data/benchmark/stableeval_507_natural/labels.csv",
        "data/full_case_metadata_507.csv": root / "data/benchmark/stableeval_507_natural/full_case_pool.csv",
        "data/full_507_prompt_packets.jsonl": root / "data/benchmark/stableeval_507_natural/prompt_packets.jsonl",
        "data/validation_case_list_120.csv": root / "results/stableeval_120_enriched/validation_case_list.csv",
        "data/validation_prompt_packets_120.jsonl": root / "data/benchmark/stableeval_120_enriched/prompt_packets.jsonl",
        "data/validation_base_calibrated_raw_predictions_120.csv": root / "results/stableeval_120_enriched/evaluation_base_calibrated/raw_predictions.csv",
        "data/validation_base_calibrated_raw_predictions_120.jsonl": root / "results/stableeval_120_enriched/evaluation_base_calibrated/raw_predictions.jsonl",
        "data/validation_prediction_quality_by_platform.csv": root / "results/stableeval_120_enriched/evaluation_base_calibrated/prediction_quality_by_platform.csv",
        "data/validation_baseline_comparison.csv": root / "results/stableeval_120_enriched/evaluation_base_calibrated/baseline_comparison.csv",
        "data/validation_computational_cost_by_platform.csv": root / "results/stableeval_120_enriched/evaluation_base_calibrated/computational_cost_by_platform.csv",
        "data/validation_cost_report.csv": root / "results/stableeval_120_enriched/evaluation_base_calibrated/cost_report.csv",
        "data/validation_failure_modes.csv": root / "results/stableeval_120_enriched/evaluation_base_calibrated/failure_modes.csv",
        "data/validation_variant_comparison.csv": root / "results/stableeval_120_enriched/validation_variant_comparison.csv",
        "data/calibration_raw_vs_calibrated_results.csv": root / "results/stableeval_120_enriched/calibration_raw_vs_calibrated_results.csv",
        "data/anonymization_ablation_results.csv": root / "results/stableeval_120_enriched/anonymization_ablation_results.csv",
        "data/agent_execution_metadata.csv": root / "results/stableeval_120_enriched/agent_execution_metadata.csv",
        "metadata/dataset_summary.json": root / "data/benchmark/stableeval_507_natural/dataset_summary.json",
        "metadata/model_backend.json": root / "results/stableeval_120_enriched/model_backend.json",
        "docs/calibration_rule.md": root / "results/stableeval_120_enriched/calibration_rule.md",
        "docs/validation_case_selection_report.md": root / "results/stableeval_120_enriched/validation_case_selection_report.md",
        "docs/validation_120_summary.md": root / "results/stableeval_120_enriched/validation_120_summary.md",
        "docs/parametric_memory_leakage_note.md": root / "results/stableeval_120_enriched/parametric_memory_leakage_note.md",
        "docs/benchmark_data_card.md": root / "data/benchmark/data_cards/benchmark_data_card.md",
        "docs/methodology_and_references.md": root / "docs/methodology/methodology_and_references.md",
        "data/stableeval_507_natural_v6_leaderboard.csv": root / "results/stableeval_507_natural/final_tables/stableeval_507_natural_v6_leaderboard.csv",
    }

    copied: list[dict[str, str]] = []
    missing: list[str] = []
    for rel, src in source_map.items():
        dst = out / rel
        if copy(src, dst):
            copied.append({"path": rel, "source": str(src.relative_to(root))})
        else:
            missing.append(f"{rel} <- {src}")

    for fig in (root / "results/stableeval_120_enriched/figures").glob("*.png"):
        copy(fig, out / "figures" / fig.name)
        copied.append({"path": f"figures/{fig.name}", "source": str(fig.relative_to(root))})

    schema_dir = out / "docs"
    write(
        schema_dir / "INPUT_PACKET_SCHEMA.md",
        """
# Input Packet Schema

Each prompt packet is a JSON object with:

- `case_id`
- `stablecoin`
- `stablecoin_name`
- `observation_time`
- `lookback_window`: start, end, hours observed
- `forecast_horizon`: start, end, hours
- `task`
- `risk_sensitive_evidence`: lookback-only stress indicators
- `evidence`: original lookback summary, context, daily lookback table, and last 48 hourly observations

The packet does not include hidden next-7-day labels, future prices, or horizon outcomes.
""",
    )
    write(
        schema_dir / "OUTPUT_SCHEMA.md",
        """
# Agent Output Schema

Each agent prediction is strict JSON with:

- `case_id`
- `platform`
- `model_backend`
- `execution_mode`
- `price_stability_next_7d`: `stable`, `watch`, or `stress`
- `p_depeg_next_7d`
- `predicted_max_abs_deviation_bps`
- `predicted_direction`
- `confidence`
- `rationale`
""",
    )
    write(
        schema_dir / "LABEL_DEFINITIONS.md",
        """
# Label Definitions

Dollar-peg deviation is computed as:

`deviation_bps = abs(hourly_close_price - 1.0) * 10000`

- Stable: no meaningful hidden-horizon deviation.
- Watch: mild but meaningful hidden-horizon instability, including any hourly close deviation at or above 50 bps absent strict sustained depeg.
- Stress: large, persistent, or operationally meaningful instability.
- Strict sustained depeg: absolute hourly close deviation at or above 100 bps for at least 3 consecutive hours.
""",
    )

    dataset_summary = json.loads((out / "metadata/dataset_summary.json").read_text(encoding="utf-8"))
    labels = pd.read_csv(out / "data/full_case_labels_507.csv")
    validation_cases = pd.read_csv(out / "data/validation_case_list_120.csv")
    quality = pd.read_csv(out / "data/validation_prediction_quality_by_platform.csv")
    best_agent = quality[quality["system_type"].eq("agent")].sort_values("taskA_macro_f1", ascending=False).iloc[0]
    best_baseline = quality[quality["system_type"].eq("baseline")].sort_values("taskA_macro_f1", ascending=False).iloc[0]

    configs = [
        ("full_case_labels_507", "full", "data/full_case_labels_507.csv"),
        ("full_case_metadata_507", "full", "data/full_case_metadata_507.csv"),
        ("full_507_prompt_packets", "full", "data/full_507_prompt_packets.jsonl"),
        ("validation_cases_120", "validation", "data/validation_case_list_120.csv"),
        ("validation_prompt_packets_120", "validation", "data/validation_prompt_packets_120.jsonl"),
        ("validation_predictions_120", "validation", "data/validation_base_calibrated_raw_predictions_120.jsonl"),
        ("validation_prediction_quality", "results", "data/validation_prediction_quality_by_platform.csv"),
        ("validation_baselines", "results", "data/validation_baseline_comparison.csv"),
        ("validation_cost", "results", "data/validation_computational_cost_by_platform.csv"),
        ("validation_ablation", "results", "data/validation_variant_comparison.csv"),
        ("anonymization_ablation", "results", "data/anonymization_ablation_results.csv"),
        ("agent_execution_metadata", "metadata", "data/agent_execution_metadata.csv"),
    ]

    yaml_lines = [
        "---",
        "pretty_name: StableEval Arena",
        "license: other",
        "language:",
        "- en",
        "task_categories:",
        "- tabular-classification",
        "- time-series-forecasting",
        "tags:",
        "- agentic-ai",
        "- stablecoin",
        "- benchmark",
        "- evaluation",
        "- trustworthiness",
        "- finance",
        "size_categories:",
        "- n<1K",
        "configs:",
    ]
    for name, split, path in configs:
        yaml_lines.extend(
            [
                f"- config_name: {name}",
                "  data_files:",
                f"  - split: {split}",
                f"    path: {path}",
            ]
        )
    yaml_lines.append("---")

    readme = f"""
{chr(10).join(yaml_lines)}

# StableEval Arena

StableEval Arena is a cost-aware agentic benchmark for stablecoin price-stability prediction. Given a frozen 30-day lookback window for USDT, USDC, or DAI, agentic systems predict next-7-day stable/watch/stress status and dollar-peg deviation.

This Hugging Face package is prepared for academic review and public reproducibility. It includes reviewer-loadable benchmark artifacts, machine-readable metadata, and Responsible AI documentation. It intentionally excludes raw vendor snapshots.

## Dataset URL Placeholder

Replace this after upload:

`{HF_URL_PLACEHOLDER}`

## Contents

- `data/full_case_labels_507.csv`: labels for the full processed case pool.
- `data/full_case_metadata_507.csv`: case-level metadata for the full processed pool.
- `data/full_507_prompt_packets.jsonl`: risk-sensitive lookback-only packets for all 507 cases; used to regenerate baselines.
- `data/validation_case_list_120.csv`: 120-case validation set.
- `data/validation_prompt_packets_120.jsonl`: lookback-only agent input packets for the 120-case validation.
- `data/validation_base_calibrated_raw_predictions_120.*`: saved raw/parsed prediction outputs for the main validation protocol.
- `data/validation_*`: evaluation, baseline, cost, failure, ablation, anonymization, and agent-execution metadata tables.
- `docs/`: schema, label, calibration, leakage, validation-selection, and model/agent documentation.
- `figures/`: paper-ready benchmark figures.
- `croissant.json`: manually prepared Croissant metadata with core and minimal RAI fields.

## Summary Statistics

- Full processed case pool: {len(labels)} cases.
- Validation set: {len(validation_cases)} cases.
- Validation distribution: {validation_cases['enhanced_stability_label'].value_counts().to_dict()}.
- Stablecoins: {', '.join(dataset_summary.get('stablecoins', []))}.
- Context assets: {', '.join(dataset_summary.get('context_symbols', []))}.
- Lookback window: {dataset_summary.get('lookback_days')} days.
- Forecast horizon: {dataset_summary.get('horizon_days')} days.

## Main Validation Result

Best agent: `{best_agent['system']}`, Macro-F1={best_agent['taskA_macro_f1']:.3f}, balanced accuracy={best_agent['taskA_balanced_accuracy']:.3f}, stress recall={best_agent['taskA_recall_stress']:.3f}.

Best baseline: `{best_baseline['system']}`, Macro-F1={best_baseline['taskA_macro_f1']:.3f}, stress recall={best_baseline['taskA_recall_stress']:.3f}.

Important caveat: agents beat baselines on Macro-F1 but do not beat the historical-persistence baseline on stress recall.

## Load Examples

```python
from datasets import load_dataset

repo = "YOUR_ORG_OR_USERNAME/{DATASET_SLUG}"
labels = load_dataset(repo, "full_case_labels_507")
validation = load_dataset(repo, "validation_cases_120")
predictions = load_dataset(repo, "validation_predictions_120")
```

## Intended Use

This dataset is intended for benchmark evaluation, reproducibility checks, and research on cost-aware trustworthy agentic AI systems for stablecoin risk prediction.

It is not intended for live trading, real-time financial advice, automated treasury control, or regulatory compliance decisions.

## License And Redistribution Caveat

The benchmark metadata, labels, prompts, agent outputs, scripts, and paper figures are research artifacts prepared for academic reproducibility. Some fields are derived from third-party market data providers. Raw CryptoCompare/CCData and DeFiLlama snapshots are not included here. Before making this dataset public, confirm that redistribution of processed/derived market values is compatible with the relevant provider terms.

See `LICENSE.md` for the current mixed-source licensing recommendation.

## Responsible AI Metadata

Responsible AI and release-readiness fields are included in `croissant.json` and summarized in `RELEASE_CHECKLIST.md`.
"""
    write(out / "README.md", readme)

    write(
        out / "LICENSE.md",
        """
# License

This package is prepared for academic review and reproducibility.

Recommended public-release structure:

1. Code, prompts, schemas, labels, evaluation outputs, figures, and written benchmark metadata: release under CC-BY-4.0 or MIT/Apache-2.0 as appropriate for code.
2. Processed market-derived case features and prompt packets: release only after confirming that redistribution is allowed under the source providers' terms.
3. Raw CryptoCompare/CCData and DeFiLlama snapshots: not included in this package.

Until source redistribution rights are confirmed, treat this dataset as `license: other` with the restrictions above.
""",
    )

    write(
        out / ".gitattributes",
        """
*.png filter=lfs diff=lfs merge=lfs -text
*.jsonl filter=lfs diff=lfs merge=lfs -text
*.csv filter=lfs diff=lfs merge=lfs -text
""",
    )

    write(
        out / "RELEASE_CHECKLIST.md",
        f"""
# StableEval Arena Hugging Face Release Checklist

- [x] Preferred hosting target selected: Hugging Face.
- [x] Dataset repository folder prepared locally.
- [x] Supported file formats used: CSV and JSONL.
- [x] Dataset card prepared: `README.md`.
- [x] Core Croissant file prepared: `croissant.json`.
- [x] Minimal Responsible AI fields included in Croissant:
  - `rai:dataLimitations`
  - `rai:dataBiases`
  - `rai:personalSensitiveInformation`
  - `rai:dataUseCases`
  - `rai:dataSocialImpact`
  - `rai:hasSyntheticData`
  - `prov:wasDerivedFrom`
  - `prov:wasGeneratedBy`
- [x] Clear license caveat included.
- [x] Raw third-party data excluded pending redistribution review.
- [ ] Upload package to Hugging Face.
- [ ] Replace placeholder URL with final dataset URL.
- [ ] Download Hugging Face-generated Croissant after upload.
- [ ] Merge/verify RAI fields in Croissant.
- [ ] Validate final Croissant using the Hugging Face Croissant validator.
- [ ] Link the final dataset URL from the paper/repository.

Prepared package path: `{out}`.
""",
    )

    write(
        out / "UPLOAD_INSTRUCTIONS.md",
        f"""
# Upload Instructions

## 1. Create Dataset Repository

On Hugging Face, create a dataset repository, for example:

`YOUR_ORG_OR_USERNAME/{DATASET_SLUG}`

## 2. Review License

Before public upload, confirm whether the processed market-derived features can be redistributed. If uncertain, keep the repository private/gated for reviewer access or remove prompt-packet files that contain derived market values.

## 3. Upload

Install and log in:

```bash
pip install -U huggingface_hub
huggingface-cli login
```

Then from this package directory:

```bash
huggingface-cli upload YOUR_ORG_OR_USERNAME/{DATASET_SLUG} . . --repo-type dataset
```

## 4. After Upload

1. Replace placeholder URLs in `README.md` and `croissant.json`.
2. Open the Hugging Face dataset page and verify the dataset viewer loads CSV/JSONL configs.
3. Download the platform-generated Croissant file.
4. Add or preserve the RAI fields from this local `croissant.json`.
5. Validate the final Croissant file with the Hugging Face Croissant validator.
""",
    )

    write(
        out / "scripts/validate_local_package.py",
        """
from pathlib import Path
import json

root = Path(__file__).resolve().parents[1]
required = [
    "README.md",
    "LICENSE.md",
    "croissant.json",
    "RELEASE_CHECKLIST.md",
    "data/full_case_labels_507.csv",
    "data/validation_case_list_120.csv",
    "data/validation_prompt_packets_120.jsonl",
    "data/validation_base_calibrated_raw_predictions_120.jsonl",
]
missing = [p for p in required if not (root / p).exists()]
if missing:
    raise SystemExit(f"Missing required files: {missing}")
croissant = json.loads((root / "croissant.json").read_text())
for key in ["@context", "@type", "name", "url", "license", "conformsTo", "distribution", "recordSet"]:
    if key not in croissant:
        raise SystemExit(f"Missing Croissant core field: {key}")
for key in ["rai:dataLimitations", "rai:dataBiases", "rai:personalSensitiveInformation", "rai:dataUseCases", "rai:dataSocialImpact", "rai:hasSyntheticData"]:
    if key not in croissant:
        raise SystemExit(f"Missing Croissant RAI field: {key}")
print("Local package structure check passed.")
""",
    )

    write(
        out / "upload_to_huggingface.sh",
        f"""
#!/usr/bin/env bash
set -euo pipefail

REPO_ID="${{1:-YOUR_ORG_OR_USERNAME/{DATASET_SLUG}}}"
echo "Uploading to Hugging Face dataset repo: $REPO_ID"
echo "Make sure you have reviewed LICENSE.md and logged in with huggingface-cli."
huggingface-cli upload "$REPO_ID" . . --repo-type dataset
""",
    )
    (out / "upload_to_huggingface.sh").chmod(0o755)

    file_objects = []
    record_sets = []
    for data_path in sorted((out / "data").glob("*")):
        if data_path.suffix not in {".csv", ".jsonl"}:
            continue
        rel = data_path.relative_to(out).as_posix()
        file_id = rel.replace("/", "_").replace(".", "_")
        file_objects.append(
            {
                "@type": "cr:FileObject",
                "@id": file_id,
                "name": data_path.name,
                "contentUrl": rel,
                "encodingFormat": "text/csv" if data_path.suffix == ".csv" else "application/jsonlines",
                "sha256": sha256(data_path),
            }
        )
        record_sets.append(
            croissant_record_set(
                file_id=file_id,
                path=data_path,
                name=data_path.stem,
                description=f"StableEval Arena artifact `{rel}`.",
            )
        )

    croissant = {
        "@context": {
            "sc": "https://schema.org/",
            "cr": "http://mlcommons.org/croissant/",
            "rai": "http://mlcommons.org/croissant/RAI/",
            "prov": "http://www.w3.org/ns/prov#",
        },
        "@type": "sc:Dataset",
        "name": DATASET_TITLE,
        "description": "A cost-aware agentic benchmark for stablecoin price-stability prediction under frozen historical replay.",
        "url": HF_URL_PLACEHOLDER,
        "license": "https://huggingface.co/datasets/YOUR_ORG_OR_USERNAME/stableeval-arena/blob/main/LICENSE.md",
        "conformsTo": "http://mlcommons.org/croissant/1.1",
        "datePublished": datetime.now(timezone.utc).date().isoformat(),
        "creator": [{"@type": "sc:Person", "name": "Wanweilin and collaborators"}],
        "keywords": ["agentic AI", "stablecoin", "benchmark", "trustworthy AI", "financial prediction"],
        "distribution": file_objects,
        "recordSet": record_sets,
        "rai:dataLimitations": "The release benchmark covers USDT, USDC, and DAI, uses historical replay rather than live trading, and includes limited off-chain/on-chain mechanism data. Stress cases are rare; strict sustained-depeg positives are especially rare.",
        "rai:dataBiases": "The 120-case validation intentionally oversamples watch/stress/near-stress cases relative to the natural full-case distribution. Results should not be interpreted as natural deployment prevalence without the full 507-case distribution.",
        "rai:personalSensitiveInformation": "No personal or sensitive human-subject information is included. The dataset concerns public market/stablecoin time-series and agent outputs.",
        "rai:dataUseCases": "Established use cases: benchmark evaluation, reproducibility, cost/reliability analysis of agentic AI systems, stablecoin price-stability prediction research. Not established: live trading, financial advice, compliance decisions, automated treasury execution.",
        "rai:dataSocialImpact": "Positive impact: improves transparent evaluation of AI agents in financially meaningful settings. Negative/misuse risk: weak stress recall or misunderstood benchmark results could create false confidence in automated risk monitoring. Mitigation: limitations and stress-recall caveats are included.",
        "rai:hasSyntheticData": False,
        "prov:wasDerivedFrom": [
            "https://min-api.cryptocompare.com/data/v2/histohour",
            "https://stablecoins.llama.fi/",
            "https://openrouter.ai/",
        ],
        "prov:wasGeneratedBy": "Generated by StableEval Arena scripts from public market data, frozen-window case construction, LLM-backed agent runs, and evaluator scripts. See docs and repository scripts for preprocessing, prompt, calibration, and evaluation details.",
    }
    (out / "croissant.json").write_text(json.dumps(croissant, indent=2), encoding="utf-8")

    checks = []
    for file in sorted(out.rglob("*")):
        if file.is_file() and file.name != "checksums.sha256":
            checks.append(f"{sha256(file)}  {file.relative_to(out).as_posix()}")
    write(out / "checksums.sha256", "\n".join(checks))

    manifest = pd.DataFrame(
        [
            {
                "path": file.relative_to(out).as_posix(),
                "bytes": file.stat().st_size,
                "sha256": sha256(file),
            }
            for file in sorted(out.rglob("*"))
            if file.is_file()
        ]
    )
    manifest.to_csv(out / "FILE_MANIFEST.csv", index=False)

    if missing:
        write(out / "MISSING_SOURCE_FILES.md", "# Missing Source Files\n\n" + "\n".join(f"- {m}" for m in missing))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".", help="Stablecoin Eval Arena root")
    parser.add_argument("--out", default="hf_dataset_package/stableeval-arena", help="Output dataset package directory")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    out = root / args.out
    build_package(root, out)
    print(f"Prepared Hugging Face dataset package at {out}")


if __name__ == "__main__":
    main()
