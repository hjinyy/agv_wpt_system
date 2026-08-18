# Official V3 Report — Revised C1 Baseline, Corrected C4, and C5 Rolling MILP

## Scope and preservation

- Previous main state was archived as `archive/v3-before-c1revised-official` before this official rerun.
- Existing older experiment branches remain available; `main` contains the latest official V3 only.
- Official V3 outputs are stored in `results_v3/` and official figures in `results_v3_figures/`.

## Official V3 model changes

### Revised conventional baseline C1

C1 is no longer the overly harsh `20% → 90%` full-charge baseline. Official V3 uses a more realistic conventional threshold baseline:

- charging starts when `SOC <= 30%`,
- charging terminates at `SOC = 70%`,
- no opportunity charging,
- no task assignment during mandatory charging.

### Corrected C4

C4 keeps the same priority equation, but candidate features are now computed from AGV-specific WMS preview tasks. This fixes the earlier issue where all candidate AGVs used the same global `next_task`, making `E_next_i` and `D_i` weak or non-informative.

### C5 rolling MILP benchmark

C5 uses `scipy.optimize.milp` / HiGHS for rolling one-slot charging-pad allocation. The same mandatory SOC safety check is now applied to C5 as to C2-C4. Therefore C5 is not claimed as a full-horizon global optimum; it is a rolling MILP charging benchmark with explicit solver overhead.

Small full-horizon solver availability check:

| mode                     |   operation_hours |   n_agvs |   n_pads |   slots |   n_binary |   status | message                                                         |   solve_time_s |
|:-------------------------|------------------:|---------:|---------:|--------:|-----------:|---------:|:----------------------------------------------------------------|---------------:|
| full_horizon_small_check |                 1 |        2 |        1 |      60 |        120 |        0 | Optimization terminated successfully. (HiGHS Status 7: Optimal) |     0.00174877 |

## Base Case means, 50 replications

| strategy   |   mean_delay |   completion_rate |   urgent_on_time_rate |   wpt_loss |   fleet_min_soc |   charging_wait |
|:-----------|-------------:|------------------:|----------------------:|-----------:|----------------:|----------------:|
| C1         |       1.3063 |           99.7518 |                   100 |     6.6596 |         29.6787 |          3.2068 |
| C2         |       0.2049 |           99.7749 |                   100 |     9.6359 |         53.4107 |          0      |
| C3         |       0.205  |           99.7749 |                   100 |     9.6431 |         55.0489 |          0      |
| C4         |       0.2049 |           99.7749 |                   100 |     9.321  |         54.9547 |          0      |
| C5         |       0.205  |           99.7749 |                   100 |     9.5143 |         54.4759 |          0      |

## Primary Challenge means, 50 replications

| strategy   |   mean_delay |   urgent_on_time_rate |   completion_rate |   wpt_loss |   fleet_min_soc |   charging_wait |   solver_computation_time_s |   solver_calls |
|:-----------|-------------:|----------------------:|------------------:|-----------:|----------------:|----------------:|----------------------------:|---------------:|
| C1         |       7.0952 |               52.6159 |           99.4022 |     8.2847 |         29.6639 |         40.9696 |                      0      |           0    |
| C2         |       4.0121 |               72.5912 |           99.0366 |     8.6561 |         19.7292 |         25.5058 |                      0      |           0    |
| C3         |       6.0735 |               85.2879 |           97.4182 |     6.9989 |         24.9219 |         54.8596 |                      0      |           0    |
| C4         |       6.4882 |               81.9243 |           97.3516 |     7.3947 |         22.3317 |         48.6591 |                      0      |           0    |
| C5         |       6.9793 |               74.3422 |           97.67   |     8.7991 |         20.0121 |         45.9584 |                      0.8756 |        1158.92 |

## C4 vs C5 metric-specific gaps

Negative `mean_diff_C4_minus_C5` means C4 is better/lower than C5 for that metric. Metrics are reported separately; no mixed-unit weighted objective is used.

