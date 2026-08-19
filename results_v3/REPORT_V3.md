# Official V3 Report — C5 independent KPI-risk 15-min RH-MILP benchmark

## Summary

This official V3 run keeps C1--C4 unchanged and replaces the previous C5 objective. The archived C5 objective used a corrected-C4 priority prior, which stabilized C5 but created a reviewer-facing weakness: C5 was no longer a fully independent optimization benchmark. We therefore ran a C5-no-prior ablation and replaced the prior with an independent physical/KPI-risk objective.

C5 remains a **15-minute rolling-horizon MILP charging benchmark**, not a 24-hour full-horizon global optimum.

## Provenance

- C4-prior C5 version archived at `archive/v3-c5-with-c4-prior-before-no-prior-ablation`.
- C5-no-prior ablation outputs are stored in `results_v3_ablation_no_prior/` and summarized in `results_v3/c5_objective_ablation_summary.csv`.
- C1--C4 were not modified.
- All V3 figures read from `results_v3/` plus the explicit C5 ablation summary where noted.

## C5 objective ablation

| variant           |   replications |   mean_delay |   urgent_on_time_rate |   completion_rate |   wpt_loss |   fleet_min_soc |
|:------------------|---------------:|-------------:|----------------------:|------------------:|-----------:|----------------:|
| C1                |             50 |       7.0952 |               52.6159 |           99.4022 |     8.2847 |         29.6639 |
| C2                |             50 |       4.0121 |               72.5912 |           99.0366 |     8.6561 |         19.7292 |
| C3                |             50 |       6.0735 |               85.2879 |           97.4182 |     6.9989 |         24.9219 |
| C4                |             50 |       6.4882 |               81.9243 |           97.3516 |     7.3947 |         22.3317 |
| C5 with C4 prior  |             50 |       6.4772 |               82.3355 |           97.1262 |     7.5472 |         21.6564 |
| (archived)        |                |              |                       |                   |            |                 |
| C5 no prior       |             20 |      57.0138 |               40.3095 |           95.6408 |     8.3137 |         19.68   |
| 20-rep ablation   |                |              |                       |                   |            |                 |
| C5 independent    |             50 |       6.7813 |               82.9783 |           97.1471 |     7.7506 |         21.654  |
| KPI-risk official |                |              |                       |                   |            |                 |

Interpretation:

1. Simply removing the C4 prior caused C5 to collapse: delay `57.0138` min and urgent on-time `40.3095%` in the 20-rep ablation.
2. This proves the prior-dependent C5 should not be presented as an independent optimization benchmark.
3. The final C5 replaces the C4 priority prior with an independent KPI-risk charging term and recovers stable performance: delay `6.7813` min and urgent on-time `82.9783%` in the official 50-rep Primary Challenge.

## Final C5 formulation

### Horizon and execution

- Horizon: `H = 900 s = 15 min`
- Slot size: `Δt = 60 s`
- Slots: `K = 15`
- MILP optimizes 15 future charging slots.
- Only the first 60-second slot is executed; the model then re-solves after DES state update.

### Decision variables

- `x[i,p,k] ∈ {0,1}`: AGV `i` charges on pad `p` in slot `k`.
- `SOC[i,k]`: forecast SOC.
- `s_soc[i,k] ≥ 0`: emergency slack below `min_soc`.
- `r_soc[i,k] ≥ 0`: reserve slack below `reserve_soc = 30%`.
- `task_slack[j] ≥ 0`: reserve-aware forecast task-energy/deadline-risk slack.

### Constraints

- Pad capacity: `Σ_i x[i,p,k] ≤ 1`.
- One pad per AGV: `Σ_p x[i,p,k] ≤ 1`.
- Actual currently busy AGVs cannot charge.
- Forecast task-overlap slots are soft-penalized, not hard-forbidden.
- SOC dynamics include WPT charging energy and predicted task energy.
- Safety: `SOC[i,k] + s_soc[i,k] ≥ min_soc`.
- Reserve: `SOC[i,k] + r_soc[i,k] ≥ reserve_soc`.
- Task-energy reserve: `SOC[i,k_task] + task_slack[j] ≥ reserve_soc + E_task[j]`.

### Objective

The final C5 objective is independent of the C4 score:

```text
minimize
  200 * Σ s_soc[i,k]
+   6 * Σ r_soc[i,k]
+ Σ_j w_j * task_slack[j]
+ Σ_i,p,k 0.02 * WPT_loss[i,k] x[i,p,k]
+ Σ_i,p,k 6.0 * forecast_conflict[i,k] x[i,p,k]
- Σ_i,p,k 0.8 * reserve_deficit[i] early_weight[k] x[i,p,k]
- Σ_i,p,k 30.0 * KPI_risk[i] early_weight[k] x[i,p,k]
```

where `KPI_risk[i]` is computed from physical/logistics quantities only:

```text
KPI_risk =
  4.00 * reserve_deficit_normalized
+ 0.75 * next_task_energy_normalized
+ 1.25 * urgent_task_indicator
+ 1.50 * deadline_pressure
+ 2.00 * critical_SOC_pressure
```

No `C4_priority_score` term is used in the final C5 objective.

## Primary Challenge — 50-rep mean

