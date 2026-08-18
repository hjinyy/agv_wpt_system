# V3 Report — C4 Next-Task Fix and C5 MILP Benchmark

## Scope and preservation

- Existing `results/` and `results_v2/` were not deleted or overwritten.
- A pre-V3 archive was created under `/home/hy/wpt_agv_before_v3_*.tar.gz` excluding `.venv`, `.git`, and the 1.6 GB task-level V2 CSV.
- V3 outputs are stored in `results_v3/`.

## Model changes

### C4 next-task fix

V2/V2-derived C4 evaluated all charging candidates with the same global `next_task`, so `E_next` and `D` could become non-informative during contention. V3 adds a WMS-preview assumption: before an opportunity-charging decision, the warehouse management system provides a short-horizon deterministic preview of the next FCFS tasks likely to be assigned to currently available AGVs. Actual task assignment remains unchanged for every strategy: FCFS queue + first-available AGV + deterministic AGV-ID tie break. C4's score equation is unchanged; only the AGV-specific task used to compute `E_next_i` and `D_i` is corrected.

### C5 MILP benchmark

C5 uses `scipy.optimize.milp`/HiGHS as a reproducible MILP solver. The implemented V3 production benchmark is a rolling one-slot MILP allocation of charging pads, because coupling a 24 h full-horizon MILP with discrete-event task timing and preemptible opportunity charging is not computationally practical in this codebase without a separate time-indexed logistics model. A small full-horizon check is solved and recorded to verify solver availability and scaling mechanics.

Small full-horizon check:

| mode                     |   operation_hours |   n_agvs |   n_pads |   slots |   n_binary |   status | message                                                         |   solve_time_s |
|:-------------------------|------------------:|---------:|---------:|--------:|-----------:|---------:|:----------------------------------------------------------------|---------------:|
| full_horizon_small_check |                 1 |        2 |        1 |      60 |        120 |        0 | Optimization terminated successfully. (HiGHS Status 7: Optimal) |     0.00161455 |

## Mean V3 results, 50 replications

| strategy   |   mean_delay |   urgent_on_time_rate |   completion_rate |   wpt_loss |   fleet_min_soc |   charging_wait |   solver_computation_time_s |   solver_calls |
|:-----------|-------------:|----------------------:|------------------:|-----------:|----------------:|----------------:|----------------------------:|---------------:|
| C1         |      38.954  |               37.8586 |           97.7099 |     9.6975 |         19.6681 |        104.995  |                      0      |           0    |
| C2         |       4.0121 |               72.5912 |           99.0366 |     8.6561 |         19.7292 |         25.5058 |                      0      |           0    |
| C3         |       6.0735 |               85.2879 |           97.4182 |     6.9989 |         24.9219 |         54.8596 |                      0      |           0    |
| C4         |       6.4882 |               81.9243 |           97.3516 |     7.3947 |         22.3317 |         48.6591 |                      0      |           0    |
| C5         |       0.4968 |               88.2382 |           99.7838 |     5.6294 |         16.2048 |          0      |                      0.9819 |        1311.72 |

## C4 vs C5 metric-specific gap

No mixed-unit weighted objective is used. Delay, urgent violation, and WPT loss gaps are reported separately.

| scenario             | metric                         |   mean_C4 |   mean_C5 |   mean_diff_C4_minus_C5 |   mean_gap_percent |   n |
|:---------------------|:-------------------------------|----------:|----------:|------------------------:|-------------------:|----:|
| v3_primary_challenge | mean_delay                     |    6.4882 |    0.4968 |                  5.9915 |          1036.01   |  50 |
| v3_primary_challenge | urgent_deadline_violation_rate |   18.0757 |   11.7618 |                  6.3139 |            48.2835 |  50 |
| v3_primary_challenge | wpt_loss                       |    7.3947 |    5.6294 |                  1.7654 |            32.4825 |  50 |

## C4 feature variance after fix

Mean per-replication standard deviations from `priority_feature_statistics.csv`:

|                    |         0 |
|:-------------------|----------:|
| E_next_std         |  0.354145 |
| D_std              |  0.038259 |
| raw_E_next_kwh_std |  0.00303  |
| raw_D_s_std        | 22.9556   |

Interpretation: `E_next` now has nonzero normalized variance and nonzero raw kWh variance across AGV candidates. `D` also has nonzero standard deviation, but it is smaller than `E_next` in this primary scenario, so deadline pressure contributes less frequently than task-energy heterogeneity.

## Required answers

1. **수정 후 `E_next`와 `D`가 AGV 간 실제 variance를 갖는가?**  
   예. 평균 `E_next_std=0.354145`, `raw_E_next_kwh_std=0.003030 kWh`, `D_std=0.038259`, `raw_D_s_std=22.956 s`로 확인됩니다.

