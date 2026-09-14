# Table 1. Final DES performance under stochastic task arrivals

| Scenario | Strategy | n | Mean delay [min] | Urgent on-time [%] | Completion [%] | WPT loss [kWh] |
| --- | --- | --- | --- | --- | --- | --- |
| Base Case | C1 | 50 | 1.10 ± 0.13 | N/A | 99.77 ± 0.04 | 5.12 ± 0.06 |
| Base Case | C2 | 50 | 0.20 ± 0.01 | N/A | 99.80 ± 0.03 | 9.21 ± 0.07 |
| Base Case | C3 | 50 | 0.20 ± 0.01 | N/A | 99.80 ± 0.03 | 9.18 ± 0.07 |
| Base Case | C4 | 50 | 0.20 ± 0.01 | N/A | 99.80 ± 0.03 | 9.18 ± 0.07 |
| Base Case | C5 | 50 | 0.20 ± 0.01 | N/A | 99.80 ± 0.03 | 8.98 ± 0.08 |
| Primary Challenge | C1 | 50 | 6.25 ± 1.37 | 55.20 ± 2.67 | 99.55 ± 0.08 | 7.01 ± 0.14 |
| Primary Challenge | C2 | 50 | 4.78 ± 1.53 | 72.37 ± 3.11 | 98.54 ± 0.46 | 8.05 ± 0.21 |
| Primary Challenge | C3 | 50 | 7.35 ± 3.66 | 84.90 ± 2.28 | 97.00 ± 1.34 | 7.11 ± 0.46 |
| Primary Challenge | C4 | 50 | 7.53 ± 3.29 | 83.33 ± 2.64 | 96.79 ± 1.19 | 7.50 ± 0.44 |
| Primary Challenge | C5 | 50 | 7.63 ± 3.18 | 82.09 ± 2.92 | 96.69 ± 1.09 | 7.63 ± 0.43 |

Note. Values are mean ± two-sided 95% t confidence-interval half-width across n=50 independent replications (df=49; seeds 4007–4056). Base Case uses an urgent-task ratio of 0, so urgent on-time completion is not applicable. Task arrivals follow the Poisson process configured for each scenario. All strategies had zero actual low-SOC stops, infeasible MILP calls, and simulation failures.
