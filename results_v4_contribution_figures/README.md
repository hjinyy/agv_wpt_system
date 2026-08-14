# Contribution Figures

This folder contains four requested contribution-oriented figures generated with matplotlib only.

## Generated files

1. `Figure1_SOC_Time_Series.png/pdf` — Contribution 2, SOC trajectory comparison.
2. `Figure2_Delay_Boxplot.png/pdf` — Contribution 2, logistics delay distribution.
3. `Figure3_Minimum_Infrastructure_Heatmap.png/pdf` — Contribution 1, minimum WPT pad guideline.
4. `Figure4_WPT_Efficiency_Ablation.png/pdf` — Contribution 3, fixed vs variable WPT efficiency ablation.

## Data sources

- Figure 1: regenerated representative Challenge Case trace using `v2_runner.py` with common random numbers, seed 1007, AGV 1.
- Figure 2: `results_v2/challenge_runs.csv`.
- Figure 3: `results/design_grid_summary.csv`.
- Figure 4: `results_v2/ablation.csv`.

All plots are saved as PNG at 350 dpi and PDF. Plot-ready CSV extracts are also saved as `plot_data_*.csv`.
