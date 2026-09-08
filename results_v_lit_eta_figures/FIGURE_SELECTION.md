# V3 Figure Provenance and Selection

## Critical provenance rule

These figures read only from `results_v3/`. The previous `create_v3_main_figures.py` incorrectly read `results_v2/`; that output is invalid for final V3 reporting.

## V3 input files

- `results_v3/base_case_runs.csv`
- `results_v3/c1_c5_results.csv`
- `results_v3/stress_grid.csv`
- `results_v3/priority_feature_statistics.csv`
- `results_v3/priority_features_raw.csv`
- `results_v3/decision_diagnostics.csv`

## Why these four figures

1. Figure 1 establishes Base vs Challenge behavior under the corrected V3 model.
2. Figure 2 honestly shows the V3 trade-off, including that C3 can beat C4 in Primary Challenge.
3. Figure 3 verifies the actual C4 fix: AGV-specific feature variance under contention.
4. Figure 4 replaces the invalid V2 heatmap with a V3 stress-grid C4-vs-C3 map, including negative regions.

No V2 stress-grid or V2 priority-feature data are used.
