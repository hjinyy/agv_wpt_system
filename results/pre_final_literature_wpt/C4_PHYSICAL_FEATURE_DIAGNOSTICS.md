# C4 Physical-Feature Diagnostics

## Frozen C4

```text
w_SOC = 0.00
w_E = 0.70
w_idle = 0.00
w_P = 0.00
w_D = 0.30
```

The selected robust Pareto candidate assigns zero weight to the predicted charging-power-quality feature. This was not constrained: non-negative simplex weights were permitted to be zero. Under these frozen operating conditions, the result means the physical condition input did not add marginal priority-ranking value beyond next-task energy and deadline-risk information; it does **not** imply that WPT condition variability is absent from actual delivered-power, SOC, and loss physics.

## Feature variation

`f_P` varied in every representative condition. Mean per-decision `f_P` standard deviation was 0.0107 (non-binding good), 0.0358 (near-transition good), 0.0922 (moderately constrained moderate), 0.0745 (strongly constrained severe), and 0.1099 (strongly constrained moderate). Contention-only values were larger: 0.0731, 0.0745, 0.1914, 0.1550, and 0.2007, respectively.

## Ranking counterfactual

The full-C4 versus `w_P`-removed counterfactual changed 0% of selections overall and 0% of contention selections because the frozen selected coefficient is exactly zero. The diagnostic is therefore internally consistent.

C4 decision diagnostics also record each C3 baseline choice and C4 choice (`c4_decision_diagnostics.csv`, `different` field) for direct selection-change analysis.

## Predicted versus realized charging power

Perfect-prediction Good scenarios had 0 MAE/RMSE/bias. For the controlled moderate-error cases, charging-power MAE was 0.267–0.284 kW, RMSE 0.515–0.543 kW, and mean bias -0.044 to +0.051 kW. These are controlled prediction-error sensitivity results, not empirical estimator-performance claims.

## Ablation

`c4_ablation_results.csv` includes Full C4, No-P (renormalized), SOC-only/C3-equivalent, and No-deadline results on the tuning block only. Full and No-P are identical as expected from `w_P=0`. No-deadline is retained to isolate deadline-feature contribution.
