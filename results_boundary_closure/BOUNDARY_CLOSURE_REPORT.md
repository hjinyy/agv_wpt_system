# C4/C5 Lower-Boundary Closure Report

## Scope
Only the specified C4 and C5 lower-boundary parameter sets were evaluated. DES architecture, strategy logic, WPT model, task generation, safety rules, scenario, and metrics were unchanged.

## CRN protocol
All candidates used the same 50 seeds: 3007-3056. Paired differences are candidate minus baseline; negative delay and positive urgent on-time favor the candidate.

## C4 lower-boundary result
C4 lower boundary is closed. Frozen C4: `{'w1': 0.55, 'w2': 0.175, 'w3': 0.105, 'w4': 0.07, 'w5': 0.1}`.
| w1 | w2 | w3 | w4 | w5 | mean_delay | urgent_on_time_rate | safety_violation_count |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0.55 | 0.15 | 0.09 | 0.06 | 0.15 | 13.85113424702132 | 79.24685226779027 | 0 |
| 0.55 | 0.175 | 0.105 | 0.07 | 0.1 | 13.359315016382942 | 79.17898534033534 | 0 |
| 0.55 | 0.2 | 0.12 | 0.08 | 0.05 | 13.39740182953452 | 79.01496517975474 | 0 |
| 0.55 | 0.225 | 0.135 | 0.09 | 0.0 | 13.81076078263531 | 78.7540044575118 | 0 |

## C5 lower-boundary result
C5 lower boundary is closed. Frozen C5: `{'lambda_soc': 2.0, 'lambda_task': 1.5, 'lambda_kpi': 1.5}`.
| lambda_soc | lambda_task | lambda_kpi | mean_delay | urgent_on_time_rate | infeasible_count | simulation_failure_count |
| --- | --- | --- | --- | --- | --- | --- |
| 2.0 | 1.0 | 1.5 | 11.791574748111874 | 78.4019089875362 | 0 | 0 |
| 2.0 | 1.25 | 1.5 | 11.801380465903973 | 78.38366490252918 | 0 | 0 |
| 2.0 | 1.5 | 1.0 | 12.404277406121913 | 77.8173957178094 | 0 | 0 |
| 2.0 | 1.5 | 1.25 | 12.461739779210145 | 78.35618579802399 | 0 | 0 |
| 2.0 | 1.5 | 1.5 | 11.77853136912135 | 78.37015138901566 | 0 | 0 |

## Paired 95% confidence intervals
| comparison | metric | mean_difference | ci95_low | ci95_high | improved_replication_rate | paired_replications |
| --- | --- | --- | --- | --- | --- | --- |
| C4_C4Parameters(w1=0.55, w2=0.225, w3=0.135, w4=0.09, w5=0.0)_minus_baseline | mean_delay | 0.45144576625236593 | -0.07173460568625806 | 0.97462613819099 | 24.0 | 50 |
| C4_C4Parameters(w1=0.55, w2=0.225, w3=0.135, w4=0.09, w5=0.0)_minus_baseline | urgent_on_time_rate | -0.4249808828235635 | -0.8825710875636736 | 0.032609321916546585 | 20.0 | 50 |
| C4_C4Parameters(w1=0.55, w2=0.2, w3=0.12, w4=0.08, w5=0.05)_minus_baseline | mean_delay | 0.03808681315157655 | -0.5326015564915068 | 0.6087751827946599 | 28.000000000000004 | 50 |
| C4_C4Parameters(w1=0.55, w2=0.2, w3=0.12, w4=0.08, w5=0.05)_minus_baseline | urgent_on_time_rate | -0.16402016058060012 | -0.6001680995205665 | 0.2721277783593662 | 22.0 | 50 |
| C4_C4Parameters(w1=0.55, w2=0.175, w3=0.105, w4=0.07, w5=0.1)_minus_baseline | mean_delay | 0.0 | 0.0 | 0.0 | 0.0 | 50 |
| C4_C4Parameters(w1=0.55, w2=0.175, w3=0.105, w4=0.07, w5=0.1)_minus_baseline | urgent_on_time_rate | 0.0 | 0.0 | 0.0 | 0.0 | 50 |
| C4_C4Parameters(w1=0.55, w2=0.15, w3=0.09, w4=0.06, w5=0.15)_minus_baseline | mean_delay | 0.4918192306383784 | -0.04961837178221751 | 1.0332568330589744 | 22.0 | 50 |
| C4_C4Parameters(w1=0.55, w2=0.15, w3=0.09, w4=0.06, w5=0.15)_minus_baseline | urgent_on_time_rate | 0.06786692745490897 | -0.4959134969382979 | 0.6316473518481158 | 32.0 | 50 |
| C5_C5Parameters(lambda_soc=2.0, lambda_task=1.25, lambda_kpi=1.5)_minus_baseline | mean_delay | 0.022849096782625793 | -0.023067882302508367 | 0.06876607586775996 | 0.0 | 50 |
| C5_C5Parameters(lambda_soc=2.0, lambda_task=1.25, lambda_kpi=1.5)_minus_baseline | urgent_on_time_rate | 0.013513513513513544 | -0.013642908609854612 | 0.0406699356368817 | 2.0 | 50 |
| C5_C5Parameters(lambda_soc=2.0, lambda_task=1.0, lambda_kpi=1.5)_minus_baseline | mean_delay | 0.013043378990523777 | -0.0362454668046525 | 0.06233222478570005 | 4.0 | 50 |
| C5_C5Parameters(lambda_soc=2.0, lambda_task=1.0, lambda_kpi=1.5)_minus_baseline | urgent_on_time_rate | 0.03175759852052437 | -0.007299743651484052 | 0.0708149406925328 | 6.0 | 50 |
| C5_C5Parameters(lambda_soc=2.0, lambda_task=1.5, lambda_kpi=1.5)_minus_baseline | mean_delay | 0.0 | 0.0 | 0.0 | 0.0 | 50 |
| C5_C5Parameters(lambda_soc=2.0, lambda_task=1.5, lambda_kpi=1.5)_minus_baseline | urgent_on_time_rate | 0.0 | 0.0 | 0.0 | 0.0 | 50 |
| C5_C5Parameters(lambda_soc=2.0, lambda_task=1.5, lambda_kpi=1.25)_minus_baseline | mean_delay | 0.683208410088793 | -0.3447505119029195 | 1.7111673320805054 | 24.0 | 50 |
| C5_C5Parameters(lambda_soc=2.0, lambda_task=1.5, lambda_kpi=1.25)_minus_baseline | urgent_on_time_rate | -0.013965590991693233 | -1.2039225709585533 | 1.175991388975167 | 26.0 | 50 |
| C5_C5Parameters(lambda_soc=2.0, lambda_task=1.5, lambda_kpi=1.0)_minus_baseline | mean_delay | 0.6257460370005673 | -0.36334552655001373 | 1.6148376005511484 | 26.0 | 50 |
| C5_C5Parameters(lambda_soc=2.0, lambda_task=1.5, lambda_kpi=1.0)_minus_baseline | urgent_on_time_rate | -0.5527556712062723 | -1.7960116111465938 | 0.6905002687340492 | 16.0 | 50 |

## Decision rule
A lower candidate could replace the current candidate only when it had zero actual low-SOC stops, zero infeasibility, zero simulation failures, better mean delay and urgent on-time rate, and both paired 95% intervals supported improvement. Otherwise, the current candidate was retained.

## Freeze scope
Only C4/C5 parameter closure was performed. No final C1-C5 comparison, Base Case, Stress Grid, or figure regeneration was run.