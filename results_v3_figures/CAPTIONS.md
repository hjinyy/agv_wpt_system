# Captions for the four selected main figures

## Figure 1. Base-case saturation and challenge-case separation.
Figure 1 compares the Original Base Case and the Scheduling Challenge Case using 50 common-random-number replications. In the Base Case, C2, C3, and C4 are practically indistinguishable in mean delay (all about 0.20 min), confirming that opportunity charging itself dominates when charging resources and task homogeneity leave little room for priority decisions. In the Challenge Case, the same strategies separate: C2 gives the lowest delay (4.01 min), while C3 and C4 provide much higher urgent-task on-time completion (85.3% and 85.0%). Error bars indicate 95% confidence intervals of the replication mean.

**Why this figure matters.** This is the opening story figure: it prevents overclaiming by showing that C4 is not needed in the easy Base Case, then motivates why the Challenge Case is necessary. It also makes C1's threshold-charging limitation visible without requiring many separate plots.

## Figure 2. Challenge-case trade-off between delay, urgent service, and WPT loss.
Figure 2 plots each strategy in the Challenge Case with mean task delay on the x-axis and urgent-task on-time completion on the y-axis. Point color and size encode WPT energy loss, selected because it directly represents the energy-side consequence of different charging choices while avoiding a cluttered 3D plot. C2 occupies the low-delay region, C3 maximizes urgent-task on-time completion, and C4 lies between them while reducing WPT loss relative to C3. C1 is dominated or nearly dominated because it has both high delay and low urgent-service performance.

**Why this figure matters.** This figure summarizes the main trade-off instead of presenting isolated metrics. It supports the interpretation that C4 is a compromise scheduler, not a universally best scheduler.

## Figure 3. Decision diagnostics explaining why C4 differs from C3.
Figure 3(a) shows that the Challenge Case generated substantial charging contention, with C4 observing an average of 662.6 contention events per replication. C4 selected a different AGV than the C3 low-SOC rule in 50.1% of contention events, confirming that the proposed priority score changed actual scheduling decisions. Figure 3(b) reports the standard deviation of normalized C4 features; E_next, eta_WPT, 1-SOC, and T_idle all have nonzero variance, while D is smaller but nonzero under the urgent-deadline setting. Together, these diagnostics show that C4 had both the opportunity and the information needed to differ from C3.

**Why this figure matters.** Performance differences alone do not prove that the scheduler is doing something different. This figure links the observed outcomes to mechanism: contention plus feature variance plus different decisions.

## Figure 4. C4 advantage region across workload, pad count, and charging power.
Figure 4 maps the stress-grid result as C4 delay improvement over C3, computed as (C3 delay − C4 delay) / C3 delay × 100. Positive cells indicate conditions where C4 reduced mean delay relative to C3, and the parenthesized annotations show the accompanying urgent-task on-time difference in percentage points. The strongest C4 delay gains occur in resource-scarce and heterogeneous operating regions, for example workload=105 tasks/h, pads=1, power=5 kW, where the delay improvement is 22.2%. Where infrastructure is more sufficient or strategies already converge, the additional C4 benefit becomes small.

**Why this figure matters.** This is the design implication figure. It converts many stress-grid runs into a compact answer to “when is the complex scheduler worth using?”
