# C5 Robust Revalidation and OAT Refinement

## Scope
- C5 structure was unchanged: 15-minute rolling horizon, 60-s slots, MILP constraints, and first-slot receding-horizon execution.
- Only lambda_soc, lambda_task, and lambda_kpi objective scales were revalidated.
- C5 is a **rolling-horizon MILP reference** / **optimization-based reference**, not a clairvoyant global optimum.

## Compute plan
```json
{
  "method": "OAT around historical starting scales under frozen literature conditions; not full 27-grid",
  "candidates": [
    {
      "lambda_soc": 2.0,
      "lambda_task": 1.5,
      "lambda_kpi": 2.0
    },
    {
      "lambda_soc": 1.5,
      "lambda_task": 1.5,
      "lambda_kpi": 2.0
    },
    {
      "lambda_soc": 2.5,
      "lambda_task": 1.5,
      "lambda_kpi": 2.0
    },
    {
      "lambda_soc": 2.0,
      "lambda_task": 1.0,
      "lambda_kpi": 2.0
    },
    {
      "lambda_soc": 2.0,
      "lambda_task": 2.0,
      "lambda_kpi": 2.0
    },
    {
      "lambda_soc": 2.0,
      "lambda_task": 1.5,
      "lambda_kpi": 1.5
    },
    {
      "lambda_soc": 2.0,
      "lambda_task": 1.5,
      "lambda_kpi": 2.5
    }
  ],
  "scenario_count": 5,
  "seed_count": 50,
  "expected_simulations": 1750,
  "final_seed_range_used": null
}
```

