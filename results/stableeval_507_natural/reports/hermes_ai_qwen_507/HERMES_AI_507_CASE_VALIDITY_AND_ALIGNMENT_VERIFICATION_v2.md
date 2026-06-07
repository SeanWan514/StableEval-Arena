# Hermes AI 507 Case Validity and Alignment Verification v2

## Executive Summary

PASS: all 507 Hermes AI cases are individually valid, complete, parsed, and included in metric computation. No API calls were made during this verification step. No files were deleted, moved, renamed, or overwritten.

This v2 report supersedes only the earlier verification report text where one stale sentence said metric reproduction was false. The metric discrepancy table shows that all reported Hermes raw and calibrated metrics reproduce within floating-point tolerance.

## Case-by-Case Validity

- Total cases checked: 507
- Valid cases: 507
- Invalid cases: 0
- Missing cases: 0
- Duplicate cases: 0
- Corrupt JSONL lines: 0
- Schema issues: 0
- Backend issues: 0
- Fallback model detections: 0
- Metric inclusion issues: 0

Canonical detailed audit: `results/stableeval_507_natural/metrics/hermes_ai_qwen_507/hermes_ai_507_case_by_case_validity_audit_v2.csv`

The earlier file `hermes_ai_507_case_by_case_validity_audit.csv` is superseded because it used inverted boolean logic for the `duplicate_detected` and `corrupt_line_detected` flags.

## Merge Integrity

- Dry-run records: 5
- Continuation records: 502
- Dry-run/continuation overlap: 0
- Dry-run records reused in final canonical output: 5
- Final raw records: 507
- Final calibrated records: 507
- Final raw unique case IDs: 507
- Final calibrated unique case IDs: 507
- Final raw matches official 507 case list: true
- Calibrated matches raw case-for-case: true
- Evaluation rows match final outputs: true
- Raw corrupt JSONL lines: 0
- Calibrated corrupt JSONL lines: 0

Supporting files:

- `results/stableeval_507_natural/metrics/hermes_ai_qwen_507/hermes_ai_507_merge_integrity_summary.csv`
- `results/stableeval_507_natural/metadata/hermes_ai_qwen_507/hermes_ai_507_merge_integrity_audit.md`

## Metric Reproducibility

PASS: reported Hermes raw and calibrated metrics reproduce from saved prediction files and official labels within tolerance.

- Discrepancy rows checked: 40
- Rows with concern: 0
- Maximum absolute delta: 1.4210854715202004e-14

Supporting file: `results/stableeval_507_natural/metrics/hermes_ai_qwen_507/hermes_ai_507_metric_recomputation_discrepancies.csv`

## Hermes 507 Metrics

| Variant | Accuracy | Macro-F1 | Balanced Acc. | Stable R | Watch R | Stress R | Missed-Depeg | Brier | MaxDev MAE |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Raw | 0.3353 | 0.2139 | 0.3879 | 0.2971 | 0.8667 | 0.0000 | 1.0000 | 0.0193 | 34.3748 |
| Calibrated | 0.4083 | 0.3011 | 0.4328 | 0.3810 | 0.8222 | 0.0952 | 1.0000 | 0.0193 | 34.3748 |

## 120-vs-507 Alignment Recheck

| Setting | Cases | Accuracy | Macro-F1 | Balanced Acc. | Stable R | Watch R | Stress R | Missed-Depeg | Brier | MaxDev MAE |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Original 120 calibrated | 120 | 0.4250 | 0.3213 | 0.3690 | 0.2593 | 0.8000 | 0.0476 | 1.0000 | 0.0475 | 57.8583 |
| 507 restricted to same 120 calibrated | 120 | 0.4583 | 0.3697 | 0.4046 | 0.2963 | 0.8222 | 0.0952 | 1.0000 | 0.0458 | 65.2917 |
| Full 507 calibrated | 507 | 0.4083 | 0.3011 | 0.4328 | 0.3810 | 0.8222 | 0.0952 | 1.0000 | 0.0193 | 34.3748 |

Verdict: PASS. The 507-restricted Hermes result is slightly better than the frozen original 120 Hermes result on calibrated accuracy, Macro-F1, balanced accuracy, and stress recall. Missed-depeg remains unchanged at 1.0000.

Supporting files:

- `results/stableeval_507_natural/metrics/hermes_ai_qwen_507/hermes_ai_120_vs_507_alignment_recheck.csv`
- `results/stableeval_507_natural/metrics/hermes_ai_qwen_507/hermes_ai_120_vs_507_alignment_recheck_deltas.csv`

## Cross-Agent Sanity Check

| Pair | Label Agreement | p Corr. | Mean p Diff | MaxDev Corr. | Mean MaxDev Diff | Direction Agreement |
|---|---:|---:|---:|---:|---:|---:|
| Hermes AI vs Nanobot | 0.7732 | 0.6827 | 0.0291 | 0.7536 | 10.3225 | 0.9546 |
| Hermes AI vs LangGraph | 0.7771 | 0.8406 | 0.0222 | 0.9759 | 8.7949 | 0.8817 |
| Nanobot vs LangGraph | 0.7909 | 0.6845 | 0.0243 | 0.7491 | 11.9063 | 0.8955 |

Stress-case audit: 19/21 actual stress cases were missed by all three completed agents; 2/21 had at least one agent correctly predict stress.

Supporting files:

- `results/stableeval_507_natural/metrics/hermes_ai_qwen_507/hermes_vs_nanobot_langgraph_pairwise_agreement.csv`
- `results/stableeval_507_natural/metrics/hermes_ai_qwen_507/hermes_ai_507_stress_case_cross_agent_audit.csv`
- `results/stableeval_507_natural/metrics/hermes_ai_qwen_507/hermes_ai_507_top_cross_agent_disagreements.csv`

## Paper Interpretation

Hermes strengthens the 507 scaling story operationally: a third native/framework-level agent completed the full 507-case natural-distribution run with valid structured outputs and reproducible metrics. It also aligns positively with the frozen 120-case Hermes result on the same 120 case IDs.

This should still be framed with caution. Hermes does not solve rare-stress detection: calibrated stress recall is 0.0952, and missed-depeg remains 1.0000. The result supports the paper's trustworthiness-gap framing rather than a claim that agentic systems dominate classical baselines.

## Recommendation

It is safe to proceed to EvoAgentX using the same resume-safe protocol and the same case-by-case validity audit afterward.
