# Final Figure Statistical Conventions

All final figures use 50 independent DES replications (seeds 4007--4056). Task arrivals are Poisson stochastic inputs.

- Figures 1--5 show the requested mean-performance comparisons without uncertainty overlays.
- Figure 6 is the dedicated replication-uncertainty figure. It reports the replication mean plus a two-sided 95% t confidence interval (df=49).
- `paired_statistics.csv` contains the paired 95% confidence intervals for C3/C4/C5 comparisons.
- `figure_statistics.csv` stores the corresponding mean, sample standard deviation, replication count, and 95% confidence-interval half-width.

Figure 5 uses a separately executed active-objective ablation: the frozen C5 full objective is compared with SOC, task, and KPI-risk terms removed one at a time under common random numbers. The archived `c5_priority_weight` ablation is not used because that coefficient is not an active C5 objective term.