## Scenario summaries
| scale_id              | scenario                        |   lambda_soc |   lambda_task |   lambda_kpi |   replications |   mean_delay_min |   urgent_on_time_percent |   completion_rate_percent |   fleet_min_soc |   mean_solver_time_s |   p95_solver_time_s |   total_solver_calls |   solver_infeasible_calls |   low_soc_stops |   simulation_failures |
|:----------------------|:--------------------------------|-------------:|--------------:|-------------:|---------------:|-----------------:|-------------------------:|--------------------------:|----------------:|---------------------:|--------------------:|---------------------:|--------------------------:|----------------:|----------------------:|
| soc1.5_task1.5_kpi2.0 | moderately_constrained_moderate |       1.5000 |        1.5000 |       2.0000 |             50 |         383.2372 |                   9.9348 |                   64.6687 |         19.2500 |               0.6419 |              1.0715 |                11789 |                         0 |               0 |                     0 |
| soc1.5_task1.5_kpi2.0 | near_transition_good            |       1.5000 |        1.5000 |       2.0000 |             50 |         135.2538 |                  10.8018 |                   84.5775 |         19.2500 |               0.7267 |              1.3607 |                12715 |                         0 |               0 |                     0 |
| soc1.5_task1.5_kpi2.0 | non_binding_good                |       1.5000 |        1.5000 |       2.0000 |             50 |           0.2001 |                  97.2451 |                   99.8314 |         47.7284 |              23.3243 |             25.4829 |               121294 |                         0 |               0 |                     0 |
| soc1.5_task1.5_kpi2.0 | strongly_constrained_moderate   |       1.5000 |        1.5000 |       2.0000 |             50 |         712.6326 |                   5.9183 |                   52.3393 |         19.1222 |               0.7155 |              1.2741 |                12584 |                         0 |               0 |                     0 |
| soc1.5_task1.5_kpi2.0 | strongly_constrained_severe     |       1.5000 |        1.5000 |       2.0000 |             50 |        4694.2721 |                   8.7242 |                   44.1446 |         19.2636 |               0.5078 |              0.7639 |                10145 |                         0 |               0 |                     0 |
| soc2.0_task1.0_kpi2.0 | moderately_constrained_moderate |       2.0000 |        1.0000 |       2.0000 |             50 |         382.2081 |                   9.9348 |                   64.6633 |         19.2500 |               0.6280 |              1.0497 |                11789 |                         0 |               0 |                     0 |
| soc2.0_task1.0_kpi2.0 | near_transition_good            |       2.0000 |        1.0000 |       2.0000 |             50 |         135.2538 |                  10.8018 |                   84.5775 |         19.2500 |               0.7096 |              1.3373 |                12715 |                         0 |               0 |                     0 |
| soc2.0_task1.0_kpi2.0 | non_binding_good                |       2.0000 |        1.0000 |       2.0000 |             50 |           0.2001 |                  97.2451 |                   99.8314 |         47.7284 |              23.8213 |             26.1494 |               121294 |                         0 |               0 |                     0 |
| soc2.0_task1.0_kpi2.0 | strongly_constrained_moderate   |       2.0000 |        1.0000 |       2.0000 |             50 |         709.7142 |                   5.9183 |                   52.4202 |         19.1222 |               0.6996 |              1.2436 |                12584 |                         0 |               0 |                     0 |
| soc2.0_task1.0_kpi2.0 | strongly_constrained_severe     |       2.0000 |        1.0000 |       2.0000 |             50 |        4735.3651 |                   8.7242 |                   44.1456 |         19.2636 |               0.4967 |              0.7493 |                10145 |                         0 |               0 |                     0 |
| soc2.0_task1.5_kpi1.5 | moderately_constrained_moderate |       2.0000 |        1.5000 |       1.5000 |             50 |         426.4060 |                   9.8812 |                   62.0539 |         19.2644 |               0.6188 |              0.9491 |                11692 |                         0 |               0 |                     0 |
| soc2.0_task1.5_kpi1.5 | near_transition_good            |       2.0000 |        1.5000 |       1.5000 |             50 |         130.5506 |                  10.9127 |                   85.1276 |         19.2491 |               0.7136 |              1.3386 |                12821 |                         0 |               0 |                     0 |
| soc2.0_task1.5_kpi1.5 | non_binding_good                |       2.0000 |        1.5000 |       1.5000 |             50 |           0.2001 |                  97.2520 |                   99.8314 |         47.7284 |              22.5980 |             24.0846 |               121145 |                         0 |               0 |                     0 |
| soc2.0_task1.5_kpi1.5 | strongly_constrained_moderate   |       2.0000 |        1.5000 |       1.5000 |             50 |         717.5198 |                   5.8554 |                   52.8011 |         19.1222 |               0.6678 |              1.1845 |                12289 |                         0 |               0 |                     0 |
| soc2.0_task1.5_kpi1.5 | strongly_constrained_severe     |       2.0000 |        1.5000 |       1.5000 |             50 |        5767.4368 |                   8.7970 |                   39.9046 |         19.2535 |               0.5125 |              0.7634 |                10310 |                         0 |               0 |                     0 |
| soc2.0_task1.5_kpi2.0 | moderately_constrained_moderate |       2.0000 |        1.5000 |       2.0000 |             50 |         382.2081 |                   9.9348 |                   64.6633 |         19.2500 |               0.6470 |              1.0893 |                11789 |                         0 |               0 |                     0 |
| soc2.0_task1.5_kpi2.0 | near_transition_good            |       2.0000 |        1.5000 |       2.0000 |             50 |         134.9629 |                  10.8066 |                   84.5954 |         19.2500 |               0.7323 |              1.3749 |                12715 |                         0 |               0 |                     0 |
| soc2.0_task1.5_kpi2.0 | non_binding_good                |       2.0000 |        1.5000 |       2.0000 |             50 |           0.2001 |                  97.2451 |                   99.8314 |         47.7284 |              22.9175 |             24.5540 |               121294 |                         0 |               0 |                     0 |
| soc2.0_task1.5_kpi2.0 | strongly_constrained_moderate   |       2.0000 |        1.5000 |       2.0000 |             50 |         709.7142 |                   5.9183 |                   52.4202 |         19.1222 |               0.7187 |              1.2756 |                12584 |                         0 |               0 |                     0 |
| soc2.0_task1.5_kpi2.0 | strongly_constrained_severe     |       2.0000 |        1.5000 |       2.0000 |             50 |        4735.3651 |                   8.7242 |                   44.1456 |         19.2636 |               0.5120 |              0.7647 |                10145 |                         0 |               0 |                     0 |
| soc2.0_task1.5_kpi2.5 | moderately_constrained_moderate |       2.0000 |        1.5000 |       2.5000 |             50 |         415.9042 |                   9.8743 |                   62.8810 |         19.2500 |               0.6147 |              1.0300 |                11649 |                         0 |               0 |                     0 |
| soc2.0_task1.5_kpi2.5 | near_transition_good            |       2.0000 |        1.5000 |       2.5000 |             50 |         137.4397 |                  10.9164 |                   84.5660 |         19.2583 |               0.7154 |              1.3320 |                12826 |                         0 |               0 |                     0 |
| soc2.0_task1.5_kpi2.5 | non_binding_good                |       2.0000 |        1.5000 |       2.5000 |             50 |           0.2000 |                  97.2572 |                   99.8314 |         47.7284 |              22.6395 |             24.2459 |               121413 |                         0 |               0 |                     0 |
| soc2.0_task1.5_kpi2.5 | strongly_constrained_moderate   |       2.0000 |        1.5000 |       2.5000 |             50 |         708.4550 |                   5.9541 |                   51.8175 |         19.1222 |               0.7014 |              1.2142 |                12629 |                         0 |               0 |                     0 |
| soc2.0_task1.5_kpi2.5 | strongly_constrained_severe     |       2.0000 |        1.5000 |       2.5000 |             50 |        5121.2200 |                   8.7848 |                   43.7672 |         19.2539 |               0.5094 |              0.7640 |                10226 |                         0 |               0 |                     0 |
| soc2.0_task2.0_kpi2.0 | moderately_constrained_moderate |       2.0000 |        2.0000 |       2.0000 |             50 |         382.2081 |                   9.9348 |                   64.6633 |         19.2500 |               0.6272 |              1.0397 |                11789 |                         0 |               0 |                     0 |
| soc2.0_task2.0_kpi2.0 | near_transition_good            |       2.0000 |        2.0000 |       2.0000 |             50 |         134.9629 |                  10.8066 |                   84.5954 |         19.2500 |               0.7109 |              1.3465 |                12715 |                         0 |               0 |                     0 |
| soc2.0_task2.0_kpi2.0 | non_binding_good                |       2.0000 |        2.0000 |       2.0000 |             50 |           0.2001 |                  97.2451 |                   99.8314 |         47.7284 |              22.6143 |             24.2150 |               121294 |                         0 |               0 |                     0 |
| soc2.0_task2.0_kpi2.0 | strongly_constrained_moderate   |       2.0000 |        2.0000 |       2.0000 |             50 |         709.7142 |                   5.9183 |                   52.4202 |         19.1222 |               0.7008 |              1.2467 |                12584 |                         0 |               0 |                     0 |
| soc2.0_task2.0_kpi2.0 | strongly_constrained_severe     |       2.0000 |        2.0000 |       2.0000 |             50 |        4784.0388 |                   8.7242 |                   44.0526 |         19.2636 |               0.4980 |              0.7497 |                10151 |                         0 |               0 |                     0 |
| soc2.5_task1.5_kpi2.0 | moderately_constrained_moderate |       2.5000 |        1.5000 |       2.0000 |             50 |         394.2611 |                   9.9516 |                   64.1393 |         19.2500 |               0.6452 |              1.0631 |                11842 |                         0 |               0 |                     0 |
| soc2.5_task1.5_kpi2.0 | near_transition_good            |       2.5000 |        1.5000 |       2.0000 |             50 |         133.2196 |                  10.7697 |                   84.7097 |         19.2500 |               0.7297 |              1.3758 |                12689 |                         0 |               0 |                     0 |
| soc2.5_task1.5_kpi2.0 | non_binding_good                |       2.5000 |        1.5000 |       2.0000 |             50 |           0.2001 |                  97.2451 |                   99.8314 |         47.7284 |              23.0431 |             24.6826 |               121294 |                         0 |               0 |                     0 |
| soc2.5_task1.5_kpi2.0 | strongly_constrained_moderate   |       2.5000 |        1.5000 |       2.0000 |             50 |         707.3501 |                   5.9183 |                   52.5270 |         19.1222 |               0.7163 |              1.2774 |                12584 |                         0 |               0 |                     0 |
| soc2.5_task1.5_kpi2.0 | strongly_constrained_severe     |       2.5000 |        1.5000 |       2.0000 |             50 |        4784.0388 |                   8.7242 |                   44.0526 |         19.2636 |               0.5096 |              0.7643 |                10151 |                         0 |               0 |                     0 |

