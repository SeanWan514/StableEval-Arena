# Calibration Rule

This rule is frozen before intermediate validation evaluation and is inherited from the improved pilot.

- Stress if `predicted_max_abs_deviation_bps >= 100`.
- Stress if `p_depeg_next_7d >= 0.35` and `predicted_max_abs_deviation_bps >= 75`.
- Watch if `p_depeg_next_7d >= 0.15` or `predicted_max_abs_deviation_bps >= 40`.
- Stable otherwise.

The rule uses only model outputs generated from lookback-window evidence. It does not use validation labels, future prices, or hidden horizon outcomes.