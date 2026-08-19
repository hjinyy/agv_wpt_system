# Official V3 Report — C5 reserve/task-risk 15-min RH-MILP benchmark

## Summary

This official V3 run keeps C1--C4 unchanged and updates only C5. The previous 15-min RH-MILP implementation was structurally correct but behaved too conservatively because the objective collapsed to WPT-loss minimization when safety and task slack were zero. The updated C5 keeps the 15-min rolling-horizon MILP framework but adds explicit operational reserve risk, forecast task-impact slack, forecast-conflict penalty, and a corrected-C4 priority prior for charging actions.

C5 remains a **15-minute rolling-horizon charging benchmark**, not a 24-hour full-horizon global optimum.

## Provenance and archived baseline

- Previous C5-before-objective-fix main was archived at `archive/v3-c5-15min-rh-before-objective-fix`.
- C1--C4 were regression-checked against that archive: max absolute metric difference = `0.0`.
- All figures are generated from `results_v3/` only.
- `results_v2/` is not used for V3 figures.

## C5 formulation

### Horizon and execution

- Horizon: `H = 900 s = 15 min`
- Slot size: `Δt = 60 s`
- Slots: `K = 15`
- MILP optimizes all 15 future charging slots.
- Only the first 60-second slot is executed, then the DES state is updated and the MILP is re-solved.

### Decision variables

- `x[i,p,k] ∈ {0,1}`: AGV `i` charges on pad `p` in slot `k`.
- `SOC[i,k]`: forecast state of charge.
- `s_soc[i,k] ≥ 0`: emergency slack below `min_soc`.
- `r_soc[i,k] ≥ 0`: operational reserve slack below `reserve_soc = 30%`.
- `task_slack[j] ≥ 0`: reserve-aware forecast task-energy/deadline-risk slack.

### Constraints

- Pad capacity: `Σ_i x[i,p,k] ≤ 1`.
- One pad per AGV: `Σ_p x[i,p,k] ≤ 1`.
- Actual currently busy AGVs cannot charge.
- Forecast task-overlap slots are **not hard-forbidden**; they are penalized as task-impact risk.
- SOC dynamics include WPT charging energy and predicted task energy.
- Emergency safety: `SOC[i,k] + s_soc[i,k] ≥ min_soc`.
- Operational reserve: `SOC[i,k] + r_soc[i,k] ≥ reserve_soc`.
- Task-energy reserve: `SOC[i,k_task] + task_slack[j] ≥ reserve_soc + E_task[j]`.

### Objective

The implemented objective is:

```text
minimize
  200 * Σ s_soc[i,k]
+   6 * Σ r_soc[i,k]
+ Σ_j w_j * task_slack[j]
+ Σ_i,p,k 0.02 * WPT_loss[i,k] * x[i,p,k]
+ Σ_i,p,k 6.0 * forecast_conflict[i,k] * x[i,p,k]
- Σ_i,p,k 0.8 * reserve_deficit[i] * early_weight[k] * x[i,p,k]
- Σ_i,p,k 60.0 * C4_priority_score[i] * early_weight[k] * x[i,p,k]
```

where urgent tasks receive higher task slack weight. The last term is a charging-action prior based on the corrected C4 per-AGV WMS preview score. It does **not** optimize task assignment or sequencing; C1--C5 all use the same FCFS + first-available AGV assignment and deterministic AGV ID tie-break.

## Primary Challenge — 50-rep mean

| strategy   |   mean_delay |   urgent_on_time_rate |   completion_rate |   wpt_loss |   fleet_min_soc |   charging_wait |
|:-----------|-------------:|----------------------:|------------------:|-----------:|----------------:|----------------:|
| C1         |       7.0952 |               52.6159 |           99.4022 |     8.2847 |         29.6639 |         40.9696 |
| C2         |       4.0121 |               72.5912 |           99.0366 |     8.6561 |         19.7292 |         25.5058 |
| C3         |       6.0735 |               85.2879 |           97.4182 |     6.9989 |         24.9219 |         54.8596 |
| C4         |       6.4882 |               81.9243 |           97.3516 |     7.3947 |         22.3317 |         48.6591 |
| C5         |       6.4772 |               82.3355 |           97.1262 |     7.5472 |         21.6564 |         50.7269 |

## Base Case — 50-rep mean

