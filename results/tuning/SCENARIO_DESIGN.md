# Scenario Design by Charging Adequacy

`rho = fleet task energy demand / available WPT supply`.
Task demand includes DES-consistent round-trip travel and service auxiliary energy; it excludes pad-detour energy because detours are scheduling-dependent.

## Catalog

| scenario                      | role                            | distances_m    |   task_arrival_rate_per_h |   n_agvs |   n_pads |   wpt_power_kw |   rho_analytical |   rho_simulation_based | rho_region             |   logistics_utilization |
|:------------------------------|:--------------------------------|:---------------|--------------------------:|---------:|---------:|---------------:|-----------------:|-----------------------:|:-----------------------|------------------------:|
| base                          | non_binding_reference           | 30|30|30|30|30 |                   75.0000 |        5 |        2 |         3.0000 |           0.2201 |                 0.2199 | non_binding            |                  0.6250 |
| primary_candidate_current     | legacy_comparator               | 20|25|30|35|40 |                   90.0000 |        5 |        1 |         3.0000 |           0.5282 |                 0.5282 | non_binding            |                  0.7500 |
| primary_candidate_60m         | candidate                       | 40|50|60|70|80 |                   90.0000 |        6 |        1 |         3.0000 |           1.0094 |                 1.0100 | transition             |                  0.8750 |
| primary_candidate_70m         | candidate_selected_if_rho_valid | 50|60|70|80|90 |                   90.0000 |        7 |        1 |         3.0000 |           1.1699 |                 1.1700 | moderately_constrained |                  0.8214 |
| primary_candidate_75m         | candidate                       | 55|65|75|85|95 |                   90.0000 |        7 |        1 |         3.0000 |           1.2501 |                 1.2502 | moderately_constrained |                  0.8571 |
| stress_non_binding            | stress                          | 30|30|30|30|30 |                   75.0000 |        5 |        2 |         3.0000 |           0.2201 |                 0.2199 | non_binding            |                  0.6250 |
| stress_near_transition        | stress                          | 45|55|65|75|85 |                   70.0000 |        7 |        1 |         3.0000 |           0.8475 |                 0.8471 | near_transition        |                  0.6111 |
| stress_transition             | stress                          | 45|55|65|75|85 |                   87.0000 |        7 |        1 |         3.0000 |           1.0533 |                 1.0530 | transition             |                  0.7595 |
| stress_moderately_constrained | stress                          | 50|60|70|80|90 |                   90.0000 |        7 |        1 |         3.0000 |           1.1699 |                 1.1700 | moderately_constrained |                  0.8214 |
| primary                       | primary_selected                | 50|60|70|80|90 |                   90.0000 |        7 |        1 |         3.0000 |           1.1699 |                 1.1700 | moderately_constrained |                  0.8214 |
| stress_strongly_constrained   | stress                          | 55|65|75|85|95 |                  105.0000 |        8 |        1 |         3.0000 |           1.4584 |                 1.4576 | strongly_constrained   |                  0.8750 |

## Selected roles

- **Base** stays at rho << 1 as a non-binding reference.
- **Primary** is `primary`: 50/60/70/80/90 m, seven AGVs, one 3-kW pad, 90 tasks/h. It has rho in the requested 1.0-1.2 transition/constrained interval while its logistics utilization remains below 1.
- The stress catalog covers non-binding, near-transition, transition, moderately constrained, and strongly constrained rho regions. It was selected by rho coverage rather than C4 outcome.

The uniform 0-175-mm eight-state misalignment assumption is retained. Mean eta is evaluated from the frozen power-dependent SS-FHA curve for each scenario power.
