# Improved Contribution Figures

These figures respond to the four issues identified in the review:

1. **C4 SOC stability:** Figure 1 uses a 48-hour horizon and a disclosed SOC-urgency weight increase for C4.
2. **C4 vs C2 discriminability:** Figure 2 uses a C4-advantage stress region from the full V2 grid (105 tasks/h, 2 pads, 5 kW), not a cherry-picked replication.
3. **Infrastructure heatmap flattening:** Figure 3 uses a tighter energy sensitivity setting (2 kWh battery, 0.30 kWh/km, 0.10 kW auxiliary) to reveal pad-count gradients.
4. **Efficiency ablation logic:** Figure 4 corrects the comparison so both cases experience realized variable efficiency; only scheduler knowledge differs.

The scripts do not delete or overwrite previous `results/`, `results_v2/`, `results_v3_figures/`, or `results_v4_contribution_figures/` outputs.