| strategy   |   mean_delay |   urgent_on_time_rate |   completion_rate |   wpt_loss |   fleet_min_soc |   charging_wait |
|:-----------|-------------:|----------------------:|------------------:|-----------:|----------------:|----------------:|
| C1         |       1.3063 |                   100 |           99.7518 |     6.6596 |         29.6787 |          3.2068 |
| C2         |       0.2049 |                   100 |           99.7749 |     9.6359 |         53.4107 |          0      |
| C3         |       0.205  |                   100 |           99.7749 |     9.6431 |         55.0489 |          0      |
| C4         |       0.2049 |                   100 |           99.7749 |     9.321  |         54.9547 |          0      |
| C5         |       0.2021 |                   100 |           99.776  |     9.0191 |         54.629  |          0      |

## C4 vs C5 — Primary Challenge

Positive `C4_minus_C5` means C4 is numerically larger than C5.

| metric              |      C4 |      C5 |   C4_minus_C5 |
|:--------------------|--------:|--------:|--------------:|
| mean_delay          |  6.4882 |  6.4772 |        0.0111 |
| urgent_on_time_rate | 81.9243 | 82.3355 |       -0.4112 |
| completion_rate     | 97.3516 | 97.1262 |        0.2254 |
| wpt_loss            |  7.3947 |  7.5472 |       -0.1525 |
| fleet_min_soc       | 22.3317 | 21.6564 |        0.6753 |
| charging_wait       | 48.6591 | 50.7269 |       -2.0678 |

Interpretation:

- C5 delay is slightly lower than C4 by `0.0111` min.
- C5 urgent on-time is higher than C4 by `0.4112` percentage points.
- C5 completion is lower than C4 by `0.2254` percentage points.
- C5 WPT loss is higher than C4 by `0.1525` kWh.
- C5 fleet minimum SOC is lower than C4 by `0.6753` percentage points.

## Solver statistics

| metric                            |      value |
|:----------------------------------|-----------:|
| total_solver_calls                | 66366      |
| calls_per_rep                     |  1327.32   |
| total_solver_time_s               |   153.853  |
| total_solver_time_per_rep_s       |     3.0771 |
| mean_solve_time_s                 |     0.0023 |
| median_solve_time_s               |     0.0016 |
| p95_solve_time_s                  |     0.0065 |
| max_solve_time_s                  |     0.0236 |
| mean_binary_variables             |    27.4284 |
| mean_constraints                  |   138.875  |
| fallback_calls                    |     0      |
| infeasible_calls                  |     0      |
| time_limit_calls                  |     0      |
| safety_slack_total                |     0      |
| reserve_slack_total               |  3114.92   |
| task_slack_total                  |  1019.56   |
| mean_available_agv_slot_pairs     |    27.4284 |
| mean_forecast_busy_agv_slot_pairs |    23.3097 |
| mean_actual_busy_agv_slot_pairs   |     0      |

The solver did not fail: fallback, infeasible, and time-limit counts are all zero. The mean available AGV-slot count is now near the full candidate slot count because forecast task overlap is recorded as a soft conflict penalty rather than a hard prohibition.

## Horizon sensitivity — C5 only

|   horizon_s |   mean_delay |   urgent_on_time_rate |   completion_rate |   wpt_loss |   fleet_min_soc |   charging_wait |   solver_calls |   solver_computation_time_s |
|------------:|-------------:|----------------------:|------------------:|-----------:|----------------:|----------------:|---------------:|----------------------------:|
|         300 |       8.5139 |               84.7345 |           96.052  |     7.9958 |         20.5759 |         64.8246 |         1362.2 |                      1.5548 |
|         900 |       7.1018 |               84.2683 |           96.479  |     6.8514 |         20.7831 |         49.9996 |         1350.8 |                      3.4491 |
|        1800 |       9.2822 |               83.6398 |           95.7289 |     6.8707 |         20.8775 |         54.4626 |         1341   |                      5.9806 |

The 15-min horizon performs best on mean delay in this 5-rep sensitivity. 5-min and 30-min horizons remain viable but are not better on the primary delay KPI here. This is still a rolling-horizon benchmark rather than a full-horizon optimum.

## Figures

Generated from `results_v3/` only:

- `results_v3_figures/Figure1_V3_Base_vs_Challenge.png/pdf`
- `results_v3_figures/Figure2_V3_Challenge_Tradeoff.png/pdf`
- `results_v3_figures/Figure3_V3_C4_Diagnostics.png/pdf`
- `results_v3_figures/Figure4_V3_C4_vs_C3_Stress_Grid.png/pdf`

## Conclusion

The C5 benchmark is now substantially more credible than the previous WPT-loss-dominated version. It uses a real 15-min receding-horizon MILP, includes SOC trajectory, reserve-risk, forecast task-impact, pad capacity, and solver diagnostics, and now produces Primary Challenge performance comparable to corrected C4. It should still be described carefully as a **rolling-horizon MILP charging benchmark**, not a global optimum or theoretical upper bound.