## Cross-region candidates
| scale_id              |   lambda_soc |   lambda_task |   lambda_kpi |   mean_delay_min |   worst_scenario_delay_min |   mean_urgent_on_time_percent |   worst_urgent_on_time_percent |   mean_completion_rate_percent |   worst_fleet_min_soc |   mean_solver_time_s |   total_solver_calls | hard_reject   |
|:----------------------|-------------:|--------------:|-------------:|-----------------:|---------------------------:|------------------------------:|-------------------------------:|-------------------------------:|----------------------:|---------------------:|---------------------:|:--------------|
| soc1.5_task1.5_kpi2.0 |       1.5000 |        1.5000 |       2.0000 |        1185.1192 |                  4694.2721 |                       26.5249 |                         5.9183 |                        69.1123 |               19.1222 |               5.1832 |               168527 | False         |
| soc2.0_task1.0_kpi2.0 |       2.0000 |        1.0000 |       2.0000 |        1192.5483 |                  4735.3651 |                       26.5249 |                         5.9183 |                        69.1276 |               19.1222 |               5.2710 |               168527 | False         |
| soc2.0_task1.5_kpi1.5 |       2.0000 |        1.5000 |       1.5000 |        1408.4227 |                  5767.4368 |                       26.5397 |                         5.8554 |                        67.9437 |               19.1222 |               5.0221 |               168257 | False         |
| soc2.0_task1.5_kpi2.0 |       2.0000 |        1.5000 |       2.0000 |        1192.4901 |                  4735.3651 |                       26.5258 |                         5.9183 |                        69.1312 |               19.1222 |               5.1055 |               168527 | False         |
| soc2.0_task1.5_kpi2.5 |       2.0000 |        1.5000 |       2.5000 |        1276.6438 |                  5121.2200 |                       26.5574 |                         5.9541 |                        68.5726 |               19.1222 |               5.0361 |               168743 | False         |
| soc2.0_task2.0_kpi2.0 |       2.0000 |        2.0000 |       2.0000 |        1202.2248 |                  4784.0388 |                       26.5258 |                         5.9183 |                        69.1126 |               19.1222 |               5.0302 |               168533 | False         |
| soc2.5_task1.5_kpi2.0 |       2.5000 |        1.5000 |       2.0000 |        1203.8139 |                  4784.0388 |                       26.5218 |                         5.9183 |                        69.0520 |               19.1222 |               5.1288 |               168560 | False         |

