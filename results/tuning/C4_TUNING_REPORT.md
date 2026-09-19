# C4 Four-Feature Robust Tuning

## Scope
- Frozen physical model: 48-V nominal DC-side SS-FHA model with power-dependent eta(delta, P).
- C4 score: `w_SOC f_SOC + w_E f_E + w_idle f_idle - w_D f_D`.
- WPT eta is not a C4 score feature; it remains in actual charging energy, SOC update, WPT loss, and rho supply.
- Tuning seeds: 5007-5056, shared under CRN within each scenario.

## Search
- Coarse simplex step 0.25: 35 candidates.
- Local 0.05 transfer neighborhood around the robust coarse Pareto anchor: 7 candidates.
- Each candidate was evaluated over all five rho-region tuning scenarios. C1/C2/C3 references and C4 candidates use identical task and initial-SOC realizations per seed/scenario.

## Selection rule
1. Reject any candidate with low-SOC stops, failure, or invalid rows.
2. Retain the non-dominated set in mean C4-C3 delay, worst-case C4-C3 delay, and mean C4-C3 urgent on-time difference.
3. Choose the robust Pareto candidate with lowest worst-case delay degradation; use mean delay, then mean urgent difference as deterministic tie-breaks.

## Frozen selected C4 weights
```json
{
  "soc": 0.75,
  "next_task_energy": 0.0,
  "idle": 0.0,
  "deadline": 0.25
}
```

## Pareto candidates
| phase   | weight_id                                          |    soc |   next_task_energy |   idle |   deadline |   mean_delay_difference |   worst_delay_degradation |   mean_urgent_difference |   worst_urgent_degradation | hard_reject   |
|:--------|:---------------------------------------------------|-------:|-------------------:|-------:|-----------:|------------------------:|--------------------------:|-------------------------:|---------------------------:|:--------------|
| coarse  | soc0.75_next_task_energy0.00_idle0.00_deadline0.25 | 0.7500 |             0.0000 | 0.0000 |     0.2500 |                 -0.9818 |                   -0.0001 |                  -0.0706 |                    -0.1253 | False         |
| local   | soc0.75_next_task_energy0.00_idle0.00_deadline0.25 | 0.7500 |             0.0000 | 0.0000 |     0.2500 |                 -0.9818 |                   -0.0001 |                  -0.0706 |                    -0.1253 | False         |
| coarse  | soc0.00_next_task_energy0.25_idle0.25_deadline0.50 | 0.0000 |             0.2500 | 0.2500 |     0.5000 |                -28.2354 |                   -0.0000 |                  -4.9987 |                   -13.1218 | False         |
| coarse  | soc0.00_next_task_energy1.00_idle0.00_deadline0.00 | 0.0000 |             1.0000 | 0.0000 |     0.0000 |                -30.6878 |                   -0.0000 |                  -4.8987 |                   -11.5067 | False         |
| coarse  | soc0.25_next_task_energy0.00_idle0.00_deadline0.75 | 0.2500 |             0.0000 | 0.0000 |     0.7500 |                 -1.8471 |                   -0.0000 |                  -0.1252 |                    -0.1796 | False         |
| coarse  | soc0.00_next_task_energy0.00_idle0.50_deadline0.50 | 0.0000 |             0.0000 | 0.5000 |     0.5000 |                -34.2177 |                   -0.0000 |                  -4.6961 |                   -10.5325 | False         |
| coarse  | soc0.00_next_task_energy0.00_idle0.25_deadline0.75 | 0.0000 |             0.0000 | 0.2500 |     0.7500 |                -34.4960 |                   -0.0000 |                  -4.5824 |                    -9.7375 | False         |
| coarse  | soc1.00_next_task_energy0.00_idle0.00_deadline0.00 | 1.0000 |             0.0000 | 0.0000 |     0.0000 |                  0.0000 |                    0.0000 |                   0.0000 |                     0.0000 | False         |
| coarse  | soc0.50_next_task_energy0.00_idle0.00_deadline0.50 | 0.5000 |             0.0000 | 0.0000 |     0.5000 |                 -1.2285 |                    0.0000 |                  -0.0779 |                    -0.1909 | False         |
| local   | soc0.75_next_task_energy0.00_idle0.05_deadline0.20 | 0.7500 |             0.0000 | 0.0500 |     0.2000 |                 -0.7319 |                    0.0000 |                  -0.0570 |                    -0.0986 | False         |
| coarse  | soc0.00_next_task_energy0.00_idle0.75_deadline0.25 | 0.0000 |             0.0000 | 0.7500 |     0.2500 |                -35.2125 |                    0.0000 |                  -4.7396 |                   -10.7114 | False         |
| coarse  | soc0.00_next_task_energy0.00_idle1.00_deadline0.00 | 0.0000 |             0.0000 | 1.0000 |     0.0000 |                -35.1152 |                    0.0000 |                  -4.3589 |                   -10.3697 | False         |
| coarse  | soc0.00_next_task_energy0.00_idle0.00_deadline1.00 | 0.0000 |             0.0000 | 0.0000 |     1.0000 |                -37.6811 |                    0.0000 |                  -4.5322 |                   -12.2428 | False         |
| local   | soc0.70_next_task_energy0.05_idle0.00_deadline0.25 | 0.7000 |             0.0500 | 0.0000 |     0.2500 |                 -1.9366 |                    0.0142 |                  -0.2267 |                    -0.5161 | False         |
| coarse  | soc0.25_next_task_energy0.00_idle0.75_deadline0.00 | 0.2500 |             0.0000 | 0.7500 |     0.0000 |                -12.6378 |                    0.7119 |                  -3.1284 |                    -9.5046 | False         |
| coarse  | soc0.50_next_task_energy0.50_idle0.00_deadline0.00 | 0.5000 |             0.5000 | 0.0000 |     0.0000 |                -12.5692 |                    0.7699 |                  -1.2667 |                    -2.4558 | False         |
| coarse  | soc0.25_next_task_energy0.25_idle0.00_deadline0.50 | 0.2500 |             0.2500 | 0.0000 |     0.5000 |                -13.3376 |                    0.8172 |                  -1.4462 |                    -2.9979 | False         |
| coarse  | soc0.25_next_task_energy0.75_idle0.00_deadline0.00 | 0.2500 |             0.7500 | 0.0000 |     0.0000 |                -13.4349 |                    1.0265 |                  -1.3002 |                    -2.2247 | False         |
| coarse  | soc0.25_next_task_energy0.50_idle0.00_deadline0.25 | 0.2500 |             0.5000 | 0.0000 |     0.2500 |                -15.3711 |                    1.1531 |                  -1.6402 |                    -3.0452 | False         |
| coarse  | soc0.25_next_task_energy0.25_idle0.50_deadline0.00 | 0.2500 |             0.2500 | 0.5000 |     0.0000 |                -16.3752 |                    1.2082 |                  -3.1298 |                    -8.9343 | False         |
| coarse  | soc0.50_next_task_energy0.25_idle0.00_deadline0.25 | 0.5000 |             0.2500 | 0.0000 |     0.2500 |                 -9.0490 |                    1.3578 |                  -1.0704 |                    -2.3916 | False         |
| coarse  | soc0.75_next_task_energy0.25_idle0.00_deadline0.00 | 0.7500 |             0.2500 | 0.0000 |     0.0000 |                 -7.2388 |                    1.5613 |                  -0.8716 |                    -1.9930 | False         |
| coarse  | soc0.25_next_task_energy0.50_idle0.25_deadline0.00 | 0.2500 |             0.5000 | 0.2500 |     0.0000 |                -15.6524 |                    1.6918 |                  -2.2055 |                    -5.1438 | False         |

