# Official V3 Report — C5 15-min Rolling-Horizon MILP Benchmark

## Preservation and source-of-truth

Before modifying C5, the previous official V3 main state was preserved as:

- `archive/v3-c1revised-before-c5-15min-rh`
- commit `5a2371fd3130663cbbb54893072a4017536955ff`

This report and all official figures use only `results_v3/`. No `results_v2/` data are used for figure generation.

## C5 formulation summary

**C5 is a 15-min rolling-horizon MILP charging benchmark, not a 24-h full-horizon global optimum.**

At each opportunity-charging decision epoch `t`, C5 solves a receding-horizon charging allocation problem over:

- horizon `H = 900 s = 15 min`,
- slot length `Δt = 60 s`,
- number of slots `K = 15`.

The MILP optimizes all 15 future charging slots, but the DES executes only the first slot decision. The remaining plan is discarded and the MILP is solved again at the next decision epoch.

Actual task assignment remains identical for C1-C5:

```text
FCFS task queue + first-available AGV + deterministic AGV-ID tie-break
```

C5 does **not** optimize task assignment. A shadow WMS forecast estimates 15-min future workload using the same deterministic FCFS + first-available rule without mutating the DES state.

## Decision variables

For candidate AGV `i`, pad `p`, and future slot `k`:

```text
x[i,p,k] ∈ {0,1}
```

`x[i,p,k]=1` means AGV `i` is assigned to pad `p` during horizon slot `k`.

Continuous variables:

```text
SOC[i,k]
s_soc[i,k] ≥ 0
task_slack[j] ≥ 0
```

where `s_soc` is an emergency SOC-safety slack and `task_slack` is a linear proxy for forecast task energy-availability pressure.

## Constraints

1. **Pad capacity**

```text
Σ_i x[i,p,k] ≤ 1
```

2. **AGV simultaneous charging capacity**

```text
Σ_p x[i,p,k] ≤ 1
```

3. **AGV availability**

Slots overlapping current DES busy intervals or shadow forecast task execution intervals are forbidden for charging.

4. **SOC dynamics**

```text
SOC[i,k+1] = SOC[i,k] + P_WPT η[i,k] Δt / battery_kWh - predicted_task_energy[i,k]
```

Predicted charging uses `predicted_eta_mode`; actual executed charging uses `realized_eta_mode`.

5. **SOC upper bound**

```text
SOC[i,k] ≤ max_soc
```

6. **SOC safety with emergency slack**

```text
SOC[i,k] + s_soc[i,k] ≥ min_soc
```

Slack is penalized strongly and recorded. In the official run, total safety slack was `0.0`.

## Objective function

An exact DES-coupled lexicographic task scheduling MILP would require jointly modeling future task start/completion times as functions of charging decisions and actual AGV dispatch. To keep 24 h × 50 replications computationally tractable, this implementation uses a documented normalized weighted proxy objective:

```text
minimize
  100 * Σ_i,k s_soc[i,k]
+ Σ_j w_j * task_slack[j]
+ 0.02 * Σ_i,p,k P_WPT(1-η[i,k])Δt x[i,p,k]
```

where:

```text
w_j = 1.0 + 4.0 * I(task j is urgent)
      + min(2, predicted_tardiness_j / H)
      + 0.25 * min(2, predicted_delay_j / H)
```

This is **not** a global optimum formulation and must not be described as a theoretical upper bound. It is a rolling-horizon optimization benchmark with a linear forecast approximation.

## Solver configuration

- Solver: `scipy.optimize.milp` / HiGHS
- Mode: `15min_rolling_horizon_milp`
- Time limit per call: 5 s
- MIP relative gap target: 0.001
- Fallback: C3 low-SOC fallback only if no incumbent solution exists

## Base Case results, 50 replications

| strategy   |   mean_delay |   urgent_on_time_rate |   completion_rate |   wpt_loss |   fleet_min_soc |   charging_wait |
|:-----------|-------------:|----------------------:|------------------:|-----------:|----------------:|----------------:|
| C1         |       1.3063 |                   100 |           99.7518 |     6.6596 |         29.6787 |          3.2068 |
| C2         |       0.2049 |                   100 |           99.7749 |     9.6359 |         53.4107 |          0      |
| C3         |       0.205  |                   100 |           99.7749 |     9.6431 |         55.0489 |          0      |
| C4         |       0.2049 |                   100 |           99.7749 |     9.321  |         54.9547 |          0      |
| C5         |       3.8763 |                   100 |           99.754  |     5.7841 |         19.6943 |         14.1436 |

