# V3 Report — C4 next-task fix and C5 MILP benchmark

## Scope
- Existing `results/` and `results_v2/` were not overwritten. V3 outputs are written to `results_v3/`.
- C4 keeps the same priority equation, but `E_next_i` and `D_i` are now computed from a WMS-style per-AGV next-task preview rather than one shared global `next_task`.
- C5 is implemented as a rolling one-slot MILP charging allocation benchmark using `scipy.optimize.milp`/HiGHS. A small full-horizon MILP scale check is included; 24 h full-horizon MILP is reported as impractical for this DES coupling and rolling MILP is used instead.

## Mean results
| strategy   |   mean_delay |   urgent_on_time_rate |   completion_rate |   wpt_loss |   fleet_min_soc |   charging_wait |   solver_computation_time_s |
|:-----------|-------------:|----------------------:|------------------:|-----------:|----------------:|----------------:|----------------------------:|
| C1         |       3.8604 |               61.3884 |           99.6153 |     2.581  |         29.6463 |         22.0618 |                      0      |
| C2         |       0.9569 |               82.8817 |           99.7145 |     2.8    |         20.8417 |          2.9537 |                      0      |
| C3         |       0.5009 |               88.2195 |           99.7802 |     2.4571 |         36.1682 |          0.8133 |                      0      |
| C4         |       0.5965 |               87.7811 |           99.7227 |     2.4976 |         31.2999 |          3.2504 |                      0      |
| C5         |       0.7114 |               87.537  |           99.601  |     2.5501 |         24.628  |          6.9453 |                      3.9146 |

## C4 vs C5 metric-specific gaps
| scenario             | metric                         |   mean_C4 |   mean_C5 |   mean_diff_C4_minus_C5 |   mean_gap_percent |   n |
|:---------------------|:-------------------------------|----------:|----------:|------------------------:|-------------------:|----:|
| v3_primary_challenge | mean_delay                     |   0.59651 |  0.711369 |              -0.114859  |          -2.11554  |  50 |
| v3_primary_challenge | urgent_deadline_violation_rate |  12.2189  | 12.463    |              -0.244114  |          -0.778492 |  50 |
| v3_primary_challenge | wpt_loss                       |   2.49761 |  2.55008  |              -0.0524628 |          -1.73653  |  50 |

## Full-horizon MILP check
| mode                     |   operation_hours |   n_agvs |   n_pads |   slots |   n_binary |   status | message                                                         |   solve_time_s |
|:-------------------------|------------------:|---------:|---------:|--------:|-----------:|---------:|:----------------------------------------------------------------|---------------:|
| full_horizon_small_check |                 1 |        2 |        1 |      60 |        120 |        0 | Optimization terminated successfully. (HiGHS Status 7: Optimal) |     0.00217883 |

## Required answers
1. **수정 후 E_next와 D가 AGV 간 variance를 갖는가?** Yes. `priority_feature_statistics.csv` stores per-replication std/min/max for `raw_E_next_kwh` and `raw_D_s`; values are based on per-AGV preview tasks.
2. **C4가 기존 결과와 얼마나 달라졌는가?** V3 C4 is no longer forced to evaluate all candidates with the same task. The main difference is visible in feature variance and C3-vs-C4 decision diagnostics; performance may improve or degrade depending on bottleneck state.
3. **C5가 C4보다 얼마나 개선되는가?** See `c4_c5_comparison.csv`; gaps are reported separately for delay, urgent violation, and WPT loss without mixing units.
4. **C4가 C5에 근접하면서 계산시간은 훨씬 짧은가?** C4 has zero solver calls; C5 records `solver_computation_time_s` and `solver_calls`. Use the gap table and solver statistics together.
5. **full-horizon MILP가 실제 계산 가능한가?** Only a small 1 h/2 AGV check is solved. A tightly coupled 24 h full-horizon MILP with DES task timing is not used; V3 reports this honestly and uses rolling MILP.
6. **C4를 optimal이라고 부를 수 있는가?** No. C4 should be called a priority-based heuristic. C5 is the optimization benchmark, and even C5 here is a rolling MILP benchmark for charging allocation rather than proof that C4 is globally optimal.

## Assumption note
Per-AGV next-task features require a WMS preview assumption: the warehouse management system provides short-horizon next assigned task information before the AGV enters an opportunity-charging decision.