## Pareto candidates
| scale_id              |   lambda_soc |   lambda_task |   lambda_kpi |   mean_delay_min |   worst_scenario_delay_min |   mean_urgent_on_time_percent |   worst_urgent_on_time_percent |   mean_completion_rate_percent |   worst_fleet_min_soc |   mean_solver_time_s |   total_solver_calls | hard_reject   |
|:----------------------|-------------:|--------------:|-------------:|-----------------:|---------------------------:|------------------------------:|-------------------------------:|-------------------------------:|----------------------:|---------------------:|---------------------:|:--------------|
| soc1.5_task1.5_kpi2.0 |       1.5000 |        1.5000 |       2.0000 |        1185.1192 |                  4694.2721 |                       26.5249 |                         5.9183 |                        69.1123 |               19.1222 |               5.1832 |               168527 | False         |
| soc2.0_task1.5_kpi2.0 |       2.0000 |        1.5000 |       2.0000 |        1192.4901 |                  4735.3651 |                       26.5258 |                         5.9183 |                        69.1312 |               19.1222 |               5.1055 |               168527 | False         |
| soc2.0_task2.0_kpi2.0 |       2.0000 |        2.0000 |       2.0000 |        1202.2248 |                  4784.0388 |                       26.5258 |                         5.9183 |                        69.1126 |               19.1222 |               5.0302 |               168533 | False         |
| soc2.0_task1.5_kpi2.5 |       2.0000 |        1.5000 |       2.5000 |        1276.6438 |                  5121.2200 |                       26.5574 |                         5.9541 |                        68.5726 |               19.1222 |               5.0361 |               168743 | False         |
| soc2.0_task1.5_kpi1.5 |       2.0000 |        1.5000 |       1.5000 |        1408.4227 |                  5767.4368 |                       26.5397 |                         5.8554 |                        67.9437 |               19.1222 |               5.0221 |               168257 | False         |

## Frozen scales
```json
{
  "lambda_soc": 1.5,
  "lambda_task": 1.5,
  "lambda_kpi": 2.0
}
```