## Primary Challenge results, 50 replications

| strategy   |   mean_delay |   urgent_on_time_rate |   completion_rate |   wpt_loss |   fleet_min_soc |   charging_wait |   solver_calls |   solver_computation_time_s |   solver_mean_time_s |   solver_p95_time_s |   solver_max_time_s |   solver_mean_binary_variables |   solver_mean_constraints |   solver_infeasible_calls |   solver_time_limit_calls |   solver_fallback_calls |   solver_safety_slack_total |   solver_task_slack_total |
|:-----------|-------------:|----------------------:|------------------:|-----------:|----------------:|----------------:|---------------:|----------------------------:|---------------------:|--------------------:|--------------------:|-------------------------------:|--------------------------:|--------------------------:|--------------------------:|------------------------:|----------------------------:|--------------------------:|
| C1         |       7.0952 |               52.6159 |           99.4022 |     8.2847 |         29.6639 |         40.9696 |           0    |                      0      |             nan      |            nan      |            nan      |                       nan      |                   nan     |                       nan |                       nan |                     nan |                         nan |                       nan |
| C2         |       4.0121 |               72.5912 |           99.0366 |     8.6561 |         19.7292 |         25.5058 |           0    |                      0      |             nan      |            nan      |            nan      |                       nan      |                   nan     |                       nan |                       nan |                     nan |                         nan |                       nan |
| C3         |       6.0735 |               85.2879 |           97.4182 |     6.9989 |         24.9219 |         54.8596 |           0    |                      0      |             nan      |            nan      |            nan      |                       nan      |                   nan     |                       nan |                       nan |                     nan |                         nan |                       nan |
| C4         |       6.4882 |               81.9243 |           97.3516 |     7.3947 |         22.3317 |         48.6591 |           0    |                      0      |             nan      |            nan      |            nan      |                       nan      |                   nan     |                       nan |                       nan |                     nan |                         nan |                       nan |
| C5         |      40.7553 |               36.622  |           97.5977 |    10.1812 |         19.664  |        109.373  |         553.44 |                      0.6258 |               0.0011 |              0.0016 |              0.0024 |                        27.9938 |                   135.293 |                         0 |                         0 |                       0 |                           0 |                         0 |

## C4 vs C5 Primary Challenge differences

| metric              |      C4 |      C5 |   C4_minus_C5 |
|:--------------------|--------:|--------:|--------------:|
| mean_delay_min      |  6.4882 | 40.7553 |      -34.2671 |
| urgent_on_time_pct  | 81.9243 | 36.622  |       45.3023 |
| completion_rate_pct | 97.3516 | 97.5977 |       -0.2461 |
| wpt_loss_kwh        |  7.3947 | 10.1812 |       -2.7865 |
| fleet_min_soc_pct   | 22.3317 | 19.664  |        2.6677 |

## C4 vs C5 metric-specific gap file

| scenario             | metric                         |   mean_C4 |   mean_C5 |   mean_diff_C4_minus_C5 |   mean_gap_percent |   n |
|:---------------------|:-------------------------------|----------:|----------:|------------------------:|-------------------:|----:|
| v3_primary_challenge | mean_delay                     |    6.4882 |   40.7553 |                -34.267  |           -82.3742 |  50 |
| v3_primary_challenge | urgent_deadline_violation_rate |   18.0757 |   63.378  |                -45.3023 |           -72.0947 |  50 |
| v3_primary_challenge | wpt_loss                       |    7.3947 |   10.1812 |                 -2.7865 |           -18.1781 |  50 |

## C5 solver statistics

|   calls_total |   calls_per_rep |   total_solver_time_per_rep_s |   mean_solve_time_s |   median_solve_time_s |   p95_solve_time_s |   max_solve_time_s |   mean_binary_variables |   mean_continuous_variables |   mean_constraints |   infeasible_calls |   time_limit_calls |   fallback_calls |   safety_slack_total |   task_slack_total |
|--------------:|----------------:|------------------------------:|--------------------:|----------------------:|-------------------:|-------------------:|------------------------:|----------------------------:|-------------------:|-------------------:|-------------------:|-----------------:|---------------------:|-------------------:|
|         27672 |          553.44 |                       0.62576 |            0.001131 |              0.001095 |           0.001611 |           0.004267 |                 28.0209 |                      82.116 |              135.4 |                  0 |                  0 |                0 |                    0 |                  0 |

## Horizon sensitivity, 5 replications each

