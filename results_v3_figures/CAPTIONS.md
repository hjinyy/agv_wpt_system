# V3 Main Figure Captions

## Figure 1. V3 Base vs Primary Challenge performance
This figure uses only `results_v3/base_case_runs.csv` and `results_v3/c1_c5_results.csv`. Panel (a) shows that the corrected C4 does not create artificial differences in the homogeneous Base Case. Panel (b) shows the V3 Primary Challenge after the per-AGV next-task fix and includes C5 as a rolling MILP benchmark.

## Figure 2. V3 Primary Challenge trade-off map
This scatter plot uses `results_v3/c1_c5_results.csv`. The x-axis is mean task delay and the y-axis is urgent-task on-time completion; marker size encodes completion rate. In V3, C3 outperforms C4 on the Primary Challenge urgent/on-time trade-off, while C5 provides a lower-delay optimization benchmark.

## Figure 3. V3 corrected C4 diagnostics
This figure uses `results_v3/c1_c5_results.csv` and `results_v3/priority_feature_statistics.csv`. Panel (a) reports contention frequency and how often C4 selects a different AGV than C3. Panel (b) verifies that corrected C4 candidate features have real nonzero variance, especially `E_next`, rather than all candidates sharing one `next_task`.

## Figure 4. V3 C4-vs-C3 stress grid
This figure uses `results_v3/stress_grid.csv`, generated with the corrected V3 C4. Cell color is the C4 delay improvement relative to C3; positive values mean C4 has lower delay, negative values mean C4 is worse. Parenthesized cell annotations give C4 minus C3 urgent on-time difference in percentage points. This replaces the invalid V2-based advantage heatmap.
