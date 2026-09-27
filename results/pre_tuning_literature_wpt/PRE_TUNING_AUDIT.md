# [3]-based WPT pre-tuning audit

No tuning or unseen-final simulation was executed.

## Deadline finding
- Legacy urgent deadline is structurally infeasible for 5/25 scenario-distance rows because its fixed 240 s budget is shorter than irreducible service time.
- Provisional rule: `deadline = arrival + minimum_service_time(distance) + urgency_slack`; urgent/normal slacks are 240/480 s and require parameter-freeze approval.

## rho definition
- `rho = lambda * E_task_avg / (N_pad * E[P_charge(delta)])`; eta is not multiplied again because `P_charge` is battery-side delivered power.

## Alignment scenarios
- Good/moderate/severe are controlled sensitivity conditions, not empirical AGV docking distributions. Extreme 250–350 mm is failure sensitivity only.

## Catalog

| scenario               | role                         | physical_condition   | prediction_case   |   n_agvs |   n_pads |   task_arrival_rate_per_h |   wpt_power_kw | distances_m    |   urgent_ratio |   mean_available_charge_power_kw |   mean_eta |   mean_delta_mm |   near_zero_charge_probability |   mean_task_energy_kwh |   analytical_demand_kw |   charging_supply_kw |   rho_analytical | rho_region             |   logistics_utilization |
|:-----------------------|:-----------------------------|:---------------------|:------------------|---------:|---------:|--------------------------:|---------------:|:---------------|---------------:|---------------------------------:|-----------:|----------------:|-------------------------------:|-----------------------:|-----------------------:|---------------------:|-----------------:|:-----------------------|------------------------:|
| resource_rich_good     | representative_resource_rich | good                 | perfect           |        5 |        2 |                   75.0000 |         3.0000 | 30|30|30|30|30 |         0.2000 |                           2.7818 |     0.7526 |         27.5000 |                         0.0000 |                 0.0141 |                 1.0562 |               5.5635 |           0.1899 | non_binding            |                  0.6250 |
| near_boundary_good     | representative_near_boundary | good                 | perfect           |        6 |        1 |                   90.0000 |         3.0000 | 40|50|60|70|80 |         0.2000 |                           2.7818 |     0.7526 |         27.5000 |                         0.0000 |                 0.0269 |                 2.4225 |               2.7818 |           0.8709 | near_transition        |                  0.8750 |
| near_boundary_moderate | representative_near_boundary | moderate             | moderate_error    |        6 |        1 |                   90.0000 |         3.0000 | 40|50|60|70|80 |         0.2000 |                           2.1289 |     0.7305 |         70.0000 |                         0.0000 |                 0.0269 |                 2.4225 |               2.1289 |           1.1379 | moderately_constrained |                  0.8750 |
| near_boundary_severe   | representative_near_boundary | severe               | moderate_error    |        6 |        1 |                   90.0000 |         3.0000 | 40|50|60|70|80 |         0.2000 |                           1.0834 |     0.6423 |        135.0000 |                         0.0000 |                 0.0269 |                 2.4225 |               1.0834 |           2.2361 | strongly_constrained   |                  0.8750 |
| constrained_moderate   | representative_constrained   | moderate             | moderate_error    |        8 |        1 |                  105.0000 |         3.0000 | 55|65|75|85|95 |         0.2000 |                           2.1289 |     0.7305 |         70.0000 |                         0.0000 |                 0.0333 |                 3.5000 |               2.1289 |           1.6441 | strongly_constrained   |                  0.8750 |

## Expected C4 tuning count
- Coarse 5-feature simplex, step 0.25: 70 candidates × 5 scenarios × 50 seeds = 17,500 C4 simulations.
- C1/C2/C3 reference: 3 × 5 × 50 = 750 simulations.
- Local 0.05 one-transfer neighborhood: at most 21 candidates × 5 × 50 = 5,250 C4 simulations.
- Maximum C4-plus-reference total before C5 revalidation: 23,500 simulations.