|   horizon_min |   mean_delay |   urgent_on_time_rate |   completion_rate |   wpt_loss |   solver_calls |   solver_computation_time_s |   solver_fallback_calls |   solver_infeasible_calls |   solver_time_limit_calls |
|--------------:|-------------:|----------------------:|------------------:|-----------:|---------------:|----------------------------:|------------------------:|--------------------------:|--------------------------:|
|             5 |      35.0661 |               41.9968 |           97.6814 |     9.8349 |          617.6 |                      0.5146 |                       0 |                         0 |                         0 |
|            15 |      35.0661 |               41.9968 |           97.6814 |     9.8349 |          617.6 |                      0.678  |                       0 |                         0 |                         0 |
|            30 |      35.0661 |               41.9968 |           97.6814 |     9.8349 |          617.6 |                      0.9974 |                       0 |                         0 |                         0 |

The 5, 15, and 30 min horizons produced identical performance in the small sensitivity run, while solver time increased with horizon length. This indicates that the current linear proxy objective is dominated by SOC-safety feasibility rather than by horizon-length lookahead. It is stable, but it is not yet a strong logistics-performance benchmark.

## C1-C4 regression check against archived official V3

The C1-C4 logic was not changed. Comparison against `archive/v3-c1revised-before-c5-15min-rh` produced max absolute mean-metric difference:

```text
0.0
```

Detailed file: `results_v3/c1_c4_regression_vs_archived_official.csv`.

## Corrected C4 diagnostic variance

|                    |         0 |
|:-------------------|----------:|
| E_next_std         |  0.354145 |
| D_std              |  0.038259 |
| raw_E_next_kwh_std |  0.00303  |
| raw_D_s_std        | 22.9556   |

Corrected C4 per-AGV WMS next-task preview remains active. `E_next` and `D` retain nonzero feature variance.

## Small full-horizon validation note

| mode                     |   operation_hours |   n_agvs |   n_pads |   slots |   n_binary |   status | message                                                         |   solve_time_s |
|:-------------------------|------------------:|---------:|---------:|--------:|-----------:|---------:|:----------------------------------------------------------------|---------------:|
| full_horizon_small_check |                 1 |        2 |        1 |      60 |        120 |        0 | Optimization terminated successfully. (HiGHS Status 7: Optimal) |      0.0020562 |

This is a solver/mechanics check, not an official 24 h global optimum.

## Figure provenance

Official figures are regenerated in `results_v3_figures/` from `results_v3/` only:

- Figure 1: Base vs Primary Challenge, C1-C5
- Figure 2: Primary Challenge trade-off map, C1-C5, C5 labeled as 15-min RH-MILP
- Figure 3: Corrected C4 diagnostics
- Figure 4: C4 vs C3 stress grid

Figure 2 data:

| strategy   |   mean_delay |   urgent_on_time_rate |   completion_rate |   wpt_loss |
|:-----------|-------------:|----------------------:|------------------:|-----------:|
| C1         |       7.0952 |               52.6159 |           99.4022 |     8.2847 |
| C2         |       4.0121 |               72.5912 |           99.0366 |     8.6561 |
| C3         |       6.0735 |               85.2879 |           97.4182 |     6.9989 |
| C4         |       6.4882 |               81.9243 |           97.3516 |     7.3947 |
| C5         |      40.7553 |               36.622  |           97.5977 |    10.1812 |

## Interpretation and limitations

### Is C5 a sufficiently valid optimization benchmark here?

Not fully. It is valid as a **well-defined 15-min rolling-horizon charging MILP benchmark** with reproducible solver statistics, but the present linear proxy objective is too conservative: because safety slack is zero in most horizons, the MILP often has little incentive to perform opportunity charging before a future mandatory-charge event appears in the forecast. As a result, C5 behaves closer to a conservative threshold-like policy than to a strong logistics-aware benchmark.

### How does C4 compare to C5?

In the official Primary Challenge, C4 outperforms C5 on the main operational metrics:

- C4 delay: `6.4882` min vs C5 `40.7553` min
- C4 urgent on-time: `81.9243%` vs C5 `36.6220%`
- C4 completion: `97.3516%` vs C5 `97.5977%`
- C4 WPT loss: `7.3947` kWh vs C5 `10.1812` kWh

C4 also has zero solver overhead. C5 averages `553.44` MILP calls/rep and `0.6258` s solver time/rep in this implementation.

### Required wording

Use:

```text
C5 is a 15-min rolling-horizon MILP charging benchmark, not a 24-h full-horizon global optimum.
```

Do not use:

- global optimum
- full-horizon optimum
- theoretical upper bound
- globally optimal charging schedule
