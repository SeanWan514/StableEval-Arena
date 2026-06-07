# Benchmark Data Card

The detailed StableEval Arena data card is maintained at:

`data/benchmark/data_cards/benchmark_data_card.md`

It documents source APIs, asset coverage, time window, frozen-window construction, label definitions, feature fields, leakage controls, limitations, and redistribution caveats.

## Release Scope

The GitHub release contains two benchmark blocks:

| Block | Contents |
|---|---|
| `StableEval-120-Enriched` | 120 stress-enriched validation cases, prompt packets, six-system predictions, metrics, ablations, and freeze manifest |
| `StableEval-507-Natural` | 507 natural-distribution cases, labels, prompt packets, baselines, four native/framework-level agents, two adapter-based `-Claw` extensions, audits, and v6 leaderboard |

## License And Redistribution Notice

Repository code, scripts, prompts, and documentation are licensed under Apache-2.0 unless otherwise stated. Benchmark data and result artifacts may include processed or derived market-data artifacts and LLM-generated outputs; these artifacts are included for academic reproducibility and may remain subject to the original providers' terms. Raw provider/vendor snapshots are not redistributed.

For the Hugging Face package, use:

```bash
python scripts/release/prepare_huggingface_dataset.py --root .
```
