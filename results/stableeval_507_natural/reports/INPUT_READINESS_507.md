# 507 Input Readiness Check

Case file: `results/stableeval_507_natural/case_ids/natural_distribution_507_case_list.csv`
Prompt packet file: `results/stableeval_507_natural/prompt_packets/natural_distribution_507_prompt_packets.jsonl`
Cases: 507
Prompt packets: 507
Unique case IDs: 507
Unique packet case IDs: 507
Case IDs match packets: True

## Label Distribution

| label | cases |
|---|---:|
| stable | 441 |
| watch | 45 |
| stress | 21 |

## Checks

- Schema match: pass (0 mismatches).
- Leakage check: pass (0 findings).
- Future horizon boundaries are present as metadata; future prices/labels/outcomes were not found in prompt packet keys.