| strategy   |   mean_delay |   urgent_on_time_rate |   completion_rate |   wpt_loss |   fleet_min_soc |   charging_wait |
|:-----------|-------------:|----------------------:|------------------:|-----------:|----------------:|----------------:|
| C1         |       7.0952 |               52.6159 |           99.4022 |     8.2847 |         29.6639 |         40.9696 |
| C2         |       4.0121 |               72.5912 |           99.0366 |     8.6561 |         19.7292 |         25.5058 |
| C3         |       6.0735 |               85.2879 |           97.4182 |     6.9989 |         24.9219 |         54.8596 |
| C4         |       6.4882 |               81.9243 |           97.3516 |     7.3947 |         22.3317 |         48.6591 |
| C5         |       6.7813 |               82.9783 |           97.1471 |     7.7506 |         21.654  |         53.0314 |

## Base Case — 50-rep mean

| strategy   |   mean_delay |   urgent_on_time_rate |   completion_rate |   wpt_loss |   fleet_min_soc |   charging_wait |
|:-----------|-------------:|----------------------:|------------------:|-----------:|----------------:|----------------:|
| C1         |       1.3063 |                   100 |           99.7518 |     6.6596 |         29.6787 |          3.2068 |
| C2         |       0.2049 |                   100 |           99.7749 |     9.6359 |         53.4107 |          0      |
| C3         |       0.205  |                   100 |           99.7749 |     9.6431 |         55.0489 |          0      |
| C4         |       0.2049 |                   100 |           99.7749 |     9.321  |         54.9547 |          0      |
| C5         |       0.2049 |                   100 |           99.7749 |     9.4489 |         54.2219 |          0      |

## C4 vs C5 — Primary Challenge

| metric              |      C4 |      C5 |   C4_minus_C5 |
|:--------------------|--------:|--------:|--------------:|
| mean_delay          |  6.4882 |  6.7813 |       -0.293  |
| urgent_on_time_rate | 81.9243 | 82.9783 |       -1.054  |
| completion_rate     | 97.3516 | 97.1471 |        0.2045 |
| wpt_loss            |  7.3947 |  7.7506 |       -0.3558 |
| fleet_min_soc       | 22.3317 | 21.654  |        0.6777 |
| charging_wait       | 48.6591 | 53.0314 |       -4.3723 |

Interpretation:

- C5 delay is `0.2930` min higher than C4.
- C5 urgent on-time is `1.0540` percentage points higher than C4.
- C5 completion is `-0.2045` percentage points relative to C4.
- C5 is now an independent optimization benchmark, but not a strict upper bound.

## Solver statistics

| metric                            |      value |
|:----------------------------------|-----------:|
| total_solver_calls                | 67268      |
| calls_per_rep                     |  1345.36   |
| total_solver_time_s               |   188.986  |
| total_solver_time_per_rep_s       |     3.7797 |
| mean_solve_time_s                 |     0.0028 |
| median_solve_time_s               |     0.0017 |
| p95_solve_time_s                  |     0.0069 |
| max_solve_time_s                  |     0.0208 |
| mean_binary_variables             |    27.4144 |
| mean_constraints                  |   138.814  |
| fallback_calls                    |     0      |
| infeasible_calls                  |     0      |
| time_limit_calls                  |     0      |
| safety_slack_total                |     0      |
| reserve_slack_total               |  5388.46   |
| task_slack_total                  |  1811.02   |
| mean_available_agv_slot_pairs     |    27.4144 |
| mean_forecast_busy_agv_slot_pairs |    23.2992 |
| mean_actual_busy_agv_slot_pairs   |     0      |

Fallback, infeasible, and time-limit counts are all zero.

## Horizon sensitivity — C5 only

|   horizon_s |   mean_delay |   urgent_on_time_rate |   completion_rate |   wpt_loss |   fleet_min_soc |   charging_wait |   solver_calls |   solver_computation_time_s |
|------------:|-------------:|----------------------:|------------------:|-----------:|----------------:|----------------:|---------------:|----------------------------:|
|         300 |       8.849  |               84.3194 |           96.0213 |     7.4164 |         21.0685 |         63.6794 |         1349.6 |                      1.6055 |
|         900 |       9.7502 |               83.2562 |           96.1115 |     7.5442 |         21.3152 |         58.5971 |         1332.4 |                      3.7405 |
|        1800 |       8.1363 |               84.4638 |           96.0749 |     7.6749 |         20.9297 |         61.324  |         1349.6 |                      7.0398 |

## Figures

Generated/updated:

- `results_v3_figures/Figure1_V3_Base_vs_Challenge.png/pdf`
- `results_v3_figures/Figure2_V3_Challenge_Tradeoff.png/pdf`
- `results_v3_figures/Figure3_V3_C4_Diagnostics.png/pdf`
- `results_v3_figures/Figure4_V3_C4_vs_C3_Stress_Grid.png/pdf`
- `results_v3_figures/Figure5_C5_Objective_Ablation.png/pdf`

## Conclusion

The final C5 should be described as an independent, reserve-aware and KPI-risk-aware 15-min rolling-horizon MILP charging benchmark. It is not a global optimum and not a theoretical upper bound. The ablation shows that simply removing the C4 prior collapses performance, while the independent KPI-risk replacement preserves benchmark-level performance without embedding C4's priority score.
