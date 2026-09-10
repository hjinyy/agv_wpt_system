# C4/C5 Parameter Refinement Report

## 1. Scope and fixed components
Only the C4 priority weights and C5 objective coefficients were changed. The DES, C1-C5 strategy structures, WPT state model, 15-minute rolling horizon, 60-second slot, first-slot execution, MILP constraints, scenario, task generation, and KPI definitions were retained.

## 2. C5 common-scale scan and boundary check
The common scale scan evaluated alpha in [1.0, 1.5, 2.0, 2.5, 3.0, 4.0] with 50 replications each. Boundary extension to alpha=5 and 6 was not triggered, because alpha=4 was not the joint mean-delay/urgent-on-time leader in the initially tested range.
| parameters | mean_delay | urgent_on_time_rate |
| --- | --- | --- |
| lambda_soc=1.00, lambda_task=1.00, lambda_kpi=1.00 | 12.4202 | 77.9799 |
| lambda_soc=1.50, lambda_task=1.50, lambda_kpi=1.50 | 11.8375 | 78.4199 |
| lambda_soc=2.00, lambda_task=2.00, lambda_kpi=2.00 | 12.0295 | 78.4065 |
| lambda_soc=2.50, lambda_task=2.50, lambda_kpi=2.50 | 12.4609 | 78.8517 |
| lambda_soc=3.00, lambda_task=3.00, lambda_kpi=3.00 | 11.9509 | 79.5835 |
| lambda_soc=4.00, lambda_task=4.00, lambda_kpi=4.00 | 12.6707 | 79.3194 |

## 3. C5 one-at-a-time refinement
OAT points changed one C5 scale at a time around the selected common-scale alpha. The locally refined C5 candidate is `lambda_soc=2.00, lambda_task=1.50, lambda_kpi=1.50`.

## 4. C4 local refinement
The local C4 grid was evaluated with 50 CRN-matched replications. Extension to w1=0.75/0.80 was not triggered. The locally refined C4 candidate is `w1=0.55, w2=0.17, w3=0.10, w4=0.07, w5=0.10`.

## 5. Safety interpretation
Hard rejection required zero MILP infeasibility, zero simulation failures, and zero actual low-SOC stops. Critical-SOC crossings are reported as preventive-rule activations and were not used as automatic disqualification.

## 6. Pareto interpretation
Safe C5 Pareto candidates: lambda_soc=1.50, lambda_task=1.50, lambda_kpi=1.50, lambda_soc=3.00, lambda_task=3.00, lambda_kpi=3.00, lambda_soc=1.00, lambda_task=1.50, lambda_kpi=1.50, lambda_soc=1.50, lambda_task=1.50, lambda_kpi=1.50, lambda_soc=1.50, lambda_task=2.00, lambda_kpi=1.50, lambda_soc=2.00, lambda_task=1.50, lambda_kpi=1.50.
Safe C4 Pareto candidates: w1=0.50, w2=0.12, w3=0.07, w4=0.05, w5=0.25, w1=0.55, w2=0.17, w3=0.10, w4=0.07, w5=0.10, w1=0.65, w2=0.05, w3=0.03, w4=0.02, w5=0.25.

## 7. Replication-wise paired uncertainty
Paired differences are new minus old, using the same seed for each member of a pair. Negative delay differences and positive urgent-on-time differences favor the refined candidate.
| comparison | metric | mean_difference | ci95_low | ci95_high | improved_replication_rate | paired_replications |
| --- | --- | --- | --- | --- | --- | --- |
| refined_C5_minus_old_C5_2_2_2 | mean_delay | -0.2509469173407942 | -1.0174232914655452 | 0.5155294567839568 | 22.0 | 50 |
| refined_C5_minus_old_C5_2_2_2 | urgent_on_time_rate | -0.03636412938301703 | -1.0327570730430582 | 0.9600288142770241 | 14.000000000000002 | 50 |
| refined_C5_minus_original_C5_1_1_1 | mean_delay | -0.6416626338356802 | -1.706142295678637 | 0.4228170280072764 | 42.0 | 50 |
| refined_C5_minus_original_C5_1_1_1 | urgent_on_time_rate | 0.3902501767140981 | -0.8737176436059574 | 1.6542179970341535 | 28.000000000000004 | 50 |
| refined_C4_minus_old_C4 | mean_delay | -0.26707295258314434 | -0.7552623024405973 | 0.2211163972743087 | 28.000000000000004 | 50 |
| refined_C4_minus_old_C4 | urgent_on_time_rate | -0.7841128330659747 | -1.3584501359992323 | -0.209775530132717 | 8.0 | 50 |

## 8. Selection rationale
Selection was restricted to safe solutions and Pareto comparisons. Where effects were practically close, proximity to the previous parameterization was preferred; no arbitrary composite score was used.

## 9. Frozen parameters
Only the selected C4 and C5 parameter values are frozen in `final_frozen_parameters.json`. A final independent-seed C1-C5 evaluation was not run in this refinement experiment.

## 10. Limitation
These conclusions apply to the tested/refined parameter range and this fixed DES scenario. They are not a claim of a global optimum.