2. **C4가 기존 결과와 얼마나 달라졌는가?**  
   V3 C4는 더 이상 모든 후보에 동일한 next task를 적용하지 않습니다. Primary Challenge 평균 기준 C4는 delay `6.488 min`, urgent on-time `81.924%`, WPT loss `7.395 kWh`입니다. 기존 V2 primary C4와 직접 비교하면 모델 수정 효과와 이전 figure용 weight/eta 수정의 영향이 섞일 수 있으므로, V3 보고서는 feature variance와 C4-C5 gap을 중심으로 해석합니다.

3. **C5가 C4보다 얼마나 개선되는가?**  
   `c4_c5_comparison.csv` 기준 C5는 C4 대비 mean delay, urgent violation, WPT loss에서 각각 별도 gap을 제공합니다. 평균 delay는 C4 `6.488 min`에서 C5 `0.497 min`로 낮아졌고, WPT loss도 C4 `7.395 kWh`에서 C5 `5.629 kWh`로 낮아졌습니다.

4. **C4가 C5에 근접하면서 계산시간은 훨씬 짧은가?**  
   C4는 solver call이 없으므로 계산시간 overhead가 사실상 0입니다. C5는 평균 solver time `0.982 s/replication`, 평균 solver calls `1311.7`회를 기록했습니다. 현재 V3 결과에서는 C5 성능 우위가 크지만 계산 overhead도 명확히 존재합니다.

5. **Full-horizon MILP가 실제 계산 가능한가?**  
   작은 1 h/2 AGV/1 pad check는 optimal로 풀렸습니다. 그러나 24 h full-horizon은 DES task timing, preemption, detour, pad queue를 모두 time-indexed MILP에 넣어야 하므로 이번 V3에서는 임의 단순화하지 않고 rolling MILP benchmark로 보고합니다.

6. **논문에서 C4를 optimal이라고 부를 수 있는가?**  
   아니요. C4는 반드시 **priority-based heuristic**으로 표현해야 합니다. C5는 optimization benchmark이지만, V3의 C5도 24 h global proof가 아니라 rolling MILP charging benchmark입니다. 따라서 논문에서는 C4를 optimal로 주장하지 말고, C5와의 성능/계산시간 trade-off를 통해 heuristic의 실용성을 논의하는 것이 타당합니다.

## Output files

- `c1_c5_results.csv`
- `c4_c5_comparison.csv`
- `milp_schedule.csv`
- `solver_statistics.csv`
- `priority_feature_statistics.csv`
- `priority_features_raw.csv`
- `task_level_results.csv`
- `agv_level_results.csv`
- `pad_level_results.csv`
- `decision_diagnostics.csv`
- `full_horizon_milp_check.json`
- `REPORT_V3.md`


## V3 final figure provenance correction

A previous file named `create_v3_main_figures.py` incorrectly read from `results_v2/` while writing to `results_v3_figures/`. That output must not be used as V3 evidence. The generator has been replaced and now hard-checks that its source directory is exactly `results_v3/`.

New V3-only figure inputs:

- `results_v3/base_case_runs.csv` — corrected C4 Base Case, 50 replications, C1-C5.
- `results_v3/c1_c5_results.csv` — corrected C4 Primary Challenge, 50 replications, C1-C5.
- `results_v3/stress_grid.csv` — corrected C4 stress grid, 18 scenarios × 50 replications × C1-C4.
- `results_v3/priority_feature_statistics.csv` and `results_v3/priority_features_raw.csv` — V3 corrected C4 feature diagnostics.
- `results_v3/decision_diagnostics.csv` — V3 C3-vs-C4 decision diagnostics.

V3 Base Case means:

| strategy   |   mean_delay |   completion_rate |   urgent_on_time_rate |
|:-----------|-------------:|------------------:|----------------------:|
| C1         |        3.427 |            99.746 |                   100 |
| C2         |        0.205 |            99.775 |                   100 |
| C3         |        0.205 |            99.775 |                   100 |
| C4         |        0.205 |            99.775 |                   100 |
| C5         |        0.205 |            99.775 |                   100 |

V3 Primary Challenge data used by Figure 2:

| strategy   |   mean_delay |   urgent_on_time_rate |   completion_rate |   wpt_loss |
|:-----------|-------------:|----------------------:|------------------:|-----------:|
| C1         |       38.954 |                37.859 |            97.71  |      9.697 |
| C2         |        4.012 |                72.591 |            99.037 |      8.656 |
| C3         |        6.073 |                85.288 |            97.418 |      6.999 |
| C4         |        6.488 |                81.924 |            97.352 |      7.395 |
| C5         |        0.497 |                88.238 |            99.784 |      5.629 |

V3 stress grid size: `3600` rows, `18` scenarios. Figure 4 reports C4-vs-C3 delay improvement with negative values preserved; it no longer claims unconditional C4 advantage.
