# [3]-Based WPT Unseen Final Evaluation

## Scope and provenance

- **One-time final CRN seeds:** `8007–8056` (50 replications).
- **Frozen pre-final archive:** `archive/pre-literature-wpt-final-20260929` at `ba0e487ff731bd4fe75f21cd4e4048764ac50374`.
- **Final-execution code:** `54ee172146a0ccbd1af25fe729e90d0e25e7ca67`.
- The physical input is the experimentally supported [3] X/Y-averaged charging-condition table. The 3-kW-normalized delivered charging power is distinct from efficiency/loss accounting.
- C4/C5 were not retuned in this stage. C4 weights: SOC 0.00, next-task energy 0.70, idle 0.00, predicted-power quality 0.00, deadline 0.30. C5 scales: lambda_SOC 1.5, lambda_task 1.5, lambda_KPI 2.0.

## Completeness and safety

- Expected/observed replication rows: **1,250 / 1,250** = 5 scenarios × 5 strategies × 50 seeds.
- Every scenario-strategy cell has exactly 50 replications; the raw table contains exactly 50 seeds, `8007` through `8056`.
- Simulation failures: **0**; low-SOC stops: **0**; replication-level solver-infeasible count: **0**.
- C5 logged **166,546** rolling-MILP calls: infeasible 0, fallback 0, bounded-solve time-limit hits 87. C5 is a rolling-horizon MILP reference, not a global optimum.

## C4 versus C3 paired final comparison

Negative delay difference means C4 has lower delay. Positive urgent-on-time difference means C4 has higher urgent on-time rate. BH correction covers these ten C4–C3 paired tests.

| Scenario | Metric | C4−C3 mean difference | 95% CI | BH-adjusted p | Interpretation |
|---|---|---:|---|---:|---|
| non_binding_good | Mean delay (s) | 0.000 | [-0.000, 0.000] | 0.891 | no resolved paired difference |
| non_binding_good | Urgent on-time rate (pp) | -0.005 | [-0.016, 0.005] | 0.460 | no resolved paired difference |
| near_transition_good | Mean delay (s) | -52.300 | [-63.656, -40.944] | 6.16e-12 | C4 lower |
| near_transition_good | Urgent on-time rate (pp) | -3.084 | [-3.641, -2.526] | 2.73e-14 | C4 lower |
| moderately_constrained_moderate | Mean delay (s) | -26.072 | [-92.732, 40.587] | 0.545 | no resolved paired difference |
| moderately_constrained_moderate | Urgent on-time rate (pp) | -2.438 | [-2.916, -1.961] | 2.87e-13 | C4 lower |
| strongly_constrained_severe | Mean delay (s) | -1726.679 | [-4277.881, 824.523] | 0.300 | no resolved paired difference |
| strongly_constrained_severe | Urgent on-time rate (pp) | -1.384 | [-1.718, -1.050] | 1.23e-10 | C4 lower |
| strongly_constrained_moderate | Mean delay (s) | -6.447 | [-100.241, 87.348] | 0.891 | no resolved paired difference |
| strongly_constrained_moderate | Urgent on-time rate (pp) | -1.434 | [-1.687, -1.180] | 2.58e-14 | C4 lower |

## Interpretation boundaries

- No universal-winner claim is made. C4 has lower paired mean delay in `near_transition_good`; elsewhere its paired delay CI crosses zero in this final evaluation.
- C4 has lower urgent on-time rate than C3 in all four constrained cases with BH-adjusted significance; the non-binding difference is unresolved. This trade-off is reported rather than hidden.
- The frozen C4 physical-score coefficient is zero by tuning result. The WPT condition model nevertheless remains active for actual delivered power, SOC, input energy, and loss.
- Controlled alignment and prediction-error distributions are sensitivity conditions, not measured AGV-fleet frequencies or a hardware-equivalence claim.

## Artifacts

- `raw/replication_metrics.csv`: final replication-level outcomes.
- `raw/c5_solver_calls.csv.gz`: losslessly compressed final solver records.
- `summary/strategy_summary.csv`: mean and standard deviation by scenario and strategy.
- `statistics/paired_statistics.csv`: same-seed C4–C3 statistics with BH correction.
- `summary/rho_catalog.csv`: frozen scenario/rho context.
- `final_result_manifest.json`: execution, seed, freeze, completeness, and safety provenance.
