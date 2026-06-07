# Full 507 Frozen Packet Build Report

Cases: 507.
Prompt packets: `data/benchmark/stableeval_507_natural/prompt_packets.jsonl`.

## Label Distribution

| label | cases |
| --- | --- |
| stable | 441 |
| watch | 45 |
| stress | 21 |

## Protocol

- 30-day frozen lookback only.
- Hidden next-7-day labels are not included in packets.
- Model backend for planned run: `qwen/qwen-2.5-72b-instruct`.
- Temperature: 0.
- Calibration is applied after raw prediction generation as a separate frozen step.