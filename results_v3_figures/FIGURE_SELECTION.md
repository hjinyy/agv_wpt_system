# Main Figure Selection for V3

## Data sources used

The four main figures were regenerated from V2 CSV outputs without changing the underlying simulation results. The inputs were:

- `results_v2/base_case_runs.csv` for Original Base Case strategy metrics.
- `results_v2/challenge_runs.csv` for Primary Challenge strategy metrics.
- `results_v2/stress_grid.csv` for workload × pad × power design-region analysis.
- `results_v2/priority_features.csv` for aggregated C4 feature variance diagnostics.
- `results_v2/priority_features_raw_sample.csv` only for traceability of feature distributions; the main plotted Figure 3(b) uses aggregated standard deviations.
- `results_v2/decision_diagnostics.csv` for contention-event and C4-vs-C3 different-decision diagnostics.

All bars and points represent means across 50 replications. Where error bars are shown, they are 95% confidence intervals of the replication mean, which is more appropriate than raw standard deviation for publication figures focused on comparing expected strategy performance.

## Why exactly these four figures were selected

The requested paper/presentation story has four logical claims, so the main figure set was limited to one figure per claim:

1. **Figure 1 — Problem motivation and base/challenge contrast.** It shows that the Base Case mainly proves the value of opportunity charging, while the Challenge Case creates meaningful separation among C2, C3, and C4. This prevents the paper from implying that C4 must always dominate.
2. **Figure 2 — Trade-off summary.** It condenses the Challenge Case into a Pareto-style view: C2 is delay-oriented, C3 is urgent-deadline-oriented, and C4 is a compromise with energy implications.
3. **Figure 3 — Mechanistic diagnosis.** It demonstrates that C4 really made different decisions from C3 and that the score inputs had nonzero variance. This supports the scheduler contribution rather than just reporting output metrics.
4. **Figure 4 — Operating-region/design implication.** It shows when C4 is useful across workload, pad count, and power, supporting the “resource scarcity + task heterogeneity” conclusion.

Together these four figures form a compact story: Base Case convergence → Challenge trade-off → C4 decision mechanism → C4 advantage region.

## Figures intentionally not selected as main figures

Several V2 figures were not carried into the main paper set:

- Separate one-metric bar charts for completion rate, low-SOC stoppage, charging waiting time, and pad utilization were omitted because they fragment the story and repeat information captured in Figures 1–2.
- Individual workload-vs-delay, workload-vs-urgent-rate, pad-count, and power line plots were replaced by Figure 4, which integrates the full stress grid more efficiently.
- Full feature-distribution plots and raw decision-event plots were reduced to Figure 3's diagnostic panels because the paper needs mechanism evidence, not every diagnostic trace.
- Large task-level or AGV-level trajectory plots were omitted from the main set because they are useful for validation but less central to the proposed scheduler argument.

## Is the four-figure main story sufficient?

Yes. The four selected figures are sufficient for the main paper/presentation because each directly supports one of the four core messages and avoids redundant metric-by-metric plotting. The set also makes the negative/conditional finding clear: C4 is not universally superior, and its value appears when contention and heterogeneity exist.

## Supplementary figure candidates, if absolutely needed

Keep the main figure count at four. If supplementary material is allowed, only these two additions are recommended:

1. **Supplementary Figure S1 — Full ablation matrix.** Equal vs variable distance, 0% vs 20% urgent tasks, and fixed vs variable eta, shown as compact grouped bars for delay, urgent on-time, and WPT loss. This would support feature-contribution claims without overloading the main paper.
2. **Supplementary Figure S2 — SOC and pad-utilization validation traces.** A representative Challenge Case run showing SOC trajectories and pad occupancy. This would reassure readers that the finite-horizon simulation and charging quantum dynamics are physically reasonable.
