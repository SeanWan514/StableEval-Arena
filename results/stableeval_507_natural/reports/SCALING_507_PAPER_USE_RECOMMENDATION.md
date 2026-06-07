# 507 Scaling Paper-Use Recommendation

Created: 2026-06-04T05:07:58.817914+00:00

## Safe To Cite

Use `results/stableeval_507_natural/tables/scaling_507_progress_leaderboard_v2_verified.csv` as the clean additive 507 progress leaderboard. It includes each system exactly once: four baselines, Nanobot raw/calibrated, and LangGraph raw/calibrated.

Use the 507 result as a **natural-distribution scaling check**, not as a replacement for the frozen 120-case stress-enriched six-agent validation.

## Main Paper vs Appendix

Recommended main-paper use: one compact robustness paragraph and, if space allows, a small table showing operational completion, valid JSON, Macro-F1, balanced accuracy, stress recall, missed-depeg rate, and cost per case for Nanobot and LangGraph.

Recommended appendix use: full 507 leaderboard, full cost/token/latency table, and 120-vs-507 alignment details.

## Interpretation

The 507 results strengthen operational robustness and evaluation discipline. They do not show that agentic AI solves stablecoin risk prediction. Both Nanobot and LangGraph remain weak on rare severe-risk detection; this should be framed as a trustworthiness finding.

## Avoid

- Do not say the six-agent benchmark has been scaled to 507 yet.
- Do not cite partial 32-case Nanobot results as final.
- Do not use older combined leaderboards with duplicate Nanobot rows for paper tables.
- Do not present always-stable high accuracy as meaningful risk-monitoring success.
