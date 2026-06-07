# Intermediate Validation Case Selection Report

Target size: 120 cases.
Actual size: 120 cases.

## Label Mix

| enhanced_stability_label | cases |
| --- | --- |
| stable | 54 |
| watch | 45 |
| stress | 21 |

## Selection Buckets

| selection_bucket | cases |
| --- | --- |
| all_watch_cases | 45 |
| natural_stable_controls | 27 |
| near_stress_stable_controls | 27 |
| all_stress_cases | 21 |

## Stress Inclusion

All enhanced stress cases included: 21/21.
All strict sustained-depeg cases included: 3/3.

## Near-Stress Definition

Near-stress controls are stable-labeled cases with at least one of: `enhanced_near_stress = true`, hidden-horizon max absolute deviation at or above 35 bps, or at least one hidden-horizon hour above 25 bps. These labels are used only for validation-set sampling; agents do not receive hidden-horizon values.

## Relation To 30-Case Pilot

Cases overlapping the prior 30-case pilot: 21.
Cases outside the prior 30-case pilot: 99.
The set is more reliable than the 30-case pilot because it contains every stress case in the dataset, all watch cases, near-stress stable controls, and a larger chronological cross-coin stable-control slice. It therefore tests both rare-event detection and more realistic deployment behavior without moving to the full 507-case benchmark.

## Leakage Control

Hidden labels and horizon statistics are used only for selecting and evaluating the validation set. The saved prompt packets contain only 30-day lookback evidence and do not include future prices, future labels, or horizon outcomes.