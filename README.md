<h1 align="center">🛡️ StableEval Arena</h1>

<p align="center">
  <strong>StableEval Arena: A Cost-Aware Agentic Benchmark for Stablecoin Price Stability Prediction</strong><br>
  Accepted at the KDD 2026 Workshop on Evaluation and Trustworthiness of Agentic AI<br>
  <strong>🎤 Selected for oral presentation</strong>
</p>

<p align="center">
  Sean Wan · Dongping Liu · Luyao Zhang
</p>

<p align="center">
  <a href="https://kdd-eval-workshop.github.io/agenticai-evaluation-kdd2026/"><img alt="KDD 2026 workshop: Accepted" src="https://img.shields.io/badge/KDD_2026_workshop-Accepted-0B7A75"></a>
  <a href="https://kdd-eval-workshop.github.io/agenticai-evaluation-kdd2026/"><img alt="Presentation: Oral" src="https://img.shields.io/badge/presentation-Oral-6f42c1"></a>
  <a href="#release-snapshot"><img alt="StableEval-120: Enriched" src="https://img.shields.io/badge/StableEval--120-Enriched-2ea44f"></a>
  <a href="#release-snapshot"><img alt="StableEval-507: Natural" src="https://img.shields.io/badge/StableEval--507-Natural-0ea5e9"></a>
  <br>
  <a href="#execution-caveats"><img alt="Agentic AI: 6 systems" src="https://img.shields.io/badge/agentic_AI-6_systems-4F6BED"></a>
  <a href="#release-snapshot"><img alt="Stablecoins: USDT, USDC, DAI" src="https://img.shields.io/badge/stablecoins-USDT_%7C_USDC_%7C_DAI-7A4FB3"></a>
  <a href="#release-snapshot"><img alt="Backend: Qwen 2.5 72B via OpenRouter" src="https://img.shields.io/badge/backend-Qwen_2.5_72B_via_OpenRouter-B35C00"></a>
  <a href="LICENSE"><img alt="Code license: Apache-2.0" src="https://img.shields.io/badge/code_license-Apache--2.0-64748b"></a>
</p>

<p align="center">
  <a href="https://kdd-eval-workshop.github.io/agenticai-evaluation-kdd2026/assets/papers/11_StableEval_Arena_A_Cost_Awa.pdf">📄 Paper</a> ·
  <a href="https://kdd-eval-workshop.github.io/agenticai-evaluation-kdd2026/assets/papers/posters/11_StableEval_Arena_A_Cost_Awa_Poster.pdf">🖼️ Poster</a> ·
  <a href="https://huggingface.co/datasets/SeanWan05/stableeval-arena">🤗 Dataset</a> ·
  <a href="#reproduce-from-saved-outputs">🚀 Quick start</a><br>
  <a href="#repository-map">🗂️ Repository map</a> ·
  <a href="data/benchmark/data_cards/benchmark_data_card.md">🗃️ Data card</a> ·
  <a href="REPRODUCIBILITY.md">🔎 Reproducibility</a> ·
  <a href="#citation">📚 Citation</a>
</p>

