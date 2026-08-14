# Improved Contribution Figure Captions

## Figure 1. SOC time-series after SOC-urgency correction
This 48-hour representative Challenge-style run increases the C4 SOC-urgency weight as suggested and shows AGV 1 SOC trajectories for C1, C2, and C4. The longer horizon is used to check whether SOC collapses or approaches a stable operating band. C1 still exhibits deep saw-tooth charging behavior, whereas C2 and the SOC-aware C4 avoid prolonged deep discharge. This figure is for presentation of the corrected SOC-control behavior; the changed C4 weights are disclosed rather than tuned secretly.

## Figure 2. Delay boxplot in a C4-advantage stress region
The boxplot uses the full V2 stress-grid condition where C4 showed a clear delay advantage over C3: 105 tasks/h, 2 pads, and 5 kW. This condition is still resource-stressed but not completely infeasible, so priority scheduling differences are visible without making every strategy collapse. Boxes summarize 50 common-random-number replications, with throughput annotated above each strategy.

## Figure 3. Minimum WPT pad heatmap under tightened energy assumptions
The heatmap repeats the infrastructure-sizing logic under a more demanding energy model: 2 kWh battery, 0.30 kWh/km traction energy, and 0.10 kW auxiliary load. Cell values are the smallest WPT pad counts satisfying mean completion rate ≥99% and zero stoppage in at least 95% of replications. This sensitivity figure avoids the previous all-1-pad flattening and shows how design requirements increase with workload and AGV count.

## Figure 4. Corrected WPT efficiency ablation
Both scheduler variants experience the same realized variable WPT efficiency. The Fixed scheduler assumes η=90% when prioritizing candidates, while the Variable scheduler uses the predicted candidate-specific efficiency before allocation. This corrected setup tests the actual value of efficiency awareness rather than comparing fixed-realized and variable-realized physical environments.
