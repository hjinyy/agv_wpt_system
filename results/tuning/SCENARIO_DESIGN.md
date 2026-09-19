# Scenario Design by Charging Adequacy

`rho = fleet task energy demand / available WPT supply`.
Task demand includes DES-consistent round-trip travel and service auxiliary energy; it excludes pad-detour energy because detours are scheduling-dependent.

## Catalog

| scenario                    | role                  | distances_m    |   task_arrival_rate_per_h |   n_agvs |   n_pads |   wpt_power_kw |   rho_analytical |   rho_simulation_based | rho_region             |   logistics_utilization |
|:----------------------------|:----------------------|:---------------|--------------------------:|---------:|---------:|---------------:|-----------------:|-----------------------:|:-----------------------|------------------------:|
| base                        | non_binding_reference | 30|30|30|30|30 |                   75.0000 |        5 |        2 |         3.0000 |           0.2201 |                 0.2199 | non_binding            |                  0.6250 |
| primary                     | primary_selected_6agv | 40|50|60|70|80 |                   90.0000 |        6 |        1 |         3.0000 |           1.0094 |                 1.0100 | moderately_constrained |                  0.8750 |
| stress_non_binding          | stress                | 30|30|30|30|30 |                   75.0000 |        5 |        2 |         3.0000 |           0.2201 |                 0.2199 | non_binding            |                  0.6250 |
| stress_near_transition      | stress                | 45|55|65|75|85 |                   70.0000 |        7 |        1 |         3.0000 |           0.8475 |                 0.8471 | near_transition        |                  0.6111 |
| stress_transition           | stress                | 45|55|65|75|85 |                   80.0000 |        7 |        1 |         3.0000 |           0.9686 |                 0.9684 | transition             |                  0.6984 |
| stress_strongly_constrained | stress                | 55|65|75|85|95 |                  105.0000 |        8 |        1 |         3.0000 |           1.4584 |                 1.4576 | strongly_constrained   |                  0.8750 |

## Selected roles

- **Base** stays at rho << 1 as a non-binding reference.
- **Primary** is `primary`: 40/50/60/70/80 m, six AGVs, one 3-kW pad, 90 tasks/h. It has rho about 1.01 while logistics utilization remains below 1.
- The stress catalog covers non-binding, near-transition, transition, moderately constrained, and strongly constrained rho regions. It was selected by rho coverage rather than C4 outcome.

The uniform 0-175-mm eight-state misalignment assumption is retained. Mean eta is evaluated from the frozen power-dependent SS-FHA curve for each scenario power.
