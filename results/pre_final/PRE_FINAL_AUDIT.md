# Pre-final Audit

## C4 terminology recommendation
- General candidate formulation: `w_SOC f_SOC + w_E f_E + w_idle f_idle - w_D f_D`.
- Robustly selected final rule from the current tuning: `0.75 f_SOC - 0.25 f_D`.
- Recommended terminology: **SOC-deadline risk priority** or **robust charging-priority heuristic**. Do not call the selected rule a four-feature multi-feature heuristic.

## C4 Primary raw-data sanity
```json
{
  "paired_replications": 50,
  "C4_minus_C3_mean_delay_min": -1.9795855713975141,
  "C4_minus_C3_mean_urgent_on_time_percentage_points": -0.09057252414133485,
  "urgent_metric_unit": "percent (0-100); difference reported in percentage points",
  "C4_urgent_range_percent": [
    4.615384615384616,
    17.96690307328605
  ],
  "C3_urgent_range_percent": [
    5.054945054945055,
    18.2033096926714
  ]
}
```

## Primary fleet-size analytical audit
| candidate                     |   n_agvs | distances_m    |   task_arrival_rate_per_h |   mean_task_energy_kwh |   rho_analytical |   rho_simulation_based |   logistics_utilization |   service_capacity_tasks_per_h |   fleet_per_pad |   charging_contention_pressure_proxy |
|:------------------------------|---------:|:---------------|--------------------------:|-----------------------:|-----------------:|-----------------------:|------------------------:|-------------------------------:|----------------:|-------------------------------------:|
| A_5AGV_40to80m_90perh         |        5 | 40|50|60|70|80 |                        90 |                 0.0269 |           1.0094 |                 1.0096 |                  1.0500 |                        85.7143 |               5 |                               5.0472 |
| B_6AGV_40to80m_90perh         |        6 | 40|50|60|70|80 |                        90 |                 0.0269 |           1.0094 |                 1.0100 |                  0.8750 |                       102.8571 |               6 |                               6.0567 |
| C_7AGV_50to90m_90perh_current |        7 | 50|60|70|80|90 |                        90 |                 0.0312 |           1.1699 |                 1.1700 |                  0.8214 |                       109.5652 |               7 |                               8.1891 |

### Finding and stop condition
- A (5 AGVs) reaches rho near 1 only with logistics utilization above 1; it confounds logistics overload with charging constraint.
- B (6 AGVs, 40/50/60/70/80 m) reaches rho about 1.01 with logistics utilization below 1 and changes fleet size by +1 relative to the historical 5-AGV basis.
- C (current 7-AGV Primary) also meets the rho target but changes fleet size by +2.
- Therefore B is the simpler, equally valid Primary design under the stated selection rules. Changing Primary invalidates the C4 tuning that used C; no C5 50-rep revalidation/refinement, manifest freeze, unseen evaluation, or final figure generation was executed.

## C5 scope status
- No C5 revalidation/refinement results are accepted in this audit because the primary scenario must be changed first.
- A one-seed C5 cost pilot was performed before the fleet verdict solely to estimate compute: 5,015 solver calls over five scenarios. It is not a 50-rep performance result and is not used for parameter selection.
- C5 remains an **optimization-based reference** / **rolling-horizon MILP reference**, never an independent or clairvoyant global-optimal benchmark.

## Freeze status
- WPT model: frozen.
- Current C4 weights: frozen only for the now-superseded 7-AGV Primary tuning; they must be retuned after approving the 6-AGV Primary.
- C5 scales: not frozen for rho-redesign final evaluation.
- Planned unseen final seeds 6007-6056: unused.