> **Accepted at the [KDD 2026 Workshop on Evaluation and Trustworthiness of Agentic AI](https://kdd-eval-workshop.github.io/agenticai-evaluation-kdd2026/). Selected for Oral Presentation.**
>
> Submission **#11** · [Paper](https://kdd-eval-workshop.github.io/agenticai-evaluation-kdd2026/assets/papers/11_StableEval_Arena_A_Cost_Awa.pdf) · [Poster](https://kdd-eval-workshop.github.io/agenticai-evaluation-kdd2026/assets/papers/posters/11_StableEval_Arena_A_Cost_Awa_Poster.pdf)

GitHub repository: https://github.com/SeanWan514/StableEval-Arena

HuggingFace repository: https://huggingface.co/datasets/SeanWan05/stableeval-arena 

---

<a id="overview"></a>

## 🔬 Overview

**StableEval Arena** is a historical-replay benchmark for evaluating whether agentic AI systems can act as cost-aware, trustworthy stablecoin risk agents. Each case gives an agent a frozen 30-day lookback packet and asks it to predict the next 7-day stable/watch/stress state, depeg probability, and dollar-peg deviation.

The release is organized around two paper-facing benchmark blocks:

| Block | Role | Current release state |
|---|---|---|
| `StableEval-120-Enriched` | Stress-enriched rare-risk diagnostic | Complete: 120 cases, six systems plus baselines, ablations, freeze manifest |
| `StableEval-507-Natural` | Natural-distribution scaling and robustness result | Complete: 507 cases, baselines, four native/framework-level agents, two adapter-based `-Claw` extensions |

API keys are never stored in the repository. Saved outputs are included so the reported tables can be recomputed without calling model APIs.

<a id="release-snapshot"></a>

## ✨ Research snapshot

| Component | Current release state |
|---|---|
| `StableEval-120-Enriched` | 54 stable, 45 watch, 21 stress cases |
| `StableEval-507-Natural` | 441 stable, 45 watch, 21 stress cases |
| Stablecoins | USDT, USDC, DAI |
| Context assets | BTC and ETH market context |
| Systems | Nanobot, LangGraph, Hermes AI, EvoAgentX, OpenClaw, NanoClaw |
| Native/framework-level agents | Nanobot, LangGraph, Hermes AI, EvoAgentX |
| Adapter-based extensions | OpenClaw and NanoClaw via StableEval adapter |
| Model backend | `qwen/qwen-2.5-72b-instruct` through OpenRouter |
| Protocol | same prompt schema, case order, temperature 0, evaluator, and calibration rule |
| Main trustworthiness caveat | stress recall remains weak; this is a central finding, not a hidden limitation |

<a id="why-this-benchmark-exists"></a>

## 🎯 Why this benchmark exists

StableEval Arena is built around three workshop-facing dimensions:

- **Evaluation:** agentic systems and non-agent baselines are compared under frozen historical replay.
- **Trustworthy:** results include missed stress, false alarms, Brier score, latency, token cost, failure rate, and raw-output validity.
- **Agentic:** execution metadata, raw outputs, parsed JSON, and ablations are logged so the benchmark evaluates agent workflows, not only final labels.

Because all six systems use the same LLM backend, the comparison measures platform-mediated agentic execution, reliability, cost, and structured-output behavior under a common model. It is not a claim about independent foundation-model ability.

<a id="repository-map"></a>

## 🗂️ Repository map

```text
data/benchmark/stableeval_120_enriched/   120 prompt packets and anonymization packets
data/benchmark/stableeval_507_natural/    507 case list, labels, prompt packets, hourly windows
data/benchmark/data_cards/                Detailed benchmark data card
prompts/templates/                        System and risk-sensitive prompt templates
protocols/                                Frozen protocol descriptors
results/stableeval_120_enriched/          120 predictions, metrics, ablations, freeze manifest
results/stableeval_507_natural/           507 predictions, metrics, audits, costs, v6 leaderboard
scripts/                                  Build, run, evaluate, and release helpers
src/                                      Agent runner and StableEval helper code
docs/                                     Methodology, release notes, artifact notes
```

<a id="main-files"></a>

## 📂 Main files

| Use | File |
|---|---|
| 120 case list | [validation_case_list.csv](results/stableeval_120_enriched/validation_case_list.csv) |
| 120 prompt packets | [prompt_packets.jsonl](data/benchmark/stableeval_120_enriched/prompt_packets.jsonl) |
| 120 raw predictions | [predictions_base_raw/](results/stableeval_120_enriched/predictions_base_raw/) |
| 120 calibrated predictions | [predictions_base_calibrated/](results/stableeval_120_enriched/predictions_base_calibrated/) |
| 120 main metrics | [evaluation_base_calibrated/](results/stableeval_120_enriched/evaluation_base_calibrated/) |
| 120 final tables | [final_tables/](results/stableeval_120_enriched/final_tables/) |
| 120 freeze manifest | [freeze_manifest/](results/stableeval_120_enriched/freeze_manifest/) |
| 507 case list | [case_list.csv](data/benchmark/stableeval_507_natural/case_list.csv) |
| 507 labels | [labels.csv](data/benchmark/stableeval_507_natural/labels.csv) |
| 507 prompt packets | [prompt_packets.jsonl](data/benchmark/stableeval_507_natural/prompt_packets.jsonl) |
| 507 raw predictions | [raw_predictions/](results/stableeval_507_natural/raw_predictions/) |
| 507 calibrated predictions | [calibrated_predictions/](results/stableeval_507_natural/calibrated_predictions/) |
| 507 v6 leaderboard | [stableeval_507_natural_v6_leaderboard.csv](results/stableeval_507_natural/final_tables/stableeval_507_natural_v6_leaderboard.csv) |
| 507 audits and metric recomputation | [metrics/](results/stableeval_507_natural/metrics/) and [reports/](results/stableeval_507_natural/reports/) |

<a id="task-definition"></a>

## 🧩 Task definition

Each case contains a target stablecoin, an observation time `t`, a frozen 30-day lookback window, and a hidden 7-day prediction horizon. Agents receive only lookback-window evidence and must output strict JSON:

```json
{
  "case_id": "...",
  "platform": "...",
  "model_backend": "qwen/qwen-2.5-72b-instruct",
  "execution_mode": "...",
  "price_stability_next_7d": "stable | watch | stress",
  "p_depeg_next_7d": 0.0,
  "predicted_max_abs_deviation_bps": 0.0,
  "predicted_direction": "below_peg | above_peg | two_sided_or_no_meaningful",
  "confidence": 0.0,
  "rationale": "..."
}
```

Dollar-peg deviation is measured from hourly close price:

```text
deviation_bps = abs(close_price - 1.0) * 10000
```

Hidden next-7-day horizon values are used only for case construction and evaluation. They are not included in agent-facing prompt packets.

<a id="reproduce-from-saved-outputs"></a>

## 🚀 Quick start: reproduce from saved outputs

Clone the repository and install the core Python requirements in a virtual environment:

```bash
git clone https://github.com/SeanWan514/StableEval-Arena.git
cd StableEval-Arena

python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-core.txt
```

The following checks read saved predictions and write to a temporary folder. They do not call model APIs.

Recompute the main 120-case metrics from saved calibrated predictions into a temporary output folder:

```bash
mkdir -p /tmp/stableeval_release_audit

python scripts/evaluate/recompute_stableeval_120_enriched.py \
  --root . \
  --out /tmp/stableeval_release_audit/stableeval_120_enriched_recompute
```

Verify the 507 v6 leaderboard from saved predictions, labels, baselines, and cost logs:

```bash
python scripts/evaluate/recompute_stableeval_507_natural.py \
  --root . \
  --out /tmp/stableeval_release_audit/stableeval_507_natural_recompute
```

The canonical 507 scaling result is materialized at:

```text
results/stableeval_507_natural/final_tables/stableeval_507_natural_v6_leaderboard.csv
```

For full reproducibility details, including which commands call APIs and which are saved-output only, see [REPRODUCIBILITY.md](REPRODUCIBILITY.md).

<a id="api-backed-reruns"></a>

## ⚙️ Optional API-backed reruns

<details>
<summary><strong>API credentials and optional rerun guidance</strong></summary>

Real LLM-backed reruns require an OpenRouter key in the shell only:

```bash
export OPENROUTER_API_KEY="..."
```

Do not write API keys into repository files. API-backed reruns spend credits and are not required to inspect or recompute the saved result tables.

Some historical manifests and one-off finalizer scripts retain pre-cleanup path names for audit provenance. The canonical public paths are the two benchmark blocks listed above and in [FILE_MANIFEST.md](FILE_MANIFEST.md).

</details>

<a id="execution-caveats"></a>

## 🔎 Execution caveats

- Nanobot, LangGraph, Hermes AI, and EvoAgentX are treated as native/framework-level comparisons.
- OpenClaw and NanoClaw are adapter-based `-Claw` extensions in this release.
- OpenClaw/NanoClaw native CMDOP execution was not verified; do not describe those rows as native CMDOP results.
- All six systems use the same OpenRouter model backend.
- Weak stress recall is a reportable trustworthiness finding. Do not describe current agents as solving stablecoin stress prediction.

<a id="license-and-data-redistribution"></a>

## 📜 License and data redistribution

Repository code, scripts, prompts, and documentation are released under Apache License 2.0; see [LICENSE](LICENSE).

Benchmark artifacts under `data/benchmark/` and `results/` may include processed or derived market-data artifacts from upstream providers such as CryptoCompare/CCData and DeFiLlama, plus LLM-generated outputs. These artifacts are included for academic reproducibility, but redistribution and reuse may remain subject to original provider terms. Raw provider/vendor snapshots are not redistributed.

<a id="citation"></a>

## 📚 Citation

If you use StableEval Arena, please cite the associated workshop paper. Machine-readable repository metadata is available in [CITATION.cff](CITATION.cff).

```bibtex
@inproceedings{wan2026stableeval,
  title     = {StableEval Arena: A Cost-Aware Agentic Benchmark for Stablecoin Price Stability Prediction},
  author    = {Wan, Sean and Liu, Dongping and Zhang, Luyao},
  booktitle = {KDD Workshop on Evaluation and Trustworthiness of Agentic AI},
  year      = {2026},
  url       = {https://kdd-eval-workshop.github.io/agenticai-evaluation-kdd2026/assets/papers/11_StableEval_Arena_A_Cost_Awa.pdf}
}
```

<p align="center">
  <a href="#overview">↑ Back to overview</a>
</p>