## Selected C4-C3 paired 95% CIs
| phase   | weight_id                                          | scenario                    | metric         |   mean_difference |   median_difference |   ci95_low |   ci95_high |   paired_replications | direction       |   C4_low_soc_stops_total |   C4_failure_count_total |    soc |   next_task_energy |   idle |   deadline |
|:--------|:---------------------------------------------------|:----------------------------|:---------------|------------------:|--------------------:|-----------:|------------:|----------------------:|:----------------|-------------------------:|-------------------------:|-------:|-------------------:|-------:|-----------:|
| coarse  | soc0.75_next_task_energy0.00_idle0.00_deadline0.25 | primary                     | delay          |           -1.9466 |             -0.9372 |    -3.6509 |     -0.2423 |                    50 | negative_better |                   0.0000 |                        0 | 0.7500 |             0.0000 | 0.0000 |     0.2500 |
| coarse  | soc0.75_next_task_energy0.00_idle0.00_deadline0.25 | primary                     | urgent_on_time |           -0.1008 |              0.0000 |    -0.2480 |      0.0465 |                    50 | positive_better |                   0.0000 |                        0 | 0.7500 |             0.0000 | 0.0000 |     0.2500 |
| coarse  | soc0.75_next_task_energy0.00_idle0.00_deadline0.25 | stress_near_transition      | delay          |           -0.1174 |              0.0000 |    -0.5275 |      0.2927 |                    50 | negative_better |                   0.0000 |                        0 | 0.7500 |             0.0000 | 0.0000 |     0.2500 |
| coarse  | soc0.75_next_task_energy0.00_idle0.00_deadline0.25 | stress_near_transition      | urgent_on_time |           -0.1253 |              0.0000 |    -0.3249 |      0.0742 |                    50 | positive_better |                   0.0000 |                        0 | 0.7500 |             0.0000 | 0.0000 |     0.2500 |
| coarse  | soc0.75_next_task_energy0.00_idle0.00_deadline0.25 | stress_non_binding          | delay          |           -0.0001 |             -0.0000 |    -0.0001 |     -0.0000 |                    50 | negative_better |                   0.0000 |                        0 | 0.7500 |             0.0000 | 0.0000 |     0.2500 |
| coarse  | soc0.75_next_task_energy0.00_idle0.00_deadline0.25 | stress_non_binding          | urgent_on_time |            0.0000 |              0.0000 |     0.0000 |      0.0000 |                    50 | positive_better |                   0.0000 |                        0 | 0.7500 |             0.0000 | 0.0000 |     0.2500 |
| coarse  | soc0.75_next_task_energy0.00_idle0.00_deadline0.25 | stress_strongly_constrained | delay          |           -2.0987 |             -2.0776 |    -3.5031 |     -0.6942 |                    50 | negative_better |                   0.0000 |                        0 | 0.7500 |             0.0000 | 0.0000 |     0.2500 |
| coarse  | soc0.75_next_task_energy0.00_idle0.00_deadline0.25 | stress_strongly_constrained | urgent_on_time |           -0.0949 |              0.0000 |    -0.1614 |     -0.0285 |                    50 | positive_better |                   0.0000 |                        0 | 0.7500 |             0.0000 | 0.0000 |     0.2500 |
| coarse  | soc0.75_next_task_energy0.00_idle0.00_deadline0.25 | stress_transition           | delay          |           -0.7462 |             -0.3704 |    -1.3053 |     -0.1871 |                    50 | negative_better |                   0.0000 |                        0 | 0.7500 |             0.0000 | 0.0000 |     0.2500 |
| coarse  | soc0.75_next_task_energy0.00_idle0.00_deadline0.25 | stress_transition           | urgent_on_time |           -0.0321 |              0.0000 |    -0.1419 |      0.0777 |                    50 | positive_better |                   0.0000 |                        0 | 0.7500 |             0.0000 | 0.0000 |     0.2500 |
| local   | soc0.75_next_task_energy0.00_idle0.00_deadline0.25 | primary                     | delay          |           -1.9466 |             -0.9372 |    -3.6509 |     -0.2423 |                    50 | negative_better |                   0.0000 |                        0 | 0.7500 |             0.0000 | 0.0000 |     0.2500 |
| local   | soc0.75_next_task_energy0.00_idle0.00_deadline0.25 | primary                     | urgent_on_time |           -0.1008 |              0.0000 |    -0.2480 |      0.0465 |                    50 | positive_better |                   0.0000 |                        0 | 0.7500 |             0.0000 | 0.0000 |     0.2500 |
| local   | soc0.75_next_task_energy0.00_idle0.00_deadline0.25 | stress_near_transition      | delay          |           -0.1174 |              0.0000 |    -0.5275 |      0.2927 |                    50 | negative_better |                   0.0000 |                        0 | 0.7500 |             0.0000 | 0.0000 |     0.2500 |
| local   | soc0.75_next_task_energy0.00_idle0.00_deadline0.25 | stress_near_transition      | urgent_on_time |           -0.1253 |              0.0000 |    -0.3249 |      0.0742 |                    50 | positive_better |                   0.0000 |                        0 | 0.7500 |             0.0000 | 0.0000 |     0.2500 |
| local   | soc0.75_next_task_energy0.00_idle0.00_deadline0.25 | stress_non_binding          | delay          |           -0.0001 |             -0.0000 |    -0.0001 |     -0.0000 |                    50 | negative_better |                   0.0000 |                        0 | 0.7500 |             0.0000 | 0.0000 |     0.2500 |
| local   | soc0.75_next_task_energy0.00_idle0.00_deadline0.25 | stress_non_binding          | urgent_on_time |            0.0000 |              0.0000 |     0.0000 |      0.0000 |                    50 | positive_better |                   0.0000 |                        0 | 0.7500 |             0.0000 | 0.0000 |     0.2500 |
| local   | soc0.75_next_task_energy0.00_idle0.00_deadline0.25 | stress_strongly_constrained | delay          |           -2.0987 |             -2.0776 |    -3.5031 |     -0.6942 |                    50 | negative_better |                   0.0000 |                        0 | 0.7500 |             0.0000 | 0.0000 |     0.2500 |
| local   | soc0.75_next_task_energy0.00_idle0.00_deadline0.25 | stress_strongly_constrained | urgent_on_time |           -0.0949 |              0.0000 |    -0.1614 |     -0.0285 |                    50 | positive_better |                   0.0000 |                        0 | 0.7500 |             0.0000 | 0.0000 |     0.2500 |
| local   | soc0.75_next_task_energy0.00_idle0.00_deadline0.25 | stress_transition           | delay          |           -0.7462 |             -0.3704 |    -1.3053 |     -0.1871 |                    50 | negative_better |                   0.0000 |                        0 | 0.7500 |             0.0000 | 0.0000 |     0.2500 |
| local   | soc0.75_next_task_energy0.00_idle0.00_deadline0.25 | stress_transition           | urgent_on_time |           -0.0321 |              0.0000 |    -0.1419 |      0.0777 |                    50 | positive_better |                   0.0000 |                        0 | 0.7500 |             0.0000 | 0.0000 |     0.2500 |

## Interpretation
The selection procedure does not choose a single-scenario winner. It prioritizes hard safety and worst-case robustness, then reports paired differences without asserting universal C4 superiority.
