# Final Figure Statistical Conventions

All final figures use 50 independent DES replications (seeds 4007--4056). Task arrivals are Poisson stochastic inputs; therefore, point estimates are reported with uncertainty.

- Figures 1--3 report the replication mean plus a two-sided 95% t confidence interval (df=49).
- Figure 4 uses the same 50 common-random-number replications for C3 and C4. Each cell reports the paired mean difference plus its 95% t confidence interval: first line is `C3 - C4` task delay in minutes, and second line is `C4 - C3` urgent on-time rate in percentage points.
- `figure_statistics.csv` stores the corresponding mean, sample standard deviation, replication count, and 95% confidence-interval half-width.

Figure 5 is intentionally not included in the final set. The archived "C5 Objective Ablation" changed `c5_priority_weight`, but the coefficient is not an active C5 objective term in the final implementation. Reusing that figure would not be a valid ablation. A future Figure 5 requires a separately pre-specified ablation of an active objective term and an independent evaluation run.