| scenario             | metric                         |   mean_C4 |   mean_C5 |   mean_diff_C4_minus_C5 |   mean_gap_percent |   n |
|:---------------------|:-------------------------------|----------:|----------:|------------------------:|-------------------:|----:|
| v3_primary_challenge | mean_delay                     |    6.4882 |    6.9793 |                 -0.4911 |           -17.7961 |  50 |
| v3_primary_challenge | urgent_deadline_violation_rate |   18.0757 |   25.6578 |                 -7.582  |           -27.9846 |  50 |
| v3_primary_challenge | wpt_loss                       |    7.3947 |    8.7991 |                 -1.4043 |            -8.9716 |  50 |

## C4 feature variance after fix

Mean per-replication standard deviations from `priority_feature_statistics.csv`:

|                    |         0 |
|:-------------------|----------:|
| E_next_std         |  0.354145 |
| D_std              |  0.038259 |
| raw_E_next_kwh_std |  0.00303  |
| raw_D_s_std        | 22.9556   |

`E_next` and `D` both have nonzero variance after the WMS-preview fix. `E_next` is the more informative feature in this scenario, while `D` is nonzero but smaller.

## Final figure provenance

The official figure generator `create_v3_main_figures.py` now reads only from `results_v3/`. It does not read `results_v2/`.

Official figure inputs:

- `results_v3/base_case_runs.csv`
- `results_v3/c1_c5_results.csv`
- `results_v3/stress_grid.csv`
- `results_v3/priority_feature_statistics.csv`
- `results_v3/priority_features_raw.csv`
- `results_v3/decision_diagnostics.csv`

Figure 2 plot data:

| strategy   |   mean_delay |   urgent_on_time_rate |   completion_rate |   wpt_loss |
|:-----------|-------------:|----------------------:|------------------:|-----------:|
| C1         |       7.0952 |               52.6159 |           99.4022 |     8.2847 |
| C2         |       4.0121 |               72.5912 |           99.0366 |     8.6561 |
| C3         |       6.0735 |               85.2879 |           97.4182 |     6.9989 |
| C4         |       6.4882 |               81.9243 |           97.3516 |     7.3947 |
| C5         |       6.9793 |               74.3422 |           97.67   |     8.7991 |

## Required interpretation

1. **수정 후 `E_next`와 `D`가 AGV 간 실제 variance를 갖는가?**  
   예. 평균 `E_next_std=0.354145`, `raw_E_next_kwh_std=0.003030 kWh`, `D_std=0.038259`, `raw_D_s_std=22.956 s`입니다.

2. **C1 revised baseline은 더 적절한가?**  
   예. Primary Challenge에서 C1 delay는 `7.095 min` 수준으로 내려와 기존 극단 baseline보다 훨씬 덜 strawman처럼 보입니다. 그러나 C1은 여전히 C2보다 delay가 크고 C3/C4보다 urgent on-time이 낮아 conventional threshold charging baseline 역할은 유지합니다.

3. **C4가 C5보다 좋은가?**  
   이번 official V3에서는 C5에 동일한 mandatory SOC safety check를 적용한 결과, C4가 C5보다 mean delay, urgent violation, WPT loss에서 더 좋게 나왔습니다. 이는 C5가 full-horizon global optimum이 아니라 rolling one-slot MILP benchmark이기 때문입니다.

4. **C4가 C5에 근접하면서 계산시간은 훨씬 짧은가?**  
   C4는 solver overhead가 0이고, C5는 평균 solver time `0.876 s/replication`, 평균 solver calls `1158.9`회를 사용합니다. 현재 implementation에서는 C4가 성능과 계산시간 모두에서 더 실용적입니다.

5. **Full-horizon MILP가 실제 계산 가능한가?**  
   작은 1 h / 2 AGV / 1 pad check는 풀렸지만, 24 h DES-coupled full-horizon MILP는 이번 codebase에서 임의 단순화하지 않았습니다. 논문에서는 C5를 rolling MILP benchmark로 명시해야 합니다.

6. **C4를 optimal이라고 부를 수 있는가?**  
   아니요. C4는 **priority-based heuristic**입니다. C5도 rolling benchmark이므로 full global optimum으로 주장하면 안 됩니다.
